"""FastAPI backend for the bilingual Indian Law RAG chatbot.

Run:  uvicorn main:app --port 8000      then open http://localhost:8000
"""
import json
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import config
from rag import catalog, pipeline, vectorstore
from rag.embeddings import OllamaError

app = FastAPI(title="Indian Law Assistant", version="1.0")

FRONTEND_DIR = config.BASE_DIR / "frontend"


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    language: Literal["auto", "en", "hi"] = "auto"      # language of the ANSWER
    conversation_id: str | None = None


class Source(BaseModel):
    n: int
    chunk_id: str = ""          # optional: older clients and payloads without it stay valid
    label: str
    act_name: str
    act_name_en: str
    unit: str
    unit_label: str
    section_number: str
    section_title: str
    language: str
    doc_id: str
    file: str
    page_start: int
    page_end: int
    text_source: str
    ocr_conf: float
    low_quality: bool
    number_verified: int
    number_inferred: bool = False
    match: str
    distance: float
    snippet: str


class ChatResponse(BaseModel):
    status: Literal["answered", "insufficient", "ocr_limited", "greeting", "unsupported_language"]
    answer: str
    language: str
    sources: list[Source]
    notes: list[str]
    disclaimer: str
    conversation_id: str
    standalone_question: str
    timings: dict[str, float]
    context_report: dict | None = None      # optional: included/excluded chunks and reasons (answered turns)
    verification: dict | None = None        # optional: confirmed errors, warnings, quotation checks (answered turns)
    generation: dict | None = None          # optional: done_reason, truncated, token counts (answered turns)


NO_CACHE = {"Cache-Control": "no-cache"}  # always revalidate the app shell so updates show up


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html", headers=NO_CACHE)


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(FRONTEND_DIR / "manifest.webmanifest", media_type="application/manifest+json", headers=NO_CACHE)


@app.get("/sw.js")
def service_worker():
    """Served from the site root so the service worker can control the whole app."""
    return FileResponse(FRONTEND_DIR / "sw.js", media_type="application/javascript", headers=NO_CACHE)


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/health")
def health():
    ollama_ok, models = False, []
    try:
        r = httpx.get(f"{config.OLLAMA_URL}/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        ollama_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama": ollama_ok,
        "models_ready": {
            "chat": any(m.startswith(config.CHAT_MODEL) for m in models),
            "embedding": any(m.startswith(config.EMBED_MODEL) for m in models),
        },
        "indexed_chunks": vectorstore.count(),
        "collection": config.COLLECTION_NAME,
        "hindi_enabled": config.ENABLE_HINDI,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        return pipeline.answer(request.question, request.language, request.conversation_id)
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:  # a readable message instead of a bare 500 page
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")


@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    """Newline-delimited JSON events: sources, token..., final (or error)."""
    def events():
        try:
            for event in pipeline.answer_stream(request.question, request.language, request.conversation_id):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except OllamaError as exc:
            yield json.dumps({"type": "error", "message": str(exc)}, ensure_ascii=False) + "\n"
        except Exception as exc:  # never leave the browser hanging on an unexpected failure
            yield json.dumps({"type": "error", "message": f"Unexpected error: {exc}"}, ensure_ascii=False) + "\n"
    return StreamingResponse(events(), media_type="application/x-ndjson")


@app.get("/pdf/{doc_id}")
def pdf(doc_id: str):
    """Serve an original source PDF (read-only) so users can verify a cited page: /pdf/bns_en#page=57"""
    doc = catalog.BY_ID.get(doc_id)
    if doc is None or not doc.path.exists():
        raise HTTPException(status_code=404, detail="Unknown document")
    return FileResponse(doc.path, media_type="application/pdf", filename=doc.filename,
                        content_disposition_type="inline")
