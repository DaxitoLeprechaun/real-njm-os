"""Tests for core/ingest.py — extraction, chunking, and pipeline."""
import os
import pytest

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


def test_extract_text_from_txt():
    """extract_text handles plain text bytes."""
    from core.ingest import extract_text

    content = b"Hola mundo. Este es un texto de prueba."
    result = extract_text(content, filename="test.txt")
    assert "Hola mundo" in result
    assert len(result) > 0


def test_extract_text_from_pdf():
    """extract_text handles a real minimal PDF via PyMuPDF."""
    import fitz  # PyMuPDF

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "CAC objetivo $120. LTV $2400.")
    pdf_bytes = doc.tobytes()
    doc.close()

    from core.ingest import extract_text

    result = extract_text(pdf_bytes, filename="brand.pdf")
    assert "CAC" in result or "120" in result


def test_chunk_text_splits_correctly():
    """chunk_text produces chunks with configured size."""
    from core.ingest import chunk_text

    text = "A" * 1200
    chunks = chunk_text(text, chunk_size=500, overlap=50)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 500


def test_chunk_text_short_text_single_chunk():
    """chunk_text with text shorter than chunk_size returns one chunk."""
    from core.ingest import chunk_text

    text = "Short text."
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == "Short text."


def test_ingest_document_returns_chunk_count(monkeypatch):
    """ingest_document calls upsert_chunks and returns chunk count > 0."""
    from core import ingest, rag

    upserted = []

    def fake_upsert(brand_id, chunks, source=""):
        upserted.extend(chunks)
        return len(chunks)

    monkeypatch.setattr(rag, "upsert_chunks", fake_upsert)

    content = b"Vector 1: CAC $120. Vector 2: LTV $2400. " * 20
    count = ingest.ingest_document(
        brand_id="test-brand",
        file_bytes=content,
        filename="brief.txt",
    )
    assert count > 0
    assert len(upserted) > 0
