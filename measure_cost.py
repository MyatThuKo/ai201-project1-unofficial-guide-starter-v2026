"""Work out what one request costs, from the structured log.

    python measure_cost.py                                    # logs/requests.jsonl
    python measure_cost.py results/capstone_m3_session.jsonl  # a saved session

Cost is measured, not looked up: token counts come from Gemini's own
usage_metadata (recorded per request by serve.py), and duration is the
server-side time.perf_counter() measurement for each request.

Answered and refused questions are reported separately because they cost very
different amounts: a refusal stops at the relevance gate and never calls Gemini.
Cache hits are excluded from the answered average because they never reach
Gemini either — run the server with AI201_CACHE=0 when measuring.
"""

import json
import sys
from pathlib import Path
from statistics import mean

DEFAULT_LOG = Path(__file__).resolve().parent / "logs" / "requests.jsonl"


def load(path: Path) -> list[dict]:
    records = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"  skipping line {n}: not valid JSON")
    return records


def summarize(label: str, records: list[dict], with_tokens: bool) -> None:
    if not records:
        print(f"{label}: none")
        return
    durations = [r["duration_ms"] for r in records]
    print(f"{label}: {len(records)} requests")
    print(f"  duration  avg {mean(durations):8.1f} ms   "
          f"min {min(durations):8.1f}   max {max(durations):8.1f}")
    if with_tokens:
        prompt = [r.get("prompt_tokens") or 0 for r in records]
        output = [r.get("output_tokens") or 0 for r in records]
        print(f"  tokens    avg {mean(prompt):8.1f} in   "
              f"{mean(output):8.1f} out   {mean(p + o for p, o in zip(prompt, output)):8.1f} total")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LOG
    if not path.exists():
        print(f"No log at {path}. Run the server and some requests first.")
        return 1

    records = load(path)
    ask = [r for r in records if r.get("path") == "/ask"]

    answered = [r for r in ask if r.get("outcome") == "answered"]
    real_answers = [r for r in answered if r.get("cache_hit") is False]
    cached = [r for r in answered if r.get("cache_hit") is True]
    unknown = [r for r in answered if "cache_hit" not in r]
    refused = [r for r in ask if r.get("outcome") == "refused"]
    failed = [r for r in ask if r.get("outcome") in ("bad_request", "error")]

    print(f"Log: {path}  ({len(records)} records, {len(ask)} to /ask)\n")
    summarize("Answered (real Gemini calls)", real_answers, with_tokens=True)
    summarize("Refused (stopped at the gate)", refused, with_tokens=True)
    summarize("Failed (400/500)", failed, with_tokens=False)

    if cached:
        print(f"\n⚠️  {len(cached)} answered request(s) were cache hits and are "
              "excluded. Restart the server with AI201_CACHE=0 to measure them.")
    if unknown:
        print(f"\n⚠️  {len(unknown)} answered record(s) predate the cache_hit field "
              "and can't be trusted for cost. Re-run the session.")
    if len(real_answers) < 10:
        print(f"\n⚠️  Only {len(real_answers)} real answered requests — the brief asks "
              "for an average over ten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
