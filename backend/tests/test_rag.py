"""Tests for core/rag.py — ChromaDB collection manager."""
import os
import pytest

# Load env before any module import
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


def test_get_collection_returns_chroma_collection():
    """get_collection(brand_id) must return a Chroma collection object."""
    from core.rag import get_collection
    col = get_collection("test-brand-pytest")
    assert col is not None
    assert hasattr(col, "add")
    assert hasattr(col, "query")


def test_upsert_chunks_stores_and_retrieves():
    """upsert_chunks stores text; query_brand retrieves relevant chunks."""
    from core.rag import upsert_chunks, query_brand

    brand = "test-brand-upsert"
    chunks = ["El CAC objetivo es $120 mensual.", "LTV proyectado: $2,400."]
    upsert_chunks(brand, chunks, source="test_doc.txt")

    results = query_brand(brand, "¿Cuál es el CAC?", n_results=1)
    assert len(results) >= 1
    assert any("CAC" in r for r in results)


def test_query_brand_empty_collection_returns_empty():
    """query_brand on a brand with no docs returns an empty list."""
    from core.rag import query_brand

    results = query_brand("brand-never-ingested-xyz-99", "test query", n_results=3)
    assert isinstance(results, list)
    assert len(results) == 0
