"""Embeddings with BGE-M3 through a local Ollama server.

An embedding turns text into a list of 1024 numbers so that texts with similar
meaning (in English OR Hindi) end up close together. Everything runs locally and free.

Replaces the earlier OpenAI-based version, which needed a paid API key.
"""
import httpx

import config


class OllamaError(RuntimeError):
    """Ollama is unreachable, or the model is missing."""


def _post(path: str, payload: dict) -> dict:
    try:
        response = httpx.post(f"{config.OLLAMA_URL}{path}", json=payload, timeout=config.OLLAMA_TIMEOUT)
    except httpx.ConnectError as exc:
        raise OllamaError(f"Cannot reach Ollama at {config.OLLAMA_URL}. Is it running? (try: ollama serve)") from exc
    if response.status_code == 404:
        raise OllamaError(f"Model not found in Ollama. Run: ollama pull {payload.get('model')}")
    response.raise_for_status()
    return response.json()


def embed_texts(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    """Embed many texts; one HTTP call per batch. Output order matches input order."""
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        data = _post("/api/embed", {"model": config.EMBED_MODEL, "input": batch})
        vectors.extend(data["embeddings"])
    if len(vectors) != len(texts):
        raise OllamaError(f"Expected {len(texts)} embeddings, got {len(vectors)}")
    return vectors


def generate_embedding(text: str) -> list[float]:
    """Embed a single text (kept from the original module)."""
    return embed_texts([text])[0]
