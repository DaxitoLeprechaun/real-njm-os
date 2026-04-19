# Fix asyncio.run() Module-Level Crash in njm_graph.py

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `asyncio.run(_build_njm_graph())` from module level so Uvicorn can start without crashing, by wiring graph initialization into FastAPI's async lifespan event.

**Architecture:** Expose an `init_graph()` coroutine in `njm_graph.py` that sets the module-level `njm_graph` variable. FastAPI's `lifespan` context manager calls `await init_graph()` on startup inside Uvicorn's event loop — no second event loop needed. All existing callers (`v1_router.py` lazy imports, `api/main.py`) access `njm_graph` from the module after it has been set. A session-scoped pytest fixture in `conftest.py` calls the same initializer so tests don't break.

**Tech Stack:** FastAPI lifespan (`contextlib.asynccontextmanager`), LangGraph `AsyncSqliteSaver`, aiosqlite, pytest.

---

### Task 1: Refactor `njm_graph.py` — remove `asyncio.run`, expose `init_graph()`

**Files:**
- Modify: `backend/agent/njm_graph.py:201-206`

Root cause: `asyncio.run()` creates a new event loop. When Uvicorn already has a running loop, calling `asyncio.run()` at import time raises `RuntimeError: asyncio.run() cannot be called from a running event loop`. Additionally, the `aiosqlite` connection created in the temporary loop dies when that loop closes — so even if `asyncio.run()` didn't crash, the checkpointer would be broken.

Fix: set `njm_graph = None` initially, expose `init_graph()` to be called once inside Uvicorn's loop via lifespan.

- [ ] **Step 1: Replace the module-level `asyncio.run()` call with a `None` sentinel and async initializer**

Replace lines 201–206 in `backend/agent/njm_graph.py`:

```python
# OLD (lines 201-206):
    conn = await aiosqlite.connect("njm_sessions.db")
    checkpointer = AsyncSqliteSaver(conn)
    return builder.compile(checkpointer=checkpointer)


njm_graph = asyncio.run(_build_njm_graph())
```

with:

```python
    conn = await aiosqlite.connect("njm_sessions.db")
    checkpointer = AsyncSqliteSaver(conn)
    return builder.compile(checkpointer=checkpointer)


njm_graph = None  # initialized by init_graph() inside Uvicorn's event loop


async def init_graph() -> None:
    """Call once from FastAPI lifespan (or test fixtures) to build njm_graph."""
    global njm_graph
    if njm_graph is not None:
        return
    njm_graph = await _build_njm_graph()
```

- [ ] **Step 2: Remove the now-unused top-level `asyncio` import if it's only used for `asyncio.run()`**

Check line 23 (`import asyncio`) — `asyncio` is also used in `v1_router.py` (separate file) and `aiosqlite` (separate package), so leave the import. No change needed here.

- [ ] **Step 3: Smoke-test the module import doesn't crash**

```bash
cd backend
.venv/bin/python3 -c "
import os; os.environ.setdefault('OPENAI_API_KEY','test')
from agent.njm_graph import njm_graph, init_graph
print('njm_graph before init:', njm_graph)
import asyncio
asyncio.run(init_graph())
from agent.njm_graph import njm_graph as g2
print('njm_graph after init:', type(g2).__name__)
"
```

Expected output:
```
njm_graph before init: None
njm_graph after init: CompiledStateGraph
```

- [ ] **Step 4: Commit**

```bash
cd backend
git add agent/njm_graph.py
git commit -m "fix: remove asyncio.run() at module level — expose init_graph() coroutine"
```

---

### Task 2: Wire `init_graph()` into FastAPI lifespan in `main.py`

**Files:**
- Modify: `backend/main.py`

FastAPI's `lifespan` context manager runs startup code inside Uvicorn's own event loop before the first request is served.

- [ ] **Step 1: Add lifespan to `main.py`**

Replace the full contents of `backend/main.py` with:

```python
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.main import router as pm_router
from api.v1_router import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from agent.njm_graph import init_graph
    await init_graph()
    yield


app = FastAPI(
    title="NJM OS API",
    description="Backend de orquestación multi-agente: Agente CEO y Agente PM",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pm_router)
app.include_router(v1_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "njm-os-backend"}
```

- [ ] **Step 2: Verify Uvicorn starts without crashing**

```bash
cd backend
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
sleep 3
curl -s http://localhost:8000/health
kill %1
```

Expected output:
```json
{"status":"ok","service":"njm-os-backend"}
```

No `RuntimeError: asyncio.run()` in the log.

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: initialize njm_graph via FastAPI lifespan — fixes asyncio.run() crash"
```

---

### Task 3: Fix top-level `njm_graph` import in `api/main.py`

**Files:**
- Modify: `backend/api/main.py:36`

`api/main.py` does `from agent.njm_graph import njm_graph` at the top of the file. This runs at import time, before lifespan fires, so it captures `None`. The `ejecutar_tarea` endpoint then calls `await None.ainvoke(...)` and crashes.

Fix: move the import inside the function body (same pattern as `v1_router.py`).

- [ ] **Step 1: Remove the top-level import and add lazy import inside `ejecutar_tarea`**

In `backend/api/main.py`, remove line 36:
```python
from agent.njm_graph import njm_graph
```

Then inside `ejecutar_tarea`, just before the `await njm_graph.ainvoke(...)` call (currently line ~191), add the local import:

```python
    # ── Ejecutar grafo con checkpointer ──────────────────────────
    from agent.njm_graph import njm_graph  # noqa: PLC0415
    try:
        estado_final: Dict[str, Any] = await njm_graph.ainvoke(estado_inicial, config)
```

Full diff context — change this block in `api/main.py`:

```python
# BEFORE (top of file, line 36):
from agent.njm_graph import njm_graph
from core.schemas import EstadoValidacion
```

```python
# AFTER (top of file, line 36):
from core.schemas import EstadoValidacion
```

And change the execution block (around line 189-192):

```python
# BEFORE:
    # ── Ejecutar grafo con checkpointer ──────────────────────────
    try:
        estado_final: Dict[str, Any] = await njm_graph.ainvoke(estado_inicial, config)
```

```python
# AFTER:
    # ── Ejecutar grafo con checkpointer ──────────────────────────
    from agent.njm_graph import njm_graph  # noqa: PLC0415
    try:
        estado_final: Dict[str, Any] = await njm_graph.ainvoke(estado_inicial, config)
```

- [ ] **Step 2: Verify import works without triggering graph build**

```bash
cd backend
.venv/bin/python3 -c "
import os; os.environ.setdefault('OPENAI_API_KEY','test')
from api.main import router
print('api/main.py imported cleanly — no graph build triggered')
"
```

Expected: prints the message without hanging or crashing.

- [ ] **Step 3: Commit**

```bash
git add api/main.py
git commit -m "fix: move njm_graph import inside ejecutar_tarea — avoid None capture at import time"
```

---

### Task 4: Add `conftest.py` to initialize graph for all tests

**Files:**
- Create: `backend/tests/conftest.py`

Without `asyncio.run()` at module level, `njm_graph` is `None` when tests import it. Tests in `test_v1_sse.py` do `monkeypatch.setattr(graph_mod.njm_graph, "astream_events", ...)` which requires a real object. A session-scoped autouse fixture initializes the graph once before any test runs.

- [ ] **Step 1: Create `backend/tests/conftest.py`**

```python
"""Session-wide fixtures for NJM OS backend tests."""
import asyncio
import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test")


@pytest.fixture(autouse=True, scope="session")
def _init_njm_graph():
    """Initialize njm_graph once per test session so monkeypatching works."""
    from agent.njm_graph import init_graph
    asyncio.run(init_graph())
```

- [ ] **Step 2: Verify the fixture runs and graph initializes**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_async_checkpointer.py -v
```

Expected:
```
PASSED tests/test_async_checkpointer.py::test_njm_graph_has_async_checkpointer
```

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add session conftest to initialize njm_graph before test suite runs"
```

---

### Task 5: Run the full test suite and fix any remaining failures

**Files:**
- Modify: `backend/tests/test_v1_sse.py` (if needed)
- Modify: `backend/tests/test_async_checkpointer.py` (if needed)

- [ ] **Step 1: Run all tests**

```bash
cd backend
.venv/bin/python3 -m pytest tests/ -v 2>&1 | head -80
```

Expected: all tests that were passing before still pass. The `test_async_checkpointer.py` test should now pass (graph is a real `CompiledStateGraph` with `AsyncSqliteSaver` checkpointer).

- [ ] **Step 2: If `test_v1_sse.py` fails because `graph_mod.njm_graph` is `None`**

This should NOT happen because `conftest.py` autouse fixture runs before any test. But if it does, check that `conftest.py` is in the right directory and that pytest discovers it:

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_v1_sse.py -v --setup-show 2>&1 | head -40
```

Look for `SETUP    S _init_njm_graph` — if missing, the conftest isn't being picked up. Verify file is at `backend/tests/conftest.py`.

- [ ] **Step 3: If `test_async_checkpointer.py` fails with `AssertionError` because checkpointer type doesn't match**

The test imports `njm_graph` at call time:
```python
from agent.njm_graph import njm_graph
```
This import runs after conftest initializes the graph, so `njm_graph` should be a real `CompiledStateGraph`. If it's still `None`, add an explicit check:

```python
def test_njm_graph_has_async_checkpointer():
    import asyncio
    from agent.njm_graph import init_graph, njm_graph as _g
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    # conftest should have initialized it; guard in case test runs in isolation
    if _g is None:
        asyncio.run(init_graph())
    from agent.njm_graph import njm_graph
    assert isinstance(njm_graph.checkpointer, AsyncSqliteSaver)
```

- [ ] **Step 4: Commit if any test files were changed**

```bash
git add tests/
git commit -m "test: fix graph initialization assumptions after lifespan refactor"
```

---

### Task 6: End-to-end Uvicorn start verification

**Files:** None (verification only)

- [ ] **Step 1: Start Uvicorn cleanly**

```bash
cd backend
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

Expected log lines (no errors):
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

No `RuntimeError`, no `asyncio` errors.

- [ ] **Step 2: Health check**

```bash
curl -s http://localhost:8000/health
```

Expected:
```json
{"status":"ok","service":"njm-os-backend"}
```

- [ ] **Step 3: Smoke-test graph nodes compile**

```bash
cd backend
.venv/bin/python3 -c "
import os; os.environ.setdefault('OPENAI_API_KEY','test')
import asyncio
from agent.njm_graph import init_graph, njm_graph
asyncio.run(init_graph())
from agent.njm_graph import njm_graph as g
print([n for n in g.get_graph().nodes])
print('checkpointer:', type(g.checkpointer).__name__)
"
```

Expected:
```
['__start__', 'ingest', 'ceo_auditor', 'human_in_loop', 'pm_execution', 'ceo_review', 'output']
checkpointer: AsyncSqliteSaver
```
