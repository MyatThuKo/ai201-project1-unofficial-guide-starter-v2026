"""
The scorer — deciding, in code, whether a run was correct.

`run_eval.py` looks for one function here:

    judge(question, expects, answer, results) -> bool

It calls it once per question per run and puts the verdict in the run log, so
whatever "correct" means has to mean the same thing on Monday and on Wednesday.
That repeatability is the whole point — a criterion I score by eye is a
criterion I score differently twice.

The first version of this file was one line:

    return expects.lower().strip() in answer.lower().strip()

which fails honest answers for cosmetic reasons. `expects` is `"16GB"` and the
model writes "16 GB of RAM"; `expects` is `"first ten days"` and the model
writes "the first 10 days"; `expects` is `"Tuesday and Wednesday mornings"` and
the model writes "Tuesday or Wednesday morning". None of those are wrong
answers, but a raw substring test marks all three as failures, which would make
my run log measure my phrasing rather than my pipeline.

So matching here works on *terms* instead: the expected phrase is split into
the words that carry meaning, and every one of them has to appear in the text,
in any order, allowing for spacing ("16 GB" / "16GB"), plurals ("morning" /
"mornings"), digits and number words ("ten" / "10"), and "$20" / "20 dollars".
Filler words are dropped, so "October and November" only requires the two
months and doesn't care whether the model joined them with "and" or "or".

`judge` answers one question: was this run right? The five criteria in
`criteria.md` are scored separately by `report()`, which returns one boolean per
criterion for a single run, and by the helpers it is built from:

    criterion 1  retrieval_hit()            the answer is in a retrieved chunk
    criterion 2  names_source()             the answer names a source document
    criterion 3  — the gate; `run_eval.py::check_out_of_scope` already measures it
    criterion 4  chunk_is_clean()           a chunk is a whole thought
    criterion 5  cited_source_supports()    the source it named really has the answer

Run `python scorer.py` to check the matcher against its own examples. That
costs no API calls.
"""

import re
from functools import lru_cache

# gate.py::REFUSAL, kept as a bare marker so this file imports without pulling
# in chromadb. A refusal is never a passing answer to a question my corpus
# covers, no matter what else is in it.
REFUSAL_MARKER = "don't have enough information"

# Words that carry no evidence. Dropping them means "October and November"
# passes when the model writes "October or November" — the months are the
# claim, the conjunction isn't.
FILLER = {
    "a", "an", "the", "and", "or", "of", "in", "on", "at", "for", "to", "is",
    "are", "was", "were", "be", "it", "its", "about", "around", "per", "up",
    "you", "your", "that", "this", "with",
}

NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12",
}
DIGIT_WORDS = {digit: word for word, digit in NUMBER_WORDS.items()}

# Anything that looks like a filename the model could have cited.
FILENAME_RE = re.compile(r"\b[\w./-]+\.(?:txt|md)\b")


# ─── Text matching ───────────────────────────────────────────────────────────


def normalize(text: str) -> str:
    """Lowercase, flatten smart punctuation, collapse whitespace.

    Commas go too, so "1,000" and "1000" are the same string.
    """
    text = (text or "").lower()
    for curly, plain in (("’", "'"), ("‘", "'"),
                         ("“", '"'), ("”", '"')):
        text = text.replace(curly, plain)
    text = re.sub(r"[‐-―]", "-", text)
    text = text.replace(",", "")
    return re.sub(r"\s+", " ", text).strip()


def terms(expects: str) -> list[str]:
    """The meaning-carrying words of an expected phrase.

    "Tuesday and Wednesday mornings" -> ["tuesday", "wednesday", "morning"]
    Trailing plurals come off here; the pattern puts them back as optional, so
    the match works whichever way round the two texts are written.
    """
    out = []
    for word in normalize(expects).split():
        word = word.strip(".!?;:()[]\"'")
        if not word or word in FILLER:
            continue
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        out.append(word)
    return out


def variants(term: str) -> set[str]:
    """Other spellings of the same claim: ten/10, $20/20 dollars."""
    out = {term}
    if term in NUMBER_WORDS:
        out.add(NUMBER_WORDS[term])
    if term in DIGIT_WORDS:
        out.add(DIGIT_WORDS[term])
    money = re.fullmatch(r"\$(\d+(?:\.\d+)?)", term)
    if money:
        out.add(f"{money.group(1)} dollars")
        out.add(f"{money.group(1)} usd")
    return out


@lru_cache(maxsize=512)
def _pattern(variant: str) -> re.Pattern:
    """A regex for one variant, tolerant of spacing and plurals.

    Digit runs, letter runs and symbols are matched with an optional separator
    between them, so "16gb" finds "16 GB" and "16-GB". The surrounding
    lookarounds keep "10" out of the middle of "100"; `(?<!\\w)` rather than
    `\\b` so that a variant starting with "$" still anchors.
    """
    parts = re.findall(r"\d+|[^\W\d_]+|[^\w\s]", variant)
    body = r"[\s\-]*".join(re.escape(part) for part in parts)
    return re.compile(rf"(?<!\w){body}(?:s|es)?(?!\w)")


def contains(text: str, expects: str) -> bool:
    """Does `text` state the fact `expects` describes?

    Every term has to be there, in any order, in any of its spellings.
    """
    haystack = normalize(text)
    wanted = terms(expects)
    if not wanted:
        return False
    return all(
        any(_pattern(v).search(haystack) for v in variants(term))
        for term in wanted
    )


def is_refusal(answer: str) -> bool:
    """The gate refused, or the model declined. Either way, not an answer."""
    return REFUSAL_MARKER in normalize(answer)


# ─── The criteria ────────────────────────────────────────────────────────────


def retrieval_hit(expects: str, results) -> bool:
    """Criterion 1: one of the retrieved chunks contains the answer.

    This reads the chunks, not the model's reply, so it separates a retrieval
    failure from a generation failure — if this is False the model never had
    the answer to work from.
    """
    return any(contains(r.text, expects) for r in results)


def sources_named(answer: str, results) -> set[str]:
    """Which retrieved source documents the answer actually names."""
    haystack = normalize(answer)
    named = set()
    for r in results:
        stem = r.source.rsplit(".", 1)[0]
        if normalize(r.source) in haystack or normalize(stem) in haystack:
            named.add(r.source)
    return named


def names_source(answer: str, results) -> bool:
    """Criterion 2: the answer names at least one source document.

    A filename that wasn't retrieved still counts as *naming* one — criterion 2
    is about citing at all. Whether the citation is the right one is
    criterion 5's job.
    """
    if is_refusal(answer):
        return False
    return bool(sources_named(answer, results)) or bool(
        FILENAME_RE.search(normalize(answer))
    )


def cited_source_supports(expects: str, answer: str, results) -> bool:
    """Criterion 5: the source the answer named really does contain the answer.

    Catches the case where retrieval returns four documents, the answer is
    right, and the model credits the wrong one of the four.
    """
    named = sources_named(answer, results)
    if not named:
        return False
    return any(contains(r.text, expects) for r in results if r.source in named)


def chunk_is_clean(text: str) -> bool:
    """Criterion 4: a chunk is a whole thought, not a fragment.

    A mechanical stand-in for "doesn't start or end mid-word": a chunk that
    begins mid-sentence starts with a lowercase letter, and one that was cut
    off doesn't end on sentence punctuation. It can't tell whether the content
    is *useful* — that part still needs reading — but it catches every chunk
    the old fixed-width splitter sliced through.
    """
    stripped = (text or "").strip()
    if not stripped:
        return False
    if stripped[0].islower():
        return False
    return stripped.endswith((".", "!", "?", '"', "'", ")"))


# ─── What run_eval.py calls ──────────────────────────────────────────────────


def report(question: str, expects: str, answer: str, results) -> dict:
    """Every per-run criterion for one question, as one dict.

    Criterion 3 isn't here: it's about the OUT_OF_SCOPE questions, which never
    reach a model, and `run_eval.py::check_out_of_scope` already measures it.
    """
    return {
        "refused": is_refusal(answer),
        "answer_correct": not is_refusal(answer) and contains(answer, expects),
        "retrieval_hit": retrieval_hit(expects, results),          # criterion 1
        "names_source": names_source(answer, results),             # criterion 2
        "cited_source_supports": cited_source_supports(            # criterion 5
            expects, answer, results
        ),
    }


def judge(question: str, expects: str, answer: str, results) -> bool:
    """Was this run right?

    Right means all three of: it didn't refuse a question my corpus covers, it
    states the fact in `expects`, and it names a source. An answer with the
    right number and no citation isn't a pass — criterion 2 says every answer
    names a source, so an uncited one fails the system's own definition of
    working.

    The per-criterion breakdown behind this verdict is in `report()`.
    """
    scores = report(question, expects, answer, results)
    return scores["answer_correct"] and scores["names_source"]


# ─── Self-check ──────────────────────────────────────────────────────────────

# Phrasings the model has produced or plausibly could, and what each one should
# score. The false cases matter more than the true ones: a matcher that says
# yes to everything is worse than no scorer at all.
_CASES = [
    ("It costs $20 a year to rent a locker.", "$20", True),
    ("The locker is 20 dollars per year.", "$20", True),
    ("Lockers cost $25 a year.", "$20", False),
    ("Get 16 GB of RAM.", "16GB", True),
    ("16GB is the answer.", "16GB", True),
    ("8GB was fine until the last project.", "16GB", False),
    ("Apply in October or November.", "October and November", True),
    ("Applications close in October.", "October and November", False),
    ("Tuesday or Wednesday morning is quietest.", "Tuesday and Wednesday mornings", True),
    ("Sunday evenings are the worst time.", "Tuesday and Wednesday mornings", False),
    ("You have the first 10 days of term.", "first ten days", True),
    ("You have the first ten days of term.", "first ten days", True),
    ("I don't have enough information about that.", "$20", False),
]

_CHUNK_CASES = [
    ("THREAD: Worth getting a parking permit?\n\n--- reply 2 ---\nStreet parking on "
     "Verrill is legal and free.", True),
    ("ing on Verrill is legal and free and unmark", False),
]


def _self_check() -> int:
    failures = 0
    for text, expects, want in _CASES:
        got = contains(text, expects)
        if got != want:
            failures += 1
        print(f"  {'ok  ' if got == want else 'FAIL'}  expects={expects!r:<32} "
              f"got={got!s:<5}  {text}")
    for text, want in _CHUNK_CASES:
        got = chunk_is_clean(text)
        if got != want:
            failures += 1
        print(f"  {'ok  ' if got == want else 'FAIL'}  chunk_is_clean -> {got}")
    print(f"\n{len(_CASES) + len(_CHUNK_CASES) - failures} of "
          f"{len(_CASES) + len(_CHUNK_CASES)} matcher cases correct")
    return failures


if __name__ == "__main__":
    import sys

    print("scorer.py::contains and scorer.py::chunk_is_clean\n")
    sys.exit(1 if _self_check() else 0)
