"""
ChromaDB client and collection manager for NJM OS RAG pipeline.

One persistent ChromaDB collection per brand_id.
Client is a module-level singleton (one HTTP/file handle per process).
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import List

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

_CHROMA_PATH = Path(__file__).resolve().parent.parent / "chroma_db"
_EMBED_MODEL = "text-embedding-3-small"

_client: chromadb.ClientAPI | None = None
_embed_fn: OpenAIEmbeddingFunction | None = None
_init_lock = threading.Lock()


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        with _init_lock:
            if _client is None:
                _CHROMA_PATH.mkdir(parents=True, exist_ok=True)
                _client = chromadb.PersistentClient(path=str(_CHROMA_PATH))
    return _client


def _get_embed_fn() -> OpenAIEmbeddingFunction:
    global _embed_fn
    if _embed_fn is None:
        with _init_lock:
            if _embed_fn is None:
                api_key = os.environ.get("OPENAI_API_KEY", "")
                _embed_fn = OpenAIEmbeddingFunction(
                    api_key=api_key,
                    model_name=_EMBED_MODEL,
                )
    return _embed_fn


def get_collection(brand_id: str) -> chromadb.Collection:
    """Return (or create) the ChromaDB collection for a brand."""
    safe_name = brand_id.replace(" ", "_").replace("/", "_")[:63]
    return _get_client().get_or_create_collection(
        name=safe_name,
        embedding_function=_get_embed_fn(),
    )


def upsert_chunks(brand_id: str, chunks: List[str], source: str = "") -> int:
    """
    Embed and upsert text chunks into brand's collection.

    IDs are deterministic: {source}::{index} so re-ingesting the same
    file is idempotent (upsert overwrites existing docs with same ID).

    Returns number of chunks stored.
    """
    if not chunks:
        return 0

    col = get_collection(brand_id)
    ids = [f"{source}::{i}" for i in range(len(chunks))]
    metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]

    col.upsert(documents=chunks, ids=ids, metadatas=metadatas)
    return len(chunks)


def query_brand(brand_id: str, query_text: str, n_results: int = 5) -> List[str]:
    """
    Semantic search over brand's collection.

    Returns list of text chunks ranked by relevance.
    Returns [] if collection is empty or brand never ingested.
    """
    col = get_collection(brand_id)
    count = col.count()
    if count == 0:
        return []

    actual_n = min(n_results, count)
    results = col.query(query_texts=[query_text], n_results=actual_n)
    docs = results.get("documents", [[]])[0]
    return docs
