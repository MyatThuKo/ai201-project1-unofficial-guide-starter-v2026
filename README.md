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

The following files contain the complete HTTP responses, structured log records, and evaluation results:

- `results/capstone_trial_1.json`
- `results/capstone_trial_2.json`
- `results/capstone_trial_3.json`

Criterion 1 was evaluated by `criterion_1()` in `run_trials.py`, verifying structured log records and request metadata.

Criterion 2 was evaluated by `criterion_2()`, which excluded the warm-up request and calculated average latency from ten measured requests per trial.

Criterion 3 was evaluated by `criterion_3()`, using five invalid HTTP requests and one mocked `RuntimeError` per trial.

Criterion 5 was evaluated by `criterion_5()`, which sent questions through `/ask` and used `scorer.judge()` with retrieved documents to check answer correctness and citations.

**Observations**

All four automated criteria met their acceptance targets across three trials.

The mean warm-request latency across the three trials was approximately 703.1 ms, below the 1,000 ms target. However, individual requests in the separate structured-logging tests occasionally exceeded three or four seconds.

This suggests that average latency alone does not fully describe response-time consistency.

Criterion 4 remains pending until the three clean-checkout trials have been documented.
