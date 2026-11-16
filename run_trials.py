"""Run one Milestone 5 trial against the capstone criteria in criteria.md.

    python run_trials.py --trial 1
    python run_trials.py --trial 2
    python run_trials.py --trial 3

Start the server first and leave it running for all three trials (criterion 2
says not to restart between them):

    AI201_CACHE=0 python serve.py

Each trial runs criteria 2, 1, 3 and 5 exactly as criteria.md words them and
writes everything it saw — every HTTP response and every new log line — to
results/capstone_trial_<N>.json, then prints a one-line result per criterion.
Criterion 4 (three fresh clones) is manual; see the note it prints.

This script only *observes* the system. It sends HTTP requests, reads the log
file, and calls scorer.judge(). It changes nothing in serve.py or the pipeline.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from unittest.mock import patch
import urllib.error
import urllib.request

import config
import questions as qs

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "logs" / "requests.jsonl"
RESULTS_DIR = ROOT / "results"
BASE_URL = f"http://localhost:{os.getenv('PORT', '5001')}"

SPACING_SECONDS = 3.0      # criteria 2 and 5: at least three seconds apart
LATENCY_TARGET_MS = 1000   # criterion 2
ANSWER_LOG_CHARS = 300     # serve.py logs the first 300 characters of an answer

IN_SCOPE = qs.answered()                  # the five, in listed order
OUT_OF_SCOPE = qs.OUT_OF_SCOPE[:3]        # criterion 5 names the first three
INVALID_BODIES = [                        # criterion 3, in its listed order
    ("Empty JSON object", {}),
    ("Empty question", {"question": ""}),
    ("Whitespace-only question", {"question": "   "}),
    ("Null question", {"question": None}),
    ("JSON array", []),
]
C1_FIELDS = [
    "timestamp", "request_id", "method", "path", "http_status",
    "question", "answer", "outcome", "duration_ms",
    "prompt_tokens", "output_tokens",
]


# ─── HTTP and log helpers ────────────────────────────────────────────────────

_last_request_at = 0.0


def post_ask(body, paced: bool = True) -> tuple[int, dict]:
    """POST to /ask. When paced, waits so requests are >= SPACING_SECONDS apart."""
    global _last_request_at
    if paced:
        wait = SPACING_SECONDS - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
    request = urllib.request.Request(
        f"{BASE_URL}/ask",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    finally:
        _last_request_at = time.monotonic()
    try:
        return status, json.loads(raw or b"{}")
    except json.JSONDecodeError:
        return status, {"_raw": raw.decode("utf-8", "replace")}


def log_line_count() -> int:
    if not LOG_PATH.exists():
        return 0
    with LOG_PATH.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def new_log_records(since: int) -> list[dict]:
    """Records appended after line number `since` (the snapshot)."""
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open(encoding="utf-8") as f:
        lines = f.read().splitlines()[since:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            out.append({"_invalid_json": line})
    return out


def is_nonneg_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def is_nonneg_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0


# ─── Criterion 2 — warm-request latency ──────────────────────────────────────


def criterion_2() -> dict:
    snapshot = log_line_count()
    warmup_q = IN_SCOPE[0]["question"]
    warmup = post_ask({"question": warmup_q})

    measured = []
    for item in IN_SCOPE * 2:
        measured.append((item["question"], *post_ask({"question": item["question"]})))

    records = new_log_records(snapshot)
    problems = []
    if len(records) != 11:
        problems.append(f"expected 11 new log records (1 warm-up + 10), found {len(records)}")
    measured_records = records[1:]
    durations = [r.get("duration_ms") for r in measured_records]
    if any(not is_nonneg_number(d) for d in durations):
        problems.append("a measured record has no numeric duration_ms")
        avg = None
    else:
        avg = round(mean(durations), 1) if durations else None

    met = not problems and avg is not None and avg <= LATENCY_TARGET_MS
    return {
        "criterion": 2,
        "met": met,
        "average_ms": avg,
        "durations_ms": durations,
        "min_ms": min(durations) if durations and avg is not None else None,
        "max_ms": max(durations) if durations and avg is not None else None,
        "warmup": {"question": warmup_q, "status": warmup[0],
                   "duration_ms": records[0].get("duration_ms") if records else None},
        "problems": problems,
        "responses": [{"question": q, "status": s, "body": b} for q, s, b in measured],
        "log_records": records,
    }


# ─── Criterion 1 — structured logging completeness ───────────────────────────


def criterion_1() -> dict:
    snapshot = log_line_count()
    sent = []
    for item in IN_SCOPE * 2:
        status, body = post_ask({"question": item["question"]})
        sent.append({"question": item["question"], "status": status, "body": body})

    records = new_log_records(snapshot)
    problems = []
    if len(records) != 10:
        problems.append(f"expected exactly 10 new log records, found {len(records)}")

    checks = []
    for i, (req, rec) in enumerate(zip(sent, records), start=1):
        issues = []
        if "_invalid_json" in rec:
            issues.append("not valid JSON")
        else:
            missing = [f for f in C1_FIELDS if f not in rec]
            if missing:
                issues.append(f"missing fields: {missing}")
            if rec.get("question") != req["question"]:
                issues.append("logged question does not match the question sent")
            returned = (req["body"].get("answer") or "")[:ANSWER_LOG_CHARS]
            if rec.get("answer") != returned:
                issues.append("logged answer does not match the returned answer")
            if not is_nonneg_number(rec.get("duration_ms")):
                issues.append("duration_ms is not a nonnegative number")
            for f in ("prompt_tokens", "output_tokens"):
                if not is_nonneg_int(rec.get(f)):
                    issues.append(f"{f} is not a nonnegative integer")
            # "representing actual API usage": a real Gemini call, not a cache hit
            if rec.get("cache_hit") is not False:
                issues.append("cache_hit is not false — tokens don't reflect a real API call")
        checks.append({"n": i, "request_id": rec.get("request_id"), "issues": issues})

    passing = sum(1 for c in checks if not c["issues"])
    met = not problems and passing == 10
    return {
        "criterion": 1,
        "met": met,
        "passing_records": passing,
        "of": 10,
        "problems": problems,
        "checks": checks,
        "responses": sent,
        "log_records": records,
    }


# ─── Criterion 3 — failure-path observability ────────────────────────────────


def criterion_3() -> dict:
    snapshot = log_line_count()
    sent = []
    for name, body in INVALID_BODIES:  # sequential, nothing concurrent
        status, resp = post_ask(body, paced=False)
        sent.append({"name": name, "body": body, "status": status, "response": resp})

    records = new_log_records(snapshot)
    problems = []
    if len(records) != 5:
        problems.append(f"expected exactly 5 new log records, found {len(records)}")

    results = []
    for req, rec in zip(sent, records):  # matched by request order
        ok = (
            req["status"] == 400
            and rec.get("http_status") == 400
            and rec.get("outcome") == "bad_request"
        )
        results.append({"name": req["name"], "status": req["status"],
                        "logged_status": rec.get("http_status"),
                        "logged_outcome": rec.get("outcome"),
                        "request_id": rec.get("request_id"), "pass": ok})

    ids = [r.get("request_id") for r in records]
    if len(set(ids)) != len(ids):
        problems.append("request_id values are not unique")

    # The simulated 500: a unit-test mock of ask_pipeline raising RuntimeError,
    # verified through the argument the mocked log_request() received.
    from serve import app

    with patch("app.ask_pipeline", side_effect=RuntimeError("simulated failure")), \
         patch("serve.log_request") as mock_log:
        response = app.test_client().post(
            "/ask", json={"question": "What is the application deadline?"}
        )
    calls = mock_log.call_count
    record = mock_log.call_args.args[0] if calls else {}
    mock_ok = (
        response.status_code == 500
        and calls == 1
        and record.get("http_status") == 500
        and record.get("outcome") == "error"
        and record.get("error_type") == "RuntimeError"
    )
    simulated = {
        "status": response.status_code,
        "log_request_calls": calls,
        "record": record,
        "pass": mock_ok,
    }

    passing = sum(r["pass"] for r in results) + int(mock_ok)
    met = not problems and passing == 6
    return {
        "criterion": 3,
        "met": met,
        "passing_scenarios": passing,
        "of": 6,
        "problems": problems,
        "invalid_requests": results,
        "simulated_500": simulated,
        "responses": sent,
        "log_records": records,
    }


# ─── Criterion 5 — original RAG behaviour preserved ──────────────────────────


def criterion_5() -> dict:
    from scorer import judge, report
    from store import search

    rows = []
    for item in IN_SCOPE:
        question, expects = item["question"], item["expects"]
        status, body = post_ask({"question": question})
        answer = body.get("answer") or ""
        # Real retrieval, same question and configuration serve.py uses.
        results = search(question, top_k=config.TOP_K, corpus=config.CORPUS)
        verdict = judge(question, expects, answer, results)
        ok = status == 200 and body.get("refused") is False and verdict
        rows.append({
            "kind": "in_scope", "question": question, "expects": expects,
            "status": status, "refused": body.get("refused"), "answer": answer,
            "judge": verdict, "report": report(question, expects, answer, results),
            "pass": ok,
        })

    for question in OUT_OF_SCOPE:
        status, body = post_ask({"question": question})
        ok = status == 200 and body.get("refused") is True
        rows.append({
            "kind": "out_of_scope", "question": question, "status": status,
            "refused": body.get("refused"), "best_distance": body.get("best_distance"),
            "answer": body.get("answer"), "pass": ok,
        })

    passing = sum(r["pass"] for r in rows)
    return {"criterion": 5, "met": passing == 8, "passing": passing, "of": 8, "rows": rows}


# ─── Main ────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trial", type=int, required=True, choices=[1, 2, 3])
    args = parser.parse_args()

    out_path = RESULTS_DIR / f"capstone_trial_{args.trial}.json"
    if out_path.exists():
        print(f"{out_path.name} already exists. Delete it first if you mean to re-run trial {args.trial}.")
        return 1

    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=10) as r:
            health = json.loads(r.read())
    except (urllib.error.URLError, OSError) as error:
        print(f"Can't reach the server at {BASE_URL}: {error}")
        print("Start it first:  AI201_CACHE=0 python serve.py")
        return 1
    if not health.get("index_ready"):
        print(f"Server has no index: {health.get('detail')}")
        return 1
    if config.CACHE_ENABLED:
        print("⚠️  AI201_CACHE is not 0 in THIS shell. That's fine for the runner, but make")
        print("   sure the SERVER was started with AI201_CACHE=0 — criterion 1 checks cache_hit.\n")

    started = datetime.now(timezone.utc).isoformat()
    print(f"Trial {args.trial} — started {started}\n")

    print("Criterion 2 (warm-up + 10 paced requests)…", flush=True)
    c2 = criterion_2()
    print("Criterion 1 (10 paced requests)…", flush=True)
    c1 = criterion_1()
    print("Criterion 3 (5 invalid requests + simulated 500)…", flush=True)
    c3 = criterion_3()
    print("Criterion 5 (5 in-scope + 3 out-of-scope, judged by scorer.judge)…", flush=True)
    c5 = criterion_5()

    trial = {
        "trial": args.trial,
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "model": config.MODEL,
        "threshold": config.THRESHOLD,
        "criteria": {"1": c1, "2": c2, "3": c3, "5": c5},
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(trial, indent=2, default=str), encoding="utf-8")

    def mark(met):
        return "MET   " if met else "MISSED"

    print(f"\nTrial {args.trial} results")
    print(f"  C1 {mark(c1['met'])} {c1['passing_records']}/10 records complete")
    print(f"  C2 {mark(c2['met'])} avg {c2['average_ms']} ms over 10 warm requests "
          f"(min {c2['min_ms']}, max {c2['max_ms']}; target ≤ {LATENCY_TARGET_MS})")
    print(f"  C3 {mark(c3['met'])} {c3['passing_scenarios']}/6 failure scenarios")
    print(f"  C5 {mark(c5['met'])} {c5['passing']}/8 questions")
    print("  C4 manual — one fresh clone per trial, following RUNNING.md")
    for c in (c1, c2, c3):
        for p in c["problems"]:
            print(f"     ⚠️  C{c['criterion']}: {p}")
    for c in c1["checks"]:
        for issue in c["issues"]:
            print(f"     ✗ C1 record {c['n']}: {issue}")
    for r in c5["rows"]:
        if not r["pass"]:
            print(f"     ✗ C5 {r['kind']}: {r['question']}  (status {r['status']}, "
                  f"refused {r['refused']}, judge {r.get('judge')})")
    print(f"\nEverything it saw is in {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
