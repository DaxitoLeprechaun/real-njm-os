"""
NJM OS — ChromaDB Vector Store (singleton)

Usa Voyage AI via langchain-community para embeddings, compatible con ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import os

from langchain_chroma import Chroma
from langchain_community.embeddings import VoyageAIEmbeddings

_PERSIST_DIR = os.environ.get("NJM_VECTOR_DIR", "/tmp/njm_vectorstore")
_VOYAGE_KEY = os.environ.get("VOYAGE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")

_EMBEDDING = VoyageAIEmbeddings(
    voyage_api_key=_VOYAGE_KEY,
    model="voyage-3",
)

vector_store = Chroma(
    collection_name="njm_os_documents",
    embedding_function=_EMBEDDING,
    persist_directory=_PERSIST_DIR,
)
