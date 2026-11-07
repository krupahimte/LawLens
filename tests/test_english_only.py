"""English-only mode: Hindi is paused but restorable through one flag."""
import pytest

import config
from rag import catalog, pipeline, retrieval
from rag.retrieval import find_reference


def test_active_documents_are_the_six_english_acts():
    active = {d.doc_id for d in catalog.active_documents()}
    assert active == {"bns_en", "bnss_en", "bsa_en", "constitution_en", "cp_en", "it_en"}
    assert all(d.language == "en" for d in catalog.active_documents())


def test_hindi_documents_stay_in_the_catalog_for_later():
    assert {"bns_hi", "bnss_hi", "bsa_hi", "constitution_hi", "cp_hi", "it_hi"} <= set(catalog.BY_ID)


def test_flag_restores_hindi(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_HINDI", True)
    assert len(catalog.active_documents()) == 12
    assert find_reference("BSA section 5")[1] == ["bsa_en", "bsa_hi"]


def test_hindi_question_gets_notice_and_never_reaches_retrieval(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("retrieval must not run for a Hindi question while Hindi is paused")
    monkeypatch.setattr(retrieval, "retrieve", boom)
    result = pipeline.answer("चोरी की सजा क्या है?", "hi")
    assert result["status"] == "unsupported_language"
    assert "English" in result["answer"] and result["sources"] == [] and result["language"] == "en"


def test_ingest_refuses_hindi_documents_while_paused():
    import subprocess, sys
    run = subprocess.run([sys.executable, "ingest.py", "--docs", "bns_hi", "--no-embed"], capture_output=True, text=True)
    assert run.returncode != 0 and "disabled" in (run.stderr + run.stdout)


@pytest.mark.parametrize("flag", [False])
def test_default_is_english_only(flag):
    assert config.ENABLE_HINDI is flag
