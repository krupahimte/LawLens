# Indian Law Assistant (English MVP)

A local, free question-answering assistant for a fixed set of Indian legal texts. You ask a question in plain English; it retrieves the
relevant provisions, has a small local language model write an answer **using only those provisions**, and shows numbered citations
that open the original PDF page. Everything runs on your own computer: no cloud AI, no API keys.

> **This is an informational legal research assistant, not a lawyer.** It can be wrong, incomplete or out of date. Read the cited source
> text and consult a qualified advocate for your own situation. See [Known limitations](#known-limitations).

## Features

* Chat interface (mobile-first, also fine on desktop, installable as a PWA) with streaming answers, a Stop button, retry on error,
  local chat history, copy-answer, and an About / disclaimer sheet.
* Numbered citations `[1]`, `[2]`: click one to open the source card (Act, section, page, text snippet, link to the original PDF page).
* Exact lookup ("What does Section 103 of the BNS say?") combined with semantic search ("What is the punishment for theft?").
* Safe refusals: if the documents do not answer, it says so instead of guessing; questions in Hindi get a clear "English only" message.
* After each answer a verification pass checks citations, quotations, section numbers and some wording against the sources and shows
  notes ("Verification error" in red, "Check" in yellow). A reply that was cut off at the length limit is marked **"Incomplete answer"**.

**Documents covered (English texts):** Constitution of India; Bharatiya Nyaya Sanhita 2023 (BNS); Bharatiya Nagarik Suraksha Sanhita 2023 (BNSS);
Bharatiya Sakshya Adhiniyam 2023 (BSA); Information Technology Act 2000; Consumer Protection Act 2019.
**Hindi is deferred** (code is kept but switched off).

## Technology and architecture

| Part | Choice |
|---|---|
| Language model | Qwen3-4B **Instruct-2507** (`qwen3:4b-instruct-2507-q4_K_M`) via [Ollama](https://ollama.com). Not the plain `qwen3:4b` tag: that is the "Thinking" build. |
| Embeddings | BGE-M3 (`bge-m3`, 1024-d, cosine) via Ollama |
| Vector store | ChromaDB (persistent, `chroma_db/`) |
| Backend | Python 3.14, FastAPI + Uvicorn |
| Frontend | Plain HTML/CSS/JS in `frontend/` (no build step), served by the backend |
| PDF reading | PyMuPDF |

```
question -> [follow-up rewrite] -> exact lookup + semantic search (ChromaDB, BGE-M3)
         -> relevance gate -> context assembly (10,000-character budget)
         -> Qwen3 answer (streamed, num_predict 700) -> verification -> answer + sources + notes + disclaimer
```

Main files: `main.py` (API + static files), `rag/pipeline.py` (the flow above), `rag/retrieval.py`, `rag/generation.py` (prompt, Ollama call),
`rag/guardrails.py` (verification), `rag/chunking.py` / `rag/extraction.py` (PDF -> chunks), `rag/vectorstore.py`, `rag/conversation.py`,
`rag/language.py` (fixed texts), `config.py` (all settings), `ingest.py`, `validate_index.py`, `run_rag_report.py`, `frontend/`, `tests/`, `docs/`.

## Prerequisites

* Windows (developed on Windows 11), about 16 GB RAM or more, no GPU needed. Disk: about 4 GB for the two models.
* Python 3.14 (other 3.11+ versions probably work but are untested).
* [Ollama](https://ollama.com/download) installed and running.
* Tesseract OCR is **not** needed for the English MVP (it is only used by the deferred Hindi OCR code).

## Installation

```bash
# from the project folder
python -m venv venv
venv\Scripts\activate              # Git Bash: source venv/Scripts/activate
pip install -r requirements.txt

ollama pull bge-m3
ollama pull qwen3:4b-instruct-2507-q4_K_M
```

The legal-text index (`chroma_db/`, collection `indian_law_en`) and the processed chunks (`data/processed/`) are already built in this
project. You do **not** need to ingest anything to run the app.

## Configuration (environment variables)

Defaults work as they are. To override, copy `.env.example` to `.env`. Variables you are most likely to care about:

| Variable | Default | Meaning |
|---|---|---|
| `COLLECTION_NAME` | `indian_law_en` | ChromaDB collection to serve. The store **creates an empty collection if the name does not exist**, so a typo gives an empty index: check `indexed_chunks` in `/health`. (`indian_law` is an older mixed English/Hindi collection, kept untouched.) |
| `OLLAMA_URL` | `http://localhost:11434` | Where Ollama listens |
| `CHAT_MODEL` | `qwen3:4b-instruct-2507-q4_K_M` | Answer model |
| `EMBED_MODEL` | `bge-m3` | Embedding model (must match how the index was built) |
| `OLLAMA_TIMEOUT` | `600` | Seconds to wait for Ollama |
| `CONVERSATIONS_DB` | `data/conversations.sqlite3` | Server-side chat log used for follow-up questions |
| `ENABLE_HINDI` | `false` | Hindi is deferred; leave off |
| `TOP_K`, `MAX_DISTANCE`, `CONTEXT_CHAR_BUDGET`, ... | see `config.py` | Retrieval and context tuning (comments in `config.py`) |

## Running

Backend and frontend are one process: the backend serves the frontend.

```bash
venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. To use it from a phone on the same Wi-Fi, start with `--host 0.0.0.0` and open `http://<your-PC-IP>:8000`
(allow it through the Windows firewall; the app has no login, so only do this on a network you trust).

Ollama must be running first (the Ollama app in the system tray, or `ollama serve`). `http://127.0.0.1:8000/health` shows whether Ollama
and both models are reachable and how many chunks are indexed (2,298 for `indian_law_en`).

## Using the chatbot

1. Type a question (Enter sends, Shift+Enter adds a line) or tap an example.
2. The reply streams in, usually after one to two minutes in total. **Stop** cancels it.
3. Tap a `[n]` marker to open its source card; "Open original PDF page" opens the PDF at that page.
4. Read the notes under the answer. Red "Incomplete answer" / "Verification error" notes mean do not rely on that part.
5. Follow-up questions in the same chat ("What about the punishment?") use the earlier turns. "New chat" starts fresh; chat history is
   stored in your browser only and can be deleted per chat.

Good questions: "What does Section 103 of the BNS say?", "What does Article 21 say?", "What is the punishment for theft?",
"How do I file a consumer complaint?". Poor questions: comparisons across many provisions (see limitations), anything outside the six texts,
requests for personal legal advice.

## Document ingestion (only if you change the documents)

Source PDFs live in `data/raw/` and are never modified. Chunks are written to `data/processed/*.jsonl`; embeddings go to ChromaDB.

```bash
python ingest.py --no-embed                 # rebuild chunk files only (no database writes)
COLLECTION_NAME=indian_law_en python ingest.py --docs bns_en   # (re)embed one document; unchanged chunks are skipped by hash
COLLECTION_NAME=indian_law_en python validate_index.py         # checks the collection; writes docs/INDEX_VALIDATION.md
```

Ingestion **writes to the collection named by `COLLECTION_NAME`**. Do not run it against `indian_law_en` casually; back up `chroma_db/` first.

## Tests

```bash
venv\Scripts\python.exe -m pytest -q -k "not health"
```

The unit tests use fakes (no Ollama, ChromaDB or chat database). The `/health` test is excluded because it opens the real ChromaDB. The
`integration` tests (deselected by default) need a live index and Ollama; some are stale (Hindi).
`run_rag_report.py --name <new-name> [case ids]` runs the 43 fixed questions through the real pipeline (slow, and it **appends to the
chat history database** unless `CONVERSATIONS_DB` points elsewhere).

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| "Cannot reach Ollama at ..." | Start Ollama (tray app or `ollama serve`); check `OLLAMA_URL`. |
| "Model not found" | `ollama pull qwen3:4b-instruct-2507-q4_K_M` and `ollama pull bge-m3`. |
| Answers are about "not enough information" for everything / `indexed_chunks` is 0 | Wrong `COLLECTION_NAME` (an empty collection was created). Set it back to `indian_law_en`. |
| Very slow first answer | The model is loading into memory; later answers are faster. Expect roughly 1 to 2.5 minutes per answer on CPU. |
| A run stalls or times out on a laptop | Windows sleep. Keep it plugged in, lid open, and set sleep to "never" while using it. |
| Page looks old after an update | Hard refresh (Ctrl+F5); the service worker caches the page shell. |
| Hindi question | Hindi is deferred; the app asks you to use English. |
| Port 8000 busy | Use `--port 8001`. |

## Known limitations

Full detail and evidence: [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) and [`docs/HARDENING_REPORT.md`](docs/HARDENING_REPORT.md).
Automated checks passing does **not** mean the answers are legally accurate.

* **Wrong or unsupported legal interpretation is possible.** The comparison question "bailable vs non-bailable offences" (case M2) is still
  unreliable: the model produced unsupported claims such as bailable offences having "no restrictions", misread an IT Act provision, and
  sometimes restated "shall" as "may" (BNSS 478). The checks flag some of these but cannot prevent them, and cannot see others.
* **The modal-change check is narrow.** It only compares wording that appears in both answer and source, and only obligation/prohibition
  turned into "may" (or the reverse). It ignores negated forms, misses paraphrases, and its false-alarm rate on new answers is unknown.
* **Existence claims.** "Does not exist" statements are detected only for a fixed list of phrases.
* **Long provisions can be partial (KL-1).** Exact-match provisions with many parts (for example the Consumer Protection Act section 2
  definitions) may only be partly supplied to the model; a note says so, but a list taken from such a section may be incomplete.
* **Incomplete answers.** Replies are capped at 700 tokens. If the cap is hit, the answer is marked "Incomplete answer" (the text is kept).
  Prompting for shorter answers means list questions may name only some items.
* **Chunk contamination.** Some stored chunks contain page running headers or Gazette fragments, so a quoted passage may not match the
  PDF character for character, and the verbatim check can fail on those pages.
* **Retrieval gaps.** Some questions use vocabulary the index does not connect (for example "anticipatory bail" -> BNSS 482), and then the
  answer may be a refusal or off-target.
* **Latency.** Typical total time was about 1 minute (median 62 s in the last live run, up to about 150 s) on a CPU-only laptop.
* **Scope.** English only; six texts only; not updated for amendments after the PDFs; no legal advice.
* **Privacy / data.** Questions are processed locally. The server keeps a chat log in `data/conversations.sqlite3`; browser chat history is in
  your browser's local storage. There is no login.
