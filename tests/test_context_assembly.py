"""Phase 1 tests: exact lookup returns every part of a provision, and context is assembled under a character budget.

No Ollama, no ChromaDB and no SQLite are used: vector-store calls and the conversation store are replaced by fakes.
"""
import pytest

import config
from rag import conversation, generation, pipeline, retrieval
from rag.retrieval import Retrieval, assemble_context

ACTS = {
    "bns_en": "Bharatiya Nyaya Sanhita, 2023", "bnss_en": "Bharatiya Nagarik Suraksha Sanhita, 2023",
    "bsa_en": "Bharatiya Sakshya Adhiniyam, 2023", "constitution_en": "The Constitution of India",
    "cp_en": "The Consumer Protection Act, 2019", "it_en": "The Information Technology Act, 2000",
}
ALLOWED_REASONS = {"budget", "provision_cap", "schedule_limit", "low_quality"}


def mk(doc, sec, part=1, total=1, n=1000, kind="operative", unit="section", match="semantic", dist=0.3, chapter=""):
    """A chunk dict shaped like the ones Chroma returns."""
    return {
        "chunk_id": f"{doc}:{sec.lower().replace(' ', '')}:{part}", "doc_id": doc, "act_name": ACTS[doc], "act_name_en": ACTS[doc],
        "language": "en", "unit": unit, "section_number": sec, "section_title": "", "chapter": chapter, "page_start": 1, "page_end": 1,
        "part": part, "parts_total": total, "chunk_kind": kind, "text_source": "text_layer", "ocr_conf": -1.0, "low_quality": False,
        "number_verified": 1, "number_inferred": False, "text": "x" * n, "distance": dist, "match": match,
    }


def sched(doc, label, part, n=1500, dist=0.3):
    return mk(doc, label, part=part, total=49, n=n, unit="schedule", dist=dist)


def ids(chunks):
    return [c["chunk_id"] for c in chunks]


def reasons(report):
    return {e["chunk_id"]: e["reason"] for e in report["excluded"]}


# ------------------------------------------------------------------ exact lookup (retrieval.py)
class FakeStore:
    def __init__(self, chunks):
        self.chunks, self.calls = chunks, []

    def get_chunks(self, where, limit=20):
        self.calls.append((where, limit))
        return list(self.chunks)


def run_retrieve(monkeypatch, question, stored):
    store = FakeStore(stored)
    monkeypatch.setattr(retrieval.vectorstore, "get_chunks", store.get_chunks)
    monkeypatch.setattr(retrieval.vectorstore, "search", lambda vector, top_k, where=None: [])
    monkeypatch.setattr(retrieval, "embed_texts", lambda texts: [[0.0, 0.0, 0.0]])
    return retrieval.retrieve(question), store


def test_exact_lookup_all_parts_has_no_part_filter_and_orders_parts_numerically(monkeypatch):
    store = FakeStore([mk("cp_en", "2", p, 12) for p in (10, 2, 1, 11, 3)])
    monkeypatch.setattr(retrieval.vectorstore, "get_chunks", store.get_chunks)
    out = retrieval.exact_lookup("2", ["cp_en"], all_parts=True)
    where, limit = store.calls[0]
    assert {"part": 1} not in where["$and"], "all-parts lookup must not filter on part=1"
    assert limit >= 60
    assert [c["part"] for c in out] == [1, 2, 3, 10, 11]          # numeric order, not 1,10,11,2,3


def test_exact_lookup_default_keeps_the_old_part_one_behaviour(monkeypatch):
    store = FakeStore([mk("bns_en", "302", 1, 1)])
    monkeypatch.setattr(retrieval.vectorstore, "get_chunks", store.get_chunks)
    retrieval.exact_lookup("302", ["bns_en", "bnss_en"])
    where, limit = store.calls[0]
    assert {"part": 1} in where["$and"] and limit == 12


def test_explicit_act_reference_retrieves_every_part_in_order(monkeypatch):
    stored = [mk("cp_en", "2", p, 13, match="x") for p in (5, 1, 3, 2, 4)]
    result, store = run_retrieve(monkeypatch, "What are the definitions in Section 2 of the Consumer Protection Act?", stored)
    where, _ = store.calls[0]
    assert {"part": 1} not in where["$and"]
    assert [h["part"] for h in result.hits] == [1, 2, 3, 4, 5]
    assert all(h["match"] == "exact" for h in result.hits)


def test_article_reference_is_explicit_and_expands_all_parts(monkeypatch):
    stored = [mk("constitution_en", "22", p, 3, unit="article") for p in (3, 1, 2)]
    result, store = run_retrieve(monkeypatch, "Explain Article 22", stored)
    assert {"part": 1} not in store.calls[0][0]["$and"]
    assert [h["part"] for h in result.hits] == [1, 2, 3]


def test_ambiguous_reference_across_several_acts_still_returns_part_one_only(monkeypatch):
    stored = [mk("bns_en", "302", 1, 1)]
    result, store = run_retrieve(monkeypatch, "What is the punishment under IPC section 302?", stored)   # no Act named
    where, limit = store.calls[0]
    assert {"part": 1} in where["$and"] and limit == 12
    assert len(where["$and"][1]["doc_id"]["$in"]) > 1                # searched across several Acts, as before


def test_find_reference_public_contract_is_unchanged():
    assert retrieval.find_reference("section 103 of the BNS") == ("103", ["bns_en"])
    assert retrieval.find_reference("what is theft") is None


# ------------------------------------------------------------------ budget and ordering (assemble_context)
def test_long_exact_provision_gets_all_parts_that_fit_in_order_and_reports_the_rest():
    hits = [mk("cp_en", "2", p, 13, n=2000, match="exact", dist=0.0) for p in range(1, 14)]
    context, flags, report = assemble_context(hits, "en", budget_chars=10_000)
    assert [c["part"] for c in context] == [1, 2, 3]                 # 60% of 10,000 = 6,000 = three 2,000-char parts
    assert report["used_chars"] == 6000 and report["budget_chars"] == 10_000
    assert {e["reason"] for e in report["excluded"]} == {"budget"} and len(report["excluded"]) == 10
    assert report["truncated_provisions"] == [{"provision": "cp_en:section:2", "parts_included": [1, 2, 3], "parts_total": 13, "exact": True}]
    assert ids(context) == [f"cp_en:2:{p}" for p in (1, 2, 3)]       # chunk ids preserved for citations


def test_exact_provision_comes_before_better_ranked_semantic_hits():
    hits = [mk("bns_en", "303", 1, 1, dist=0.2), mk("it_en", "66C", 1, 1, match="exact", dist=0.0)]
    context, _, report = assemble_context(hits, "en")
    assert ids(context)[0] == "it_en:66c:1"
    assert [e["reason"] for e in report["included"]] == ["exact", "semantic"]


def test_several_chunks_of_the_same_semantic_provision_are_all_kept_in_part_order():
    hits = [mk("bnss_en", "480", 1, 3, n=1969, dist=0.346), mk("bnss_en", "480", 3, 3, n=1434, dist=0.378),
            mk("bnss_en", "480", 2, 3, n=1500, dist=0.394), mk("bnss_en", "2", 1, 4, n=1813, dist=0.403)]
    context, _, report = assemble_context(hits, "en", budget_chars=10_000)
    assert ids(context) == ["bnss_en:480:1", "bnss_en:480:2", "bnss_en:480:3", "bnss_en:2:1"]
    reasons_in = {e["chunk_id"]: e["reason"] for e in report["included"]}
    assert reasons_in["bnss_en:480:1"] == "semantic" and reasons_in["bnss_en:480:2"] == "extra_part"


def test_m2_shape_includes_478_and_all_480_parts_and_defers_the_schedule():
    """The failure that motivated this phase: BNSS 478 was retrieved but cut by the four-provision limit."""
    hits = [mk("bnss_en", "480", 1, 3, n=1969, dist=0.346), mk("bnss_en", "480", 3, 3, n=1434, dist=0.378),
            mk("bnss_en", "480", 2, 3, n=1500, dist=0.394), mk("bnss_en", "2", 1, 4, n=1813, dist=0.403),
            mk("it_en", "77B", 1, 1, n=313, dist=0.418), sched("bnss_en", "The First Schedule", 39, n=1931, dist=0.419),
            mk("bnss_en", "478", 1, 1, n=1583, dist=0.43)]
    context, _, report = assemble_context(hits, "en", budget_chars=10_000)
    got = set(ids(context))
    assert {"bnss_en:478:1", "bnss_en:480:1", "bnss_en:480:2", "bnss_en:480:3"} <= got
    assert report["used_chars"] == 1969 + 1500 + 1434 + 1813 + 313 + 1583 == 8612
    assert reasons(report) == {"bnss_en:thefirstschedule:39": "budget"}   # 8,612 + 1,931 > 10,000


def test_provision_cap_is_six_not_four_and_overflow_is_reported_with_its_reason():
    hits = [mk("bns_en", str(100 + i), dist=0.3 + i / 100, n=500) for i in range(9)]
    context, _, report = assemble_context(hits, "en", budget_chars=10_000)
    assert len(context) == 6 == config.MAX_PROVISIONS
    assert [reasons(report)[f"bns_en:{100 + i}:1"] for i in range(6, 9)] == ["provision_cap"] * 3


def test_budget_is_never_exceeded_and_chunks_are_never_cut():
    hits = [mk("bns_en", str(i), n=n, dist=0.3 + i / 100) for i, n in enumerate((1900, 2100, 1700, 2200, 900, 800), start=1)]
    context, _, report = assemble_context(hits, "en", budget_chars=6_000)
    assert sum(len(c["text"]) for c in context) == report["used_chars"] <= 6_000
    originals = {h["chunk_id"]: h["text"] for h in hits}
    assert all(c["text"] == originals[c["chunk_id"]] for c in context)        # whole chunks only
    assert all(e["reason"] == "budget" for e in report["excluded"])


def test_first_chunk_is_included_even_if_it_alone_exceeds_the_budget():
    hits = [mk("bns_en", "1", n=3000, dist=0.2), mk("bns_en", "2", n=100, dist=0.3)]
    context, _, report = assemble_context(hits, "en", budget_chars=1_000)
    assert ids(context) == ["bns_en:1:1"] and report["used_chars"] == 3000
    assert reasons(report) == {"bns_en:2:1": "budget"}


def test_illustrations_are_dropped_before_operative_parts_of_an_exact_provision():
    hits = [mk("bns_en", "303", 1, 4, n=2000, match="exact"), mk("bns_en", "303", 2, 4, n=2000, kind="illustration", match="exact"),
            mk("bns_en", "303", 3, 4, n=2000, kind="illustration", match="exact"), mk("bns_en", "303", 4, 4, n=2000, match="exact")]
    context, _, report = assemble_context(hits, "en", budget_chars=10_000)     # exact budget 6,000 = three chunks
    assert [c["part"] for c in context] == [1, 2, 4]                        # operative 1 and 4 first, then one illustration; shown in part order
    assert reasons(report) == {"bns_en:303:3": "budget"}


# ------------------------------------------------------------------ schedules
def test_schedule_chunks_of_one_schedule_are_separate_candidates_and_only_one_is_admitted():
    hits = [mk("bnss_en", "35", dist=0.3, n=800), sched("bnss_en", "The First Schedule", 8, dist=0.31),
            sched("bnss_en", "The First Schedule", 9, dist=0.32), mk("bnss_en", "47", dist=0.33, n=500),
            mk("bnss_en", "58", dist=0.34, n=500), mk("bnss_en", "60", dist=0.35, n=500)]
    context, _, report = assemble_context(hits, "en")
    scheduled = [c for c in context if c["unit"] == "schedule"]
    assert [c["part"] for c in scheduled] == [8]                              # the better-ranked one, not both
    assert reasons(report) == {"bnss_en:thefirstschedule:9": "schedule_limit"}


def test_schedule_is_considered_only_after_three_non_schedule_provisions():
    hits = [sched("bnss_en", "The First Schedule", 8, dist=0.2)] + [mk("bns_en", str(100 + i), n=600, dist=0.3 + i / 100) for i in range(4)]
    context, _, report = assemble_context(hits, "en")
    assert ids(context)[-1] == "bnss_en:thefirstschedule:8" and len(context) == 5     # best-ranked, but placed last
    assert report["included"][-1]["reason"] == "schedule"


def test_schedule_is_still_used_when_there_is_little_else():
    hits = [sched("bnss_en", "The First Schedule", 8, dist=0.2), mk("bns_en", "78", n=600, dist=0.3)]
    context, _, _ = assemble_context(hits, "en")
    assert "bnss_en:thefirstschedule:8" in ids(context)


# ------------------------------------------------------------------ preserved behaviours
def test_ambiguous_exact_references_each_keep_their_part_one_without_expansion():
    hits = [mk("bns_en", "302", match="exact", dist=0.0), mk("bnss_en", "302", match="exact", dist=0.0), mk("it_en", "84C", dist=0.47)]
    context, _, report = assemble_context(hits, "en")
    assert ids(context) == ["bns_en:302:1", "bnss_en:302:1", "it_en:84c:1"]
    assert [e["reason"] for e in report["included"]] == ["exact", "exact", "semantic"]


def test_chapter_siblings_are_not_boosted():
    """Chapter-sibling boosting stays disabled: provisions keep their distance order whatever their chapter."""
    hits = [mk("bnss_en", "480", dist=0.30, chapter="CHAPTER XXXV"), mk("it_en", "77B", dist=0.31, chapter="CHAPTER XI"),
            mk("bnss_en", "478", dist=0.32, chapter="CHAPTER XXXV")]
    context, _, _ = assemble_context(hits, "en")
    assert ids(context) == ["bnss_en:480:1", "it_en:77b:1", "bnss_en:478:1"]


def test_report_accounts_for_every_chunk_exactly_once_with_known_reasons():
    hits = ([mk("cp_en", "2", p, 13, n=2000, match="exact", dist=0.0) for p in range(1, 14)]
            + [mk("bns_en", str(i), dist=0.3 + i / 100) for i in range(1, 9)] + [sched("bnss_en", "The First Schedule", 8)])
    context, _, report = assemble_context(hits, "en")
    seen = [e["chunk_id"] for e in report["included"]] + [e["chunk_id"] for e in report["excluded"]]
    assert sorted(seen) == sorted(h["chunk_id"] for h in hits) and len(seen) == len(set(seen))
    assert {e["reason"] for e in report["excluded"]} <= ALLOWED_REASONS
    assert sum(e["chars"] for e in report["included"]) == report["used_chars"] == sum(len(c["text"]) for c in context)


def test_hindi_mode_keeps_the_legacy_selection(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_HINDI", True)
    monkeypatch.setattr(retrieval, "counterpart", lambda hit, lang: None)
    hits = [mk("bns_en", "103", dist=0.2), mk("bns_en", "103", 2, 2, dist=0.25), mk("bns_en", "104", dist=0.3)]
    context, flags, report = assemble_context(hits, "en")
    legacy, _ = retrieval.select_context(hits, "en")
    assert ids(context) == ids(legacy) and report["mode"] == "legacy"


# ------------------------------------------------------------------ pipeline wiring
def test_pipeline_uses_the_assembled_context_and_exposes_the_report(monkeypatch):
    hits = [mk("cp_en", "2", p, 13, n=2000, match="exact", dist=0.0) for p in range(1, 14)]
    monkeypatch.setattr(retrieval, "retrieve", lambda q: Retrieval(query_language="en", hits=hits, best_distance=0.3, exact_reference="2"))
    monkeypatch.setattr(generation, "stream_chat", lambda messages, max_tokens=700, stats=None: iter(["The definitions are listed [1]."]))
    monkeypatch.setattr(conversation, "get_history", lambda cid, limit=6: [])
    monkeypatch.setattr(conversation, "add_message", lambda *a, **k: None)
    monkeypatch.setattr(conversation, "new_conversation_id", lambda: "test-conversation")
    final = pipeline.answer("What are the definitions in Section 2 of the Consumer Protection Act?", "en")
    assert final["status"] == "answered"
    assert [s["chunk_id"] for s in final["sources"]] == ["cp_en:2:1", "cp_en:2:2", "cp_en:2:3"]
    report = final["context_report"]
    assert [e["chunk_id"] for e in report["included"]] == [s["chunk_id"] for s in final["sources"]]
    assert len(report["excluded"]) == 10 and report["truncated_provisions"][0]["parts_total"] == 13
