"""Retrieval: find the legal provisions relevant to a question, in either language.

Two complementary strategies are combined:
1. Exact lookup  - the question names a provision ("Section 103 BNS", "Article 21",
                   "धारा 103"). Embeddings are weak at numbers, so we fetch it by metadata.
2. Semantic search - the question is embedded with BGE-M3 and matched against ALL chunks,
                   English and Hindi together (cross-language retrieval).

Then ``select_context`` picks, per provision, the version in the user's language when a
reliable one exists, otherwise falls back to the other language and says so.
"""
import re
from dataclasses import dataclass, field

import config
from rag import catalog, vectorstore
from rag.embeddings import embed_texts
from rag.language import detect_language
from rag.preprocessing import normalize_unicode

# alias words found in a question -> act key (the prefix shared by that Act's doc_ids)
ACT_ALIASES: dict[str, list[str]] = {
    "bns": ["bns", "bharatiya nyaya", "भारतीय न्याय", "बीएनएस"],
    "bnss": ["bnss", "nagarik suraksha", "नागरिक सुरक्षा", "बीएनएसएस"],
    "bsa": ["bsa", "sakshya", "साक्ष्य", "बीएसए"],
    "constitution": ["constitution", "संविधान"],
    "it": ["it act", "information technology", "सूचना प्रौद्योगिकी", "आईटी अधिनियम"],
    "cp": ["consumer protection", "उपभोक्ता संरक्षण"],
}
# 'bnss' contains 'bns' so check longer aliases first
_ALIAS_ORDER = sorted(((a, k) for k, v in ACT_ALIASES.items() for a in v), key=lambda x: -len(x[0]))

REFERENCE_RE = re.compile(
    r"(?P<kind>section|sec\.?|s\.|धारा|article|art\.?|अनुच्छेद)\s*(?P<num>\d{1,3}[A-Za-z]{0,2})\b",
    re.IGNORECASE,
)
ARTICLE_WORDS = {"article", "art", "art.", "अनुच्छेद"}
ILLUSTRATION_PENALTY = 0.03


@dataclass
class Retrieval:
    query_language: str
    hits: list[dict] = field(default_factory=list)       # all candidates, best first
    best_distance: float = 1.0
    exact_reference: str | None = None


def _doc_ids_for(act_key: str) -> list[str]:
    # page-unit documents (the Hindi BNS booklet) have no real section numbers: never match them by number
    return [d.doc_id for d in catalog.active_documents() if d.doc_id.rsplit("_", 1)[0] == act_key and d.unit != "page"]


def _resolve_reference(question: str) -> tuple[str, list[str], bool] | None:
    """(number, doc_ids to look in, explicit). ``explicit`` is True when the question names the Act
    ("section 103 of the BNS") or says "Article" (Constitution); False for a bare "section 302", which is
    searched across every Act and therefore stays ambiguous."""
    q = normalize_unicode(question)
    m = REFERENCE_RE.search(q)
    if not m:
        return None
    number = m.group("num").upper()
    is_article = m.group("kind").lower() in ARTICLE_WORDS
    lowered = q.lower()
    for alias, key in _ALIAS_ORDER:
        if alias in lowered:
            return number, _doc_ids_for(key), True
    if is_article:
        return number, _doc_ids_for("constitution"), True
    return number, [d.doc_id for d in catalog.active_documents() if d.unit == "section"], False


def find_reference(question: str) -> tuple[str, list[str]] | None:
    """('103', [doc_ids to look in]) if the question names a specific section/article."""
    resolved = _resolve_reference(question)
    return None if resolved is None else (resolved[0], resolved[1])


EXACT_ALL_PARTS_LIMIT = 80   # a provision has at most 13 parts today; this leaves room
EXACT_PART_ONE_LIMIT = 12    # ambiguous references: first part of the provision in each Act, as before


def exact_lookup(number: str, doc_ids: list[str], all_parts: bool = False) -> list[dict]:
    """Fetch a provision by number. ``all_parts=True`` returns every chunk of it, in part order;
    the default keeps the earlier behaviour (part 1 only), which is still used for ambiguous references."""
    conditions = [{"section_number": number}, {"doc_id": {"$in": doc_ids}}]
    if not all_parts:
        conditions.append({"part": 1})
    chunks = vectorstore.get_chunks({"$and": conditions}, limit=EXACT_ALL_PARTS_LIMIT if all_parts else EXACT_PART_ONE_LIMIT)
    return sorted(chunks, key=lambda c: (c["doc_id"], int(c["part"])))    # numeric: part 10 comes after part 9


def retrieve(question: str, top_k: int | None = None) -> Retrieval:
    top_k = top_k or config.TOP_K
    result = Retrieval(query_language=detect_language(question))
    seen: set[str] = set()

    ref = _resolve_reference(question)
    if ref:
        number, doc_ids, explicit = ref
        result.exact_reference = number
        # An explicit reference gets every part of the provision; an ambiguous one keeps part 1 per Act.
        for hit in exact_lookup(number, doc_ids, all_parts=explicit):
            hit["match"] = "exact"
            seen.add(hit["chunk_id"])
            result.hits.append(hit)

    vector = embed_texts([question])[0]
    only_english = None if config.ENABLE_HINDI else {"language": "en"}   # belt and braces: even a mixed index is safe
    semantic = vectorstore.search(vector, top_k=top_k * 3, where=only_english)
    for hit in semantic:  # worked examples explain the law but are not the law: rank them slightly lower
        if hit.get("chunk_kind") == "illustration":
            hit["distance"] += ILLUSTRATION_PENALTY
    semantic.sort(key=lambda h: h["distance"])
    for hit in semantic:
        if hit["chunk_id"] not in seen:
            hit["match"] = "semantic"
            result.hits.append(hit)

    result.best_distance = min((h["distance"] for h in semantic), default=1.0)
    return result


def counterpart(hit: dict, language: str) -> dict | None:
    """Same provision in the other language, if it was found there with a matching number."""
    doc_ids = [d.doc_id for d in catalog.active_documents()
               if d.act_name_en == hit["act_name_en"] and d.language == language and d.unit != "page"]
    if not doc_ids or hit["unit"] in ("schedule", "page"):
        return None
    found = vectorstore.get_chunks(
        {"$and": [{"section_number": hit["section_number"]}, {"doc_id": {"$in": doc_ids}}, {"part": 1}]}, limit=1)
    return found[0] if found else None


def select_context(hits: list[dict], answer_language: str, max_provisions: int = 4) -> tuple[list[dict], dict]:
    """Choose which chunks the language model will see.

    One entry per provision (Act + section). Prefer a reliable chunk in ``answer_language``;
    otherwise use the other language. Returns (context_chunks, flags).
    """
    flags = {"used_fallback_language": False, "only_unreliable_ocr": False}
    provisions: dict[tuple, list[dict]] = {}
    for h in hits:
        provisions.setdefault((h["act_name_en"], h["unit"], h["section_number"]), []).append(h)

    context: list[dict] = []
    unreliable: list[dict] = []
    for group in provisions.values():
        if len(context) >= max_provisions:
            break
        best = group[0]
        candidates = [h for h in group if h["language"] == answer_language and not h["low_quality"]]
        chosen = candidates[0] if candidates else None
        if chosen is None:  # look for the answer-language version of this provision
            other = counterpart(best, answer_language)
            if other and not other["low_quality"]:
                chosen = other
        if chosen is None:  # fall back to any reliable version
            reliable = [h for h in group if not h["low_quality"]]
            if not reliable:
                other_lang = "en" if answer_language == "hi" else "hi"
                alt = counterpart(best, other_lang)
                reliable = [alt] if alt and not alt["low_quality"] else []
            if reliable:
                chosen = reliable[0]
                if answer_language == "hi" and chosen["language"] != "hi":
                    flags["used_fallback_language"] = True      # note only matters when a Hindi reader gets English text
            else:
                unreliable.append(best)
                continue
        context.append(chosen)

    if not context and unreliable:
        flags["only_unreliable_ocr"] = True
    flags["unreliable_sources"] = unreliable
    return context, flags


# --------------------------------------------------------------------------- budgeted context (English-only mode)
def _provision_key(chunk: dict) -> tuple:
    if chunk["unit"] == "schedule":
        # Every Schedule chunk is its own candidate: one table chunk must not stand for a whole Schedule.
        return (chunk["act_name_en"], "schedule", chunk["section_number"], chunk["chunk_id"])
    return (chunk["act_name_en"], chunk["unit"], chunk["section_number"])


def _provision_name(chunk: dict) -> str:
    return f"{chunk['doc_id']}:{chunk['unit']}:{chunk['section_number']}"


def _priority(chunk: dict) -> tuple:
    """Within one provision: operative text before illustrations, then in part order."""
    return (chunk.get("chunk_kind") != "operative", int(chunk["part"]))


def assemble_context(hits: list[dict], answer_language: str = "en", budget_chars: int | None = None,
                     max_provisions: int | None = None) -> tuple[list[dict], dict, dict]:
    """Choose the chunks the language model will see, under a character budget.

    Returns (context_chunks, flags, report). Order of preference:
      1. EXACT provisions (the question named them): every part, operative before illustrations, up to
         EXACT_BUDGET_FRACTION of the budget. The first part is always taken if the total budget allows.
      2. SEMANTIC provisions in rank order: the best-ranked chunk of each, up to MAX_PROVISIONS provisions.
      3. Other retrieved parts of provisions already included (they were relevant enough to be retrieved).
      4. SCHEDULE chunks (each its own candidate), at most MAX_SCHEDULE_CHUNKS, and only once
         MIN_PROVISIONS_BEFORE_SCHEDULE provisions are in (or nothing else was available).
    Chunks are whole: nothing is ever cut. The only chunk allowed to exceed the budget is the very first one.
    ``report`` lists every chunk with its reason: included (exact / semantic / extra_part / schedule) or excluded
    (budget / provision_cap / schedule_limit / low_quality), plus provisions that are only partly shown.
    Hindi mode keeps the earlier one-chunk-per-provision selection.
    """
    if config.ENABLE_HINDI:
        context, flags = select_context(hits, answer_language)
        report = {"mode": "legacy", "budget_chars": None, "used_chars": sum(len(c["text"]) for c in context),
                  "max_provisions": 4, "excluded": [], "truncated_provisions": [],
                  "included": [{"chunk_id": c["chunk_id"], "provision": _provision_name(c), "reason": "legacy",
                                "chars": len(c["text"]), "part": int(c["part"]), "parts_total": int(c["parts_total"])} for c in context]}
        return context, flags, report

    budget = config.CONTEXT_CHAR_BUDGET if budget_chars is None else budget_chars
    cap = config.MAX_PROVISIONS if max_provisions is None else max_provisions
    exact_budget = int(budget * config.EXACT_BUDGET_FRACTION)
    flags: dict = {"used_fallback_language": False, "only_unreliable_ocr": False, "unreliable_sources": []}
    included: list[tuple[dict, str]] = []
    excluded: list[tuple[dict, str]] = []
    used = 0

    def fits(chunk: dict) -> bool:
        return used == 0 or used + len(chunk["text"]) <= budget      # the very first chunk is always allowed

    def add(chunk: dict, reason: str) -> None:
        nonlocal used
        used += len(chunk["text"])
        included.append((chunk, reason))

    exact_groups: dict[tuple, list[dict]] = {}
    semantic_groups: dict[tuple, list[dict]] = {}
    for hit in hits:
        if hit["low_quality"]:
            flags["unreliable_sources"].append(hit)
            excluded.append((hit, "low_quality"))
            continue
        target = exact_groups if hit.get("match") == "exact" else semantic_groups
        target.setdefault(_provision_key(hit), []).append(hit)
    for key in [k for k in semantic_groups if k in exact_groups]:    # later parts of an exact provision found by search
        exact_groups[key].extend(semantic_groups.pop(key))

    chosen: dict[tuple, list[dict]] = {}                             # provision -> chunks taken (insertion order = priority)

    # 1. exact provisions
    exact_used = 0
    for key, chunks in exact_groups.items():
        ordered = sorted(chunks, key=_priority)
        if len(chosen) >= cap:
            excluded.extend((c, "provision_cap") for c in ordered)
            continue
        for chunk in ordered:
            size = len(chunk["text"])
            first_of_provision = key not in chosen
            if fits(chunk) and (first_of_provision or exact_used + size <= exact_budget):
                add(chunk, "exact")
                exact_used += size
                chosen.setdefault(key, []).append(chunk)
            else:
                excluded.append((chunk, "budget"))

    # 2. best chunk of each semantic provision, in rank order
    non_schedule = [(k, v) for k, v in semantic_groups.items() if k[1] != "schedule"]
    schedule = [(k, v) for k, v in semantic_groups.items() if k[1] == "schedule"]
    for key, chunks in non_schedule:
        if len(chosen) >= cap:
            excluded.extend((c, "provision_cap") for c in chunks)
        elif fits(chunks[0]):
            add(chunks[0], "semantic")
            chosen[key] = [chunks[0]]
        else:
            excluded.extend((c, "budget") for c in chunks)

    # 3. other retrieved parts of the provisions already included
    for key, chunks in non_schedule:
        if key in chosen:
            for chunk in sorted(chunks[1:], key=_priority):
                if fits(chunk):
                    add(chunk, "extra_part")
                    chosen[key].append(chunk)
                else:
                    excluded.append((chunk, "budget"))

    # 4. Schedule chunks: few, and late
    available = len(exact_groups) + len(non_schedule)
    eligible = len(chosen) >= config.MIN_PROVISIONS_BEFORE_SCHEDULE or available < config.MIN_PROVISIONS_BEFORE_SCHEDULE
    taken = 0
    for key, chunks in schedule:
        chunk = chunks[0]
        if len(chosen) >= cap:
            excluded.append((chunk, "provision_cap"))
        elif not eligible or taken >= config.MAX_SCHEDULE_CHUNKS:
            excluded.append((chunk, "schedule_limit"))
        elif fits(chunk):
            add(chunk, "schedule")
            chosen[key] = [chunk]
            taken += 1
        else:
            excluded.append((chunk, "budget"))

    # what the model will see: provisions in priority order, each in part order
    reason_of = {c["chunk_id"]: r for c, r in included}
    context: list[dict] = []
    included_entries: list[dict] = []
    truncated: list[dict] = []
    for key, chunks in chosen.items():
        ordered = sorted(chunks, key=lambda c: int(c["part"]))
        for chunk in ordered:
            context.append(chunk)
            included_entries.append({"chunk_id": chunk["chunk_id"], "provision": _provision_name(chunk),
                                     "reason": reason_of[chunk["chunk_id"]], "chars": len(chunk["text"]),
                                     "part": int(chunk["part"]), "parts_total": int(chunk["parts_total"])})
        parts_total = max(int(c["parts_total"]) for c in ordered)
        if key[1] != "schedule" and len(ordered) < parts_total:
            truncated.append({"provision": _provision_name(ordered[0]), "parts_included": [int(c["part"]) for c in ordered],
                              "parts_total": parts_total, "exact": key in exact_groups})
    if not context and flags["unreliable_sources"]:
        flags["only_unreliable_ocr"] = True
    report = {
        "mode": "budget", "budget_chars": budget, "used_chars": used, "max_provisions": cap,
        "included": included_entries,
        "excluded": [{"chunk_id": c["chunk_id"], "provision": _provision_name(c), "reason": r, "chars": len(c["text"]),
                      "part": int(c["part"]), "parts_total": int(c["parts_total"])} for c, r in excluded],
        "truncated_provisions": truncated,
    }
    return context, flags, report
