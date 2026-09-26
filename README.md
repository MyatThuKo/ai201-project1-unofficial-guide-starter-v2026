# The Unofficial Guide

<!-- Replace this line with your name and which corpus you picked. -->

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

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

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

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

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

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
