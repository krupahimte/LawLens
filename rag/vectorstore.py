"""ChromaDB wrapper: persistent storage of chunk vectors + metadata, and similarity search.

Chroma stores, per chunk: an id, the embedding vector, the chunk text ("document")
and scalar metadata (Act, section, pages, language, OCR confidence...).
Distance is cosine distance: 0 = identical direction, ~1 = unrelated.
"""
import chromadb

import config

_client = None


def get_collection():
    global _client
    if _client is None:
        config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return _client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# Fields from a chunk dict that become Chroma metadata (everything except the text itself).
METADATA_FIELDS = [
    "doc_id", "act_name", "act_name_en", "language", "unit", "section_number", "section_title",
    "chapter", "page_start", "page_end", "part", "parts_total", "chunk_kind", "number_inferred", "text_source", "ocr_conf",
    "low_quality", "number_verified", "text_hash",
]


def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]) -> None:
    collection = get_collection()
    collection.upsert(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[{k: c[k] for k in METADATA_FIELDS} for c in chunks],
    )


def existing_metadata(ids: list[str]) -> dict[str, dict]:
    """chunk_id -> stored metadata for chunks already in the index."""
    found: dict[str, dict] = {}
    collection = get_collection()
    for i in range(0, len(ids), 500):
        got = collection.get(ids=ids[i:i + 500], include=["metadatas"])
        found.update(zip(got["ids"], got["metadatas"]))
    return found


def update_metadata(chunks: list[dict]) -> None:
    """Change metadata only (the stored vectors stay as they are)."""
    get_collection().update(ids=[c["chunk_id"] for c in chunks],
                            metadatas=[{k: c[k] for k in METADATA_FIELDS} for c in chunks])


def delete_stale(doc_id: str, keep_ids: set[str]) -> int:
    """Remove chunks of a document that no longer exist (e.g. after re-chunking)."""
    collection = get_collection()
    stored = collection.get(where={"doc_id": doc_id}, include=[])["ids"]
    stale = [cid for cid in stored if cid not in keep_ids]
    for i in range(0, len(stale), 500):
        collection.delete(ids=stale[i:i + 500])
    return len(stale)


def search(query_embedding: list[float], top_k: int, where: dict | None = None) -> list[dict]:
    """Nearest chunks to the query vector, as dicts with text, metadata and distance."""
    result = get_collection().query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for cid, text, meta, dist in zip(result["ids"][0], result["documents"][0],
                                     result["metadatas"][0], result["distances"][0]):
        hits.append({"chunk_id": cid, "text": text, "distance": dist, **meta})
    return hits


def get_chunks(where: dict, limit: int = 20) -> list[dict]:
    """Exact metadata lookup (no similarity), e.g. every chunk of 'Section 103' in given documents."""
    got = get_collection().get(where=where, limit=limit, include=["documents", "metadatas"])
    return [{"chunk_id": cid, "text": text, "distance": 0.0, **meta}
            for cid, text, meta in zip(got["ids"], got["documents"], got["metadatas"])]


def count() -> int:
    return get_collection().count()
