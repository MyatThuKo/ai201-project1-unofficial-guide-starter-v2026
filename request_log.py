import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "logs" / "requests.jsonl"
_lock = threading.Lock()


def log_request(record: dict) -> None:
    """Append one structured JSON record to the request log.

    Logging must never break a request, so this function never raises:
    - a `ts` (UTC, ISO 8601) is added if the caller didn't supply one
    - the caller's dict is copied, never modified
    - values JSON can't handle (NumPy floats, exceptions, Paths) become strings
    - if the record still can't be serialized, a minimal fallback line is written
    - if the file can't be written, a warning goes to stderr and the request carries on
    """
    try:
        entry = dict(record) if isinstance(record, dict) else {"record": record}
        entry.setdefault("ts", datetime.now(timezone.utc).isoformat())

        try:
            line = json.dumps(entry, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            line = json.dumps(
                {
                    "ts": entry["ts"],
                    "log_error": f"unserializable record: {type(exc).__name__}: {exc}",
                }
            )

        with _lock:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            # One write() of the whole line keeps each record intact.
            with LOG_PATH.open("a", encoding="utf-8") as file:
                file.write(line + "\n")
    except Exception as exc:  # noqa: BLE001 — never let logging fail a request
        print(f"[request_log] failed to write log: {type(exc).__name__}: {exc}", file=sys.stderr)
