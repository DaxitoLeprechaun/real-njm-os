# AsyncSqliteSaver Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `SqliteSaver` with `AsyncSqliteSaver` so `njm_graph.astream_events`, `ainvoke`, and `aget_state` all work inside FastAPI's async event loop.

**Architecture:** `AsyncSqliteSaver` (from `langgraph.checkpoint.sqlite.aio`) wraps an `aiosqlite.Connection`, which uses a background thread — not the event loop — for sqlite operations, making it safe to initialize at module load time via `asyncio.run()` before uvicorn starts its own loop. All callers of `.invoke` and `.get_state` (sync) are migrated to `.ainvoke` and `.aget_state` (async). Tests are updated to monkeypatch the async variants.

**Tech Stack:** `aiosqlite`, `langgraph-checkpoint-sqlite==2.0.11`, FastAPI, pytest + monkeypatch

---

## File Map

| Action | File |
|--------|------|
| Modify | `backend/requirements.txt` |
| Modify | `backend/agent/njm_graph.py` |
| Modify | `backend/api/v1_router.py` |
| Modify | `backend/api/main.py` |
| Modify | `backend/tests/test_v1_sse.py` |

---

### Task 1: Add `aiosqlite` to requirements and install it

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add `aiosqlite` to requirements.txt**

In `backend/requirements.txt`, after the `# Async / utilities` section add:

```
aiosqlite>=0.19.0
```

Final `# Async / utilities` block should read:
```
# Async / utilities
python-dotenv==1.0.1
httpx==0.28.1
python-multipart==0.0.9
aiosqlite>=0.19.0
```

- [ ] **Step 2: Install the dependency**

```bash
cd backend && .venv/bin/pip install "aiosqlite>=0.19.0"
```

Expected output: `Successfully installed aiosqlite-X.Y.Z` (or already satisfied)

- [ ] **Step 3: Verify import works**

```bash
cd backend && .venv/bin/python3 -c "import aiosqlite; from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd backend
git add requirements.txt
git commit -m "feat: add aiosqlite for AsyncSqliteSaver support"
```

---

### Task 2: Migrate `njm_graph.py` to `AsyncSqliteSaver`

**Files:**
- Modify: `backend/agent/njm_graph.py`

**Why this works:** `aiosqlite` uses a background thread per connection — not the event loop — for sqlite I/O. Calling `asyncio.run(_build_njm_graph())` at module load time (before uvicorn starts its loop) is safe. When uvicorn's loop later calls `await checkpointer.aput(...)`, aiosqlite schedules work to that same background thread via whatever loop is currently running.

- [ ] **Step 1: Write a failing smoke test**

```python
# backend/tests/test_async_checkpointer.py
import os
os.environ.setdefault("OPENAI_API_KEY", "test")

def test_njm_graph_has_async_checkpointer():
    """njm_graph checkpointer must support async methods."""
    from agent.njm_graph import njm_graph
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    assert isinstance(njm_graph.checkpointer, AsyncSqliteSaver)
```

Run it to confirm it fails:
```bash
cd backend && .venv/bin/python3 -m pytest tests/test_async_checkpointer.py -v
```

Expected: `FAILED — AssertionError` (njm_graph still uses SqliteSaver)

- [ ] **Step 2: Update imports in `njm_graph.py`**

Remove these lines:
```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
```

Add these lines (in their place):
```python
import asyncio
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
```

Note: `asyncio` may already be imported elsewhere; add it only if not present.

- [ ] **Step 3: Replace `_build_njm_graph` with async version**

Replace the entire `_build_njm_graph` function (lines 165–203 in the original):

```python
async def _build_njm_graph() -> Any:
    builder = StateGraph(NJM_OS_State)

    builder.add_node("ingest", ingest_node)
    builder.add_node("ceo_auditor", ceo_auditor_node)
    builder.add_node("human_in_loop", human_in_loop_stub_node)
    builder.add_node("pm_execution", pm_execution_node)
    builder.add_node("ceo_review", ceo_review_stub_node)
    builder.add_node("output", output_node)

    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "ceo_auditor")

    builder.add_conditional_edges(
        "ceo_auditor",
        _route_after_ceo,
        {"pm_execution": "pm_execution", "human_in_loop": "human_in_loop", "output": "output"},
    )

    builder.add_edge("human_in_loop", "ceo_auditor")

    builder.add_conditional_edges(
        "pm_execution",
        _route_after_pm,
        {"output": "output", "ceo_review": "ceo_review"},
    )

    builder.add_conditional_edges(
        "ceo_review",
        _route_after_ceo_review,
        {"pm_execution": "pm_execution", "output": "output", "human_in_loop": "human_in_loop"},
    )

    builder.add_edge("output", END)

    conn = await aiosqlite.connect("njm_sessions.db")
    checkpointer = AsyncSqliteSaver(conn)
    return builder.compile(checkpointer=checkpointer)


njm_graph = asyncio.run(_build_njm_graph())
```

- [ ] **Step 4: Run the smoke test**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_async_checkpointer.py -v
```

Expected: `PASSED`

- [ ] **Step 5: Run the existing graph import smoke**

```bash
cd backend && .venv/bin/python3 -c "
import os; os.environ.setdefault('OPENAI_API_KEY','test')
from agent.njm_graph import njm_graph, ceo_graph
print([n for n in njm_graph.get_graph().nodes])
print('checkpointer:', type(njm_graph.checkpointer).__name__)
"
```

Expected output includes: `AsyncSqliteSaver`

- [ ] **Step 6: Commit**

```bash
cd backend
git add agent/njm_graph.py tests/test_async_checkpointer.py
git commit -m "feat: migrate njm_graph checkpointer to AsyncSqliteSaver"
```

---

### Task 3: Update `v1_router.py` to use async state reads

**Files:**
- Modify: `backend/api/v1_router.py`

`get_state` (sync) on an `AsyncSqliteSaver`-backed graph raises `NotImplementedError`. All three call sites must switch to `await graph.aget_state(config)`.

- [ ] **Step 1: Update `_sse_njm_stream` — replace sync `get_state` with `aget_state`**

In `_sse_njm_stream`, find this block (after the `except asyncio.CancelledError` block):
```python
    # Post-stream: check final state for interrupts / terminal states
    try:
        snapshot = njm_graph.get_state(config)
```

Replace with:
```python
    # Post-stream: check final state for interrupts / terminal states
    try:
        snapshot = await njm_graph.aget_state(config)
```

- [ ] **Step 2: Update `get_session_state` endpoint — replace sync `get_state` with `aget_state`**

Find:
```python
    try:
        snapshot = njm_graph.get_state(config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Checkpointer error: {exc}") from exc
```

Replace with:
```python
    try:
        snapshot = await njm_graph.aget_state(config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Checkpointer error: {exc}") from exc
```

- [ ] **Step 3: Verify file syntax**

```bash
cd backend && .venv/bin/python3 -c "import ast; ast.parse(open('api/v1_router.py').read()); print('syntax OK')"
```

Expected: `syntax OK`

- [ ] **Step 4: Commit**

```bash
cd backend
git add api/v1_router.py
git commit -m "fix: use aget_state in v1_router (AsyncSqliteSaver compat)"
```

---

### Task 4: Update `api/main.py` — replace sync `invoke` with `ainvoke`

**Files:**
- Modify: `backend/api/main.py`

`njm_graph.invoke` is sync and will fail with `AsyncSqliteSaver`. The FastAPI handler is already `async def`, so we can call `await njm_graph.ainvoke(...)` directly — no `asyncio.to_thread` needed.

- [ ] **Step 1: Replace the `asyncio.to_thread` call with `ainvoke`**

Find:
```python
    try:
        estado_final: Dict[str, Any] = await asyncio.to_thread(
            njm_graph.invoke, estado_inicial, config
        )
    except Exception as exc:
```

Replace with:
```python
    try:
        estado_final: Dict[str, Any] = await njm_graph.ainvoke(estado_inicial, config)
    except Exception as exc:
```

- [ ] **Step 2: Remove unused `asyncio` import if it's no longer needed**

Check if `asyncio` is used anywhere else in `api/main.py`. If not (only use was `asyncio.to_thread`), remove `import asyncio`. If it's still used elsewhere, keep it.

```bash
cd backend && grep -n "asyncio" api/main.py
```

Remove the import line if the only match is the import itself.

- [ ] **Step 3: Verify file syntax**

```bash
cd backend && .venv/bin/python3 -c "import ast; ast.parse(open('api/main.py').read()); print('syntax OK')"
```

Expected: `syntax OK`

- [ ] **Step 4: Commit**

```bash
cd backend
git add api/main.py
git commit -m "fix: replace asyncio.to_thread(invoke) with ainvoke (AsyncSqliteSaver compat)"
```

---

### Task 5: Update SSE tests to monkeypatch `aget_state` instead of `get_state`

**Files:**
- Modify: `backend/tests/test_v1_sse.py`

The router now calls `await njm_graph.aget_state(config)` instead of `njm_graph.get_state(config)`. Tests that monkeypatch `get_state` must be updated to patch `aget_state` as an async function.

Affected tests:
- `test_agent_stream_accepts_brand_id_and_session_id`
- `test_agent_stream_emits_done_event`
- `test_agent_stream_emits_action_required_on_bloqueo_ceo`
- `test_agent_stream_emits_action_required_on_gap_detected`
- `test_session_state_endpoint_returns_snapshot`

`test_agent_resume_endpoint_invokes_graph` is not affected (patches `ainvoke`, no `get_state`).

- [ ] **Step 1: Write the updated test file**

Replace all occurrences of:
```python
    def fake_get_state(config):
        class _Snap:
            ...
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)
```

With the async variant:
```python
    async def fake_aget_state(config):
        class _Snap:
            ...
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "aget_state", fake_aget_state)
```

Apply this change to all 5 affected tests. The `_Snap` inner class and its attributes remain identical — only the outer function becomes `async def` and the patched attribute name changes from `"get_state"` to `"aget_state"`.

Example — full updated `test_agent_stream_accepts_brand_id_and_session_id`:
```python
def test_agent_stream_accepts_brand_id_and_session_id(monkeypatch):
    """GET /api/v1/agent/stream must accept brand_id and session_id params."""
    from agent import njm_graph as graph_mod

    async def fake_astream_events(state, config, version="v2", **_kwargs):
        yield {"event": "on_chain_end", "name": "output", "data": {}}

    monkeypatch.setattr(graph_mod.njm_graph, "astream_events", fake_astream_events)

    async def fake_aget_state(config):
        class _Snap:
            values = {"estado_validacion": "LISTO_PARA_FIRMA", "audit_status": "COMPLETE"}
            next = []
            tasks = []
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "aget_state", fake_aget_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/agent/stream",
        params={"sequenceId": "ceo-audit", "brand_id": "acme", "session_id": "ses-001"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
```

Apply the same pattern to the remaining 4 tests. For `test_session_state_endpoint_returns_snapshot`, the patched method changes from `get_state` to `aget_state`.

- [ ] **Step 2: Run all SSE tests**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_v1_sse.py -v
```

Expected: all 6 tests PASSED

- [ ] **Step 3: Run the async checkpointer test too**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_async_checkpointer.py tests/test_v1_sse.py -v
```

Expected: all 7 tests PASSED

- [ ] **Step 4: Commit**

```bash
cd backend
git add tests/test_v1_sse.py
git commit -m "test: update SSE tests to monkeypatch aget_state (async checkpointer)"
```

---

### Task 6: Smoke-test the running server

**Files:** none (verification only)

- [ ] **Step 1: Start the backend**

```bash
cd backend && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Wait for: `Application startup complete.`

- [ ] **Step 2: Verify health endpoint**

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

Expected: `{ "status": "ok" }`

- [ ] **Step 3: Smoke-test the SSE stream**

```bash
curl -N "http://localhost:8000/api/v1/agent/stream?sequenceId=ceo-audit&brand_id=disrupt&session_id=dev-session-1"
```

Expected: stream of SSE lines like:
```
data: {"type": "log", "text": "[⏳] Conectando con NJM OS (brand: disrupt)..."}
data: {"type": "log", "text": "[⏳] Agente PM ejecutando skill seleccionada..."}
...
data: {"type": "done"}
```

No `NotImplementedError`. No 500 errors.

- [ ] **Step 4: Verify session state endpoint**

```bash
curl -s "http://localhost:8000/api/v1/session/state?brand_id=disrupt&session_id=dev-session-1" | python3 -m json.tool
```

Expected: JSON with `audit_status`, `documentos_count`, etc. No 500.

- [ ] **Step 5: Run full test suite one final time**

```bash
cd backend && .venv/bin/python3 -m pytest tests/ -v
```

Expected: all tests PASSED (or pre-existing failures only — none introduced by this migration).

---

## Self-Review

**Spec coverage:**
- ✅ `aiosqlite` installed
- ✅ `AsyncSqliteSaver` replaces `SqliteSaver` in `njm_graph.py`
- ✅ `v1_router.py` uses `aget_state` in both call sites
- ✅ `api/main.py` uses `ainvoke` instead of `asyncio.to_thread(invoke)`
- ✅ Tests updated to monkeypatch async variants

**Type consistency:**
- `aget_state` used consistently in `v1_router.py` and test mocks
- `ainvoke` used in `api/main.py` and already used in `agent_resume` endpoint
- `astream_events` unchanged — already async in the original
