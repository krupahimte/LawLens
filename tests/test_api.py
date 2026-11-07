"""API tests with the RAG pipeline stubbed out (fast; no Ollama needed)."""
import json

import pytest
from fastapi.testclient import TestClient

import main
from rag import pipeline
from rag.embeddings import OllamaError

client = TestClient(main.app)

SOURCE = {
    "n": 1, "label": "Bharatiya Nyaya Sanhita, 2023, Section 303", "act_name": "Bharatiya Nyaya Sanhita, 2023",
    "act_name_en": "Bharatiya Nyaya Sanhita, 2023", "unit": "section", "unit_label": "Section", "section_number": "303",
    "section_title": "Theft", "language": "en", "doc_id": "bns_en", "file": "bns_english.pdf", "page_start": 50,
    "page_end": 50, "text_source": "text_layer", "ocr_conf": -1.0, "low_quality": False, "number_verified": 1,
    "match": "semantic", "distance": 0.31, "snippet": "Theft...",
}
FINAL = {
    "type": "final", "status": "answered", "answer": "Theft is punishable [1].", "language": "en",
    "sources": [SOURCE], "notes": [], "disclaimer": "Not legal advice.", "conversation_id": "abc",
    "standalone_question": "q", "timings": {"total_s": 1.0},
}


def test_source_chunk_id_is_optional_and_returned_when_present(monkeypatch):
    """Backward compatibility: payloads without chunk_id stay valid; payloads with it keep it in /chat."""
    monkeypatch.setattr(pipeline, "answer", lambda q, lang, cid: FINAL)
    without = client.post("/chat", json={"question": "punishment for theft?"}).json()
    assert without["sources"][0]["chunk_id"] == ""                       # default, nothing breaks
    with_id = {**FINAL, "sources": [{**SOURCE, "chunk_id": "bns_en:303:5"}]}
    monkeypatch.setattr(pipeline, "answer", lambda q, lang, cid: with_id)
    assert client.post("/chat", json={"question": "punishment for theft?"}).json()["sources"][0]["chunk_id"] == "bns_en:303:5"


def test_make_source_carries_chunk_id():
    chunk = {"chunk_id": "bns_en:303:5", "doc_id": "bns_en", "act_name": "Bharatiya Nyaya Sanhita, 2023",
             "act_name_en": "Bharatiya Nyaya Sanhita, 2023", "unit": "section", "section_number": "303", "section_title": "Theft",
             "language": "en", "page_start": 50, "page_end": 50, "text_source": "text_layer", "ocr_conf": -1.0,
             "low_quality": False, "number_verified": 1, "distance": 0.2, "text": "x" * 10}
    source = pipeline.make_source(1, chunk)
    assert source["chunk_id"] == "bns_en:303:5" and source["section_number"] == "303"


def test_home_serves_frontend():
    r = client.get("/")
    assert r.status_code == 200 and "Indian Law Assistant" in r.text


def test_health_reports_components():
    body = client.get("/health").json()
    assert {"status", "ollama", "models_ready", "indexed_chunks"} <= body.keys()


def test_chat_returns_answer_and_sources(monkeypatch):
    monkeypatch.setattr(pipeline, "answer", lambda q, lang, cid: FINAL)
    r = client.post("/chat", json={"question": "punishment for theft?"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered" and body["sources"][0]["section_number"] == "303"
    assert body["disclaimer"]


@pytest.mark.parametrize("payload", [{"question": ""}, {"question": "x"}, {"question": "ok question", "language": "fr"},
                                     {"question": "a" * 1001}, {}])
def test_chat_rejects_bad_input(payload):
    assert client.post("/chat", json=payload).status_code == 422


def test_chat_reports_ollama_down_as_503(monkeypatch):
    def boom(*a):
        raise OllamaError("Cannot reach Ollama")
    monkeypatch.setattr(pipeline, "answer", boom)
    r = client.post("/chat", json={"question": "what is bail?"})
    assert r.status_code == 503 and "Ollama" in r.json()["detail"]


def test_stream_emits_ndjson_events(monkeypatch):
    events = [{"type": "sources", "sources": [SOURCE], "language": "en", "conversation_id": "abc"},
              {"type": "token", "text": "Theft"}, FINAL]
    monkeypatch.setattr(pipeline, "answer_stream", lambda q, lang, cid: iter(events))
    r = client.post("/chat/stream", json={"question": "punishment for theft?"})
    lines = [json.loads(x) for x in r.text.strip().splitlines()]
    assert [e["type"] for e in lines] == ["sources", "token", "final"]


def test_stream_turns_failures_into_error_event(monkeypatch):
    def broken(*a):
        raise OllamaError("model missing")
        yield
    monkeypatch.setattr(pipeline, "answer_stream", broken)
    lines = [json.loads(x) for x in client.post("/chat/stream", json={"question": "what is bail?"}).text.strip().splitlines()]
    assert lines[-1]["type"] == "error" and "model missing" in lines[-1]["message"]


def test_pdf_endpoint_serves_original_and_rejects_unknown():
    ok = client.get("/pdf/bsa_en")
    assert ok.status_code == 200 and ok.headers["content-type"] == "application/pdf" and ok.content[:4] == b"%PDF"
    assert client.get("/pdf/../../etc/passwd").status_code in (404, 422)
    assert client.get("/pdf/not_a_doc").status_code == 404
