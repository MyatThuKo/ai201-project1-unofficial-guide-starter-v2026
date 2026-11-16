"""Measure start-up time and the first request after a fresh server start.

    python measure_cold_start.py --label before
    python measure_cold_start.py --label after

Do NOT have the server running — this script starts it itself, three times.
Each run:

  1. launches `python serve.py` with AI201_CACHE=0 (a brand-new process),
  2. times how long until the port accepts connections  -> startup_ms,
  3. sends ONE /ask — the first request that process ever serves,
  4. reads that request's duration_ms from logs/requests.jsonl -> first_request_ms,
  5. stops the server.

Readiness is checked by opening a TCP connection, NOT by calling /health:
/health opens the Chroma client, which would warm up part of what we are
trying to measure.

Results go to results/capstone_coldstart_<label>.json.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "logs" / "requests.jsonl"
RESULTS_DIR = ROOT / "results"
PORT = int(os.getenv("PORT", "5001"))
QUESTION = "How much does it cost to rent a locker in the commuter lounge for a year?"
RUNS = 3
STARTUP_TIMEOUT_S = 120


def port_open() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def log_line_count() -> int:
    if not LOG_PATH.exists():
        return 0
    with LOG_PATH.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def new_records(since: int) -> list[dict]:
    with LOG_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f.read().splitlines()[since:] if line.strip()]


def one_cold_start(n: int) -> dict:
    env = dict(os.environ, AI201_CACHE="0", PORT=str(PORT))
    env.pop("AI201_DEBUG", None)  # the reloader would start two processes

    launched = time.perf_counter()
    proc = subprocess.Popen(
        [sys.executable, "serve.py"],
        cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    try:
        while not port_open():
            if proc.poll() is not None:
                raise RuntimeError(f"server exited early:\n{proc.stderr.read()}")
            if time.perf_counter() - launched > STARTUP_TIMEOUT_S:
                raise RuntimeError("server did not open the port in time")
            time.sleep(0.05)
        startup_ms = (time.perf_counter() - launched) * 1000

        snapshot = log_line_count()
        request = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/ask",
            data=json.dumps({"question": QUESTION}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        sent = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=120) as r:
                status, body = r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            status, body = e.code, {}
        client_ms = (time.perf_counter() - sent) * 1000

        time.sleep(0.2)  # let the after_request hook finish writing
        records = new_records(snapshot)
        if len(records) != 1:
            raise RuntimeError(f"expected 1 new log record, found {len(records)}")
        rec = records[0]
        result = {
            "run": n,
            "startup_ms": round(startup_ms, 1),
            "first_request_ms": rec.get("duration_ms"),
            "client_round_trip_ms": round(client_ms, 1),
            "status": status,
            "outcome": rec.get("outcome"),
            "cache_hit": rec.get("cache_hit"),
            "prompt_tokens": rec.get("prompt_tokens"),
            "answer": body.get("answer"),
            "log_record": rec,
        }
        print(f"  run {n}: startup {result['startup_ms']:>8.1f} ms   "
              f"first request {result['first_request_ms']:>8.1f} ms   "
              f"(HTTP {status}, {result['outcome']}, cache_hit={result['cache_hit']})")
        return result
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        while port_open():  # wait until the port is free for the next run
            time.sleep(0.1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", required=True, help="before or after")
    args = parser.parse_args()

    out = RESULTS_DIR / f"capstone_coldstart_{args.label}.json"
    if out.exists():
        print(f"{out.name} already exists. Delete it first to re-measure.")
        return 1
    if port_open():
        print(f"Port {PORT} is already in use. Stop the running server first:")
        print(f"  lsof -t -iTCP:{PORT} -sTCP:LISTEN | xargs kill")
        return 1

    print(f"Cold-start measurement ({args.label}), {RUNS} fresh server starts on port {PORT}")
    runs = [one_cold_start(n) for n in range(1, RUNS + 1)]

    first = [r["first_request_ms"] for r in runs]
    startup = [r["startup_ms"] for r in runs]
    summary = {
        "label": args.label,
        "question": QUESTION,
        "first_request_ms": {"values": first, "avg": round(mean(first), 1),
                             "min": min(first), "max": max(first)},
        "startup_ms": {"values": startup, "avg": round(mean(startup), 1),
                       "min": min(startup), "max": max(startup)},
        "runs": runs,
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\n  first request: avg {summary['first_request_ms']['avg']} ms "
          f"(min {min(first)}, max {max(first)})")
    print(f"  startup:       avg {summary['startup_ms']['avg']} ms "
          f"(min {min(startup)}, max {max(startup)})")
    print(f"\nSaved to {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
