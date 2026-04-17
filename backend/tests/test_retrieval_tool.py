"""Tests for tools/retrieval_tool.py — buscar_contexto_marca @tool."""
import os
import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key-for-unit-tests")


def test_buscar_contexto_marca_returns_formatted_string(monkeypatch):
    """buscar_contexto_marca calls query_brand and returns formatted context."""
    from core import rag as rag_mod

    monkeypatch.setattr(
        rag_mod,
        "query_brand",
        lambda brand_id, query_text, n_results: [
            "CAC objetivo $120.",
            "LTV proyectado $2,400.",
        ],
    )

    from tools.retrieval_tool import buscar_contexto_marca

    result = buscar_contexto_marca.invoke({
        "brand_id": "disrupt",
        "consulta": "¿Cuál es el CAC?",
        "n_resultados": 3,
    })

    assert "CAC objetivo $120" in result
    assert "LTV proyectado" in result
    assert "Fragmento 1" in result


def test_buscar_contexto_marca_no_docs(monkeypatch):
    """Returns a clear message when brand has no ingested documents."""
    from core import rag as rag_mod

    monkeypatch.setattr(
        rag_mod,
        "query_brand",
        lambda brand_id, query_text, n_results: [],
    )

    from tools.retrieval_tool import buscar_contexto_marca

    result = buscar_contexto_marca.invoke({
        "brand_id": "brand-sin-docs",
        "consulta": "cualquier cosa",
        "n_resultados": 3,
    })

    assert "sin documentos" in result.lower() or "no se encontró" in result.lower()
