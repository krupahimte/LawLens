"""Build the searchable knowledge base: PDFs -> chunks -> embeddings -> ChromaDB.

Usage (from the project root):
    python ingest.py                    # every document whose text is ready
    python ingest.py --docs bns_en it_en
    python ingest.py --no-embed         # only (re)build data/processed/*.jsonl and the report

Hindi documents need OCR first (python -m rag.ocr). Documents with incomplete OCR are skipped.
Chunks whose text did not change since the last run are not re-embedded.
"""
import argparse
import hashlib
import json
import time

import config
from rag import catalog, vectorstore
from rag.chunking import build_chunks, embedding_text
from rag.embeddings import embed_texts
from rag.extraction import load_pages


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def english_sections() -> dict[str, set[str]]:
    """act_name_en -> set of section/article numbers found in the English PDF (the reference)."""
    sections: dict[str, set[str]] = {}
    for doc in catalog.DOCUMENTS:
        if doc.language == "en":
            chunks = build_chunks(doc, load_pages(doc))
            sections[doc.act_name_en] = {c["section_number"] for c in chunks if c["unit"] != "schedule"}
    return sections


def prepare(doc: catalog.Document, reference: dict[str, set[str]]) -> list[dict]:
    chunks = build_chunks(doc, load_pages(doc))
    for c in chunks:
        c["text_hash"] = text_hash(c["text"])
        if c["unit"] in ("schedule", "page"):
            c["number_verified"] = -1            # not a numbered provision: nothing to verify
        elif doc.language == "en":
            c["number_verified"] = 1
        else:  # Hindi: does this section number also exist in the English text of the same Act?
            c["number_verified"] = int(c["section_number"] in reference.get(doc.act_name_en, set()))
    return chunks


def save_chunks(doc: catalog.Document, chunks: list[dict]) -> None:
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = config.PROCESSED_DIR / f"{doc.doc_id}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


def embed_and_store(doc: catalog.Document, chunks: list[dict]) -> int:
    known = vectorstore.existing_metadata([c["chunk_id"] for c in chunks])
    todo = [c for c in chunks if known.get(c["chunk_id"], {}).get("text_hash") != c["text_hash"]]
    todo_ids = {c["chunk_id"] for c in todo}
    # same text, different metadata (e.g. a new field): update metadata only, no re-embedding
    meta_only = [c for c in chunks if c["chunk_id"] not in todo_ids
                 and any(known[c["chunk_id"]].get(k) != c[k] for k in vectorstore.METADATA_FIELDS)]
    for i in range(0, len(meta_only), 500):
        vectorstore.update_metadata(meta_only[i:i + 500])
    removed = vectorstore.delete_stale(doc.doc_id, {c["chunk_id"] for c in chunks})
    if meta_only or removed:
        print(f"   metadata updated for {len(meta_only)} chunks, removed {removed} stale chunks")
    for i in range(0, len(todo), 64):  # store in slices so progress is saved
        part = todo[i:i + 64]
        vectors = embed_texts([embedding_text(c, doc) for c in part])
        vectorstore.upsert_chunks(part, vectors)
        print(f"   embedded {min(i + 64, len(todo))}/{len(todo)}", flush=True)
    return len(todo)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--docs", nargs="*", help="doc_ids to process (default: all ready)")
    parser.add_argument("--no-embed", action="store_true", help="skip embedding/ChromaDB")
    args = parser.parse_args()

    docs = [catalog.get(d) for d in args.docs] if args.docs else catalog.active_documents()
    blocked = [d.doc_id for d in docs if d not in catalog.active_documents()]
    if blocked:
        raise SystemExit(f"Hindi ingestion is disabled (ENABLE_HINDI=false): {blocked}")
    print(f"Collection: {config.COLLECTION_NAME} | documents: {[d.doc_id for d in docs]}")
    reference = english_sections()
    report = {}
    for doc in docs:
        try:
            chunks = prepare(doc, reference)
        except RuntimeError as exc:  # OCR not finished
            print(f"[{doc.doc_id}] SKIPPED: {exc}")
            continue
        save_chunks(doc, chunks)
        sections = [c for c in chunks if c["unit"] not in ("schedule", "page") and c["part"] == 1]
        unverified = [c["section_number"] for c in sections if c["number_verified"] == 0]
        low_quality = sum(c["low_quality"] for c in chunks)
        report[doc.doc_id] = {
            "chunks": len(chunks), "sections": len(sections),
            "unverified_numbers": unverified, "low_quality_chunks": low_quality,
        }
        print(f"[{doc.doc_id}] {len(chunks)} chunks, {len(sections)} sections, "
              f"{len(unverified)} numbers not found in English, {low_quality} low-quality chunks")
        if not args.no_embed:
            start = time.time()
            n = embed_and_store(doc, chunks)
            print(f"[{doc.doc_id}] embedded {n} new/changed chunks in {time.time() - start:.0f}s")
    (config.PROCESSED_DIR / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if not args.no_embed:
        print(f"ChromaDB now holds {vectorstore.count()} chunks")


if __name__ == "__main__":
    main()
