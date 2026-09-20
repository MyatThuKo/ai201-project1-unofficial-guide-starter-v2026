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
