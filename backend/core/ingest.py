"""
Text extraction + chunking pipeline for NJM OS RAG ingestion.

Supports PDF (via PyMuPDF) and plain text (txt, md, csv).
chunk_text uses a simple sliding-window strategy.
"""
from __future__ import annotations

from typing import List

import fitz  # PyMuPDF

from core import rag as _rag

_CHUNK_SIZE = 500   # characters per chunk
_CHUNK_OVERLAP = 80 # overlap to preserve context across boundaries


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from file bytes.

    PDF: extracted via PyMuPDF page-by-page.
    Text-like files: decoded as UTF-8 (replace errors).
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            pages = [page.get_text() for page in doc]
        return "\n".join(pages)

    return file_bytes.decode("utf-8", errors="replace")


def chunk_text(
    text: str,
    chunk_size: int = _CHUNK_SIZE,
    overlap: int = _CHUNK_OVERLAP,
) -> List[str]:
    """
    Split text into overlapping character-level chunks.

    Overlap preserves sentence context at chunk boundaries.
    Returns a list with at least one element even for short texts.
    """
    if len(text) <= chunk_size:
        stripped = text.strip()
        return [stripped] if stripped else []

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def ingest_document(brand_id: str, file_bytes: bytes, filename: str) -> int:
    """
    Full pipeline: extract -> chunk -> embed -> upsert into ChromaDB.

    Returns number of chunks stored.
    Raises ValueError if extracted text is empty.
    """
    text = extract_text(file_bytes, filename)
    if not text.strip():
        raise ValueError(f"No extractable text found in '{filename}'.")

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError(f"Text in '{filename}' produced zero chunks.")

    return _rag.upsert_chunks(brand_id, chunks, source=filename)
