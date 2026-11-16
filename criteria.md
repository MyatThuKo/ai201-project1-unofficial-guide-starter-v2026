# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**

My 5 test questions come from different advice threads and each has a specific answer in the corpus. I chose 4 of out 5 because retrieval may miss one question depending on how the documents are chunked or how similar the question is to the stored text.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**

The purpose of this system is to answer questions only using the given information from the advice_threads corpus. Thus, every answer produced by the system should have at least source document.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**

The advice_threads corpus contains 23 documents and covers variety of student topics. A few words from the OUT_OF_SCOPE questions could have been similar to the ones inside the documents or slightly similar meaning to a stored chunk. I chose 4 out of 5 becuase I want the relevance gate to reject most unsuppored questions while allowing for one borderline retrieval result.

---

## 4. Something about your chunks

When inspecting 5 sampled chunks, at least 4 of them should contain complete replies or compte thoughts
and should not start or end in the middle of a word or a sentence.

**Why this target:**

The chunker sometimes cuts some advice replies in the middle of sentences or words. Since each advice thread contains short replies, I want the most retrieved chunks to preserve enough of a reply to make sense on its own.

---

## 5. Your choice

For at least 4 out of my 5 test questions, the source named in the answer should actually contain the information used to answer the question.

**Why this target:**

Retrieval can return multiple documents for one question, including documents that are not relevant at all. I chose 4 out of 5 test questions because I want the system to cite the actual document that supports the answer.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->

# Unit 9 — Capstone Acceptance Criteria

## Criterion 1 — Structured Logging Completeness

For each of three independent trials, submit 10 valid HTTP requests to `/ask`, using the five in-scope questions from `questions.py` twice in their listed order.

All 10 requests must produce exactly one valid JSONL record each, with the following fields:

- `timestamp` and `request_id`
- `method`, `path`, and `http_status`
- `question` (input) and `answer` (output)
- `outcome`
- `duration_ms`
- `prompt_tokens` and `output_tokens`

Each record must contain the corresponding question and returned answer. The `duration_ms` value must be a nonnegative number, and token counts must be nonnegative integers representing actual API usage.

All 10 records must pass these checks in each of the three trials.

**Why this target:** The Unofficial Guide relies on retrieval and Gemini to produce answers. Since the relevance gate can refuse a question while returning HTTP 200, the logs must provide enough information to distinguish answers from refusals and measure API consumption. I chose 100% because missing records would make request tracking and cost analysis incomplete.

### Testing Conditions

- Set `AI201_CACHE=0` before starting the service.
- Use the five in-scope questions from `questions.py`,
  repeated twice in their listed order.
- Use the same question set for all three trials.
- Verify exactly 10 new JSONL entries per trial.
- Use a separate log snapshot for each trial to identify
  its records.
- Token counts must reflect actual API usage.

## Criterion 2 — Warm-Request Latency

After one warm-up request, send 10 valid, in-scope questions to `/ask` using the five questions in `questions.py` twice, in their listed order.

The average `duration_ms` for the 10 measured requests must be **1,000 milliseconds (1 second) or less**.

Testing conditions:

- Disable Gemini answer caching by setting `AI201_CACHE=0` before starting the server.
- Start each trial with the service running and the retrieval index loaded.
- Perform one unmeasured warm-up request before each trial.
- Space requests at least three seconds apart to remain below the configured limit of 30 API requests per minute.
- Use the same questions and ordering across all trials.
- Calculate the average from the actual JSONL records, excluding warm-up requests.
- Do not restart the service between trials.
- Use the first in-scope question from `questions.py` as the unmeasured warm-up request.
- The measurement script must pause at least three seconds between requests.
- Include the warm-up request when accounting for the configured rate limit.

All three trials must independently achieve an average of 1,000 milliseconds or less.

**Why this target:** Previous observations showed approximately 2 seconds for the first request and 600 milliseconds for subsequent requests. I chose a 1-second warm-request average because it allows some variation above the observed normal latency while remaining sensitive to meaningful slowdowns. Disabling caching and controlling request pacing prevent cached responses and rate-limit waiting from distorting the measurement.

## Criterion 3 — Failure-Path Observability

Each trial must submit the following five invalid requests to `/ask`:

1. Empty JSON object: `{}`
2. Empty question: `{"question": ""}`
3. Whitespace-only question: `{"question": "   "}`
4. Null question: `{"question": null}`
5. JSON array: `[]`

All five requests must return HTTP 400 and generate exactly one JSONL record each containing:

- `http_status`: `400`
- `outcome`: `bad_request`

Additionally, simulate a `RuntimeError` from `ask_pipeline()` using a unit-test mock.

The simulated failure must return HTTP 500, and the mocked `log_request()` function must receive exactly one record containing:

- `http_status`: `500`
- `outcome`: `error`
- `error_type`: `RuntimeError`

Send the five invalid requests sequentially, with no concurrent requests to the service.

Record the JSONL line count before the trial and inspect only the five newly appended records.

Match each response to its corresponding record using request order.

Verify that every record has a unique `request_id`.

**All six failure scenarios must pass in each of three independent trials.**

**Why this target:** The Unofficial Guide treats relevance-gate refusals as successful HTTP 200 responses. Invalid requests and internal pipeline exceptions must therefore have distinct outcomes so operators can distinguish expected refusals from actual failures. I chose 100% because even one unrecorded failure would weaken the system's observability.

## Criterion 4 — Reproducible Local Execution

Using only the instructions in `RUNNING.md`, the system must start successfully from a clean repository checkout in three independent trials.
Installation or startup warnings do not count as failures unless they prevent a required step from completing successfully.
A trial fails if dependency installation, index creation, service startup, health verification, or the required question-answering request fails.

Each trial must use:

- A separate fresh repository clone.
- A newly created Python 3.13 virtual environment.
- Dependencies installed from `requirements.txt`.
- A newly generated retrieval index.
- API credentials configured according to `RUNNING.md`.

Each trial must verify:

1. Dependencies install without errors.
2. The retrieval index builds successfully.
3. The Flask service starts without errors.
4. `/health` returns HTTP 200 with `index_ready: true`.
5. At least one valid `/ask` request returns HTTP 200 and generates a JSONL log entry.

Shared model-download caches are permitted, but each trial must create its own environment and retrieval index. Record any shared caches and ensure the configured port is available before starting.

**All three trials must pass.**

**Why this target:** A fresh checkout lacks the local `.env` file, ChromaDB index, and installed Python dependencies. Successfully running the system from the original development directory does not prove another developer can reproduce it. Three separate clean setups provide evidence that the documented startup procedure is complete and repeatable.

## Criterion 5 — Original RAG Behavior Preservation

Across three independent trials, evaluate the following eight questions using the existing HTTP `/ask` endpoint.

### Five in-scope questions

Use the five questions and their `expects` values from `questions.py`:

1. Annual commuter-lounge locker cost — `$20`
2. Recommended RAM for CS courses — `16GB`
3. Internship application timing at large employers — `October and November`
4. Best dorm laundry times — `Tuesday and Wednesday mornings`
5. Meal-plan change deadline — `first ten days`

For each in-scope question:

1. Submit the question through the HTTP `/ask` endpoint.
2. Capture the returned answer and refusal status.
3. Run the existing retrieval function with the same question and corpus configuration.
4. Pass the resulting retrieval objects, question, expected value, and HTTP answer to `scorer.judge()`.
5. Use the returned scorer verdict to determine whether the answer satisfies the correctness requirement.

Do not construct synthetic retrieval results or pass an empty list in place of actual retrieved documents.

### Three out-of-scope questions

Use these exact questions from `OUT_OF_SCOPE` in `questions.py`:

1. "What is the capital of Mongolia?"
2. "How do I change the oil in a diesel engine?"
3. "Who won the 1994 World Cup?"

For each out-of-scope question:

- The endpoint must return HTTP 200.
- `refused` must be `true`.

### Testing conditions

- Set `AI201_CACHE=0` before starting the service.
- Use the same eight questions in the same order for all three trials.
- Use the existing retrieval configuration and relevance threshold.
- Apply the existing `scorer.py` evaluation rules rather than manually judging answer wording.
- Space requests at least three seconds apart to avoid unnecessary rate-limit waiting.
- Record the actual responses and evaluation results for every trial.

**All eight questions must satisfy their expected behavior in each of the three trials.**

**Why this target:** Adding instrumentation should not change the existing retrieval, relevance gate, or Gemini answer generation. A response with `refused: false` may still contain incorrect information. Using the previously established evaluator allows answers to be checked against known facts and source-citation requirements, while separately verifying that unrelated questions are refused.
