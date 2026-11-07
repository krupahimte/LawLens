"""Phase 2 tests: prompt rules, answer verification, partial-provision handling and pipeline wiring.

Real baseline answers and the exact chunks the model saw are read from tests/fixtures/phase2_baseline.json
(a snapshot of the 43-case baseline; the baseline report itself is never touched).

What these tests do NOT claim: that Qwen obeys the prompt, or that the checks catch every legal error.
Two baseline failures cannot be detected by word-level checks and are pinned with strict xfail tests below.
"""
import json
from pathlib import Path

import pytest

from rag import conversation, generation, guardrails, pipeline, retrieval
from rag.retrieval import Retrieval

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "phase2_baseline.json").read_text(encoding="utf-8"))


def case(cid):
    c = FIXTURE["cases"][cid]
    return c["answer"], c["question"], [FIXTURE["chunks"][i] for i in c["source_ids"]]


def verify(cid):
    answer, question, context = case(cid)
    return guardrails.verify_answer(answer, question, context)


def types(items):
    return [i["type"] for i in items]


BNSS_480 = FIXTURE["chunks"]["bnss_en:480:1"]
IT_77B = FIXTURE["chunks"]["it_en:77b:1"]
QUOTE_480 = ("such person shall not be so released if there appear reasonable grounds for believing that he has been guilty of "
             "an offence punishable with death or imprisonment for life")


# ------------------------------------------------------------------ 1. the prompt (instructions present, not obeyed-by-proof)
def test_prompt_carries_the_legal_accuracy_rules():
    p = generation.SYSTEM_PROMPT.lower()
    for phrase in ["shall not", "either", "keep and and or exactly", "three years and above", "double quotation marks",
                   "provided that", "part k of n", 'begin your reply with exactly: "the available documents do not answer"',
                   "do not use outside knowledge", "never present a list", "do not cite anything when you decline"]:
        assert phrase in p, phrase


def test_prompt_still_formats_with_a_language():
    assert "English" in generation.SYSTEM_PROMPT.format(language="English")        # no stray braces


def test_context_header_labels_parts_of_a_multi_part_provision():
    long_chunk = {**BNSS_480, "part": 2, "parts_total": 13}
    assert "part 2 of 13" in generation.build_context([long_chunk])
    assert "part " not in generation.build_context([{**IT_77B, "part": 1, "parts_total": 1}]).split("\n")[0]


def test_user_message_says_when_a_provision_is_only_partly_supplied():
    partial = [{"provision": "cp_en:section:2", "parts_included": [1, 2, 3], "parts_total": 13, "exact": True}]
    _, question, context = case("S13")
    message = generation.build_messages(question, context, "en", partial=partial)[-1]["content"]
    assert "INCOMPLETE" in message and "The Consumer Protection Act, 2019, Section 2" in message and "parts 1-3 of 13" in message
    assert "INCOMPLETE" not in generation.build_messages(question, context, "en")[-1]["content"]


# ------------------------------------------------------------------ 2. quotations
def test_exact_quotation_from_the_source_is_verified():
    answer = f'Section 480 says "{QUOTE_480}" [1].'
    v = guardrails.verify_answer(answer, "bail", [BNSS_480])
    assert v["errors"] == [] and v["warnings"] == []


def test_quotation_survives_case_curly_quotes_dashes_and_whitespace():
    answer = f"The rule is “Such  person SHALL NOT be so released—if there appear reasonable grounds for believing that he has been guilty” [1]."
    assert guardrails.verify_answer(answer, "bail", [BNSS_480])["errors"] == []


def test_quotation_with_ellipsis_is_checked_piece_by_piece():
    answer = 'It says "such person shall not be so released ... an offence punishable with death or imprisonment for life" [1].'
    assert guardrails.verify_answer(answer, "bail", [BNSS_480])["errors"] == []


def test_dropping_not_from_a_quotation_is_a_confirmed_error():
    altered = QUOTE_480.replace("shall not be so released", "shall be so released")
    v = guardrails.verify_answer(f'Section 480 says "{altered}" [1].', "bail", [BNSS_480])
    assert types(v["errors"]) == ["quote_altered_legal_term"] and "not" in v["errors"][0]["detail"]


def test_swapping_a_modal_or_connective_inside_a_quotation_is_a_confirmed_error():
    altered = QUOTE_480.replace("death or imprisonment", "death and imprisonment")
    assert types(guardrails.verify_answer(f'It says "{altered}" [1].', "bail", [BNSS_480])["errors"]) == ["quote_altered_legal_term"]


def test_a_changed_ordinary_word_is_only_a_warning():
    altered = QUOTE_480.replace("believing", "suspecting")
    v = guardrails.verify_answer(f'It says "{altered}" [1].', "bail", [BNSS_480])
    assert v["errors"] == [] and types(v["warnings"]) == ["quote_not_exact"]


def test_fabricated_quotation_is_a_confirmed_error():
    v = guardrails.verify_answer('The Sanhita says "the accused shall be released immediately upon payment of a nominal fine" [1].', "bail", [BNSS_480])
    assert types(v["errors"]) == ["quote_not_found"]


def test_quotation_attributed_to_the_wrong_source_is_a_warning_not_an_error():
    v = guardrails.verify_answer(f'Section 480 says "{QUOTE_480}" [2].', "bail", [BNSS_480, IT_77B])
    assert v["errors"] == [] and types(v["warnings"]) == ["quote_cited_to_wrong_source"]


def test_short_quoted_terms_are_not_treated_as_quotations():
    assert guardrails.verify_answer('The term "bailable offence" is defined [1].', "bail", [BNSS_480])["errors"] == []


# ------------------------------------------------------------------ 3. citations
def test_citation_to_a_nonexistent_source_is_a_confirmed_error():
    v = guardrails.verify_answer("Bail may be granted [1][7].", "bail", [BNSS_480])
    assert types(v["errors"]) == ["invalid_citation"] and "7" in v["errors"][0]["detail"]
    assert guardrails.strip_invalid_citations("Bail may be granted [1][7].", 1) == "Bail may be granted [1]."


def test_a_statement_cited_to_a_source_that_does_not_say_it_is_a_warning():
    """S13 baseline: 'the defect must be specified in the complaint [2]' - source [2] (CP section 35) never mentions a defect."""
    v = verify("S13")
    miscited = [w for w in v["warnings"] if w["type"] == "miscited_claim"]
    assert any("defect must be specified" in w["sentence"] for w in miscited)
    assert v["errors"] == []


def test_citations_on_a_refusal_are_noted_but_never_an_error_or_warning():
    v = verify("U3")
    assert v["refusal"] and v["errors"] == [] and v["warnings"] == [] and types(v["info"]) == ["refusal_with_citations"]


# ------------------------------------------------------------------ 4. negations and refusals
@pytest.mark.parametrize("cid", ["E8", "U6", "U1", "U3", "U4", "S11"])
def test_correct_refusals_are_recognised_and_not_flagged(cid):
    v = verify(cid)
    assert v["refusal"] is True
    assert v["errors"] == [] and v["warnings"] == []


@pytest.mark.parametrize("cid", ["E8", "U6"])
def test_denying_a_nonexistent_section_is_not_an_unverified_reference(cid):
    answer, question, context = case(cid)
    assert "999" in answer
    assert guardrails.unverified_references(answer, question, context) == []
    assert "unsupported_section_reference" not in types(guardrails.verify_answer(answer, question, context)["errors"])


def test_affirming_a_nonexistent_section_is_a_confirmed_error():
    _, _, context = case("E8")
    v = guardrails.verify_answer("Section 999 of the BNS punishes jaywalking with death [1].", "What does Section 999 say?", context)
    assert types(v["errors"]) == ["unsupported_section_reference"] and v["errors"][0]["detail"] == "999"


def test_a_substantive_answer_is_not_mistaken_for_a_refusal():
    assert guardrails.is_refusal(case("S10")[0]) is False
    assert guardrails.is_refusal("The available documents do not answer the question about X.") is True


# ------------------------------------------------------------------ 5. unsupported claims (warnings only) and clean answers
@pytest.mark.parametrize("cid", ["S10", "S18", "S6"])
def test_good_baseline_answers_raise_no_errors_and_no_warnings(cid):
    v = verify(cid)
    assert v["errors"] == [] and v["warnings"] == [], v


def test_m2_concluding_claim_that_no_source_states_is_flagged_as_weak_support():
    v = verify("M2")
    weak = [w for w in v["warnings"] if w["type"] == "weak_support"]
    assert any("judicial discretion" in w["sentence"] for w in weak)
    assert v["errors"] == []                                    # a heuristic never produces a "confirmed" error


def test_interpretive_gloss_beyond_the_source_is_flagged_as_weak_support():
    assert any("regardless of their background" in w["sentence"] for w in verify("E2")["warnings"] if w["type"] == "weak_support")


def test_miscited_claim_names_the_source_that_does_match():
    m3 = [w for w in verify("M3")["warnings"] if w["type"] == "miscited_claim"]
    assert m3 and "best match" in m3[0]["detail"]


# ------------------------------------------------------------------ 6. thresholds (M2: do not blur "more than" and "three years and above")
def test_more_than_three_years_is_flagged_when_the_source_says_three_years_and_above():
    v = guardrails.verify_answer("Offences punishable with imprisonment of more than three years shall be bailable [1].", "bail", [IT_77B])
    assert types(v["warnings"]) == ["threshold_qualifier_mismatch"] and v["errors"] == []


def test_three_years_and_above_paraphrase_is_not_flagged():
    answer = "Offences punishable with imprisonment of three years and above are cognizable [1]."
    assert guardrails.verify_answer(answer, "bail", [IT_77B])["warnings"] == []


def test_beyond_the_first_fifteen_days_matches_beyond_15_days():
    answer = "Police custody beyond 15 days does not by itself prevent bail [1]."
    assert [w for w in guardrails.verify_answer(answer, "bail", [BNSS_480])["warnings"] if w["type"].startswith("threshold")] == []


def test_a_duration_that_is_in_no_source_is_a_warning():
    v = guardrails.verify_answer("The accused may be held for 45 days [1].", "bail", [BNSS_480])
    assert "number_not_in_sources" in types(v["warnings"])


@pytest.mark.xfail(strict=True, reason="M2 misreading of IT 77B ('three years or more ... bailable'): every word and number is in the source, "
                                       "so only an entailment check (multi-pass answering, out of scope) could catch it")
def test_m2_it_77b_misreading_is_detected():
    answer, question, context = case("M2")
    v = guardrails.verify_answer(answer, question, context)
    assert any("77B" in (i.get("sentence") or "") for i in v["errors"] + v["warnings"])


@pytest.mark.xfail(strict=True, reason="M2 reversal of BNSS 480(1)(ii) ('shall not be released if ... cognizable and previously convicted' restated as a "
                                       "permission): the paraphrase reuses the source's words, so word-level checks cannot see the inversion")
def test_m2_480_reversal_is_detected():
    answer, question, context = case("M2")
    v = guardrails.verify_answer(answer, question, context)
    assert any("may only be released" in (i.get("sentence") or "") for i in v["errors"] + v["warnings"])


# ------------------------------------------------------------------ 7. partial answers are never presented as complete
def test_partial_exact_provision_adds_a_deterministic_note():
    notes = guardrails.partial_provision_notes(
        [{"provision": "cp_en:section:2", "parts_included": [1, 2, 3], "parts_total": 13, "exact": True}], "en")
    assert len(notes) == 1 and "parts 1-3 of 13" in notes[0] and "Section 2" in notes[0] and "incomplete" in notes[0]


def test_semantic_partial_provisions_do_not_trigger_the_note_and_nonconsecutive_parts_are_listed():
    assert guardrails.partial_provision_notes([{"provision": "bnss_en:section:2", "parts_included": [1], "parts_total": 4, "exact": False}], "en") == []
    note = guardrails.partial_provision_notes([{"provision": "bns_en:section:2", "parts_included": [1, 2, 4], "parts_total": 7, "exact": True}], "en")[0]
    assert "parts 1-2, 4 of 7" in note


# ------------------------------------------------------------------ 8. notes shown to the user
def test_errors_and_warnings_are_worded_differently():
    v = {"refusal": False, "info": [], "errors": [{"type": "quote_not_found", "detail": "x"}],
         "warnings": [{"type": "quote_not_exact", "detail": "y"}]}
    errors_note, warning_note = guardrails.verification_notes(v, "en")
    assert errors_note.startswith("Verification error") and warning_note.startswith("Check")


def test_notes_are_capped_and_weak_support_is_summarised_once():
    warnings = [{"type": t, "detail": "d", "sentence": "s", "missing": []} for t in
                ("weak_support", "weak_support", "weak_support", "miscited_claim", "threshold_qualifier_mismatch", "number_not_in_sources", "quote_not_exact")]
    notes = guardrails.verification_notes({"refusal": False, "info": [], "errors": [], "warnings": warnings}, "en")
    assert len(notes) <= 3 and sum("add explanation" in n for n in notes) <= 1


def test_a_refusal_produces_no_notes():
    assert guardrails.verification_notes(verify("E8"), "en") == []


# ------------------------------------------------------------------ 9. pipeline wiring (fakes: no Ollama, ChromaDB or SQLite)
def mk(part, total=13, n=2000):
    return {**BNSS_480, "chunk_id": f"cp_en:2:{part}", "doc_id": "cp_en", "act_name": "The Consumer Protection Act, 2019",
            "act_name_en": "The Consumer Protection Act, 2019", "section_number": "2", "part": part, "parts_total": total,
            "text": "x" * n, "distance": 0.0, "match": "exact"}


def run_pipeline(monkeypatch, hits, reply):
    seen = {}
    monkeypatch.setattr(retrieval, "retrieve", lambda q: Retrieval(query_language="en", hits=hits, best_distance=0.3, exact_reference="2"))

    def fake_stream(messages, max_tokens=700, stats=None):
        seen["messages"] = messages
        yield reply

    monkeypatch.setattr(generation, "stream_chat", fake_stream)
    monkeypatch.setattr(conversation, "get_history", lambda cid, limit=6: [])
    monkeypatch.setattr(conversation, "add_message", lambda *a, **k: None)
    monkeypatch.setattr(conversation, "new_conversation_id", lambda: "test-conversation")
    return pipeline.answer("What is in Section 2 of the Consumer Protection Act?", "en"), seen


def test_pipeline_reports_confirmed_errors_and_strips_invalid_citations(monkeypatch):
    bnss = {**BNSS_480, "distance": 0.3, "match": "semantic"}
    reply = 'The text says "the accused shall be released immediately upon payment of a nominal fine" [9]. Bail is regulated [1].'
    final, _ = run_pipeline(monkeypatch, [bnss], reply)
    assert {"invalid_citation", "quote_not_found"} <= set(types(final["verification"]["errors"]))
    assert "[9]" not in final["answer"] and "[1]" in final["answer"]
    assert any(n.startswith("Verification error") for n in final["notes"])


def test_pipeline_does_not_annotate_a_correct_refusal(monkeypatch):
    bnss = {**BNSS_480, "distance": 0.3, "match": "semantic"}
    final, _ = run_pipeline(monkeypatch, [bnss], "The available documents do not answer the question about Section 999 of the BNS. It is not mentioned in the sources.")
    assert final["verification"]["refusal"] is True and final["verification"]["errors"] == [] and final["notes"] == []


def test_pipeline_tells_the_model_and_the_user_when_an_exact_provision_is_only_partly_shown(monkeypatch):
    hits = [mk(p) for p in range(1, 14)]
    final, seen = run_pipeline(monkeypatch, hits, "The definitions include the first few terms [1].")
    assert "INCOMPLETE" in seen["messages"][-1]["content"] and "parts 1-3 of 13" in seen["messages"][-1]["content"]
    assert any("parts 1-3 of 13" in n and "incomplete" in n for n in final["notes"])
    assert "part 2 of 13" in seen["messages"][-1]["content"]          # each chunk is labelled with its part


def test_non_answer_statuses_carry_no_verification(monkeypatch):
    monkeypatch.setattr(conversation, "new_conversation_id", lambda: "t")
    assert pipeline.answer("hello", "en")["verification"] is None
