"""Send a fixed set of requests to the running service, so a session is repeatable.

    python run_capstone_requests.py

Start the server first (see RUNNING.md). Sends the ten questions below, then
two deliberately bad requests so the session also records the failure path.
Every request is logged by serve.py into logs/requests.jsonl.
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = f"http://localhost:{os.getenv('PORT', '5001')}"
TIMEOUT_SECONDS = 120  # a Gemini call can wait on the rate limiter

QUESTIONS = [
    "Is the housing lottery random?",
    "How much does a storage locker cost?",
    "How much RAM should my laptop have?",
    "When are the quiet times?",
    "How long is the add/drop period?",
    "When do applications open?",
    "What are the application deadlines?",
    "Can students use storage lockers?",
    "What are the laptop requirements?",
    "What is the process for joining the housing lottery?",
    # Two of the Unit 1 test questions, so at least ten get past the gate even
    # though two of the questions above are usually refused.
    "What time is the best to do laundry in the dorms?",
    "How long do I have to change my meal plan?",
]

# Requests that should be rejected, so the log shows the failure path too.
BAD_REQUESTS = [
    ("empty question", {}),
    ("not a JSON object", ["hi"]),
]


def post(body) -> tuple[int, dict]:
    request = urllib.request.Request(
        f"{BASE_URL}/ask",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read() or b"{}")
        except json.JSONDecodeError:
            return error.code, {}


def main() -> int:
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=10) as response:
            health = json.loads(response.read())
    except (urllib.error.URLError, OSError) as error:
        print(f"Can't reach the server at {BASE_URL}: {error}")
        print("Start it first:  AI201_CACHE=0 python serve.py")
        return 1
    if not health.get("index_ready"):
        print(f"Server is up but has no index: {health.get('detail')}")
        return 1

    for i, question in enumerate(QUESTIONS, start=1):
        try:
            status, body = post({"question": question})
        except (urllib.error.URLError, OSError) as error:
            print(f"{i:>2}: request failed: {error}")
            continue
        if status == 200:
            label = "refused" if body.get("refused") else "answered"
        else:
            label = body.get("error", "error")
        print(f"{i:>2}: HTTP {status}  {label:<9} {question}")

    for name, body in BAD_REQUESTS:
        try:
            status, _ = post(body)
            print(f" -: HTTP {status}  ({name})")
        except (urllib.error.URLError, OSError) as error:
            print(f" -: request failed ({name}): {error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
