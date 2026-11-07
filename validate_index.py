"""Validate a ChromaDB collection before the application is switched to it.

Usage:  COLLECTION_NAME=indian_law_en python validate_index.py
Writes docs/INDEX_VALIDATION.md and exits non-zero if any check fails.

Checks: chunk ids match data/processed/*.jsonl, English-only, section/article coverage against the known
structure of each Act, metadata completeness, page numbers inside the PDF, vector dimension, and a random
text spot-check that chunk text really occurs on the cited PDF pages.
"""
import collections
import datetime
import json
import random
import re
import sys
import unicodedata

import chromadb
import pymupdf

import config
from rag import catalog

# Validation configuration (all of it is echoed at the top of the report)
SPOT_SAMPLE = 60            # chunks checked verbatim against the PDF
SPOT_SEED = 7               # fixed seed: the same chunks are sampled on every run
SPOT_MAX_FAIL = 2           # tolerated misses (a 50-character window can straddle a page break)
SPOT_WINDOW = 50            # characters compared at the start and at the end of each sampled chunk
LENGTH_MIN, LENGTH_MAX = 30, 2500
EXPECTED_DIM = 1024         # BGE-M3 dense vector size

# Known structure of the enacted English texts. Constitution: articles omitted from the text by amendment.
EXPECTED_TOP_NUMBER = {"bns_en": 358, "bnss_en": 531, "bsa_en": 170, "cp_en": 107, "it_en": 94, "constitution_en": 395}
KNOWN_OMITTED = {"constitution_en": {232, 238, 259, 272}}
REQUIRED = ["doc_id", "act_name", "act_name_en", "language", "unit", "section_number", "page_start", "page_end",
            "part", "text_source", "chunk_kind"]
DEVANAGARI = re.compile(r"[ऀ-ॿ]")

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + (f" - {detail}" if detail else ""))


def squash(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text)).replace("\x01", "")


def open_existing_collection():
    """Open the collection named by COLLECTION_NAME and NEVER create it.

    (vectorstore.get_collection uses get_or_create_collection, so a mistyped name would silently create an
    empty collection. A validator must only look.)"""
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    names = sorted(c.name for c in client.list_collections())
    if config.COLLECTION_NAME not in names:
        raise SystemExit(f"Collection '{config.COLLECTION_NAME}' does not exist in {config.CHROMA_DIR}. "
                         f"Existing collections: {names}. Nothing was created. "
                         f"Set COLLECTION_NAME to one of them (for the English-only build: indian_law_en).")
    return client.get_collection(config.COLLECTION_NAME)


def config_lines() -> list[tuple[str, str]]:
    return [
        ("Collection validated", config.COLLECTION_NAME),
        ("Chroma directory", str(config.CHROMA_DIR)),
        ("Run at", datetime.datetime.now().isoformat(timespec="seconds")),
        ("chromadb version", chromadb.__version__),
        ("Embedding model", config.EMBED_MODEL),
        ("ENABLE_HINDI", str(config.ENABLE_HINDI)),
        ("Active documents", ", ".join(d.doc_id for d in catalog.active_documents())),
        ("Expected top section/article numbers", json.dumps(EXPECTED_TOP_NUMBER)),
        ("Known omitted numbers", json.dumps({k: sorted(v) for k, v in KNOWN_OMITTED.items()})),
        ("Required metadata fields", ", ".join(REQUIRED)),
        ("Chunk length bounds (characters)", f"{LENGTH_MIN}..{LENGTH_MAX}"),
        ("Expected vector dimension", str(EXPECTED_DIM)),
        ("PDF spot-check", f"{SPOT_SAMPLE} random chunks, seed {SPOT_SEED}, first and last {SPOT_WINDOW} characters, "
                           f"at most {SPOT_MAX_FAIL} misses tolerated"),
        ("Processed files compared", str(config.PROCESSED_DIR / "<doc_id>.jsonl")),
    ]


def main() -> int:
    col = open_existing_collection()
    for key, value in config_lines():
        print(f"{key}: {value}")
    got = col.get(include=["documents", "metadatas", "embeddings"])
    ids, docs, metas, embs = got["ids"], got["documents"], got["metadatas"], got["embeddings"]
    print(f"Collection '{config.COLLECTION_NAME}': {len(ids)} chunks")

    expected_ids: set[str] = set()
    for d in catalog.active_documents():
        for line in (config.PROCESSED_DIR / f"{d.doc_id}.jsonl").open(encoding="utf-8"):
            expected_ids.add(json.loads(line)["chunk_id"])
    check("chunk ids equal the processed files (nothing missing, nothing extra)", set(ids) == expected_ids,
          f"collection={len(ids)} expected={len(expected_ids)} missing={len(expected_ids - set(ids))} extra={len(set(ids) - expected_ids)}")
    check("chunk ids are unique", len(ids) == len(set(ids)))
    check("no Hindi chunks: every chunk has language=en", all(m["language"] == "en" for m in metas),
          str(collections.Counter(m["language"] for m in metas)))
    check("no Devanagari characters in any chunk text", not any(DEVANAGARI.search(t) for t in docs))
    check("only English documents present", {m["doc_id"] for m in metas} == {d.doc_id for d in catalog.active_documents()},
          str(sorted({m["doc_id"] for m in metas})))

    per_doc = collections.defaultdict(list)
    for cid, text, m in zip(ids, docs, metas):
        per_doc[m["doc_id"]].append((cid, text, m))

    rows = []
    for doc_id, top in EXPECTED_TOP_NUMBER.items():
        items = per_doc.get(doc_id, [])
        numbers = {int(re.match(r"\d+", m["section_number"]).group()) for _, _, m in items if m["unit"] in ("section", "article")}
        missing = sorted(set(range(1, top + 1)) - numbers - KNOWN_OMITTED.get(doc_id, set()))
        extra = sorted(n for n in numbers if n > top)
        lettered = sorted({m["section_number"] for _, _, m in items if re.search(r"[A-Z]$", m["section_number"])})
        rows.append((doc_id, len(items), len(numbers), top, missing, extra, len(lettered)))
        check(f"{doc_id}: every section/article 1..{top} present"
              + (f" (known omitted: {sorted(KNOWN_OMITTED[doc_id])})" if doc_id in KNOWN_OMITTED else ""),
              not missing and not extra, f"chunks={len(items)} distinct numbers={len(numbers)} missing={missing} beyond={extra} lettered={len(lettered)}")

    bad_meta = [cid for cid, m in zip(ids, metas) if any(m.get(k) in (None, "") for k in REQUIRED)]
    check("required metadata present on every chunk", not bad_meta, f"{len(bad_meta)} incomplete {bad_meta[:3]}")
    check("provenance fields correct (text_layer, not low quality, no OCR confidence)",
          all(m["text_source"] == "text_layer" and not m["low_quality"] and m["ocr_conf"] == -1.0 and not m.get("number_inferred") for m in metas))
    check("chunk_kind is operative or illustration", all(m["chunk_kind"] in ("operative", "illustration") for m in metas),
          str(collections.Counter(m["chunk_kind"] for m in metas)))
    check("page ranges valid", all(1 <= m["page_start"] <= m["page_end"] for m in metas))
    check(f"chunk lengths sane ({LENGTH_MIN}..{LENGTH_MAX} characters)", all(LENGTH_MIN <= len(t) <= LENGTH_MAX for t in docs),
          f"min={min(map(len, docs))} max={max(map(len, docs))}")
    dims = {len(e) for e in embs}
    check(f"every vector has {EXPECTED_DIM} dimensions (BGE-M3)", dims == {EXPECTED_DIM}, str(dims))

    # pages inside each PDF + random spot-check that the chunk text is really on the cited pages
    random.seed(SPOT_SEED)
    sample = random.sample(range(len(ids)), min(SPOT_SAMPLE, len(ids)))
    pdf_cache: dict[str, pymupdf.Document] = {}
    page_text_cache: dict[tuple[str, int], str] = {}
    page_errors, spot_fail = [], []
    for doc_id, items in per_doc.items():
        pdf_cache[doc_id] = pymupdf.open(catalog.get(doc_id).path)
        n_pages = len(pdf_cache[doc_id])
        page_errors += [cid for cid, _, m in items if m["page_end"] > n_pages]
    check("page numbers lie inside the PDFs", not page_errors, f"{len(page_errors)} out of range")

    def page_text(doc_id: str, page: int) -> str:
        key = (doc_id, page)
        if key not in page_text_cache:
            page_text_cache[key] = squash(pdf_cache[doc_id][page - 1].get_text("text"))
        return page_text_cache[key]

    for i in sample:
        m, text = metas[i], docs[i]
        cited = "".join(page_text(m["doc_id"], p) for p in range(m["page_start"], m["page_end"] + 1))
        flat = squash(text)
        head, tail = flat[:SPOT_WINDOW], flat[-SPOT_WINDOW:]
        if head not in cited or tail not in cited:
            spot_fail.append((ids[i], head in cited, tail in cited))
    check(f"random spot-check: {len(sample)} chunks' first and last {SPOT_WINDOW} characters occur on the cited PDF pages",
          len(spot_fail) <= SPOT_MAX_FAIL, f"{len(sample) - len(spot_fail)}/{len(sample)} verbatim; failures: {spot_fail[:5]}")

    # markdown report
    lines = [f"# Index validation: collection `{config.COLLECTION_NAME}`", "",
             "## Validation configuration", "", "| Setting | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in config_lines()]
    lines += ["", f"Total chunks: **{len(ids)}**", "", "## Checks", "", "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f"| {n} | {'PASS' if ok else '**FAIL**'} | {d} |" for n, ok, d in results]
    lines += ["", "## Coverage by document", "", "| Document | Chunks | Distinct numbers | Expected top number | Missing | Beyond |", "|---|---|---|---|---|---|"]
    lines += [f"| {d} | {c} | {n} | {t} | {mi or '-'} | {ex or '-'} |" for d, c, n, t, mi, ex, _ in rows]
    (config.BASE_DIR / "docs").mkdir(exist_ok=True)
    (config.BASE_DIR / "docs" / "INDEX_VALIDATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed" + (f"; FAILED: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
