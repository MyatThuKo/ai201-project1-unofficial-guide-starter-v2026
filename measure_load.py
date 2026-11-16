"""Stretch: load observation. Same requests, normal rate vs. ~10x the rate.

    python measure_load.py --label baseline --interval 3.0
    python measure_load.py --label load     --interval 0.3

Start the server first and leave it running for both (restart it after any
change to serve.py so the new log fields are present):

    AI201_CACHE=0 python serve.py

Requests are sent on a fixed schedule (one every --interval seconds, each in
its own thread), so at 0.3 s they overlap instead of waiting for each other —
that is what "10x the rate" means for a service. The five in-scope questions
from questions.py are cycled, so every request is a real Gemini call.

Everything is read back from logs/requests.jsonl (new lines only) and saved,
with a summary, to results/capstone_load_<label>.json.
"""

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from statistics import mean, median

import questions as qs

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "logs" / "requests.jsonl"
RESULTS_DIR = ROOT / "results"
BASE_URL = f"http://localhost:{os.getenv('PORT', '5001')}"
QUESTIONS = [q["question"] for q in qs.answered()]


def log_line_count() -> int:
    if not LOG_PATH.exists():
        return 0
    with LOG_PATH.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def new_records(since: int) -> list[dict]:
    with LOG_PATH.open(encoding="utf-8") as f:
        return [json.loads(l) for l in f.read().splitlines()[since:] if l.strip()]


def send(i: int, question: str, out: list) -> None:
    body = json.dumps({"question": question}).encode()
    req = urllib.request.Request(f"{BASE_URL}/ask", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            status = r.status
            payload = json.loads(r.read())
            error = None
    except urllib.error.HTTPError as e:
        status, payload, error = e.code, {}, f"HTTP {e.code}"
    except (urllib.error.URLError, OSError) as e:
        status, payload, error = None, {}, f"{type(e).__name__}: {e}"
    out.append({
        "i": i, "question": question, "status": status, "error": error,
        "refused": payload.get("refused"),
        "client_ms": round((time.perf_counter() - started) * 1000, 1),
    })


def stats(values: list) -> dict | None:
    values = [v for v in values if isinstance(v, (int, float))]
    if not values:
        return None
    ordered = sorted(values)
    p90 = ordered[max(0, int(round(0.9 * len(ordered))) - 1)]
    return {"n": len(values), "avg": round(mean(values), 1), "median": round(median(values), 1),
            "p90": round(p90, 1), "min": round(min(values), 1), "max": round(max(values), 1)}


def overlapping(records: list[dict]) -> int:
    """How many requests were in flight at the same time as at least one other."""
    from datetime import datetime

    spans = []
    for r in records:
        end = datetime.fromisoformat(r["timestamp"]).timestamp()
        spans.append((end - r["duration_ms"] / 1000, end))
    count = 0
    for i, (s1, e1) in enumerate(spans):
        if any(s1 < e2 and s2 < e1 for j, (s2, e2) in enumerate(spans) if j != i):
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", required=True, help="e.g. baseline or load")
    parser.add_argument("--interval", type=float, required=True, help="seconds between request starts")
    parser.add_argument("--count", type=int, default=40, help="requests to send (default 40)")
    args = parser.parse_args()

    out_path = RESULTS_DIR / f"capstone_load_{args.label}.json"
    if out_path.exists():
        print(f"{out_path.name} already exists. Delete it first to re-run.")
        return 1
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=10) as r:
            if not json.loads(r.read()).get("index_ready"):
                print("Server has no index.")
                return 1
    except (urllib.error.URLError, OSError) as e:
        print(f"Can't reach {BASE_URL}: {e}\nStart it first:  AI201_CACHE=0 python serve.py")
        return 1

    snapshot = log_line_count()
    rate = 60 / args.interval
    print(f"{args.label}: {args.count} requests, one every {args.interval} s "
          f"(~{rate:.0f}/min) — about {args.count * args.interval:.0f} s to send…", flush=True)

    client: list = []
    threads = []
    start = time.perf_counter()
    for i in range(args.count):
        target = start + i * args.interval
        delay = target - time.perf_counter()
        if delay > 0:
            time.sleep(delay)
        t = threading.Thread(target=send, args=(i, QUESTIONS[i % len(QUESTIONS)], client))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    wall_s = time.perf_counter() - start
    time.sleep(0.3)  # let the last log lines land

    records = [r for r in new_records(snapshot) if r.get("path") == "/ask"]
    answered = [r for r in records if r.get("outcome") == "answered"]
    errors = [r for r in records if r.get("outcome") in ("error", "bad_request")]
    client_failures = [c for c in client if c["error"] and c["status"] is None]

    summary = {
        "label": args.label,
        "interval_s": args.interval,
        "requests_sent": args.count,
        "target_rate_per_min": round(rate, 1),
        "wall_time_s": round(wall_s, 1),
        "log_records": len(records),
        "outcomes": {o: sum(1 for r in records if r.get("outcome") == o)
                     for o in sorted({r.get("outcome") for r in records})},
        "error_rate": round(len(errors) / len(records), 3) if records else None,
        "client_failures": len(client_failures),
        "duration_ms": stats([r.get("duration_ms") for r in answered]),
        "retrieval_ms": stats([r.get("retrieval_ms") for r in answered]),
        "generation_ms": stats([r.get("generation_ms") for r in answered]),
        "tokens_per_answer": stats([(r.get("prompt_tokens") or 0) + (r.get("output_tokens") or 0)
                                    for r in answered]),
        "cache_hits": sum(1 for r in records if r.get("cache_hit")),
        "overlapping_requests": overlapping(records) if records else 0,
        "error_types": sorted({r.get("error_type") for r in errors if r.get("error_type")}),
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path.write_text(json.dumps({"summary": summary, "client": sorted(client, key=lambda c: c["i"]),
                                    "log_records": records}, indent=2), encoding="utf-8")

    s = summary
    print(f"\n  sent {s['requests_sent']} in {s['wall_time_s']} s | log records {s['log_records']} | "
          f"outcomes {s['outcomes']} | error rate {s['error_rate']} | client failures {s['client_failures']}")
    for key in ("duration_ms", "retrieval_ms", "generation_ms", "tokens_per_answer"):
        v = s[key]
        if v:
            print(f"  {key:<18} avg {v['avg']:>8}  median {v['median']:>8}  p90 {v['p90']:>8}  max {v['max']:>8}")
    print(f"  overlapping requests: {s['overlapping_requests']} of {s['log_records']}"
          + ("  ⚠️ per-request token counts may include other requests' tokens"
             if s['overlapping_requests'] else ""))
    if s["cache_hits"]:
        print(f"  ⚠️ {s['cache_hits']} cache hits — was the server started with AI201_CACHE=0?")
    print(f"\nSaved to {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
