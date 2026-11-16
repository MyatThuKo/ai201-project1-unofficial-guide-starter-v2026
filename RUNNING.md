# Running this project

Everything about how the starter works and how to use it.

---

## Before your first class

Setup happens **before class**, not during it. The
[environment setup page](../pages/ide_setup) has the per-operating-system
commands, the exact versions, and where to get your API key.

The short version, from inside this repo after you've forked and cloned it:

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then paste your key into .env
python test.py
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env         # then paste your key into .env
python test.py
```

**You're ready when `python test.py` passes.** The first run is slow — it
downloads the embedding model, about 80 MB. That's exactly why this happens
before class rather than during it.

The model comes down from Chroma's own servers, not from Hugging Face, and
embedding runs entirely on your machine. If your network blocks one of those
and not the other, this is the one that has to get through:
`chroma-onnx-models.s3.amazonaws.com`.

If it doesn't pass and you've made one honest attempt at the error, post the
**whole** output in the help channel. Setup problems are normal and nobody has
ever been judged for having one.

> **Activate the virtual environment every time you open a new terminal.** You
> should see `(.venv)` at the start of your prompt. Installing into your system
> Python instead is the single most common cause of "it worked yesterday."

---

## Your first five minutes

```bash
python app.py corpora                     # see what's available
python app.py index                       # build the search index
python app.py ask "is the housing lottery random?"
```

That's the whole pipeline running end to end. The answer won't be great yet —
you're checking that it runs at all and that your key works.

To use a different corpus:

```bash
python app.py --corpus city_guides index
python app.py --corpus city_guides ask "how do I get to Kestrelford?"
```

Or set `CORPUS` in `config.py` once and stop typing it. **Re-run `index` after
switching corpora.**

---

## Every command

| Command                             | What it does                                                                                                                 |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `python test.py`                    | Checks your environment. Run it whenever something feels off                                                                 |
| `python app.py corpora`             | Lists the provided corpora with a one-line description                                                                       |
| `python app.py index`               | Loads, chunks, embeds and stores your corpus. Run after any change to chunking                                               |
| `python app.py ask "question"`      | Asks one question, end to end                                                                                                |
| `python app.py ask`                 | Keeps asking until you press Enter on an empty line                                                                          |
| `python app.py chunks`              | Prints sample chunks — **Milestone 3**                                                                                       |
| `python app.py retrieve "question"` | Shows distances without spending a model call — **Milestone 4**                                                              |
| `python run_eval.py --label before` | Runs every test question three times, puts every `OUT_OF_SCOPE` question through the gate, and writes a run log — **unit 2** |

Useful flags:

| Flag              | Works on                   | What it does                                                   |
| ----------------- | -------------------------- | -------------------------------------------------------------- |
| `--corpus NAME`   | all                        | Use a different corpus without editing `config.py`             |
| `--variant NAME`  | `index`, `ask`, `retrieve` | Keep two different indexes of the same corpus side by side     |
| `-n 5`            | `chunks`                   | How many chunks to print                                       |
| `--top-k 8`       | `ask`, `retrieve`          | Retrieve more or fewer chunks                                  |
| `--threshold 0.7` | `ask`                      | Try a different relevance cutoff without editing `config.py`   |
| `--label before`  | `run_eval.py`              | Names the output file, so before and after are distinguishable |

---

## Which command goes with which milestone

| Milestone | What you're doing                   | Command                                                       |
| --------- | ----------------------------------- | ------------------------------------------------------------- |
| 1         | Pick a corpus and see it work       | `app.py corpora`, `app.py index`, `app.py ask "..."`          |
| 2         | Write your acceptance criteria      | Edit `criteria.md` and `questions.py`                         |
| 3         | Swap in your own chunker            | Edit `chunker.py`, then `app.py index` and `app.py chunks`    |
| 4         | Tune retrieval, set your cutoff     | `app.py retrieve "..."`, then edit `THRESHOLD` in `config.py` |
| 5         | Write it up                         | Fill in `README.md`                                           |
| Unit 2    | Run the test, fix one thing, re-run | `run_eval.py --label before` … `run_eval.py --label after`    |

`app.py chunks` prints each chunk with its **source file and the function that
produced it** — both of which your README has to name. Copy them straight
across.

`run_eval.py` also runs the five questions in `OUT_OF_SCOPE` at the bottom of
`questions.py` through retrieval and the relevance gate, and puts what happened
in the run log under its own heading. That's the evidence for criterion 3, and
it costs you nothing: a question the gate refuses never reaches the model, so
there is no API call. It runs them once rather than three times, because
retrieval is deterministic and the gate is a comparison against a fixed
number — three passes would produce the same three answers.

---

## Where everything lives

| File           | What it does                                                                                                     |
| -------------- | ---------------------------------------------------------------------------------------------------------------- |
| `config.py`    | Every setting worth changing: chunk size, overlap, top-k, the relevance cutoff                                   |
| `ingest.py`    | Loads documents off disk and cleans them — **stage 1**                                                           |
| `chunker.py`   | Splits documents into chunks — **stage 2, and the file you replace in Milestone 3**                              |
| `store.py`     | Embeds chunks, stores them, retrieves them with distances — **stages 3 and 4**                                   |
| `gate.py`      | The relevance gate. Refuses questions nothing came back close enough for                                         |
| `generate.py`  | Writes the answer — **stage 5**. The only thing that calls out to a service                                      |
| `app.py`       | The command line                                                                                                 |
| `serve.py`     | The same pipeline behind HTTP, for when it has to run as a service — **unit 9**                                  |
| `run_eval.py`  | Runs your questions repeatedly and writes the run log                                                            |
| `questions.py` | Your five test questions, and the five out-of-corpus ones the gate should refuse. **You fill in the first five** |
| `criteria.md`  | Your five acceptance criteria. **You fill this in**                                                              |
| `README.md`    | Your submission                                                                                                  |
| `corpora/`     | The provided documents, and `corpora/README.md` describing each                                                  |
| `results/`     | Run logs, written by `run_eval.py`. **Commit these** — they're your evidence                                     |

The five stages matter more than they look. In unit 2 you diagnose each failure
by naming which stage caused it, so it's worth knowing now which file is which.

---

## About rate limits

The free tier allows a small number of calls per minute. `generate.py` handles
this for you:

- **It paces its own requests** and prints a message when it's waiting. **A
  pause is the starter doing its job, not a bug.**
- **It caches repeated prompts** while you're building, so re-running the same
  question twenty times while debugging costs one call.
- **Caching turns itself off during evaluation runs.** Three runs of the same
  question have to be three real answers, not one answer repeated.
- **It stops if a session makes an unreasonable number of calls**, rather than
  silently draining your whole day's allowance. If you hit that, you almost
  certainly have a loop running away — look for it before raising the limit in
  `config.py`.
- **It prints how many calls and tokens you've used** when you exit. The
  token counts come off the responses themselves, so they're a measurement of
  what a run cost rather than an estimate.

If you see a `429` or "resource exhausted" error, that's a rate limit and not a
broken key. Wait a minute and re-run.

---

## When something goes wrong

| What you see                                            | What it means                                                                                                  |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `No index called '...'. Run python app.py index first.` | You haven't indexed, or you switched corpus without re-indexing                                                |
| `No GEMINI_API_KEY found`                               | No `.env` file, or the key wasn't pasted in. On Windows check it didn't save as `.env.txt`                     |
| `No corpus at ...`                                      | The corpus name is wrong. `python app.py corpora` lists the real ones                                          |
| The system refuses everything                           | Your cutoff is too low for this corpus. Try `--threshold 0.75` to confirm, then set it properly in Milestone 4 |
| The system never refuses anything                       | Your cutoff is too high. Same process in reverse                                                               |
| `[rate limit] ... Waiting 34s`                          | Working as intended. Leave it                                                                                  |
| `QuotaGuard: This session has made 300 requests`        | A loop is running away. Find it before raising the budget                                                      |
| Indexing is very slow                                   | Expected on the first run — it's downloading the embedding model. Later runs are much faster                   |

Still stuck after one honest attempt? Post in the help channel with the full
error, what you ran, and what you expected. You are not expected to debug your
own machine alone.

---

## Running it somewhere else — **unit 9**

Unit 1 doesn't need this. It's here because the file it describes ships in the
starter, and finding out in unit 9 that it exists is worse than reading one
table now.

`serve.py` puts the same pipeline behind HTTP, so it can run as a service that
stays up instead of a command that exits.

```bash
python serve.py                    # locally, on port 5001
gunicorn serve:app                 # the way a host starts it
```

| Thing           | What it does                                                                    |
| --------------- | ------------------------------------------------------------------------------- |
| `POST /ask`     | Send `{"question": "..."}`, get the answer and its sources back as JSON         |
| `GET /health`   | Says whether the service is up and whether an index exists to search            |
| `PORT`          | The port to listen on. Hosts set it for you; on your laptop it defaults to 5001 |
| `AI201_DEBUG=1` | Flask's reloader and debugger. Local only — never set it on a deployed service  |

> The free hosting tier sleeps after about fifteen minutes with no traffic, so
> the first request after a quiet spell waits roughly a minute for it to wake
> up. That's the tier, not your code.

`serve.py` now writes a structured log record for every request — see
**Running The Unofficial Guide (Capstone)** at the bottom of this file.

---

## Stretch features

Optional, for extra credit. **Say what you're adding in your README before you
start** — a feature the README never claims earns nothing.

- **Metadata filtering** — let people narrow results by source or date. Chroma
  supports a `where` clause on `collection.query`; `store.py::search` is where
  it would go.
- **Conversational memory** — let the next question build on the last.
- **A second embedding model** — swap `EMBEDDING_MODEL` in `config.py`, index
  into a different `--variant`, and write down what moved. This is the one
  option that needs a package the default install doesn't have:
  `pip install 'sentence-transformers>=3.4,<3.5'` first. It's a large install
  (it brings PyTorch), so do it before class, not during. Expect your
  threshold to move too — a different model means different distances, and
  the 0.6 you measured in Milestone 4 was measured against this one.

`rank-bm25` is already installed for unit 2's hybrid-search option. The
dependency ships; the implementation is yours.

---

## A note on committing

Commit as you go — at least four new commits in unit 1, at least four more in
unit 2. Your commit history is what shows your criteria existed before your
results did.

**Do not delete and recreate this repository.** You submit the same URL both
units.

`results/` is deliberately **not** in `.gitignore`. Your run logs are evidence
that the test actually happened, and they're part of what gets graded.

# Running The Unofficial Guide (Capstone)

## Run path

**Path B — local with logs.** The system runs on your machine as a Flask HTTP
service (`serve.py`). Every request to it writes one structured JSON record to
`logs/requests.jsonl`.

## What the environment needs

| Thing | Requirement |
|---|---|
| Python | 3.11, 3.12 or 3.13 (tested on **3.13.15**). Not 3.14 — several dependencies don't support it yet |
| Dependencies | `requirements.txt` — every package pinned with lower and upper bounds |
| API key | A Gemini API key in `.env` as `GEMINI_API_KEY` (free at https://aistudio.google.com) |
| Model files | Chroma's ONNX build of **all-MiniLM-L6-v2**, downloaded automatically the first time you build the index into `~/.cache/chroma` (**166 MB** on disk) |
| Corpus | `advice_threads` (ships in `corpora/`) |
| Disk | About 380 MB for `.venv`, plus the model cache above |

`.env` and `chroma_db/` are both in `.gitignore`, so **a fresh clone has neither
a key nor an index**. Steps 3 and 4 below create them.

## From a clean checkout

> The code blocks below have **no `#` comments in them** on purpose. macOS's
> default shell (zsh) does not treat `#` as a comment when you paste commands,
> so an inline comment gets passed to the command as extra arguments. This was
> found by testing these instructions from a fresh clone.

**1. Get the code**

```bash
git clone <repository-url> unofficial-guide
cd unofficial-guide
```

**2. Create the environment and install the pinned dependencies**

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**3. Add your key.** Copy the template, then open `.env` and paste your key
after `GEMINI_API_KEY=`.

```bash
cp .env.example .env
```

**4. Build the index.** The first run also downloads the 166 MB embedding model.

```bash
python app.py index
```

## Start the service — the single command

```bash
AI201_CACHE=0 python serve.py
```

It listens on **http://localhost:5001**.

- **Why 5001, not 5000:** on macOS, AirPlay Receiver already listens on port
  5000 and answers every request with an empty `403 Forbidden`, so requests
  never reach Flask. Set `PORT=...` to use a different port.
- **Why `AI201_CACHE=0`:** with the cache on, a repeated question is answered
  from `.cache/` without calling Gemini, so its duration and token count are
  not a real run. Leave the cache off whenever you're measuring.

## Check it's working (second terminal)

```bash
source .venv/bin/activate
curl http://localhost:5001/health
```

Expect `"index_ready": true`. Then ask one question:

```bash
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Is the housing lottery random?"}'
```

## Run a measured session

With the server running in the first terminal, in the second:

```bash
rm -f logs/requests.jsonl
python run_capstone_requests.py
python measure_cost.py
cp logs/requests.jsonl results/capstone_m3_session.jsonl
```

In order: start from an empty log; send 12 questions plus 2 bad requests;
print the averages from the log; save the session as evidence. `logs/` is in
`.gitignore`, so the copy in `results/` is the committed run record.

## The structured log

`logs/requests.jsonl` — one JSON object per line, one line per request,
written for every route and every outcome (including 400s and 500s).

| Field | Meaning |
|---|---|
| `timestamp`, `ts` | When the request finished (UTC, ISO 8601) |
| `request_id` | A UUID for this request |
| `method`, `path`, `http_status` | The HTTP request and response status |
| `outcome` | `answered`, `refused` (gate said no — still a 200), `bad_request` (400), `error` (500), or `completed` (`/health`) |
| `question`, `question_length` | The input |
| `answer` | The output, first 300 characters |
| `sources`, `n_sources` | Documents the answer was grounded in |
| `best_distance` | Closest retrieved chunk's distance — the number the gate compared to its threshold |
| `prompt_tokens`, `output_tokens` | Gemini tokens this request used, from the API's own `usage_metadata` (0 for refusals and cache hits) |
| `cache_hit` | `true` if the answer came from the local cache instead of Gemini |
| `duration_ms` | Server-side time from request in to response out, via `time.perf_counter()` |
| `error_type` | The exception class name on a 500, otherwise `null` |

Read it with:

```bash
jq -c '{outcome, http_status, duration_ms, prompt_tokens, output_tokens, question}' logs/requests.jsonl
```

`duration_ms` does not include writing the log line or network time to the
client. The **first** `/ask` after start-up is slower: it loads Chroma and the
index.

## Tests

```bash
python -m unittest test_capstone_logging.py -v
```

Checks the log record for every outcome without calling Gemini.
