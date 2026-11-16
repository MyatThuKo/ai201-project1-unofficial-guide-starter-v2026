# The Unofficial Guide

**Myat Thu Ko — Corpus: `advice_threads`**

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

I used `advice_threads` corpus to build an unofficial guide that answers questions. The corpus contains a thread with questions, followed by multiple answers replied about topics such as commuting, internships and meal plans. The system splits the documents into searchable chunks, creates embeddings, and retrieves chunks that are relevant to a user's question. A relevance gate stops questions that are not covered by the `advice_threads` corpus, and the model generates a grounded answer using only the retrieved documents while naming its source.

## Chunking Strategy

**Chunk size:** Question with one complete reply instead of a fixed character limit
**Overlap:** No character limit or overlap is needed since I prepend the question in every chunk before adding an answer.

<!-- What about YOUR documents made you pick these numbers? Short posts and
     long sectioned guides don't want the same chunking, and "800 seemed
     reasonable" earns nothing. Point at something you noticed when you read
     the documents in Milestone 1.

     If you changed your mind partway through, say so and say why. That's worth
     more than pretending you got it right first time.

     Milestone 3. -->

When I was reading `advice_threads`, I noticed that each document contains a question followed by multiple replies separated by blank lines. Thus, I decided to chunk around those blank lines instead of using fixed character limits. Each chunk will keep the question together with a complete replied answer. This will give the retrieved text both context and a complete thought.

## Sample Chunks

<!-- Five chunks, pasted as text. Label each one and name the file it came from
     AND the function that produced it — the grader checks your code against
     what you claim here.

     `python app.py chunks -n 5` prints all three for you. Copy them straight
     across.

     Milestone 3. -->

**Chunk 1** — source: thread_bike_commute.txt#0 `— produced by:` chunker.py::split_documents

```
THREAD: Is a bike worth it for a 20 minute walk commute?

--- reply 1 (14 votes) ---
Yeah. Cuts an 18 minute walk to about 6. The thing nobody mentions is storage — covered bike parking exists at three buildings and is full by 9am at all three.
```

**Chunk 2** — source: thread_first_gen.txt#1 `— produced by:` chunker.py::split_documents

```
THREAD: Anything specific for first-generation students?

--- reply 2 (41 votes) ---
The thing I'd say: the unwritten rules are the hard part, not the coursework. Ask about the unwritten rules explicitly. People are happy to explain them and nobody volunteers them.
```

**Chunk 3** — source: thread_laptop_specs.txt#2 `— produced by:` chunker.py::split_documents

```
THREAD: How much laptop do I actually need for CS courses?

--- reply 3 (12 votes) ---
I did two years on an 8GB machine and it was fine until the last project, at which point it very much wasn't. 16 is the answer.
```

**Chunk 4** — source: thread_parking.txt#1 `— produced by:` chunker.py::split_documents

```
THREAD: Worth getting a parking permit?

--- reply 2 (21 votes) ---
Street parking on Verrill is legal and free and unmarked, which is why half the upper years do it.
```

**Chunk 5** — source: thread_sleep_schedule.txt#1 `— produced by:` chunker.py::split_documents

```
THREAD: Everyone says fix your sleep. Does it actually matter?

--- reply 2 (37 votes) ---
The library being open until 2am is a trap. It's a resource, not a schedule.
```

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:**
"How much does it cost to rent a locker in the commuter lounge for a year?"
**Answer:**

```
(best distance 0.279, cutoff 0.6)

It costs $20 a year to rent a locker in the commuter lounge (from thread_commuting.txt).

Sources retrieved: thread_bike_commute.txt, thread_commuting.txt, thread_laundry_timing.txt, thread_study_spots.txt

1 model calls this session, 483 tokens (460 in, 23 out)
```

**My relevance cutoff:** 0.6

I kept the relevance cutoff at 0.6 because my 5 sample questions had best distances between 0.239 and 0.279. For the `OUT_OF_SCOPE` questions, the distances are between 0.807 and 0.896. Since there was a large gap between the two groups (0.279 and 0.807), I decided to keep the relevance cutoff as 0.6 without changing it to allow the supported questions while rejecting the unsupported ones.

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question                                                                          | In corpus? | Best distance |
| --------------------------------------------------------------------------------- | ---------- | ------------- |
| How much does it cost to rent a locker in the commuter lounge for a year?         | Yes        | 0.279         |
| What is the memory size or RAM recommended for CS courses?                        | Yes        | 0.243         |
| When is the latest time a student can apply for an internship at large employers? | Yes        | 0.239         |
| What time is the best to do laundry in the dorms?                                 | Yes        | 0.275         |
| How long do I have to change my meal plan?                                        | Yes        | 0.240         |
| What is the capital of Mongolia?                                                  | No         | 0.893         |
| How do I change the oil in a diesel engine?                                       | No         | 0.896         |
| Who won the 1994 World Cup?                                                       | No         | 0.893         |
| What is the recommended dosage of ibuprofen for a headache?                       | No         | 0.807         |
| How do I write a for loop in Rust?                                                | No         | 0.835         |

## How I Used AI

**1.** I asked Claude to help me understand why the stater chunker was producing incomplete chunks. It explained that changing the character limit alone would not solve the problem because the fixed-size splitter was cutting through words and replies. I originally considered splitting on newline characters `\n`, then changed my implementation to use the blank-line structure of the `advice_threads` corpus. This way the chunk keeps the thread question with a complete reply.

**2.** I asked Claude to help me interpret the retrieval distances when I was
setting the relevance cutoff. It suggested comparing the five in-corpus
questions against the five out-of-scope questions instead of changing the
cutoff just because one earlier question failed. After changing my chunking
strategy, my in-corpus distances were about 0.239–0.279 and my out-of-scope
distances were about 0.807–0.896, so I kept the existing cutoff of 0.6 instead
of changing it.

**3.** In Unit 2, I asked Claude to help me interpret my baseline results after all five acceptance criteria passed. It suggested checking Criterion 4 across all 75 chunks instead of relying only on the five deterministic samples. After running that check, I found that all 75 chunks were clean. That changed my understanding of the issue: the chunker itself was working, but my original acceptance criterion was too weak. I then added `validate_chunk()` as a defensive check rather than rewriting the chunking strategy.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

### Stretch Improvement

For the extra-credit experiment, I will reduce `top_k` from 5 to 3. My current retrieval returns the correct source but often includes unrelated chunks as well. I want to test whether retrieving fewer chunks keeps all five questions correct while reducing unnecessary context.

### Stretch Improvement (Unit 2) — Reduce top-k Finding

I tested reducing `top_k` from 5 to 3 because my original retrieval often returned the correct document along with several unrelated documents.

I ran: `python run_eval.py --top-k 3 --label stretch`

All five in-corpus questions still passed in all three runs, and the relevance gate still refused all 5 out-of-scope questions.

The number of unique retrieved source documents also decreased. Across my five test questions, the average dropped from 3.0 sources with `top_k = 5` to 1.4 sources with `top_k = 3`. Four of the five questions retrieved only the correct source document.

**Did it help?**

Yes. Reducing `top_k` did not change the acceptance-criteria scores, but it made retrieval more focused and reduced unrelated context without losing the supporting chunk.

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion                                   | Target | Run 1  | Run 2  | Run 3  | Verdict |
| ------------------------------------------- | ------ | ------ | ------ | ------ | ------- |
| 1. Retrieved chunk contains the answer      | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 2. Every answer names a source              | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 3. Gate stops out-of-corpus questions       | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 4. Sampled chunks contain complete thoughts | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 5. Cited source supports the answer         | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

### Evidence from the before run

- Produced by: `run_eval.py::main`
- Retrieval: `store.py::search`, chunks from `chunker.py::split_documents`
- Corpus: `advice_threads` (index variant `default`)
- top-k: 5 · relevance cutoff: 0.6
- Runs per question: 3, caching off
- When: 2026-09-26 18:03

### How much does it cost to rent a locker in the commuter lounge for a year? — run 1

- Best distance: 0.2786 (passed the gate)
- Sources retrieved: thread_bike_commute.txt, thread_commuting.txt, thread_laundry_timing.txt, thread_study_spots.txt

```
It costs $20 a year to rent a locker in the commuter lounge (from thread_commuting.txt).
```

### How much does it cost to rent a locker in the commuter lounge for a year? — run 2

- Best distance: 0.2786 (passed the gate)
- Sources retrieved: thread_bike_commute.txt, thread_commuting.txt, thread_laundry_timing.txt, thread_study_spots.txt

```
It costs $20 a year to rent a locker in the commuter lounge (from thread_commuting.txt).
```

### How much does it cost to rent a locker in the commuter lounge for a year? — run 3

- Best distance: 0.2786 (passed the gate)
- Sources retrieved: thread_bike_commute.txt, thread_commuting.txt, thread_laundry_timing.txt, thread_study_spots.txt

```
It costs $20 a year to rent a locker in the commuter lounge (from thread_commuting.txt).
```

#### Criterion 3 evidence:

Produced by `run_eval.py::check_out_of_scope`, cutoff 0.6. Refused 5 of 5.

Retrieval is deterministic and the gate is a comparison against a
fixed number, so these do not vary between runs — one pass over the
list is the whole measurement.

| Out-of-scope question                                       | Best distance | Gate    |
| ----------------------------------------------------------- | ------------- | ------- |
| What is the capital of Mongolia?                            | 0.893         | refused |
| How do I change the oil in a diesel engine?                 | 0.896         | refused |
| Who won the 1994 World Cup?                                 | 0.893         | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.807         | refused |
| How do I write a for loop in Rust?                          | 0.835         | refused |

---

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| #   | Criterion                                | Verdict | How I decided                                                                                                                      |
| --- | ---------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Retrieved chunk contains the answer      | MET     | All 5 test questions retrieved at least one chunk containing the expected answer, exceeding my 4 of 5 target.                      |
| 2   | Every answer names a source              | MET     | All 5 answers named at least one source document in every run, meeting my 5 of 5 target.                                           |
| 3   | Gate stops out-of-corpus questions       | MET     | The relevance gate refused all 5 out-of-scope questions, exceeding my 4 of 5 target.                                               |
| 4   | Sampled chunks contain complete thoughts | MET     | All 5 sampled chunks contained complete replies or complete thoughts and did not begin or end in the middle of a word or sentence. |
| 5   | Cited source supports the answer         | MET     | For all 5 test questions, the cited source contained the expected information used in the answer, exceeding my 4 of 5 target.      |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

None of my five acceptance criteria were missed in the baseline run.

However, Criterion 4 was less strict than it could have been. My original
target only checked 4 of 5 sampled chunks, while my corpus contains 75 chunks.
The `chunks -n 5` command also returned the same deterministic five chunks each
time, so the criterion did not test much of the corpus.

I ran `chunk_is_clean()` against all 75 chunks and found that 75 of 75 passed.
This means the chunking implementation is working well, but if I were defining
the criterion again, I would require all generated chunks to pass the
clean-chunk check instead of only 4 of 5 sampled chunks.

## The Improvement

**What I changed:**
I added extra check on my chunking strategy to make sure that every generated chunk is checked for the expected `advice_threads` structure before it is returned. I decided that a chunk must preserve the `THREAD:` question and a reply block instead of silently accepting mismatched text or an incorrect text.

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

The reason why I picked it because my Milestone 3 diagonsis showed that criterion #4 only checked 5 sampled chunks even though my selected `advice_threads` corpus produced 75 chunks in total. All 75 of those chunks happened to be clean, but the current chunker depends on the corpus keeping the same question-and-reply format. If the corpus format changes, the validator will now raise an error instead of allowing malformed chunks to pass silently into the pipeline.

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion                                   | Target | Run 1  | Run 2  | Run 3  | Verdict |
| ------------------------------------------- | ------ | ------ | ------ | ------ | ------- |
| 1. Retrieved chunk contains the answer      | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 2. Every answer names a source              | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 3. Gate stops out-of-corpus questions       | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 4. Sampled chunks contain complete thoughts | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 5. Cited source supports the answer         | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

The changes did not show an improvement in the scores since the baseline already met all five of the criteria I have written in Unit 1. Before the change, all five criteria scored 5 of 5 in all three runs. After the change, all five criteria still scored 5 of 5 in all three runs. Therefore, the improvement did not change the acceptance-criteria scores.

However, the improvement made the chunking pipeline more robust. Before the change, malformed chunks could be returned silently if the `advice_threads` format changed from a `THREAD:` question followed by reply blocks to a different structure. After adding a new method `validate_chunk()` before returning the chunk in `split_documents()` method, every generated chunk is checked for the expected format of `THREAD:` header followed by replies with complete ending and meaningful sentence. I also made sure that all 75 chunks produced passed the validation and that chunk with an incorrect format raised a `ValueError`.

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

None of my five acceptance criteria are still missed after the improvement.

However, the chunking strategy is still tightly coupled to the structure of the `advice_threads` corpus. It expects each document to begin with a `THREAD:` question followed by reply blocks separated by blank lines. The new validation step will catch malformed chunks if that structure changes, but the chunker itself would still need to be updated to support a different document format.

I stopped here because Unit 2 asks for one measured improvement, and changing the chunking strategy again would introduce a second system change.

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->

If I were writing my acceptance criteria again, I would make Criterion 4 morestrict. Instead of checking whether 4 of 5 sampled chunks contain complete thoughts, I would require every generated chunk to pass the clean-chunk check.

My corpus produced 75 chunks, and `python app.py chunks -n 5` returned the same five deterministic samples each time. That meant my original criterion tested only a small portion of the corpus. When I later checked all 75 chunks with `chunk_is_clean()`, all 75 passed, so a full-corpus criterion would have been both measurable and more meaningful.

### Run Log — Stretch

| Criterion                                   | Target | Run 1  | Run 2  | Run 3  | Verdict |
| ------------------------------------------- | ------ | ------ | ------ | ------ | ------- |
| 1. Retrieved chunk contains the answer      | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 2. Every answer names a source              | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 3. Gate stops out-of-corpus questions       | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 4. Sampled chunks contain complete thoughts | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |
| 5. Cited source supports the answer         | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET     |

## Capstone

**The System**

I chose to extend The Unofficial Guide, my RAG-based question-answering system from Units 1–2. The system retrieves relevant information from the `advice_threads` corpus, checks whether the question is supported by the retrieved documents, and generates an answer grounded in those documents.

**The Shape**

I chose Shape A — Deploy and Instrument, using Path B — Local with Logs.

I will extend the existing HTTP service in `serve.py` by adding structured JSONL logging and request execution-time measurement. Each request will produce a record containing its timestamp, request outcome, HTTP status, execution duration, and relevant metadata. Both successful and failed requests will be recorded.

The service will run locally using a documented command, and the logs will provide evidence of its behavior. I will measure the average execution time across multiple requests and use the results to evaluate the extension.

**Out of Scope**

- I will not modify the existing chunking strategy, embedding model, or retrieval logic.
- I will not change the relevance threshold, Gemini model, or grounded-answer generation.
- I will not build a frontend, monitoring dashboard, or external database.

The goal is to make the existing system observable and reproducible, not to change how it answers questions.

**Instrumentation**

Every request to `serve.py` writes one JSON record to `logs/requests.jsonl` (field list in [RUNNING.md](RUNNING.md#the-structured-log)). The record is written in Flask's `after_request` hook, so every route and every outcome is logged — including 400s and 500s. Each record holds the input (`question`), the output (`answer`, `sources`), the duration, the Gemini tokens used, whether the answer came from the cache, and the retrieval distance the gate based its decision on.

The session below was produced with `AI201_CACHE=0 python serve.py` and `python run_capstone_requests.py`, and is committed in full as [results/capstone_m3_session.jsonl](results/capstone_m3_session.jsonl).

```jsonl
{"timestamp": "2026-11-16T01:10:03.554110+00:00", "request_id": "66a28574-0fdc-4330-8a20-93731e0c7e82", "method": "GET", "path": "/health", "http_status": 200, "outcome": "completed", "question": null, "answer": null, "sources": null, "n_sources": null, "best_distance": null, "prompt_tokens": null, "output_tokens": null, "cache_hit": null, "duration_ms": 759.39, "question_length": null, "error_type": null, "ts": "2026-11-16T01:10:03.554291+00:00"}
{"timestamp": "2026-11-16T01:10:05.355251+00:00", "request_id": "8c8a8639-aac6-43e4-9cca-f04bf58e3aa9", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "Is the housing lottery random?", "answer": "I don't have enough information to answer whether the housing lottery is random (thread_transfer_credits.txt).", "sources": ["thread_clubs.txt", "thread_laundry_timing.txt", "thread_parking.txt", "thread_roommate_conflict.txt", "thread_transfer_credits.txt"], "n_sources": 5, "best_distance": 0.5773, "prompt_tokens": 414, "output_tokens": 24, "cache_hit": false, "duration_ms": 1798.96, "question_length": 30, "error_type": null, "ts": "2026-11-16T01:10:05.355309+00:00"}
{"timestamp": "2026-11-16T01:10:06.139012+00:00", "request_id": "4af80098-9740-47e1-a9c8-d0c73efe97eb", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "How much does a storage locker cost?", "answer": "A storage locker in the commuter lounge costs $20 a year, according to `thread_commuting.txt`.", "sources": ["thread_commuting.txt", "thread_laundry_timing.txt", "thread_printing.txt", "thread_study_spots.txt"], "n_sources": 4, "best_distance": 0.5567, "prompt_tokens": 433, "output_tokens": 23, "cache_hit": false, "duration_ms": 779.9, "question_length": 36, "error_type": null, "ts": "2026-11-16T01:10:06.139080+00:00"}
{"timestamp": "2026-11-16T01:10:06.812456+00:00", "request_id": "c9c3051a-78fd-4008-b7a0-03bcafd093b6", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "How much RAM should my laptop have?", "answer": "Your laptop should have 16GB of RAM, as it is the one number worth paying for and prevents issues on later projects. (Source: thread_laptop_specs.txt)", "sources": ["thread_internship_timing.txt", "thread_laptop_specs.txt", "thread_professor_email.txt"], "n_sources": 3, "best_distance": 0.3612, "prompt_tokens": 431, "output_tokens": 38, "cache_hit": false, "duration_ms": 668.78, "question_length": 35, "error_type": null, "ts": "2026-11-16T01:10:06.812506+00:00"}
{"timestamp": "2026-11-16T01:10:06.896938+00:00", "request_id": "ae85acc6-0d21-4b3b-8cc4-9a59660a8c1b", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "refused", "question": "When are the quiet times?", "answer": "I don't have enough information about that.", "sources": [], "n_sources": 0, "best_distance": 0.6099, "prompt_tokens": 0, "output_tokens": 0, "cache_hit": false, "duration_ms": 80.88, "question_length": 25, "error_type": null, "ts": "2026-11-16T01:10:06.897006+00:00"}
{"timestamp": "2026-11-16T01:10:07.613622+00:00", "request_id": "7940a6ea-f87a-4e24-9f11-39b474ed8d26", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "How long is the add/drop period?", "answer": "I do not have enough information to answer how long the add/drop period is, as the provided documents only mention that the add/drop deadline and the withdrawal deadline are different dates (*thread_first_year_regret.txt*).", "sources": ["thread_commuting.txt", "thread_first_year_regret.txt", "thread_late_work.txt", "thread_pass_fail.txt"], "n_sources": 4, "best_distance": 0.5949, "prompt_tokens": 448, "output_tokens": 49, "cache_hit": false, "duration_ms": 714.87, "question_length": 32, "error_type": null, "ts": "2026-11-16T01:10:07.613693+00:00"}
{"timestamp": "2026-11-16T01:10:08.353548+00:00", "request_id": "9d0e802c-f90f-4637-ba91-51e2c63e70aa", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "When do applications open?", "answer": "Based on the provided documents, there is no mention of when applications *open*. The documents only state that large employers close their applications in October and November for the following summer (thread_internship_timing.txt).", "sources": ["thread_first_year_regret.txt", "thread_internship_timing.txt", "thread_laundry_timing.txt", "thread_sleep_schedule.txt", "thread_study_spots.txt"], "n_sources": 5, "best_distance": 0.5892, "prompt_tokens": 413, "output_tokens": 44, "cache_hit": false, "duration_ms": 735.01, "question_length": 26, "error_type": null, "ts": "2026-11-16T01:10:08.353610+00:00"}
{"timestamp": "2026-11-16T01:10:09.075041+00:00", "request_id": "8db682fd-d185-493d-82da-045ca7ca49cb", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "What are the application deadlines?", "answer": "According to the documents, large employers close applications in October and November for the following summer (thread_internship_timing.txt).", "sources": ["thread_first_year_regret.txt", "thread_internship_timing.txt", "thread_late_work.txt"], "n_sources": 3, "best_distance": 0.5257, "prompt_tokens": 449, "output_tokens": 27, "cache_hit": false, "duration_ms": 716.71, "question_length": 35, "error_type": null, "ts": "2026-11-16T01:10:09.075106+00:00"}
{"timestamp": "2026-11-16T01:10:10.072615+00:00", "request_id": "2f8c755e-24eb-4fee-b6dd-727a5d30c478", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "Can students use storage lockers?", "answer": "Yes, students can rent lockers in the commuter lounge in the student centre for $20 a year. \n\nSource: `thread_commuting.txt`", "sources": ["thread_commuting.txt", "thread_first_gen.txt", "thread_roommate_conflict.txt", "thread_study_spots.txt"], "n_sources": 4, "best_distance": 0.5511, "prompt_tokens": 424, "output_tokens": 32, "cache_hit": false, "duration_ms": 993.58, "question_length": 33, "error_type": null, "ts": "2026-11-16T01:10:10.072712+00:00"}
{"timestamp": "2026-11-16T01:10:10.832508+00:00", "request_id": "94349e20-d3ca-4b3e-a14a-f8f55faae1a2", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "What are the laptop requirements?", "answer": "Based on the provided documents, 16GB of RAM is the one number worth paying for, as an 8GB machine may not be enough for the final projects (thread_laptop_specs.txt).", "sources": ["thread_first_gen.txt", "thread_first_year_regret.txt", "thread_laptop_specs.txt"], "n_sources": 3, "best_distance": 0.4684, "prompt_tokens": 438, "output_tokens": 43, "cache_hit": false, "duration_ms": 754.88, "question_length": 33, "error_type": null, "ts": "2026-11-16T01:10:10.832582+00:00"}
{"timestamp": "2026-11-16T01:10:10.909304+00:00", "request_id": "7380bc87-6150-4eab-aec2-bc1febcba5c3", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "refused", "question": "What is the process for joining the housing lottery?", "answer": "I don't have enough information about that.", "sources": [], "n_sources": 0, "best_distance": 0.6008, "prompt_tokens": 0, "output_tokens": 0, "cache_hit": false, "duration_ms": 69.6, "question_length": 52, "error_type": null, "ts": "2026-11-16T01:10:10.909325+00:00"}
{"timestamp": "2026-11-16T01:10:11.487827+00:00", "request_id": "ecec2e7c-5a67-4a21-bbdf-410e0ff01691", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "What time is the best to do laundry in the dorms?", "answer": "Based on the provided documents, Tuesday and Wednesday mornings are the best times to do laundry in every building (from `thread_laundry_timing.txt`).", "sources": ["thread_commuting.txt", "thread_laundry_timing.txt", "thread_roommate_conflict.txt"], "n_sources": 3, "best_distance": 0.2749, "prompt_tokens": 428, "output_tokens": 32, "cache_hit": false, "duration_ms": 576.94, "question_length": 49, "error_type": null, "ts": "2026-11-16T01:10:11.487920+00:00"}
{"timestamp": "2026-11-16T01:10:12.178935+00:00", "request_id": "3b1b5bde-0d92-4817-84ca-55d0dffbde62", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "How long do I have to change my meal plan?", "answer": "You can only change your meal plan in the first ten days (from thread_meal_plan_tier.txt).", "sources": ["thread_first_year_regret.txt", "thread_meal_plan_tier.txt"], "n_sources": 2, "best_distance": 0.2404, "prompt_tokens": 444, "output_tokens": 24, "cache_hit": false, "duration_ms": 686.97, "question_length": 42, "error_type": null, "ts": "2026-11-16T01:10:12.178956+00:00"}
{"timestamp": "2026-11-16T01:10:12.180713+00:00", "request_id": "6796584a-3953-4991-9861-2fa90772353e", "method": "POST", "path": "/ask", "http_status": 400, "outcome": "bad_request", "question": null, "answer": null, "sources": null, "n_sources": null, "best_distance": null, "prompt_tokens": null, "output_tokens": null, "cache_hit": null, "duration_ms": 0.1, "question_length": 0, "error_type": null, "ts": "2026-11-16T01:10:12.180732+00:00"}
{"timestamp": "2026-11-16T01:10:12.182215+00:00", "request_id": "6750e664-9d29-465f-bb03-cf310c6028a3", "method": "POST", "path": "/ask", "http_status": 400, "outcome": "bad_request", "question": null, "answer": null, "sources": null, "n_sources": null, "best_distance": null, "prompt_tokens": null, "output_tokens": null, "cache_hit": null, "duration_ms": 0.08, "question_length": 0, "error_type": null, "ts": "2026-11-16T01:10:12.182231+00:00"}
```

**What It Costs**

| Request type                | n   | Avg duration              | Avg prompt tokens | Avg output tokens | Avg total tokens |
| --------------------------- | --- | ------------------------- | ----------------- | ----------------- | ---------------- |
| Answered (real Gemini call) | 10  | 842.7 ms (576.9 - 1799.0) | 432.2             | 33.6              | 465.8            |
| Refused at the gate         | 2   | avg 75.2 ms (69.6 - 80.9) | 0                 | 0                 | 0                |
| Failed (400/500)            | 2   | avg 0.1 ms (0.1 - 0.1)    | n/a               | n/a               | n/a              |

**How I measured it:**

- **Tokens** are Gemini's own count of what each call used, read from the response's `usage_metadata` by `generate.py`. `serve.py` reads the running totals (`generate.token_counts()`) before and after each request and logs the difference as `prompt_tokens` and `output_tokens`, so each log line carries the cost of that one request.
- **Duration** is measured server-side with `time.perf_counter()`, from when the request arrives to when the response is ready. It does not include network time to the client.
- **The cache was off** (`AI201_CACHE=0`), so every answered request was a real Gemini call. `measure_cost.py` excludes any record with `cache_hit: true` anyway.
- **Answered and refused requests are reported separately** because they cost very different amounts. A refusal stops at the relevance gate before Gemini is called, so it uses 0 tokens and only local compute (embedding the question plus a Chroma search).
- **The first request after start-up is slower** because it loads Chroma and the index. It's included in the average, as one of the ten.

**In money:** the project runs on Gemini's free tier, so the actual spend was $0. The real cost is the tokens above, taken from the free tier's request and token quota.

**Run Log and Verdicts — Before Improvement**

The capstone was evaluated using `run_trials.py` with three separate trials. Answer caching was disabled, and the test runner sent paced HTTP requests against the locally running Flask service.

| Criterion                 | Target     | Run 1                                                | Run 2                                                 | Run 3                                                | Verdict |
| ------------------------- | ---------- | ---------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------- | ------- |
| 1. Logging completeness   | 10/10      | 10/10                                                | 10/10                                                 | 10/10                                                | MET     |
| 2. Warm-request latency   | <= 1000 ms | avg 659.0 ms over 10 warm requests (491.97 - 949.13) | avg 718.8 ms over 10 warm requests (535.33 - 1018.44) | avg 731.5 ms over 10 warm requests (500.58 — 957.27) | MET     |
| 3. Failure observability  | 6/6        | 6/6                                                  | 6/6                                                   | 6/6                                                  | MET     |
| 4. Reproducible execution | 5/5 steps  | 5/5                                                  | 5/5                                                   | 5/5                                                  | MET     |
| 5. RAG behavior           | 8/8        | 8/8                                                  | 8/8                                                   | 8/8                                                  | MET     |

**Evidence**

The complete HTTP responses, structured log records, and evaluation results for every trial are in:

- `results/capstone_trial_1.json`, `results/capstone_trial_2.json`, `results/capstone_trial_3.json` (criteria 1, 2, 3, 5)
- `results/capstone_c4_trial_1.txt`, `results/capstone_c4_trial_2.txt`, `results/capstone_c4_trial_3.txt` (criterion 4)

Real output for each criterion, all from **trial 1**:

**Criterion 1: Structured logging completeness.** Produced by `run_trials.py::criterion_1()`. The log lines were written by `serve.py::record_request()` through `request_log.py::log_request()`. These are the first 2 of the 10 new records in `logs/requests.jsonl` (`criteria["1"]["log_records"]`):

```json
{"timestamp": "2026-11-16T02:43:50.496191+00:00", "request_id": "638336cb-017d-4bf4-99d5-b882f556481e", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "How much does it cost to rent a locker in the commuter lounge for a year?", "answer": "It costs $20 a year to rent a locker in the commuter lounge (from thread_commuting.txt).", "sources": ["thread_bike_commute.txt", "thread_commuting.txt", "thread_laundry_timing.txt", "thread_study_spots.txt"], "n_sources": 4, "best_distance": 0.2786, "prompt_tokens": 460, "output_tokens": 23, "cache_hit": false, "duration_ms": 492.01, "question_length": 73, "error_type": null, "ts": "2026-11-16T02:43:50.496213+00:00"}
{"timestamp": "2026-11-16T02:43:55.100002+00:00", "request_id": "6658767c-3930-4058-b372-2b62b0d230c7", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "What is the memory size or RAM recommended for a CS courses?", "answer": "16GB of RAM is recommended (or worth paying for) for CS courses (thread_laptop_specs.txt).", "sources": ["thread_first_year_regret.txt", "thread_laptop_specs.txt", "thread_pass_fail.txt"], "n_sources": 3, "best_distance": 0.243, "prompt_tokens": 459, "output_tokens": 25, "cache_hit": false, "duration_ms": 1597.69, "question_length": 60, "error_type": null, "ts": "2026-11-16T02:43:55.100024+00:00"}
```

All 10 records passed every check (no issues in `criteria["1"]["checks"]`).

**Criterion 2: Warm-request latency.** Produced by `run_trials.py::criterion_2()` from the `duration_ms` field of the 11 new log records (`criteria["2"]`):

```json
{
  "warmup": {
    "question": "How much does it cost to rent a locker in the commuter lounge for a year?",
    "status": 200,
    "duration_ms": 2766.31
  },
  "durations_ms": [
    624.79, 850.05, 949.13, 577.99, 792.19, 512.29, 556.81, 505.97, 491.97,
    729.11
  ],
  "average_ms": 659.0,
  "min_ms": 491.97,
  "max_ms": 949.13,
  "met": true
}
```

**Criterion 3: Failure-path observability.** Produced by `run_trials.py::criterion_3()`. The five invalid requests went over HTTP and were matched to their log records by order. The 500 is the record the mocked `serve.log_request()` received (`criteria["3"]`):

```json
{"name": "Empty JSON object", "status": 400, "logged_status": 400, "logged_outcome": "bad_request", "request_id": "e2c6d0bf-7d62-4f12-b75b-ed486daad438", "pass": true}
{"name": "Empty question", "status": 400, "logged_status": 400, "logged_outcome": "bad_request", "request_id": "55d41180-49f9-475e-825f-6251a8316b7e", "pass": true}
{"name": "Whitespace-only question", "status": 400, "logged_status": 400, "logged_outcome": "bad_request", "request_id": "e16e13c9-62ff-49af-bf51-c152997cc8a2", "pass": true}
{"name": "Null question", "status": 400, "logged_status": 400, "logged_outcome": "bad_request", "request_id": "4896a885-61ca-4db5-a650-d75f2905388a", "pass": true}
{"name": "JSON array", "status": 400, "logged_status": 400, "logged_outcome": "bad_request", "request_id": "ebcb0583-89d6-466d-99e8-b664eb31631f", "pass": true}
{"status": 500, "log_request_calls": 1, "record": {"request_id": "d33e0eab-df22-4b74-8ea8-67a7e8222623", "method": "POST", "path": "/ask", "http_status": 500, "outcome": "error", "question": "What is the application deadline?", "duration_ms": 0.12, "error_type": "RuntimeError"}, "pass": true}
```

**Criterion 4: Reproducible local execution.** Each trial cloned the repo into its own folder and followed `RUNNING.md` only. The output was captured with `tee` into `results/capstone_c4_trial_1.txt`. Below are the index build (`app.py index`), the health check and `/ask` (`serve.py::health()`, `serve.py::ask()`), then the clone's own log:

```text
Python 3.13.15
  chunked  75 chunks, 202 characters on average (shortest 132, longest 281), produced by chunker.py::split_documents
  stored   75 chunks in 10.8s
{"corpus":"advice_threads","detail":"ready","index_ready":true,"status":"ok"}
HTTP 200
{"answer":"You can only change your meal plan in the first ten days (thread_meal_plan_tier.txt).","best_distance":0.2404,"corpus":"advice_threads","question":"How long do I have to change my meal plan?","refused":false,"sources":["thread_first_year_regret.txt","thread_meal_plan_tier.txt"],"threshold":0.6}
HTTP 200
{"timestamp": "2026-11-16T03:26:26.656832+00:00", "request_id": "6d4aaf52-e130-4caa-b947-e4b4b95a3f2a", "method": "POST", "path": "/ask", "http_status": 200, "outcome": "answered", "question": "How long do I have to change my meal plan?", "answer": "You can only change your meal plan in the first ten days (thread_meal_plan_tier.txt).", "sources": ["thread_first_year_regret.txt", "thread_meal_plan_tier.txt"], "n_sources": 2, "best_distance": 0.2404, "prompt_tokens": 444, "output_tokens": 23, "cache_hit": false, "duration_ms": 2189.26, "question_length": 42, "error_type": null, "ts": "2026-11-16T03:26:26.656870+00:00"}
```

All three clean-checkout trials reused the embedding model already in `~/.cache/chroma` (`onnx_models/`, downloaded 2026-09-16), as criterion 4 permits. The listing is at the top of each `capstone_c4_trial_*.txt`. The index output's "first run downloads the model" is the fixed message `app.py` prints; no download happened.

**Criterion 5: Original RAG behaviour preserved.** Produced by `run_trials.py::criterion_5()`. Each answer came from `/ask`, and each in-scope verdict is `scorer.py::judge()` run against a fresh `store.py::search()` (`criteria["5"]["rows"]`):

```json
{"kind": "in_scope", "question": "How much does it cost to rent a locker in the commuter lounge for a year?", "expects": "$20", "status": 200, "refused": false, "judge": true, "answer": "It costs $20 a year to rent a locker in the commuter lounge (from thread_commuting.txt)."}
{"kind": "in_scope", "question": "What is the memory size or RAM recommended for a CS courses?", "expects": "16GB", "status": 200, "refused": false, "judge": true, "answer": "Based on the documents, 16GB of RAM is recommended for CS courses. This comes from `thread_laptop_specs.txt`."}
{"kind": "in_scope", "question": "When is the closing date or the latest time a student can apply for an internship at large employers?", "expects": "October and November", "status": 200, "refused": false, "judge": true, "answer": "Large employers close applications in October and November for the following summer. \n\nSource: thread_internship_timing.txt"}
{"kind": "in_scope", "question": "What time is the best to do laundry in the dorms?", "expects": "Tuesday and Wednesday mornings", "status": 200, "refused": false, "judge": true, "answer": "Tuesday and Wednesday mornings are the best times to do laundry in every building (thread_laundry_timing.txt)."}
{"kind": "in_scope", "question": "How long do I have to change my meal plan?", "expects": "first ten days", "status": 200, "refused": false, "judge": true, "answer": "You can only change your meal plan in the first ten days (from thread_meal_plan_tier.txt)."}
{"kind": "out_of_scope", "question": "What is the capital of Mongolia?", "status": 200, "refused": true, "best_distance": 0.8935, "answer": "I don't have enough information about that."}
{"kind": "out_of_scope", "question": "How do I change the oil in a diesel engine?", "status": 200, "refused": true, "best_distance": 0.8964, "answer": "I don't have enough information about that."}
{"kind": "out_of_scope", "question": "Who won the 1994 World Cup?", "status": 200, "refused": true, "best_distance": 0.8934, "answer": "I don't have enough information about that."}
```

**Which results repeat across trials, and why.** Criterion 3 and the out-of-scope half of criterion 5 come out the same in all three trials by design. Criterion 3 never calls the model, and retrieval gives the same distances for the same question every time. The model-dependent results do vary between trials, which shows each trial was a real rerun with `cache_hit: false` on every record. For example, the second criterion 1 request used 484, 486, then 481 tokens. Criterion 2's averages were 659.0, 718.8 and 731.5 ms. The criterion 5 answers are worded differently from trial to trial. The trial 1 warm-up (2,766 ms) was a cold start. Trials 2 and 3 ran on the same server without a restart, as criterion 2 requires, so their warm-ups were already warm (844 and 636 ms).

**Observations**

All five criteria met their acceptance targets in all three trials.

The mean warm-request latency across the three trials was approximately 703.1 ms, below the 1,000 ms target. However, individual warm requests in the criterion 1 runs occasionally took three to four seconds: 4,265.71 ms in trial 1 and 3,952.50 ms in trial 2. Within criterion 2's own measured requests, trial 2 had one request at 1,018.44 ms.

This suggests that average latency alone does not fully describe response-time consistency.

**Milestone 6 — Diagnosis and Improvement**

**Verdicts**

All five automated acceptance criteria were MET across three trials.

No missed automated criterion required diagnosis. However, the results exposed a limitation in the latency criterion.

**Assessment of the Targets**

Criterion 2 measured average warm-request latency and excluded the first request after startup. Although all three trials met the 1,000 ms average target, the first request in Trial 1 took 2,766.31 ms.

Individual requests in the logging tests also reached 4,265.71 ms and 3,952.50 ms.

The original average-based target therefore did not capture cold-start overhead or occasional latency spikes.

**Criterion I Would Tighten**

I would tighten Criterion 2 in a future evaluation by including first-request latency after a fresh server start and setting a separate measurable target for it.

The original `criteria.md` remains unchanged so the before-and-after results can be compared against the same standards.

**Diagnosis**

**Stage:** service start-up. **Mechanism:** the pipeline's heavy dependencies are created lazily, inside the first `/ask` a fresh server receives, so the first user pays for set-up as well as for their answer.

I timed each lazy step on its own (no Gemini call):

| Created on first use                                      | Where                                                                | Time    |
| --------------------------------------------------------- | -------------------------------------------------------------------- | ------- |
| Chroma client                                             | `store.py::_client`                                                  | 184 ms  |
| ONNX embedding model (loads on the first thing it embeds) | `store.py::search` (707 ms on the first search, 65 ms on the second) | ~640 ms |
| Gemini client                                             | `generate.py::_get_client`                                           | 483 ms  |

Together that is about 1.3 s that only the first request pays. The cold-start measurement below confirms it: the first request after a fresh start averaged 2,230 ms, against about 700 ms for a warm request.

**Chosen Improvement**

I added `serve.py::warm_up()`, called from `main()` before `app.run()`. It imports the pipeline, runs one real `store.search()` (which opens the Chroma client and loads the embedding model), and creates the Gemini client. It makes no Gemini API call, uses no tokens, and writes nothing to the request log. Retrieval, the relevance gate and answer generation are unchanged; the same functions are just called earlier. If warm-up fails (no index, no API key), it reports the failure and the server still starts, so `/health` and `/ask` behave exactly as before.

**Measurement Plan**

1. Measure three cold first requests and the start-up time on the unchanged code (`python measure_cold_start.py --label before`, committed in `1662b4b` before the fix).
2. Make the fix (`e86211d`).
3. Measure the same way again (`--label after`).
4. Rerun the full acceptance set, three trials each, in the same format (`python run_trials.py --trial N --label after`, plus three fresh clones for criterion 4).

`measure_cold_start.py` launches `python serve.py` itself and checks readiness by opening a TCP connection, not by calling `/health`, because `/health` opens the Chroma client and would warm up part of what is being measured.

**Results: Cold Start Before and After**

From `results/capstone_coldstart_before.json` and `results/capstone_coldstart_after.json`, produced by `measure_cold_start.py::one_cold_start()`. Each run is a brand-new server process with `AI201_CACHE=0`. All six first requests were real answers: HTTP 200, `cache_hit: false`, 460 prompt tokens.

| Measure                                              | Before (runs 1 / 2 / 3)  | Before avg   | After (runs 1 / 2 / 3)   | After avg    | Change               |
| ---------------------------------------------------- | ------------------------ | ------------ | ------------------------ | ------------ | -------------------- |
| First request after a fresh start                    | 2,529 / 2,165 / 1,994 ms | **2,230 ms** | 569 / 1,010 / 651 ms     | **743 ms**   | **−1,486 ms (−67%)** |
| Start-up (launch until the port accepts connections) | 161 / 142 / 190 ms       | **164 ms**   | 2,100 / 1,478 / 1,519 ms | **1,699 ms** | **+1,535 ms**        |

The same effect shows up in the full trials. Criterion 2's warm-up request in trial 1, the first request a freshly started server answered, took **2,766 ms before** the fix and **725 ms after**.

**Run Log and Verdicts — After Improvement**

Same criteria, same `run_trials.py`, same question sets, server started once with `AI201_CACHE=0` and not restarted between trials. Results are in `results/capstone_trial_{1,2,3}_after.json`.

| Criterion                 | Target         | Run 1                      | Run 2                            | Run 3                            | Verdict    |
| ------------------------- | -------------- | -------------------------- | -------------------------------- | -------------------------------- | ---------- |
| 1. Logging completeness   | 10/10          | 10/10                      | 10/10                            | 10/10                            | MET        |
| 2. Warm-request latency   | ≤ 1,000 ms avg | 822.4 ms (432.19–1,151.94) | **1,039.2 ms** (477.26–3,514.16) | **1,104.3 ms** (590.07–1,730.78) | **MISSED** |
| 3. Failure observability  | 6/6            | 6/6                        | 6/6                              | 6/6                              | MET        |
| 4. Reproducible execution | 5/5 steps      | _pending_                  | _pending_                        | _pending_                        | _pending_  |
| 5. RAG behaviour          | 8/8            | 8/8                        | 8/8                              | 8/8                              | MET        |

**Before and after, side by side**

| Criterion                 | Before (T1 / T2 / T3)  | Before | After (T1 / T2 / T3)       | After      |
| ------------------------- | ---------------------- | ------ | -------------------------- | ---------- |
| 1. Logging completeness   | 10/10, 10/10, 10/10    | MET    | 10/10, 10/10, 10/10        | MET        |
| 2. Warm-request latency   | 659.0, 718.8, 731.5 ms | MET    | 822.4, 1,039.2, 1,104.3 ms | **MISSED** |
| 3. Failure observability  | 6/6, 6/6, 6/6          | MET    | 6/6, 6/6, 6/6              | MET        |
| 4. Reproducible execution | 5/5, 5/5, 5/5          | MET    | _pending_                  | _pending_  |
| 5. RAG behaviour          | 8/8, 8/8, 8/8          | MET    | 8/8, 8/8, 8/8              | MET        |

**Diagnosis of the Criterion 2 Miss**

Criterion 2 missed in after-trials 2 and 3. The target has to hold in all three trials, so the verdict is MISSED.

**Stage:** generation, the Gemini API call in `generate.py::generate`. **Mechanism:** Gemini's response time varies from minute to minute, and criterion 2's target is an _average of ten requests_, so one slow response, or a few slow minutes, pushes the whole trial over 1,000 ms.

The per-request durations show both patterns (`criteria["2"]["durations_ms"]`):

| Trial     | Median  | Average     | Measured durations (ms)                                                                    |
| --------- | ------- | ----------- | ------------------------------------------------------------------------------------------ |
| Before T1 | 601.4   | 659.0       | 624.79, 850.05, 949.13, 577.99, 792.19, 512.29, 556.81, 505.97, 491.97, 729.11             |
| Before T2 | 682.1   | 718.8       | 682.26, 879.10, 663.66, 791.62, 535.33, 589.25, 1,018.44, 682.03, 695.22, 650.84           |
| Before T3 | 687.9   | 731.5       | 898.56, 590.75, 655.67, 690.40, 878.99, 957.27, 868.04, 588.90, 500.58, 685.49             |
| After T1  | 881.8   | 822.4       | 659.12, 867.64, 1,151.94, 672.43, 1,067.55, 649.48, 918.06, 432.19, 896.01, 909.84         |
| After T2  | 712.1   | **1,039.2** | 477.26, 762.48, 655.81, 661.70, **3,514.16**, 952.69, 658.07, 924.09, 1,168.71, 617.43     |
| After T3  | 1,136.9 | **1,104.3** | 1,730.78, 881.97, 664.17, 1,185.07, 1,378.01, 1,088.64, 1,480.62, 590.07, 1,384.59, 659.29 |

- **After T2 is one outlier.** Its median (712 ms) is almost the same as before (682 ms). A single 3,514 ms response lifted the average from about 760 ms to 1,039 ms.
- **After T3 was slow throughout** (median 1,137 ms). Its unmeasured warm-up took 2,828 ms on a server that had already warmed up and already served two trials, so that time cannot be start-up. It was spent waiting on the model.

**Why the fix is not the cause:** commit `e86211d` only adds `warm_up()` before `app.run()`. A warm request runs exactly the same code as before the fix (the `/ask` handler, retrieval, the gate and generation are unchanged), and Gemini received identical prompts (prompt tokens 460, 459, 446 … in both before and after trials).

**Limit of this diagnosis:** the log records only total `duration_ms`. It does not split retrieval time from Gemini time, so attributing the slow requests to Gemini is an inference from the evidence above, not a direct measurement.

This is the same weakness named under _Assessment of the Targets_: an average-based latency target is sensitive to single spikes. In the before trials, spikes of 4,265 ms and 3,952 ms happened to land in criterion 1's requests, not criterion 2's. After the fix, they landed in criterion 2's.

**Did It Help?**

**Yes, for what it targeted, at a cost, and with no effect on warm requests.**

- **Helped:** the first request after a fresh start dropped from 2,230 ms to 743 ms, which is now the same as a warm request. The first user no longer pays for set-up.
- **The trade-off:** start-up went from 164 ms to 1,699 ms. The work moved; it did not disappear. Start-up plus first request totals about 2,394 ms before and 2,442 ms after. The fix helps whenever the server is started before a user arrives, which is how a running service is used. It does not help someone who starts the server and asks a question immediately.
- **No effect on warm requests:** the fix does not touch the request path, and criterion 2's miss after the fix comes from the model's response time, not from this change.
- **Limitation:** `warm_up()` runs only from `main()`, so `python serve.py` (the Path B run command) benefits. `gunicorn serve:app` never calls `main()` and would still start cold.

**What I'd Do Next**

- **Log retrieval and generation time separately** (`retrieval_ms`, `generation_ms`), so a slow request can be attributed to a stage directly instead of by inference.
- **Tighten criterion 2** to a per-request or slowest-1-in-10 target instead of an average, plus a separate target for the first request after a fresh start. With these data, an average hides exactly the requests a user would notice.
- **Move the warm-up into module load or a gunicorn hook**, so it also runs when a host starts the service.
