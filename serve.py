#!/usr/bin/env python3
"""
The Unofficial Guide — the same pipeline, over HTTP.

    python serve.py                          run it locally on port 5000
    gunicorn serve:app                       run it the way a host runs it

Nothing new happens in this file. It is a wrapper: a request comes in, it
hands the question to `app.py::ask_pipeline` — the exact function the command
line uses — and hands the answer back as JSON. Retrieval, the relevance gate
and the grounded prompt all still live where they lived. If you change how
your system answers, you change it in those files and this one follows.

Two routes:

    POST /ask       {"question": "..."} in, the answer and its sources out
    GET  /health    is the service up, and is there an index to search

Why this exists: `app.py` runs once and exits, which is fine on your laptop
and impossible to deploy. A hosted service has to stay up and wait for
requests. This is the smallest thing that does that.

⚠️ There is deliberately no logging, no timing and no metrics in this file.
Unit 9 has you build the structured log yourself — the request line, the
timing field everyone skips, the whole instrument-before-you-deploy exercise.
Shipping a logger here would hand you the answer to that. Add yours in unit 9;
this file stays the bare shell until then.
"""

import os
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request

from request_log import log_request

import config
import generate

app = Flask(__name__)

# Answers are cut to this many characters in the log so each line stays readable.
ANSWER_LOG_CHARS = 300


@app.before_request
def start_request():
    g.started_at = time.perf_counter()
    g.request_id = str(uuid.uuid4())


@app.after_request
def record_request(response):
    duration_ms = (
        time.perf_counter() - g.started_at
    ) * 1000

    status = response.status_code

    if status >= 500:
        outcome = "error"
    elif status >= 400:
        outcome = "bad_request"
    elif request.path == "/ask":
        outcome = (
            "refused"
            if getattr(g, "refused", False)
            else "answered"
        )
    else:
        outcome = "completed"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": g.request_id,
        "method": request.method,
        "path": request.path,
        "http_status": status,
        "outcome": outcome,
        "question": getattr(g, "question", None),
        "answer": getattr(g, "answer", None),
        "sources": getattr(g, "sources", None),
        "n_sources": getattr(g, "n_sources", None),
        "best_distance": getattr(g, "best_distance", None),
        "prompt_tokens": getattr(g, "prompt_tokens", None),
        "output_tokens": getattr(g, "output_tokens", None),
        "cache_hit": getattr(g, "cache_hit", None),
        "retrieval_ms": getattr(g, "retrieval_ms", None),
        "generation_ms": getattr(g, "generation_ms", None),
        "duration_ms": round(duration_ms, 2),
        "question_length": getattr(
            g, "question_length", None
        ),
        "error_type": getattr(
            g, "error_type", None
        ),
    }

    log_request(record)
    return response


@app.get("/health")
def health():
    """Is the service up, and is there an index to search?

    Two different questions, and the second one is the one that bites. A
    freshly deployed service answers this route happily while every /ask
    returns "no index" — hosts give you no disk that survives a restart, so
    the index has to be built as part of getting the service up. Checking
    here means you find that out in one request instead of five.
    """
    from store import index_exists

    ready = index_exists(config.CORPUS)
    return jsonify(
        {
            "status": "ok",
            "corpus": config.CORPUS,
            "index_ready": ready,
            "detail": (
                "ready"
                if ready
                else "no index for this corpus — run `python app.py index`"
            ),
        }
    )


@app.post("/ask")
def ask():
    """One question in, one grounded answer out.

    A refused question is a 200, not an error. The gate refusing is your
    system working — it is an answer, and the JSON says so with
    `"refused": true` so whatever calls this can tell the two apart.
    """
    from app import ask_pipeline

    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):
        payload = {}
    question = str(payload.get("question") or "").strip()
    g.question_length = len(question)
    g.question = question or None

    if not question:
        return (
            jsonify(
                {
                    "error": "Send JSON with a question in it, like "
                    '{"question": "is the housing lottery random?"}'
                }
            ),
            400,
        )

    # Token and cache counters in generate.py are running totals for the whole
    # process, so the cost of THIS request is the difference across the call.
    tokens_before = generate.token_counts()
    cache_hits_before = generate._cache_hits

    # Stretch: latency breakdown. ask_pipeline already calls on_gate right after
    # retrieval + the relevance gate, and on_prompt right before the Gemini call,
    # so timing between them splits the request into stages without changing
    # retrieval, the gate or generation.
    marks = {}
    pipeline_start = time.perf_counter()

    try:
        outcome = ask_pipeline(
            question,
            corpus=config.CORPUS,
            on_gate=lambda _decision: marks.setdefault("gate", time.perf_counter()),
            on_prompt=lambda _prompt: marks.setdefault("prompt", time.perf_counter()),
        )
    except Exception as exc:  # noqa: BLE001 — a reader gets this, not a traceback
        g.error_type = type(exc).__name__
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500
    finally:
        pipeline_end = time.perf_counter()
        tokens_after = generate.token_counts()
        g.prompt_tokens = tokens_after["prompt"] - tokens_before["prompt"]
        g.output_tokens = tokens_after["output"] - tokens_before["output"]
        g.cache_hit = generate._cache_hits > cache_hits_before

        # retrieval_ms: embed the question + Chroma search + relevance gate.
        # generation_ms: the Gemini call (0 when the gate refused, since the
        # model is never called). None means that stage was never reached.
        if "gate" in marks:
            g.retrieval_ms = round((marks["gate"] - pipeline_start) * 1000, 2)
            if "prompt" in marks:
                g.generation_ms = round((pipeline_end - marks["prompt"]) * 1000, 2)
            elif "error_type" not in g:
                g.generation_ms = 0.0

    g.refused = outcome["refused"]
    g.answer = (outcome["answer"] or "")[:ANSWER_LOG_CHARS]
    g.sources = outcome["sources"]
    g.n_sources = len(outcome["sources"])
    g.best_distance = round(outcome["best_distance"], 4)

    return jsonify(
        {
            "question": question,
            "answer": outcome["answer"],
            "refused": outcome["refused"],
            "sources": outcome["sources"],
            "best_distance": round(outcome["best_distance"], 4),
            "threshold": outcome["threshold"],
            "corpus": config.CORPUS,
        }
    )


def warm_up() -> None:
    """Load the pipeline's heavy dependencies before the first request arrives.

    Milestone 6 fix. Everything below is otherwise created lazily, inside the
    first /ask, so the first user after a start paid ~1.5 s extra (measured:
    results/capstone_coldstart_before.json). Doing it here moves that cost to
    start-up instead. Nothing about retrieval, the gate or generation changes —
    this only calls the same functions earlier.

    Makes no Gemini API call and writes nothing to the request log. A failure
    here (no index, no API key) is reported and the server still starts, so
    /health and /ask report the problem exactly as they did before this fix.
    """
    print("Warming up (loading index, embedding model and Gemini client)...")
    total_start = time.perf_counter()

    steps = []

    def step(name, fn):
        start = time.perf_counter()
        try:
            fn()
            steps.append(f"{name} {(time.perf_counter() - start) * 1000:.0f} ms")
        except Exception as exc:  # noqa: BLE001 — never block start-up
            steps.append(f"{name} FAILED ({type(exc).__name__}: {exc})")

    def load_pipeline():
        from app import ask_pipeline  # noqa: F401 — the same import /ask does

    def load_retrieval():
        # One real search: opens the Chroma client and collection, and loads the
        # ONNX embedding model (it only loads on the first thing it embeds).
        from store import search

        search("warm-up", corpus=config.CORPUS)

    def load_gemini_client():
        generate._get_client()  # creates the client; sends no request

    step("pipeline import", load_pipeline)
    step("retrieval + embedder", load_retrieval)
    step("Gemini client", load_gemini_client)

    total_ms = (time.perf_counter() - total_start) * 1000
    print(f"Warm-up done in {total_ms:.0f} ms: " + "; ".join(steps) + "\n")


def main():
    # Hosts tell you which port to listen on through PORT, and they expect you
    # on 0.0.0.0. Binding 127.0.0.1 instead works perfectly on your laptop and
    # then answers nothing at all once deployed, because the host's router
    # can't reach a socket that only accepts connections from inside the
    # container. It is the single most common way a first deploy "succeeds"
    # and is unreachable.
    # Defaults to 5001, not 5000: on macOS the AirPlay Receiver already listens
    # on 5000 and answers every request with an empty 403.
    port = int(os.getenv("PORT", "5001"))

    # Debug mode reloads on save, which is handy, and prints a console that
    # runs arbitrary code, which is not something to leave switched on where
    # strangers can reach it. Off unless you ask for it.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    # Load the heavy dependencies now so the first request doesn't pay for them.
    # Only runs under `python serve.py` (the Path B run command); a host running
    # `gunicorn serve:app` never calls main() and would still start cold.
    warm_up()

    print(f"Serving The Unofficial Guide on http://localhost:{port}")
    print(f"Corpus: {config.CORPUS}    (Ctrl-C to stop)\n")
    print("Try it from another terminal:\n")
    print(f"  curl http://localhost:{port}/health")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"question\": \"is the housing lottery random?\"}}'\n"
    )

    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
