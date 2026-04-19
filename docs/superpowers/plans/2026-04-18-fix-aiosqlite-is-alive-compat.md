# Fix aiosqlite/langgraph `is_alive` Compatibility Shim

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `AttributeError: 'Connection' object has no attribute 'is_alive'` that crashes the server during SSE streaming.

**Architecture:** `langgraph-checkpoint-sqlite 2.0.11` calls `conn.is_alive()` inside `AsyncSqliteSaver.setup()`. `aiosqlite 0.22.1` refactored `Connection` away from inheriting `Thread` — it now wraps a `Thread` in `._thread` but does not expose `is_alive()` directly. The fix adds a one-line compatibility shim at module level in `njm_graph.py`: `aiosqlite.Connection.is_alive = lambda self: self._thread.is_alive()`. This is idempotent, guarded by `hasattr`, and runs once at import time before any checkpointer is constructed.

`from_conn_string()` hits the same bug — it passes the same `aiosqlite.Connection` type to the same `AsyncSqliteSaver` constructor, so the shim is the correct fix regardless of which constructor form is used.

**Tech Stack:** aiosqlite 0.22.1, langgraph-checkpoint-sqlite 2.0.11, Python 3.9.

---

### Task 1: Add `aiosqlite.Connection.is_alive` compatibility shim to `njm_graph.py`

**Files:**
- Modify: `backend/agent/njm_graph.py` (after imports, before first function definition)

The shim must be added after `import aiosqlite` (already present) and before `_build_njm_graph()`. It patches the class once at import time.

- [ ] **Step 1: Locate the correct insertion point**

In `backend/agent/njm_graph.py`, find the block after all imports (around line 40) and before the first function definition (`ingest_node`). It looks like this:

```python
from agentes.agente_ceo import nodo_ceo
from agentes.agente_pm import nodo_pm
from core.estado import NJM_OS_State
from core.schemas import EstadoValidacion

# ══════════════════════════════════════════════════════════════════
# NODOS STUB (Phase 2.1)
```

- [ ] **Step 2: Add the compatibility shim between the imports and the first comment block**

Insert after the last import line and before the `# ══ NODOS STUB` banner:

```python
# Compatibility shim: aiosqlite 0.22+ removed is_alive() from Connection,
# but langgraph-checkpoint-sqlite 2.0.x calls conn.is_alive() in setup().
# _thread is a threading.Thread — is_alive() exists there.
if not hasattr(aiosqlite.Connection, "is_alive"):
    aiosqlite.Connection.is_alive = lambda self: self._thread.is_alive()
```

Full context (what the file should look like after the change):

```python
from agentes.agente_ceo import nodo_ceo
from agentes.agente_pm import nodo_pm
from core.estado import NJM_OS_State
from core.schemas import EstadoValidacion

# Compatibility shim: aiosqlite 0.22+ removed is_alive() from Connection,
# but langgraph-checkpoint-sqlite 2.0.x calls conn.is_alive() in setup().
# _thread is a threading.Thread — is_alive() exists there.
if not hasattr(aiosqlite.Connection, "is_alive"):
    aiosqlite.Connection.is_alive = lambda self: self._thread.is_alive()


# ══════════════════════════════════════════════════════════════════
# NODOS STUB (Phase 2.1)
# ══════════════════════════════════════════════════════════════════
```

- [ ] **Step 3: Verify shim is applied at import time**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend
.venv/bin/python3 -c "
import os; os.environ.setdefault('OPENAI_API_KEY','test')
import aiosqlite
from agent import njm_graph  # triggers shim
print('is_alive on Connection:', hasattr(aiosqlite.Connection, 'is_alive'))
import inspect
print('is_alive source:', inspect.getsource(aiosqlite.Connection.is_alive))
"
```

Expected:
```
is_alive on Connection: True
is_alive source: aiosqlite.Connection.is_alive = lambda self: self._thread.is_alive()
```

- [ ] **Step 4: Verify init_graph() runs to completion without is_alive error**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend
.venv/bin/python3 -c "
import os; os.environ.setdefault('OPENAI_API_KEY','test')
import asyncio
from agent.njm_graph import init_graph

async def test():
    await init_graph()
    from agent.njm_graph import njm_graph as g
    # Trigger setup() by calling aget_state — this is where is_alive was called
    config = {'configurable': {'thread_id': 'test:smoke'}}
    snapshot = await g.aget_state(config)
    print('aget_state OK — snapshot:', snapshot)
    print('PASS: no is_alive AttributeError')

asyncio.run(test())
" 2>&1 | grep -v "NotOpenSSL\|warnings.warn\|urllib3"
```

Expected output (no AttributeError):
```
aget_state OK — snapshot: ...
PASS: no is_alive AttributeError
```

- [ ] **Step 5: Run the full test suite to confirm no regressions**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend
.venv/bin/python3 -m pytest tests/test_v1_sse.py tests/test_async_checkpointer.py -v 2>&1 | tail -15
```

Expected:
```
tests/test_v1_sse.py::test_agent_stream_accepts_brand_id_and_session_id PASSED
tests/test_v1_sse.py::test_agent_stream_emits_done_event PASSED
tests/test_v1_sse.py::test_agent_stream_emits_action_required_on_bloqueo_ceo PASSED
tests/test_v1_sse.py::test_agent_stream_emits_action_required_on_gap_detected PASSED
tests/test_v1_sse.py::test_session_state_endpoint_returns_snapshot PASSED
tests/test_v1_sse.py::test_agent_resume_endpoint_invokes_graph PASSED
tests/test_async_checkpointer.py::test_njm_graph_has_async_checkpointer PASSED
7 passed in ...
```

- [ ] **Step 6: Commit**

```bash
cd /Users/juanduran/Downloads/real-njm-os
git add backend/agent/njm_graph.py
git commit -m "fix: add aiosqlite.Connection.is_alive shim for langgraph-checkpoint-sqlite 2.0.x compat"
```

---

### Task 2: End-to-end SSE stream verification

**Files:** None (verification only)

The crash happened specifically during `astream_events`, which triggers `AsyncSqliteSaver.setup()` → `conn.is_alive()`. This task verifies the full streaming path works after the shim is applied.

- [ ] **Step 1: Start Uvicorn**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 &
sleep 3
```

Expected log (no errors):
```
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

- [ ] **Step 2: Hit the health endpoint**

```bash
curl -s http://localhost:8000/health
```

Expected:
```json
{"status":"ok","service":"njm-os-backend"}
```

- [ ] **Step 3: Stream the SSE ceo-audit endpoint and confirm no is_alive error**

```bash
curl -s --max-time 30 \
  "http://localhost:8000/api/v1/agent/stream?sequenceId=ceo-audit&brand_id=disrupt&session_id=smoke-test-1" \
  | head -20
```

Expected: JSON SSE events appear (no `AttributeError: 'Connection' object has no attribute 'is_alive'`). The stream should start with:
```
data: {"type": "log", "text": "[⏳] Conectando con NJM OS (brand: disrupt)..."}
data: {"type": "log", "text": "[⏳] ..."}
```

- [ ] **Step 4: Kill Uvicorn**

```bash
kill %1
```
