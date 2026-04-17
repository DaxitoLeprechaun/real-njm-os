"""Integration test for POST /api/v1/ingest with RAG pipeline."""
import os
import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key-for-unit-tests")

from fastapi.testclient import TestClient


def test_ingest_endpoint_calls_rag_pipeline(monkeypatch):
    """POST /api/v1/ingest must call ingest_document and return chunks_stored."""
    from core import ingest as ingest_mod

    calls = []

    def fake_ingest(brand_id, file_bytes, filename):
        calls.append({"brand_id": brand_id, "filename": filename})
        return 7

    monkeypatch.setattr(ingest_mod, "ingest_document", fake_ingest)

    from main import app
    client = TestClient(app)

    response = client.post(
        "/api/v1/ingest",
        data={"brand_id": "disrupt", "context": "test", "vectorId": "v1"},
        files={"file": ("brief.txt", b"hola mundo " * 50, "text/plain")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["chunks_stored"] == 7
    assert len(calls) == 1
    assert calls[0]["brand_id"] == "disrupt"


def test_ingest_endpoint_empty_file_returns_422(monkeypatch):
    """POST /api/v1/ingest with unextractable file returns 422."""
    from core import ingest as ingest_mod

    def fake_ingest(brand_id, file_bytes, filename):
        raise ValueError("No extractable text found.")

    monkeypatch.setattr(ingest_mod, "ingest_document", fake_ingest)

    from main import app
    client = TestClient(app)

    response = client.post(
        "/api/v1/ingest",
        data={"brand_id": "disrupt", "context": "", "vectorId": ""},
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 422
