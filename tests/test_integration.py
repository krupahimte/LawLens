"""End-to-end tests against the real index and local models.

Needs: Ollama running with bge-m3 + qwen3:4b, and `python ingest.py` already run.
Run:  pytest -m integration -v
"""
import re

import pytest

from rag import pipeline, retrieval, vectorstore

pytestmark = pytest.mark.integration


def _ready() -> bool:
    try:
        return vectorstore.count() > 500
    except Exception:
        return False


@pytest.fixture(scope="module", autouse=True)
def _index_must_exist():
    """Skip this module's tests when the index is missing.

    This is a fixture, not module-level code, on purpose: module-level code runs while pytest merely
    COLLECTS tests, so every ordinary `pytest` run (even with integration tests deselected) opened ChromaDB.
    A fixture runs only when an integration test really executes (`pytest -m integration`).
    """
    if not _ready():
        pytest.skip("index not built (run: python ingest.py)")


def has(hits, doc_prefix, section, top=6):
    return any(h["doc_id"].startswith(doc_prefix) and h["section_number"] == section for h in hits[:top])


# ---------------------------------------------------------------- retrieval
def test_english_question_finds_theft_section():
    assert has(retrieval.retrieve("What is the punishment for theft?").hits, "bns", "303")


def test_hindi_question_retrieves_english_provision():
    """Cross-language retrieval: a Hindi query must reach the English BNS text."""
    hits = retrieval.retrieve("चोरी की सजा क्या है?").hits
    assert any(h["doc_id"] == "bns_en" and h["section_number"] == "303" for h in hits)


def test_english_question_can_reach_hindi_text():
    hits = retrieval.retrieve("punishment for theft").hits
    assert any(h["language"] == "hi" for h in hits), "no Hindi chunk among candidates"


def test_exact_article_lookup():
    r = retrieval.retrieve("What does Article 21 of the Constitution say?")
    assert r.exact_reference == "21"
    assert any(h["match"] == "exact" and h["doc_id"].startswith("constitution") and h["section_number"] == "21" for h in r.hits)


def test_it_act_hacking_question():
    hits = retrieval.retrieve("unauthorised access to a computer system penalty").hits
    assert has(hits, "it", "43") or has(hits, "it", "66")


def test_consumer_complaint_question():
    assert any(h["doc_id"].startswith("cp") for h in retrieval.retrieve("how to file a consumer complaint for defective goods").hits[:6])


# ---------------------------------------------------------------- guardrails
def test_out_of_scope_question_is_refused_without_inventing():
    r = pipeline.answer("What is the capital of France?", "en")
    assert r["status"] == "insufficient" and r["sources"] == []


def test_hindi_out_of_scope_refusal_is_in_hindi():
    r = pipeline.answer("आज मौसम कैसा रहेगा?", "auto")
    assert r["status"] == "insufficient" and re.search(r"[ऀ-ॿ]", r["answer"])


def test_greeting_does_not_call_retrieval():
    assert pipeline.answer("hello", "en")["status"] == "greeting"


# ---------------------------------------------------------------- full answers
def test_full_english_answer_is_grounded_and_cited():
    r = pipeline.answer("What is the punishment for theft?", "en")
    assert r["status"] == "answered" and r["disclaimer"]
    assert any(s["section_number"] == "303" for s in r["sources"])
    assert re.search(r"\[\d\]", r["answer"]), "answer has no citation markers"
    assert not any("not in the retrieved sources" in n for n in r["notes"]), r["notes"]


def test_hindi_answer_is_in_hindi_with_sources():
    r = pipeline.answer("चोरी की सजा क्या है?", "hi")
    assert r["status"] == "answered" and re.search(r"[ऀ-ॿ]{10,}", r["answer"])
    assert r["sources"]


def test_follow_up_is_resolved_with_conversation_history():
    first = pipeline.answer("What is the punishment for murder?", "en")
    follow = pipeline.answer("And what about attempt to commit it?", "en", first["conversation_id"])
    assert "murder" in follow["standalone_question"].lower()
