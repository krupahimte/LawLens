"""Central configuration: paths, model names, and tunable settings.

Every module imports from here so nothing is hard-coded elsewhere.
Values can be overridden with environment variables (or a .env file).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# ---- data locations ---------------------------------------------------------
RAW_DIR = BASE_DIR / "data" / "raw"            # original PDFs: never modified
OCR_DIR = BASE_DIR / "data" / "ocr"            # per-page OCR output (derived)
PROCESSED_DIR = BASE_DIR / "data" / "processed"  # chunks.jsonl (derived)
CHROMA_DIR = BASE_DIR / "chroma_db"            # persistent vector database

# ---- Tesseract OCR ----------------------------------------------------------
TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA_DIR = BASE_DIR / "tessdata"           # holds hin.traineddata + eng.traineddata
OCR_DPI = int(os.getenv("OCR_DPI", "300"))
OCR_WORKERS = int(os.getenv("OCR_WORKERS", "4"))

# ---- Ollama models ----------------------------------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")
# Qwen3-4B *Instruct-2507*: answers directly. The plain "qwen3:4b" tag is the Thinking build, which
# reasons for minutes on CPU and leaks that reasoning into the answer.
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen3:4b-instruct-2507-q4_K_M")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "600"))

# ---- scope ------------------------------------------------------------------
# Hindi support is paused (Hindi PDFs are scans/Bills with unreliable OCR). All Hindi/OCR code is kept;
# set ENABLE_HINDI=true to bring Hindi documents, retrieval and the language selector back.
ENABLE_HINDI = os.getenv("ENABLE_HINDI", "false").strip().lower() in ("1", "true", "yes")

# ---- vector store -----------------------------------------------------------
# "indian_law_en" is the clean English-only collection the MVP serves. "indian_law" is the old mixed English+Hindi
# collection (kept untouched, backed up under backups/). NOTE: the vector store creates a collection if the name does not
# exist, so a typo here silently gives an empty collection: check /health ("indexed_chunks") after starting.
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "indian_law_en")

# ---- chat history ------------------------------------------------------------
# Server-side conversation log (used for follow-up questions). Point this at another file to run experiments
# without touching the real history.
CONVERSATIONS_DB = Path(os.getenv("CONVERSATIONS_DB", str(BASE_DIR / "data" / "conversations.sqlite3")))

# ---- chunking ---------------------------------------------------------------
MAX_CHUNK_CHARS = int(os.getenv("MAX_CHUNK_CHARS", "2000"))
CHUNK_OVERLAP_CHARS = int(os.getenv("CHUNK_OVERLAP_CHARS", "200"))

# ---- retrieval --------------------------------------------------------------
TOP_K = int(os.getenv("TOP_K", "6"))
# Cosine distance above this means "not relevant enough" (0 = identical).
# Calibrated later against real queries; see rag/retrieval.py.
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "0.65"))

# ---- context assembly (rag/retrieval.py: assemble_context) -------------------
# How much source text the language model may see, counted in characters (~4 characters per token).
# 10,000 characters is about 2,500 tokens, which fits easily inside the 8,192-token context window together with
# the instructions and a 700-token answer.
CONTEXT_CHAR_BUDGET = int(os.getenv("CONTEXT_CHAR_BUDGET", "10000"))
EXACT_BUDGET_FRACTION = float(os.getenv("EXACT_BUDGET_FRACTION", "0.6"))    # share of the budget reserved for exact matches
MAX_PROVISIONS = int(os.getenv("MAX_PROVISIONS", "6"))                      # distinct provisions (was a hard-coded 4)
MAX_SCHEDULE_CHUNKS = int(os.getenv("MAX_SCHEDULE_CHUNKS", "1"))            # Schedule table chunks per answer
MIN_PROVISIONS_BEFORE_SCHEDULE = int(os.getenv("MIN_PROVISIONS_BEFORE_SCHEDULE", "3"))
# ---- answer verification (rag/guardrails.py) ----------------------------------
# Warnings come from heuristics that were measured on the 43-case baseline; "confirmed errors" are deterministic.
QUOTE_MIN_WORDS = int(os.getenv("QUOTE_MIN_WORDS", "4"))                    # shorter quoted terms are not treated as quotations
QUOTE_APPROX_RATIO = float(os.getenv("QUOTE_APPROX_RATIO", "0.85"))         # similarity at which a near-match is "approximate"
SUPPORT_MIN_RATIO = float(os.getenv("SUPPORT_MIN_RATIO", "0.5"))            # share of a sentence's content words found in the sources
MISCITED_ALL_MIN_RATIO = float(os.getenv("MISCITED_ALL_MIN_RATIO", "0.75")) # ...in ALL sources, for a "wrong source cited" warning
if not 1_000 <= CONTEXT_CHAR_BUDGET <= 20_000:
    raise ValueError("CONTEXT_CHAR_BUDGET must be between 1,000 and 20,000 characters (the model window is 8,192 tokens)")
