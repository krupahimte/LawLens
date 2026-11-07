"""Unit tests for language helpers, reference parsing and the guardrails."""
from rag import guardrails
from rag.language import DISCLAIMER, detect_language, is_greeting
from rag.retrieval import find_reference, select_context


def chunk(section="103", act="Bharatiya Nyaya Sanhita, 2023", text="Murder punishment.", lang="en", low=False):
    return {"section_number": section, "act_name_en": act, "unit": "section", "text": text,
            "language": lang, "low_quality": low, "doc_id": "bns_en", "chunk_id": f"x:{section}:1"}


def test_language_detection():
    assert detect_language("What is the punishment for theft?") == "en"
    assert detect_language("चोरी की सजा क्या है?") == "hi"
    assert detect_language("BNS धारा 303 क्या है") == "hi"


def test_disclaimer_exists_in_both_languages():
    assert "not legal advice" in DISCLAIMER["en"] and "कानूनी सलाह नहीं" in DISCLAIMER["hi"]


def test_greeting_detection():
    assert is_greeting("Hello!") and is_greeting("नमस्ते") and not is_greeting("hello what is bail")


def test_find_reference_named_act_and_article():
    # the Hindi BNS file is a booklet indexed by page, so "section 103" must never match it
    assert find_reference("What does section 103 of the BNS say?") == ("103", ["bns_en"])
    assert find_reference("Explain Article 21")[0] == "21"
    assert find_reference("Explain Article 21")[1] == ["constitution_en"]        # Hindi Constitution is page-indexed
    assert find_reference("धारा १०३ बीएनएस")[0] == "103"
    assert find_reference("BNSS section 35")[1] == ["bnss_en"]                    # not confused with BNS
    assert find_reference("BSA section 5")[1] == ["bsa_en"]                       # Hindi is paused (ENABLE_HINDI=false)
    assert find_reference("what is theft") is None


def test_unverified_reference_is_detected():
    ctx = [chunk("303", text="Theft punishment. See also section 305.")]
    assert guardrails.unverified_references("Under Section 303 and section 305 theft ...", "theft?", ctx) == []
    assert guardrails.unverified_references("Under Section 999 theft ...", "theft?", ctx) == ["999"]


def test_number_only_the_user_mentioned_is_not_trusted():
    ctx = [chunk("303", text="Theft.")]
    # the user asked about a fake Section 999; an answer repeating it must be flagged
    assert guardrails.unverified_references("Section 999 punishes jaywalking.", "What does section 999 say?", ctx) == ["999"]


def test_reference_lists_and_hindi():
    ctx = [chunk("10")]
    assert guardrails.referenced_sections("sections 3, 4 and 5") == {"3", "4", "5"}
    assert guardrails.unverified_references("धारा 10 और धारा 77", "q", ctx) == ["77"]


def test_invalid_citation_markers_removed():
    assert guardrails.strip_invalid_citations("Fact [1] and fact [7].", 2) == "Fact [1] and fact ."


def test_relevance_threshold():
    assert guardrails.is_relevant(0.3, False)
    assert not guardrails.is_relevant(0.95, False)
    assert guardrails.is_relevant(0.95, True)         # an exact section lookup always counts


def test_select_context_one_entry_per_provision(monkeypatch):
    monkeypatch.setattr("rag.retrieval.counterpart", lambda hit, lang: None)
    good = chunk("103", lang="en")
    context, flags = select_context([good, dict(good, chunk_id="x:103:2")], "en")
    assert len(context) == 1 and not flags["only_unreliable_ocr"]


def test_unreliable_ocr_with_no_alternative_is_flagged(monkeypatch):
    monkeypatch.setattr("rag.retrieval.counterpart", lambda hit, lang: None)
    context, flags = select_context([chunk("5", lang="hi", low=True)], "hi")
    assert context == [] and flags["only_unreliable_ocr"]


def test_unreliable_hindi_falls_back_to_english_and_says_so(monkeypatch):
    english = chunk("5", lang="en")
    monkeypatch.setattr("rag.retrieval.counterpart", lambda hit, lang: english if lang == "en" else None)
    context, flags = select_context([chunk("5", lang="hi", low=True)], "hi")
    assert context == [english] and flags["used_fallback_language"]
