"""Final MVP hardening tests: truncation detection, existence claims, verification false positives, M2 regressions.

No Ollama, ChromaDB or SQLite is used: Ollama's HTTP stream and the retrieval/conversation layers are faked.
Real answers that went wrong in the live evaluation (docs/PHASE2_LIVE_comparison.md) are pasted in as regression inputs.

What these tests do NOT claim: that the model now obeys the prompt, or that the checks catch every legal error.
The two M2 problems the checks cannot see are pinned with strict xfail tests at the end.
"""
import json
from pathlib import Path

import pytest

from rag import conversation, generation, guardrails, pipeline, retrieval
from rag.retrieval import Retrieval

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "phase2_baseline.json").read_text(encoding="utf-8"))
BNSS_480 = FIXTURE["chunks"]["bnss_en:480:1"]


def chunk(text, cid="bnss_en:478:1", number="478"):
    return {**BNSS_480, "chunk_id": cid, "section_number": number, "text": text, "part": 1, "parts_total": 1}


def types(items):
    return [i["type"] for i in items]


# --------------------------------------------------------------------------- 1. Ollama stream: done_reason is captured
class FakeStream:
    status_code = 200

    def __init__(self, events):
        self.lines = [json.dumps(e) for e in events]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        pass

    def iter_lines(self):
        return iter(self.lines)


def piece(text):
    return {"message": {"content": text}, "done": False}


def finish(reason, tokens=700):
    return {"message": {"content": ""}, "done": True, "done_reason": reason, "eval_count": tokens, "prompt_eval_count": 3100}


def run_stream(monkeypatch, events, max_tokens=700):
    monkeypatch.setattr(generation.httpx, "stream", lambda *a, **k: FakeStream(events))
    stats = {}
    text = "".join(generation.stream_chat([{"role": "user", "content": "q"}], max_tokens=max_tokens, stats=stats))
    return text, stats


def test_stream_reports_length_stop(monkeypatch):
    text, stats = run_stream(monkeypatch, [piece("Section 35 lists "), piece("the cases in which"), finish("length")])
    assert text == "Section 35 lists the cases in which"
    assert stats["done_reason"] == "length" and stats["done"] is True
    assert stats["eval_count"] == 700 and stats["prompt_eval_count"] == 3100 and stats["token_limit"] == 700
    assert generation.stopped_early(stats) is True


def test_stream_reports_a_natural_stop(monkeypatch):
    _, stats = run_stream(monkeypatch, [piece("Done."), finish("stop", tokens=2)])
    assert stats["done_reason"] == "stop" and generation.stopped_early(stats) is False


def test_stream_that_ends_without_a_done_message_counts_as_incomplete(monkeypatch):
    _, stats = run_stream(monkeypatch, [piece("The answer begins"), piece(" but the connection")])
    assert stats["done"] is False and generation.stopped_early(stats) is True


def test_empty_stats_are_not_treated_as_truncated():
    assert generation.stopped_early({}) is False          # e.g. a test double that never fills the dictionary


def test_stream_chat_still_works_without_a_stats_argument(monkeypatch):
    monkeypatch.setattr(generation.httpx, "stream", lambda *a, **k: FakeStream([piece("ok"), finish("stop", 1)]))
    assert "".join(generation.stream_chat([{"role": "user", "content": "q"}])) == "ok"


# --------------------------------------------------------------------------- 2. the pipeline never presents a cut-off answer as complete
def run_pipeline(monkeypatch, reply, stats_to_set, question="What does Section 480 of the BNSS say?"):
    hit = {**BNSS_480, "distance": 0.3, "match": "exact"}
    monkeypatch.setattr(retrieval, "retrieve", lambda q: Retrieval(query_language="en", hits=[hit], best_distance=0.3, exact_reference="480"))

    def fake_stream(messages, max_tokens=700, stats=None):
        if stats is not None:
            stats.update(stats_to_set)
        yield reply

    monkeypatch.setattr(generation, "stream_chat", fake_stream)
    monkeypatch.setattr(conversation, "get_history", lambda cid, limit=6: [])
    monkeypatch.setattr(conversation, "add_message", lambda *a, **k: None)
    monkeypatch.setattr(conversation, "new_conversation_id", lambda: "t")
    return pipeline.answer(question, "en")


LENGTH = {"done": True, "done_reason": "length", "eval_count": 700, "prompt_eval_count": 3100, "token_limit": 700}
STOP = {"done": True, "done_reason": "stop", "eval_count": 210, "prompt_eval_count": 3100, "token_limit": 700}


def test_truncated_answer_is_flagged_in_notes_and_in_a_structured_field(monkeypatch):
    final = run_pipeline(monkeypatch, "The Section lists (a) the first case; (b) the second", LENGTH)
    assert final["status"] == "answered"
    assert final["generation"]["truncated"] is True and final["generation"]["done_reason"] == "length"
    assert final["notes"][0].startswith("Incomplete answer")           # the most important note comes first
    assert "cut off" in final["notes"][0] and "incomplete" in final["notes"][0].lower()
    assert final["answer"].startswith("The Section lists (a)")        # the text is kept, not hidden or rewritten


def test_complete_answer_has_no_truncation_note(monkeypatch):
    final = run_pipeline(monkeypatch, "Section 480 regulates bail [1].", STOP)
    assert final["generation"]["truncated"] is False and not any("Incomplete" in n for n in final["notes"])


def test_interrupted_stream_is_flagged_even_without_done_reason(monkeypatch):
    final = run_pipeline(monkeypatch, "Section 480 regulates", {"done": False, "token_limit": 700})
    assert final["generation"]["truncated"] is True and final["notes"][0].startswith("Incomplete answer")


def test_generation_details_are_reported_for_latency_analysis(monkeypatch):
    g = run_pipeline(monkeypatch, "Section 480 regulates bail [1].", STOP)["generation"]
    assert g["output_tokens"] == 210 and g["prompt_tokens"] == 3100 and g["token_limit"] == 700


def test_non_answer_statuses_have_no_generation_details(monkeypatch):
    monkeypatch.setattr(conversation, "new_conversation_id", lambda: "t")
    assert pipeline.answer("hello", "en")["generation"] is None


def test_incomplete_note_exists_in_both_languages():
    from rag.language import ANSWER_INCOMPLETE_NOTE
    assert set(ANSWER_INCOMPLETE_NOTE) == {"en", "hi"} and all(len(t) > 60 for t in ANSWER_INCOMPLETE_NOTE.values())


def test_api_response_model_accepts_the_generation_field():
    import main
    assert "generation" in main.ChatResponse.model_fields


def test_prompt_asks_for_short_answers_that_do_not_copy_whole_lists():
    p = generation.SYSTEM_PROMPT.lower()
    assert "under about 300 words" in p and "do not copy the whole list" in p


# --------------------------------------------------------------------------- 3. U4: 'not in the sources' is not 'does not exist'
U4_LIVE = ("The available documents do not answer the question. While [1] refers to Section 302 of the Bharatiya Nyaya Sanhita, 2023, it does not "
           "correspond to any section of the Indian Penal Code (IPC). The question asks for the punishment under \"IPC section 302,\" but no such "
           "section exists in the Indian Penal Code. The provided sources do not contain any reference to Section 302 of the IPC. Therefore, based "
           "on the given sources, there is no information about IPC Section 302.")


def existence_errors(answer, context=None):
    v = guardrails.verify_answer(answer, "What is the punishment under IPC section 302?", context or [chunk("302. Punishment for murder.", "bns_en:302:1", "302")])
    return [e for e in v["errors"] if e["type"] == "unsupported_existence_claim"]


def test_u4_claim_that_a_section_does_not_exist_is_a_confirmed_error():
    errors = existence_errors(U4_LIVE)
    assert errors and any("no such section exists" in e["sentence"] for e in errors)


def test_u4_note_says_not_found_is_different_from_does_not_exist():
    v = guardrails.verify_answer(U4_LIVE, "q", [chunk("x")])
    note = next(n for n in guardrails.verification_notes(v, "en") if "exist" in n)
    assert note.startswith("Verification error") and "not found" in note


@pytest.mark.parametrize("sentence", [
    "The available documents do not answer this. The provided sources do not contain a Section for the IPC.",
    "There is no such section in the provided sources.",
    "No such section is mentioned in the retrieved documents.",
    "The sources do not cover the Indian Penal Code, so I cannot say what it provides.",
    "The available documents do not answer the question; the IPC is not among the sources.",
])
def test_statements_about_the_sources_are_not_existence_claims(sentence):
    assert existence_errors(sentence) == []


@pytest.mark.parametrize("sentence", [
    "Section 999 does not exist.",
    "There is no such section in the Bharatiya Nyaya Sanhita.",
    "That Act does not actually exist.",
    "Article 400 is non-existent.",
    "The IPC never existed in this form.",
])
def test_flat_claims_of_non_existence_are_errors(sentence):
    assert existence_errors(sentence)


def test_an_omitted_or_repealed_provision_may_be_said_to_be_gone_when_a_source_says_so():
    omitted = chunk("31. [Omitted.] Compulsory acquisition of property.—Omitted by the Constitution (Forty-fourth Amendment) Act, 1978.", "constitution_en:31:1", "31")
    assert existence_errors("Article 31 no longer exists; it was omitted [1].", [omitted]) == []
    assert existence_errors("Article 31 no longer exists.", [chunk("Equality before law.")])        # nothing in the sources says so


def test_baseline_answers_contain_no_existence_claims():
    for cid, c in FIXTURE["cases"].items():
        context = [FIXTURE["chunks"][i] for i in c["source_ids"]]
        assert [e for e in guardrails.verify_answer(c["answer"], c["question"], context)["errors"]
                if e["type"] == "unsupported_existence_claim"] == [], cid


def test_prompt_separates_not_found_from_does_not_exist():
    p = generation.SYSTEM_PROMPT.lower()
    assert "is not the same as a provision that does not exist" in p and "the sources provided do not contain it" in p


# --------------------------------------------------------------------------- 4. E8: a sentence that STATES absence is not flagged
E8_LIVE = ("The available documents do not answer the question because there is no source provided that contains Section 999 of the Bharatiya "
           "Nagarik Suraksha Sanhita, 2023. All the cited sources cover different sections (e.g., 509, 299, 119, 500, 219), but none mention "
           "Section 999. Therefore, based on the provided sources, the content of Section 999 cannot be determined.")


def section_errors(answer):
    ctx = [chunk("509. Insulting the modesty of a woman.", "bns_en:509:1", "509")]
    return [e for e in guardrails.verify_answer(answer, "What does Section 999 of the BNS say?", ctx)["errors"]
            if e["type"] == "unsupported_section_reference"]


def test_e8_negated_section_reference_is_not_a_false_error():
    assert section_errors(E8_LIVE) == []


@pytest.mark.parametrize("sentence", [
    "None mention Section 999.",
    "None of the cited sources mention Section 999.",
    "None of these documents contain Section 999.",
    "None of the retrieved passages address Section 999.",
])
def test_none_mention_phrasings_are_recognised_as_absence(sentence):
    assert section_errors(sentence) == []


@pytest.mark.parametrize("sentence", [
    "Section 999 of the BNS punishes jaywalking with death.",          # asserting it as real stays an error
    "None of this is in doubt, and Section 999 applies.",
])
def test_asserting_a_missing_section_is_still_an_error(sentence):
    assert section_errors(sentence)


# --------------------------------------------------------------------------- 5. M1: 'above the age of eighteen years' == 'above 18 years of age'
def test_age_of_phrase_is_read_as_a_greater_than_threshold():
    assert guardrails.thresholds("being above the age of eighteen years, suffers death") == [(18, "year", "gt")]
    assert guardrails.thresholds("a person above 18 years of age") == [(18, "year", "gt")]
    assert guardrails.thresholds("not less than the age of eighteen years") == [(18, "year", "ge")]


def test_m1_wording_difference_is_no_longer_a_threshold_warning():
    source = chunk("101. Culpable homicide is murder if ... the person whose death is caused, being above the age of eighteen years, "
                   "suffers death or takes the risk of death with his own consent.", "bns_en:101:6", "101")
    answer = "If the person whose death is caused consents to the risk and is above 18 years of age, it is not murder [1]."
    v = guardrails.verify_answer(answer, "difference between culpable homicide and murder", [source])
    assert "threshold_qualifier_mismatch" not in types(v["warnings"])


def test_a_real_threshold_difference_is_still_reported():
    source = chunk("The person, being above the age of eighteen years, suffers death.", "bns_en:101:6", "101")
    answer = "This applies to a person of not less than 18 years of age [1]."
    v = guardrails.verify_answer(answer, "q", [source])
    assert "threshold_qualifier_mismatch" in types(v["warnings"])          # 'not less than' (>=) is not 'above' (>)


# --------------------------------------------------------------------------- 6. M2: shall -> may, malformed markers
S478 = chunk("478. (1) When any person other than a person accused of a non-bailable offence is arrested or detained without warrant, and is prepared "
             "to give bail, such person shall be released on bail: Provided that such officer or Court, if he or it thinks fit, may, and shall, "
             "if such person is indigent, discharge him on his executing a bond for his appearance.")
M2_LIVE_SENTENCE = ("According to Section 478(1), when a person is not accused of a non-bailable offence, they may be released on bail if they "
                    "are prepared to give bail, and if they are indigent, they may be discharged on a bond for appearance [1].")


def test_m2_shall_changed_to_may_is_reported():
    v = guardrails.verify_answer(M2_LIVE_SENTENCE, "bailable vs non-bailable", [S478])
    w = [x for x in v["warnings"] if x["type"] == "modal_changed"]
    assert w and "shall" in w[0]["detail"] and "may" in w[0]["detail"]
    note = guardrails.verification_notes(v, "en")[0]
    assert note.startswith("Check") and "shall" in note


@pytest.mark.parametrize("sentence", [
    "Such a person shall be released on bail [1].",
    "Such a person must be released on bail [1].",                      # shall -> must keeps the obligation
    "The officer may discharge him on his executing a bond [1].",     # 'may' in the source as well
])
def test_faithful_modals_are_not_flagged(sentence):
    assert "modal_changed" not in types(guardrails.verify_answer(sentence, "q", [S478])["warnings"])


def test_a_permission_turned_into_an_obligation_is_reported():
    source = chunk("In that case the Court may release the accused on bail on his own bond.", "x:1:1", "1")
    v = guardrails.verify_answer("In that case the Court shall release the accused on bail on his own bond [1].", "q", [source])
    assert "modal_changed" in types(v["warnings"])


@pytest.mark.parametrize("answer, source", [
    # live M3: the source says "No person ... shall be detained"; "shall not be detained" means the same
    ("The person shall not be detained in custody beyond the period [1].", "No person who is arrested shall be detained in custody without being informed."),
    # live M2/480: the source says "he may be released on bail, but such person shall not be so released if ..."
    ("A person shall not be released on bail if the offence is cognizable [1].", "He may be released on bail, but such person shall not be so released if the offence is cognizable."),
])
def test_negated_forms_are_not_judged(answer, source):
    v = guardrails.verify_answer(answer, "q", [chunk(source, "x:1:1", "1")])
    assert "modal_changed" not in types(v["warnings"])


def test_a_prohibition_turned_into_a_permission_is_reported():
    source = chunk("Such person shall not be so released if there appear reasonable grounds for believing that he is guilty.", "bnss_en:480:1", "480")
    v = guardrails.verify_answer("Such a person may be so released if there appear reasonable grounds for believing that he is guilty [1].", "q", [source])
    assert "modal_changed" in types(v["warnings"])


def test_modal_check_only_looks_at_the_cited_sources():
    other = chunk("Where the Court thinks fit, the accused may be released on bail.", "x:1:1", "1")
    v = guardrails.verify_answer("They may be released on bail [2].", "q", [S478, other])
    assert "modal_changed" not in types(v["warnings"])               # [2] says 'may be'; only [1] says 'shall be'


def test_baseline_answers_have_no_modal_warnings():
    for cid, c in FIXTURE["cases"].items():
        context = [FIXTURE["chunks"][i] for i in c["source_ids"]]
        assert "modal_changed" not in types(guardrails.verify_answer(c["answer"], c["question"], context)["warnings"]), cid


def test_malformed_citation_marker_is_reported():
    v = guardrails.verify_answer("Bailable offences carry no requirement of a bond [4(c)].", "q", [S478])
    w = [x for x in v["warnings"] if x["type"] == "malformed_citation"]
    assert w and "[4(c)]" in w[0]["detail"]


@pytest.mark.parametrize("answer", ["Fine [1].", "Fine [1][2].", "Section 478(1) says so [1]."])
def test_ordinary_markers_are_not_malformed(answer):
    assert "malformed_citation" not in types(guardrails.verify_answer(answer, "q", [S478, S478])["warnings"])


def test_prompt_has_the_m2_rules():
    p = generation.SYSTEM_PROMPT.lower()
    assert 'if a source says "shall be released", do not write "may be released"' in p
    assert "unless a source says so in words" in p and "never [4(c)]" in p


def test_both_new_warning_kinds_have_notes_in_both_languages():
    from rag.language import VERIFICATION_NOTES
    for kind in ("modal_changed", "malformed_citation", "unsupported_existence_claim"):
        assert kind in VERIFICATION_NOTES["en"] and kind in VERIFICATION_NOTES["hi"]


def test_new_prompt_stays_formattable_and_bounded():
    assert "English" in generation.SYSTEM_PROMPT.format(language="English")
    assert len(generation.SYSTEM_PROMPT) < 4200            # prompt processing is part of the latency; keep growth deliberate


# --------------------------------------------------------------------------- 6a. schedule tables list section numbers bare (live re-run, M2)
def test_section_numbers_listed_in_a_schedule_table_are_allowed():
    table = {**chunk("Resisting lawful apprehension. Imprisonment for 2 years. Cognizable. Bailable. 263(b) If charged with an offence punishable "
                     "with imprisonment for life. Imprisonment for 3 years. Non-bailable. 263(e) If under sentence of death.", "bnss_en:thefirstschedule:33", "thefirstschedule"),
             "unit": "schedule"}
    answer = "Under Section 263(a), resistance to lawful apprehension is bailable [1]."
    v = guardrails.verify_answer(answer, "bailable offences", [table])
    assert [e for e in v["errors"] if e["type"] == "unsupported_section_reference"] == []


def test_a_bare_number_in_a_schedule_does_not_allow_unrelated_sections():
    table = {**chunk("Imprisonment for 2 years. Cognizable. Bailable. 263(b) If charged with an offence. Imprisonment for 3 years.",
                     "bnss_en:thefirstschedule:33", "thefirstschedule"), "unit": "schedule"}
    v = guardrails.verify_answer("Section 2 and Section 999 apply [1].", "q", [table])
    assert {e["detail"] for e in v["errors"] if e["type"] == "unsupported_section_reference"} == {"2", "999"}


def test_only_schedule_chunks_get_the_bare_number_allowance():
    section = chunk("263(b) If charged with an offence punishable with imprisonment.", "bnss_en:263:1", "264")
    v = guardrails.verify_answer("Section 263 applies [1].", "q", [section])
    assert [e["detail"] for e in v["errors"] if e["type"] == "unsupported_section_reference"] == ["263"]


# --------------------------------------------------------------------------- 6b. quotation pairing (found in the live re-run, case L2)
L2_STYLE = ('Section 2 defines "act", "animal", "child" means any person below the age of eighteen years [1](3); "counterfeit" means causing '
            'one thing to resemble another with intent to deceive [1](4); "injury" means any harm illegally caused to a person in body [1](14).')


def test_short_quoted_terms_do_not_shift_the_pairing_of_quote_marks():
    """Skipping a short quoted term used to make its CLOSING quote pair with the next term's OPENING quote, so the words
    between two defined terms were checked as if they were a quotation (6 false 'quotation not found' errors in L2)."""
    assert guardrails.extract_quotes(L2_STYLE) == []
    v = guardrails.verify_answer(L2_STYLE, "definitions", [chunk("unrelated text about bail and bonds in this provision")])
    assert [e for e in v["errors"] if e["type"].startswith("quote_")] == []


def test_real_quotations_are_still_extracted_and_checked_next_to_defined_terms():
    answer = ('The term "bail" is not defined, but the section says "such person shall be released on bail" [1]. '
              'It also says "a fabricated passage that is not in the source at all" [1].')
    quotes = guardrails.extract_quotes(answer)
    assert [q["quote"] for q in quotes] == ["such person shall be released on bail", "a fabricated passage that is not in the source at all"]
    assert quotes[0]["cited"] == [1]
    v = guardrails.verify_answer(answer, "q", [S478])
    assert [e["type"] for e in v["errors"]] == ["quote_not_found"]


def test_curly_quotes_are_paired_explicitly():
    quotes = guardrails.extract_quotes("It says “such person shall be released on bail” [1] and “child” means a person.")
    assert [q["quote"] for q in quotes] == ["such person shall be released on bail"]


# --------------------------------------------------------------------------- 7. evaluation harness
def test_refusals_do_not_fail_the_citation_check_but_unreferenced_answers_do():
    import run_rag_report as r
    refusal = "The available documents do not answer the question about Section 999."
    assert r.citations_ok("answered", refusal) is True                  # a correct refusal has nothing to cite
    assert r.citations_ok("answered", "Section 103 punishes murder.") is False
    assert r.citations_ok("answered", "Section 103 punishes murder [1].") is True
    assert r.citations_ok("insufficient", "anything") is True


def test_harness_flags_a_truncated_answer_that_was_not_reported():
    import run_rag_report as r
    assert r.truncation_reported({"truncated": True}, ["Incomplete answer: ..."]) is True
    assert r.truncation_reported({"truncated": True}, ["Check: something else"]) is False
    assert r.truncation_reported({"truncated": False}, []) is True
    assert r.truncation_reported(None, []) is True


# --------------------------------------------------------------------------- 8. what the checks cannot see (pinned, strict)
@pytest.mark.xfail(strict=True, reason="'bailable offences need no bond' is a negative claim. 'bond' occurs in the sources, so no word-level check "
                   "can tell that no source states it. Only the prompt rule and a human reader (or entailment checking, out of scope) catch it.")
def test_unsupported_negative_claim_is_detected():
    answer = "Such person shall be released on bail without executing a bond for his appearance [1]."      # every word occurs in the source
    v = guardrails.verify_answer(answer, "bailable vs non-bailable", [S478])
    assert v["errors"] or v["warnings"]


@pytest.mark.xfail(strict=True, reason="A condition dropped in a sentence built only from the source's own words has nothing for a word-level check "
                   "to compare. Only entailment checking (out of scope) would catch this.")
def test_dropped_condition_in_a_paraphrase_is_detected():
    v = guardrails.verify_answer("Court, if it thinks fit, released such person on bail, whether or not prepared to give bail [1].", "q", [S478])
    assert v["errors"] or v["warnings"]
