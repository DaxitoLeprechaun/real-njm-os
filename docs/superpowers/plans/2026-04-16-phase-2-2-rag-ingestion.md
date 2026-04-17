# Phase 2.2 — RAG Ingestion Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `POST /api/v1/ingest` to extract text from PDF/TXT uploads, chunk it, embed with OpenAI, persist in ChromaDB keyed by `brand_id`, and expose a `buscar_contexto_marca` retrieval tool to both CEO and PM agents.

**Architecture:** A new `core/rag.py` module owns all ChromaDB I/O (one persistent collection per brand). A new `core/ingest.py` orchestrates extraction → chunking → embedding → upsert. The existing v1 router calls `ingest.py` after saving the file. Both agent nodes gain a `buscar_contexto_marca` @tool that queries `core/rag.py`.

**Tech Stack:** PyMuPDF (`pymupdf`) for PDF extraction, ChromaDB (`chromadb`) for vector storage, `langchain-chroma` + `langchain-openai` `OpenAIEmbeddings` for embedding, Python 3.11+.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/requirements.txt` | Modify | Add `pymupdf`, `chromadb`, `langchain-chroma` |
| `backend/core/rag.py` | Create | ChromaDB client singleton, get/upsert/query per brand |
| `backend/core/ingest.py` | Create | Extract text (PDF/TXT), chunk, embed, call rag.py |
| `backend/api/v1_router.py` | Modify | Call `ingest_document_rag()` after file save, pass `brand_id` |
| `backend/tools/retrieval_tool.py` | Create | `buscar_contexto_marca` @tool wrapping rag.py |
| `backend/agentes/agente_ceo.py` | Modify | Add `buscar_contexto_marca` to `CEO_TOOLS` |
| `backend/agentes/agente_pm.py` | Modify | Add `buscar_contexto_marca` to `PM_SKILLS` / tool list |
| `backend/tests/test_rag.py` | Create | Unit tests for rag.py and ingest.py |
| `backend/tests/test_ingest_endpoint.py` | Create | Integration test for `POST /api/v1/ingest` |

---

## Task 1: Add dependencies

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add packages**

Open `backend/requirements.txt` and append after `python-multipart`:

```
# RAG pipeline
pymupdf==1.24.5
chromadb==0.5.20
langchain-chroma==0.1.4
```

- [ ] **Step 2: Install and verify**

```bash
cd backend
.venv/bin/pip install pymupdf==1.24.5 chromadb==0.5.20 langchain-chroma==0.1.4
.venv/bin/python3 -c "import fitz; import chromadb; from langchain_chroma import Chroma; print('OK')"
```

Expected output: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add pymupdf, chromadb, langchain-chroma for Phase 2.2 RAG"
```

---

## Task 2: Create `core/rag.py` — ChromaDB client and collection manager

**Files:**
- Create: `backend/core/rag.py`
- Test: `backend/tests/test_rag.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_rag.py`:

```python
"""Tests for core/rag.py — ChromaDB collection manager."""
import pytest
from unittest.mock import patch, MagicMock


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

    results = query_brand("brand-never-ingested-xyz", "test query", n_results=3)
    assert isinstance(results, list)
    assert len(results) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_rag.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'core.rag'`

- [ ] **Step 3: Implement `core/rag.py`**

Create `backend/core/rag.py`:

```python
"""
ChromaDB client and collection manager for NJM OS RAG pipeline.

One persistent ChromaDB collection per brand_id.
Client is a module-level singleton (one HTTP/file handle per process).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

_CHROMA_PATH = Path(__file__).resolve().parent.parent / "chroma_db"
_EMBED_MODEL = "text-embedding-3-small"

_client: chromadb.ClientAPI | None = None
_embed_fn: OpenAIEmbeddingFunction | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(_CHROMA_PATH))
    return _client


def _get_embed_fn() -> OpenAIEmbeddingFunction:
    global _embed_fn
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
```

- [ ] **Step 4: Run tests**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_rag.py -v
```

Expected: 3 PASSED (will make real OpenAI embedding calls — ensure `OPENAI_API_KEY` is set in `.env`)

- [ ] **Step 5: Commit**

```bash
git add backend/core/rag.py backend/tests/test_rag.py
git commit -m "feat: add core/rag.py — ChromaDB collection manager with upsert + query"
```

---

## Task 3: Create `core/ingest.py` — text extraction + chunking

**Files:**
- Create: `backend/core/ingest.py`
- Test: `backend/tests/test_ingest.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_ingest.py`:

```python
"""Tests for core/ingest.py — extraction, chunking, and pipeline."""
import io
import pytest
from pathlib import Path


def test_extract_text_from_txt():
    """extract_text handles plain text bytes."""
    from core.ingest import extract_text

    content = b"Hola mundo. Este es un texto de prueba."
    result = extract_text(content, filename="test.txt")
    assert "Hola mundo" in result
    assert len(result) > 0


def test_extract_text_from_pdf(tmp_path):
    """extract_text handles a real minimal PDF via PyMuPDF."""
    import fitz  # PyMuPDF

    # Create a minimal PDF in memory
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "CAC objetivo $120. LTV $2400.")
    pdf_bytes = doc.tobytes()
    doc.close()

    from core.ingest import extract_text

    result = extract_text(pdf_bytes, filename="brand.pdf")
    assert "CAC" in result or "120" in result


def test_chunk_text_splits_correctly():
    """chunk_text produces chunks with configured size and overlap."""
    from core.ingest import chunk_text

    text = "A" * 1200  # 1200 chars
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_ingest.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'core.ingest'`

- [ ] **Step 3: Implement `core/ingest.py`**

Create `backend/core/ingest.py`:

```python
"""
Text extraction + chunking pipeline for NJM OS RAG ingestion.

Supports PDF (via PyMuPDF) and plain text (txt, md, csv).
chunk_text uses a simple sliding-window strategy.
"""
from __future__ import annotations

from typing import List

import fitz  # PyMuPDF

from core.rag import upsert_chunks

_SUPPORTED_TEXT_EXTS = {".txt", ".md", ".csv", ".json"}
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
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
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
    Full pipeline: extract → chunk → embed → upsert into ChromaDB.

    Returns number of chunks stored.
    Raises ValueError if extracted text is empty.
    """
    text = extract_text(file_bytes, filename)
    if not text.strip():
        raise ValueError(f"No extractable text found in '{filename}'.")

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError(f"Text in '{filename}' produced zero chunks.")

    return upsert_chunks(brand_id, chunks, source=filename)
```

- [ ] **Step 4: Run tests**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_ingest.py -v
```

Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/core/ingest.py backend/tests/test_ingest.py
git commit -m "feat: add core/ingest.py — PDF/text extraction, chunking, ingest pipeline"
```

---

## Task 4: Wire `POST /api/v1/ingest` to RAG pipeline

**Files:**
- Modify: `backend/api/v1_router.py:32-48`
- Test: `backend/tests/test_ingest_endpoint.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_ingest_endpoint.py`:

```python
"""Integration test for POST /api/v1/ingest with RAG pipeline."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


def test_ingest_endpoint_calls_rag_pipeline(monkeypatch):
    """POST /api/v1/ingest must call ingest_document and return chunk_count."""
    import os
    os.environ.setdefault("OPENAI_API_KEY", "test")

    from core import ingest as ingest_mod

    calls = []

    def fake_ingest(brand_id, file_bytes, filename):
        calls.append({"brand_id": brand_id, "filename": filename})
        return 7  # fake chunk count

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
    import os
    os.environ.setdefault("OPENAI_API_KEY", "test")

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_ingest_endpoint.py -v 2>&1 | head -20
```

Expected: FAIL — endpoint returns no `chunks_stored`, no `brand_id` param.

- [ ] **Step 3: Modify `api/v1_router.py`**

Replace the `ingest_document` function in `backend/api/v1_router.py` (lines 32–48):

```python
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
# (keep all existing imports above, add HTTPException)

@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    brand_id: str = Form(default="disrupt"),
    context: str = Form(default=""),
    vectorId: str = Form(default=""),
):
    import asyncio
    from core.ingest import ingest_document as _ingest  # noqa: PLC0415

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / file.filename
    contents = await file.read()
    dest.write_bytes(contents)

    try:
        chunks_stored = await asyncio.to_thread(
            _ingest, brand_id, contents, file.filename
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "status": "success",
        "message": "Documento procesado e indexado",
        "filename": file.filename,
        "brand_id": brand_id,
        "chunks_stored": chunks_stored,
    }
```

Also add `HTTPException` to the existing import line:
```python
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
```

- [ ] **Step 4: Run tests**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_ingest_endpoint.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/api/v1_router.py backend/tests/test_ingest_endpoint.py
git commit -m "feat: wire POST /api/v1/ingest to RAG pipeline — extract, chunk, embed, upsert"
```

---

## Task 5: Create `buscar_contexto_marca` retrieval tool

**Files:**
- Create: `backend/tools/retrieval_tool.py`
- Test: `backend/tests/test_retrieval_tool.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_retrieval_tool.py`:

```python
"""Tests for tools/retrieval_tool.py — buscar_contexto_marca @tool."""
import pytest
from unittest.mock import patch


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_retrieval_tool.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'tools.retrieval_tool'`

- [ ] **Step 3: Implement `tools/retrieval_tool.py`**

Create `backend/tools/retrieval_tool.py`:

```python
"""
Retrieval tool for NJM OS agents.

buscar_contexto_marca: semantic search over ChromaDB for a given brand.
Usable by both nodo_ceo and nodo_pm.
"""
from __future__ import annotations

from langchain_core.tools import tool

from core.rag import query_brand


@tool
def buscar_contexto_marca(
    brand_id: str,
    consulta: str,
    n_resultados: int = 5,
) -> str:
    """
    Busca fragmentos relevantes del material de onboarding de una marca
    en la base de datos vectorial (ChromaDB).

    Úsala antes de auditar o generar entregables para obtener contexto
    real de los documentos subidos por el Encargado Real.

    Args:
        brand_id: Identificador de la marca. Ej.: "disrupt".
        consulta: Pregunta o tema a buscar. Ej.: "¿Cuál es el CAC objetivo?".
        n_resultados: Número de fragmentos a recuperar (1–10). Default: 5.
    """
    n_resultados = max(1, min(n_resultados, 10))
    chunks = query_brand(brand_id, consulta, n_results=n_resultados)

    if not chunks:
        return (
            f"No se encontró contexto para la marca '{brand_id}'. "
            "El Encargado Real aún no ha subido documentos de onboarding. "
            "Procede con la entrevista de profundidad para obtener la información."
        )

    lines = [f"CONTEXTO RECUPERADO — Marca: {brand_id} | Consulta: '{consulta}'\n"]
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"--- Fragmento {i} ---")
        lines.append(chunk.strip())
        lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_retrieval_tool.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/tools/retrieval_tool.py backend/tests/test_retrieval_tool.py
git commit -m "feat: add buscar_contexto_marca @tool — semantic retrieval from ChromaDB"
```

---

## Task 6: Add retrieval tool to `nodo_ceo`

**Files:**
- Modify: `backend/agentes/agente_ceo.py:567-573`

- [ ] **Step 1: Add import and register tool**

In `backend/agentes/agente_ceo.py`, add import after the existing imports (around line 22):

```python
from tools.retrieval_tool import buscar_contexto_marca
```

Then add `buscar_contexto_marca` to `CEO_TOOLS` list (around line 567):

```python
CEO_TOOLS = [
    escanear_directorio_onboarding,
    generar_reporte_brechas,
    iniciar_entrevista_profundidad,
    escribir_libro_vivo,
    levantar_tarjeta_roja,
    buscar_contexto_marca,   # Phase 2.2 — RAG retrieval
]
```

Also add `buscar_contexto_marca` to `_TOOL_MAP`:

```python
_TOOL_MAP: Dict[str, Any] = {t.name: t for t in CEO_TOOLS}
```

(The `_TOOL_MAP` line already uses `CEO_TOOLS` so no change needed — it rebuilds automatically.)

- [ ] **Step 2: Verify smoke test still passes**

```bash
cd backend
.venv/bin/python3 -c "
import os; os.environ.setdefault('OPENAI_API_KEY','test')
from agent.njm_graph import njm_graph, ceo_graph
from agentes.agente_ceo import nodo_ceo, CEO_TOOLS
names = [t.name for t in CEO_TOOLS]
assert 'buscar_contexto_marca' in names, f'Missing tool. Got: {names}'
print('CEO tools OK:', names)
"
```

Expected: `CEO tools OK: [..., 'buscar_contexto_marca']`

- [ ] **Step 3: Commit**

```bash
git add backend/agentes/agente_ceo.py
git commit -m "feat: add buscar_contexto_marca to CEO_TOOLS for RAG retrieval"
```

---

## Task 7: Add retrieval tool to `nodo_pm`

**Files:**
- Modify: `backend/agentes/agente_pm.py`
- Modify: `backend/tools/pm_skills.py` (check if PM_SKILLS is defined there)

- [ ] **Step 1: Locate PM tool registration**

```bash
cd backend
grep -n "PM_SKILLS\|_SKILL_MAP\|bind_tools" agentes/agente_pm.py tools/pm_skills.py
```

Note the line numbers where tools are registered.

- [ ] **Step 2: Add import in `agente_pm.py`**

Add after the `from tools.pm_skills import PM_SKILLS, _SKILL_MAP` line:

```python
from tools.retrieval_tool import buscar_contexto_marca as _buscar_contexto
```

- [ ] **Step 3: Register in PM tool set**

Find where `PM_SKILLS` is used in `nodo_pm` and extend the list. Locate the `model_with_tools = _LLM.bind_tools(...)` call and change it to:

```python
_ALL_PM_TOOLS = PM_SKILLS + [_buscar_contexto]
model_with_tools = _LLM.bind_tools(_ALL_PM_TOOLS)
```

Also extend the skill map used for tool execution. Find `_SKILL_MAP.get(nombre_tool)` pattern and replace the map lookup to include retrieval:

```python
_PM_TOOL_MAP = {**_SKILL_MAP, _buscar_contexto.name: _buscar_contexto}
# then use _PM_TOOL_MAP.get(nombre_tool) instead of _SKILL_MAP.get(nombre_tool)
```

- [ ] **Step 4: Verify smoke test**

```bash
cd backend
.venv/bin/python3 -c "
import os; os.environ.setdefault('OPENAI_API_KEY','test')
from agentes.agente_pm import nodo_pm
print('PM node loaded OK with retrieval tool')
"
```

Expected: `PM node loaded OK with retrieval tool`

- [ ] **Step 5: Commit**

```bash
git add backend/agentes/agente_pm.py
git commit -m "feat: add buscar_contexto_marca to PM agent tool set for RAG retrieval"
```

---

## Task 8: End-to-end smoke test

**Files:**
- No new files — manual verification

- [ ] **Step 1: Start backend**

```bash
cd backend && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- [ ] **Step 2: Upload a test document**

In a second terminal:

```bash
echo "CAC objetivo: 120 USD. LTV proyectado: 2400 USD. Mercados: México, Colombia." > /tmp/brief_disrupt.txt

curl -s -X POST http://localhost:8000/api/v1/ingest \
  -F "file=@/tmp/brief_disrupt.txt" \
  -F "brand_id=disrupt" \
  -F "context=test" \
  -F "vectorId=v1" | python3 -m json.tool
```

Expected response:
```json
{
  "status": "success",
  "message": "Documento procesado e indexado",
  "filename": "brief_disrupt.txt",
  "brand_id": "disrupt",
  "chunks_stored": 1
}
```

- [ ] **Step 3: Verify retrieval via Python**

```bash
cd backend
.venv/bin/python3 -c "
from core.rag import query_brand
results = query_brand('disrupt', '¿Cuál es el CAC objetivo?', n_results=3)
print('Results:', results)
assert any('CAC' in r or '120' in r for r in results), 'CAC not found in results'
print('RAG retrieval OK')
"
```

Expected: results containing `CAC` text; final line `RAG retrieval OK`.

- [ ] **Step 4: Run full test suite**

```bash
cd backend
.venv/bin/python3 -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: All tests PASSED (no regressions from Phase 2.1).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "test: Phase 2.2 end-to-end verification — ingest + retrieval confirmed"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Task |
|---|---|
| PDF/text extraction library | Task 3 — PyMuPDF in `core/ingest.py` |
| ChromaDB local setup | Task 2 — `core/rag.py` with `PersistentClient` |
| Ingest endpoint: chunk + embed + store | Task 4 — `v1_router.py` modified |
| `brand_id` association in ChromaDB | Task 2, 4 — collection name = `brand_id` |
| Retrieval tool for CEO | Task 5, 6 — `buscar_contexto_marca` in `CEO_TOOLS` |
| Retrieval tool for PM | Task 5, 7 — `buscar_contexto_marca` in PM tools |
| Tests | Tasks 2, 3, 4, 5 — full coverage |

**No placeholders detected.** All code is complete and runnable.

**Type consistency:** `upsert_chunks(brand_id: str, chunks: List[str], source: str)` in `rag.py` matches calls in `ingest.py`. `buscar_contexto_marca.invoke({"brand_id", "consulta", "n_resultados"})` matches tool signature. `_ALL_PM_TOOLS` properly extends `PM_SKILLS` list.

**Edge case noted:** `query_brand` guards `col.count() == 0` before calling `.query()` to avoid ChromaDB error on empty collections. The `buscar_contexto_marca` tool surfaces this as a user-readable message.
