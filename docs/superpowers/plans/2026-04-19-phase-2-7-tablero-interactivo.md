# Phase 2.7 — Tablero Interactivo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Kanban board interactive — users can click task cards to cycle their estado (BACKLOG → EN_PROGRESO → DONE → BACKLOG), changes persist to the LangGraph checkpointer, and state survives a page refresh.

**Architecture:** Add `task_estado_overrides: Dict[str, str]` (last-write-wins field, no reducer) to `NJM_OS_State`; a new `PATCH /api/v1/tasks/{task_id}` endpoint fetches the current overrides dict, merges the single change, and calls `njm_graph.aupdate_state()` to persist. The existing `GET /session/state` endpoint is extended to return merged task list (tareas + overrides), enabling hydration on refresh. Frontend maintains `localTasks` state in `pm/page.tsx` with optimistic updates on click.

**Tech Stack:** FastAPI + LangGraph `aupdate_state()`, Pydantic v2, Next.js 14 App Router, TypeScript strict

---

## File Map

| File | Action | Change |
|---|---|---|
| `backend/core/estado.py` | Modify | Add `task_estado_overrides: Dict[str, str]` field |
| `backend/api/v1_router.py` | Modify | Add `PATCH /api/v1/tasks/{task_id}` + extend `GET /session/state` |
| `backend/tests/test_tablero_interactivo.py` | Create | Tests for new endpoint + session/state merge |
| `frontend/app/brand/[id]/pm/page.tsx` | Modify | `localTasks` state, click handler, PATCH integration, mount hydration |

---

## Task 1: Add `task_estado_overrides` to NJM_OS_State

**Files:**
- Modify: `backend/core/estado.py:101-104` (after `tareas_generadas` field)
- Test: `backend/tests/test_tablero_interactivo.py` (create)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_tablero_interactivo.py`:

```python
import typing
from core.estado import NJM_OS_State


def test_njm_os_state_has_task_estado_overrides():
    hints = typing.get_type_hints(NJM_OS_State, include_extras=True)
    assert "task_estado_overrides" in hints
    # Must be a plain Dict (no reducer) — not Annotated
    raw = hints["task_estado_overrides"]
    import typing as t
    origin = getattr(raw, "__origin__", None)
    assert origin is dict or str(raw).startswith("typing.Dict"), (
        f"task_estado_overrides must be Dict[str, str], got {raw}"
    )
```

- [ ] **Step 2: Run the failing test**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_tablero_interactivo.py::test_njm_os_state_has_task_estado_overrides -v
```

Expected: `FAILED` — `AssertionError: assert 'task_estado_overrides' in hints`

- [ ] **Step 3: Add the field to NJM_OS_State**

In `backend/core/estado.py`, add after line 103 (`tareas_generadas` block):

```python
    task_estado_overrides: Dict[str, str]
    # Maps task_id → EstadoTarea value. Updated by PATCH /api/v1/tasks/{id}.
    # No reducer: PATCH endpoint fetches + merges before writing.
```

The `Dict` import is already present on line 21.

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_tablero_interactivo.py::test_njm_os_state_has_task_estado_overrides -v
```

Expected: `PASSED`

- [ ] **Step 5: Verify existing tests still pass**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py -v
```

Expected: all PASSED (new field is optional in TypedDict — no breakage)

- [ ] **Step 6: Commit**

```bash
git add backend/core/estado.py backend/tests/test_tablero_interactivo.py
git commit -m "feat: add task_estado_overrides field to NJM_OS_State for Kanban persistence"
```

---

## Task 2: PATCH /api/v1/tasks/{task_id} endpoint

**Files:**
- Modify: `backend/api/v1_router.py`
- Test: `backend/tests/test_tablero_interactivo.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_tablero_interactivo.py`:

```python
import asyncio
import json
import pytest
from fastapi.testclient import TestClient


def _make_app():
    import os
    os.environ.setdefault("OPENAI_API_KEY", "test")
    from agent.njm_graph import init_graph
    asyncio.run(init_graph())
    from main import app
    return app


@pytest.fixture(scope="module")
def client():
    app = _make_app()
    with TestClient(app) as c:
        yield c


def test_patch_task_updates_override(client, monkeypatch):
    from agent.njm_graph import njm_graph

    class FakeSnapshot:
        values = {"task_estado_overrides": {}}
        next = []

    captured_update = {}

    async def fake_aget_state(config):
        return FakeSnapshot()

    async def fake_aupdate_state(config, values, **kwargs):
        captured_update.update(values)

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)
    monkeypatch.setattr(njm_graph, "aupdate_state", fake_aupdate_state)

    res = client.patch(
        "/api/v1/tasks/tarea-001",
        json={"brand_id": "disrupt", "session_id": "dev-session-1", "estado": "EN_PROGRESO"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["task_id"] == "tarea-001"
    assert data["estado"] == "EN_PROGRESO"
    assert captured_update["task_estado_overrides"] == {"tarea-001": "EN_PROGRESO"}


def test_patch_task_invalid_estado(client):
    res = client.patch(
        "/api/v1/tasks/tarea-001",
        json={"brand_id": "disrupt", "session_id": "dev-session-1", "estado": "INVALID"},
    )
    assert res.status_code == 422


def test_patch_task_merges_existing_overrides(client, monkeypatch):
    from agent.njm_graph import njm_graph

    class FakeSnapshotWithExisting:
        values = {"task_estado_overrides": {"tarea-001": "EN_PROGRESO"}}
        next = []

    captured_update = {}

    async def fake_aget_state(config):
        return FakeSnapshotWithExisting()

    async def fake_aupdate_state(config, values, **kwargs):
        captured_update.update(values)

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)
    monkeypatch.setattr(njm_graph, "aupdate_state", fake_aupdate_state)

    res = client.patch(
        "/api/v1/tasks/tarea-002",
        json={"brand_id": "disrupt", "session_id": "dev-session-1", "estado": "DONE"},
    )
    assert res.status_code == 200
    # Both overrides must be present
    assert captured_update["task_estado_overrides"] == {
        "tarea-001": "EN_PROGRESO",
        "tarea-002": "DONE",
    }
```

- [ ] **Step 2: Run the failing tests**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_tablero_interactivo.py::test_patch_task_updates_override tests/test_tablero_interactivo.py::test_patch_task_invalid_estado tests/test_tablero_interactivo.py::test_patch_task_merges_existing_overrides -v
```

Expected: `FAILED` — `404 Not Found` (endpoint doesn't exist yet)

- [ ] **Step 3: Add the PATCH endpoint to v1_router.py**

In `backend/api/v1_router.py`, add after the `ResumeRequest` class and `agent_resume` function (after line 431), before the end of file:

```python
# ══════════════════════════════════════════════════════════════════
# PATCH /api/v1/tasks/{task_id}
# ══════════════════════════════════════════════════════════════════

_VALID_ESTADOS = {"BACKLOG", "EN_PROGRESO", "DONE"}


class TaskUpdateRequest(_BaseModel):
    brand_id: str
    session_id: str
    estado: str

    @classmethod
    def validate_estado(cls, v: str) -> str:
        if v not in _VALID_ESTADOS:
            raise ValueError(f"estado must be one of {_VALID_ESTADOS}")
        return v


from pydantic import field_validator as _field_validator  # noqa: PLC0415, E402


class TaskUpdateRequest(_BaseModel):  # noqa: F811 — redefine with validator
    brand_id: str
    session_id: str
    estado: str

    @_field_validator("estado")
    @classmethod
    def _check_estado(cls, v: str) -> str:
        if v not in _VALID_ESTADOS:
            raise ValueError(f"estado must be one of {_VALID_ESTADOS}")
        return v


@router.patch("/tasks/{task_id}")
async def update_task_estado(task_id: str, body: TaskUpdateRequest):
    """
    Persist a Kanban task estado change to the LangGraph checkpointer.

    Fetches current task_estado_overrides, merges the single change,
    and calls aupdate_state() to write back.
    """
    from agent.njm_graph import njm_graph  # noqa: PLC0415

    thread_id = f"{body.brand_id}:{body.session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        snapshot = await njm_graph.aget_state(config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Checkpointer read error: {exc}") from exc

    current_overrides: dict = {}
    if snapshot:
        current_overrides = dict(snapshot.values.get("task_estado_overrides") or {})

    current_overrides[task_id] = body.estado

    try:
        await njm_graph.aupdate_state(config, {"task_estado_overrides": current_overrides})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Checkpointer write error: {exc}") from exc

    return {"task_id": task_id, "estado": body.estado}
```

**Note:** The double-definition of `TaskUpdateRequest` above is a mistake in the step text. Write it once with the validator:

```python
# ══════════════════════════════════════════════════════════════════
# PATCH /api/v1/tasks/{task_id}
# ══════════════════════════════════════════════════════════════════

from pydantic import field_validator as _fv  # noqa: PLC0415

_VALID_ESTADOS = {"BACKLOG", "EN_PROGRESO", "DONE"}


class TaskUpdateRequest(_BaseModel):
    brand_id: str
    session_id: str
    estado: str

    @_fv("estado")
    @classmethod
    def _check_estado(cls, v: str) -> str:
        if v not in _VALID_ESTADOS:
            raise ValueError(f"estado must be one of {_VALID_ESTADOS}")
        return v


@router.patch("/tasks/{task_id}")
async def update_task_estado(task_id: str, body: TaskUpdateRequest):
    """
    Persist a Kanban task estado change to the LangGraph checkpointer.

    Fetches current task_estado_overrides, merges the single change,
    and calls aupdate_state() to write back.
    """
    from agent.njm_graph import njm_graph  # noqa: PLC0415

    thread_id = f"{body.brand_id}:{body.session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        snapshot = await njm_graph.aget_state(config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Checkpointer read error: {exc}") from exc

    current_overrides: dict = {}
    if snapshot:
        current_overrides = dict(snapshot.values.get("task_estado_overrides") or {})

    current_overrides[task_id] = body.estado

    try:
        await njm_graph.aupdate_state(config, {"task_estado_overrides": current_overrides})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Checkpointer write error: {exc}") from exc

    return {"task_id": task_id, "estado": body.estado}
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_tablero_interactivo.py::test_patch_task_updates_override tests/test_tablero_interactivo.py::test_patch_task_invalid_estado tests/test_tablero_interactivo.py::test_patch_task_merges_existing_overrides -v
```

Expected: all 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/api/v1_router.py backend/tests/test_tablero_interactivo.py
git commit -m "feat: add PATCH /api/v1/tasks/{id} — persists Kanban estado to checkpointer"
```

---

## Task 3: Extend GET /session/state to return merged tasks

**Files:**
- Modify: `backend/api/v1_router.py:376-399` (`get_session_state` function)
- Test: `backend/tests/test_tablero_interactivo.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_tablero_interactivo.py`:

```python
def test_session_state_returns_merged_tasks(client, monkeypatch):
    from agent.njm_graph import njm_graph

    class FakeSnapshot:
        values = {
            "audit_status": "COMPLETE",
            "tareas_generadas": [
                {
                    "id": "tarea-001",
                    "titulo": "Validar CAC",
                    "descripcion": "desc",
                    "responsable": "PM",
                    "prioridad": "ALTA",
                    "estado": "BACKLOG",
                    "skill_origen": "generar_business_case",
                },
                {
                    "id": "tarea-002",
                    "titulo": "Presentar a CEO",
                    "descripcion": "desc2",
                    "responsable": "CEO",
                    "prioridad": "MEDIA",
                    "estado": "BACKLOG",
                    "skill_origen": "generar_business_case",
                },
            ],
            "task_estado_overrides": {"tarea-001": "EN_PROGRESO"},
        }
        next = []

    async def fake_aget_state(config):
        return FakeSnapshot()

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)

    res = client.get("/api/v1/session/state?brand_id=disrupt&session_id=dev-session-1")
    assert res.status_code == 200
    data = res.json()
    assert "tasks" in data
    assert len(data["tasks"]) == 2
    # tarea-001 override applied
    t1 = next(t for t in data["tasks"] if t["id"] == "tarea-001")
    assert t1["estado"] == "EN_PROGRESO"
    # tarea-002 unchanged
    t2 = next(t for t in data["tasks"] if t["id"] == "tarea-002")
    assert t2["estado"] == "BACKLOG"


def test_session_state_tasks_empty_when_no_tareas(client, monkeypatch):
    from agent.njm_graph import njm_graph

    class FakeSnapshot:
        values = {"audit_status": "PENDING"}
        next = []

    async def fake_aget_state(config):
        return FakeSnapshot()

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)

    res = client.get("/api/v1/session/state?brand_id=disrupt&session_id=dev-session-1")
    assert res.status_code == 200
    data = res.json()
    assert data["tasks"] == []
```

- [ ] **Step 2: Run the failing tests**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_tablero_interactivo.py::test_session_state_returns_merged_tasks tests/test_tablero_interactivo.py::test_session_state_tasks_empty_when_no_tareas -v
```

Expected: `FAILED` — `KeyError: 'tasks'` (field not returned yet)

- [ ] **Step 3: Update get_session_state in v1_router.py**

Replace the existing `get_session_state` function body (lines 382-399) with:

```python
@router.get("/session/state")
async def get_session_state(
    brand_id: str = "disrupt",
    session_id: str = "dev-session-1",
):
    """Return current checkpointer snapshot for a brand/session thread."""
    from agent.njm_graph import njm_graph  # noqa: PLC0415

    thread_id = f"{brand_id}:{session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        snapshot = await njm_graph.aget_state(config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Checkpointer error: {exc}") from exc

    values = snapshot.values if snapshot else {}
    overrides: dict = values.get("task_estado_overrides") or {}
    tareas_raw: list = values.get("tareas_generadas") or []

    merged_tasks = []
    for t in tareas_raw:
        task_copy = dict(t)
        if task_copy.get("id") in overrides:
            task_copy["estado"] = overrides[task_copy["id"]]
        merged_tasks.append(task_copy)

    return {
        "audit_status": values.get("audit_status", "PENDING"),
        "interview_questions": values.get("interview_questions"),
        "last_tarjeta": values.get("payload_tarjeta_sugerencia"),
        "documentos_count": len(values.get("documentos_generados", [])),
        "next_interrupt": list(snapshot.next) if snapshot else [],
        "tasks": merged_tasks,
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_tablero_interactivo.py::test_session_state_returns_merged_tasks tests/test_tablero_interactivo.py::test_session_state_tasks_empty_when_no_tareas -v
```

Expected: both PASSED

- [ ] **Step 5: Run full test suite to guard against regressions**

```bash
cd backend && .venv/bin/python3 -m pytest tests/ -v
```

Expected: all PASSED (smoke test + motor_desglose + v1_sse + tablero_interactivo)

- [ ] **Step 6: Commit**

```bash
git add backend/api/v1_router.py backend/tests/test_tablero_interactivo.py
git commit -m "feat: extend GET /session/state to return merged tasks with estado overrides"
```

---

## Task 4: Frontend — localTasks state + click-to-advance + mount hydration

**Files:**
- Modify: `frontend/app/brand/[id]/pm/page.tsx`

No Jest infrastructure. TypeScript strict mode + `npm run build` is the safety net for this task.

- [ ] **Step 1: Type-check baseline**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit
```

Expected: 0 errors

- [ ] **Step 2: Add ESTADO_CYCLE constant and localTasks state**

In `pm/page.tsx`, add the constant after `PRIORIDAD_BADGE` (after line 24):

```typescript
const ESTADO_CYCLE: Record<Tarea["estado"], Tarea["estado"]> = {
  BACKLOG: "EN_PROGRESO",
  EN_PROGRESO: "DONE",
  DONE: "BACKLOG",
};
```

In the `PMWorkspacePage` component, add after `const { tasks } = agentConsole;` (after line 227):

```typescript
const [localTasks, setLocalTasks] = useState<Tarea[]>([]);
const [patchingTaskId, setPatchingTaskId] = useState<string | null>(null);
```

- [ ] **Step 3: Add useEffect to sync localTasks from agentConsole.tasks**

Add after the existing `useEffect` blocks (after line 263), still inside the component:

```typescript
// Sync incoming SSE tasks into localTasks, preserving any local estado overrides.
useEffect(() => {
  if (tasks.length === 0) return;
  setLocalTasks((prev) => {
    const overrideMap = Object.fromEntries(prev.map((t) => [t.id, t.estado]));
    return tasks.map((t) => ({ ...t, estado: overrideMap[t.id] ?? t.estado }));
  });
}, [tasks]);
```

- [ ] **Step 4: Add mount-time hydration from session/state**

Add after the previous `useEffect`:

```typescript
// Hydrate localTasks from persisted session state on mount.
useEffect(() => {
  const controller = new AbortController();
  fetch(
    `${API_URL}/api/v1/session/state?brand_id=${params.id}&session_id=${SESSION_ID}`,
    { signal: controller.signal }
  )
    .then((r) => r.json())
    .then((data) => {
      if (Array.isArray(data.tasks) && data.tasks.length > 0) {
        setLocalTasks(data.tasks as Tarea[]);
      }
      if (data.last_tarjeta) setTarjeta(data.last_tarjeta as TarjetaResultado);
    })
    .catch(() => {});
  return () => controller.abort();
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);
```

- [ ] **Step 5: Add handleEstadoChange function**

Add after the `tarjetaToArtefacto` function (after line 290):

```typescript
function handleEstadoChange(tareaId: string, currentEstado: Tarea["estado"]) {
  const nextEstado = ESTADO_CYCLE[currentEstado];
  // Optimistic update
  setLocalTasks((prev) =>
    prev.map((t) => (t.id === tareaId ? { ...t, estado: nextEstado } : t))
  );
  setPatchingTaskId(tareaId);
  fetch(`${API_URL}/api/v1/tasks/${tareaId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      brand_id: params.id,
      session_id: SESSION_ID,
      estado: nextEstado,
    }),
  })
    .catch(() => {
      // Rollback on failure
      setLocalTasks((prev) =>
        prev.map((t) => (t.id === tareaId ? { ...t, estado: currentEstado } : t))
      );
    })
    .finally(() => setPatchingTaskId(null));
}
```

- [ ] **Step 6: Update Kanban to use localTasks and make cards interactive**

In the Kanban section, replace the line that reads `const col = tasks.filter(...)` with `const col = localTasks.filter(...)`.

Then replace the task card `div` with a `button`:

**Find (inside `col.map((tarea) => (...))`):**
```tsx
<div
  key={tarea.id}
  className="glass-subtle rounded-lg p-3 border border-white/[0.06] flex flex-col gap-1.5"
>
  <p className="text-xs font-medium text-foreground/80 leading-snug">
    {tarea.titulo}
  </p>
  <p className="text-[10px] text-muted-foreground/50 leading-relaxed">
    {tarea.descripcion}
  </p>
  <div className="flex items-center gap-1.5 mt-0.5">
    <span
      className={`text-[9px] px-1.5 py-0.5 rounded border font-mono uppercase tracking-wide ${PRIORIDAD_BADGE[tarea.prioridad as Tarea["prioridad"]] ?? ""}`}
    >
      {tarea.prioridad}
    </span>
    <span className="text-[9px] text-muted-foreground/30 font-mono">
      {tarea.responsable}
    </span>
  </div>
</div>
```

**Replace with:**
```tsx
<button
  key={tarea.id}
  onClick={() => handleEstadoChange(tarea.id, tarea.estado)}
  disabled={patchingTaskId === tarea.id}
  className="glass-subtle rounded-lg p-3 border border-white/[0.06] flex flex-col gap-1.5 text-left w-full cursor-pointer hover:border-white/[0.12] active:scale-[0.98] transition-all duration-100 disabled:opacity-50 disabled:cursor-not-allowed"
>
  <p className="text-xs font-medium text-foreground/80 leading-snug">
    {tarea.titulo}
  </p>
  <p className="text-[10px] text-muted-foreground/50 leading-relaxed">
    {tarea.descripcion}
  </p>
  <div className="flex items-center gap-1.5 mt-0.5">
    <span
      className={`text-[9px] px-1.5 py-0.5 rounded border font-mono uppercase tracking-wide ${PRIORIDAD_BADGE[tarea.prioridad as Tarea["prioridad"]] ?? ""}`}
    >
      {tarea.prioridad}
    </span>
    <span className="text-[9px] text-muted-foreground/30 font-mono">
      {tarea.responsable}
    </span>
  </div>
</button>
```

Also update the empty-state guard: replace `tasks.length === 0` with `localTasks.length === 0`.

And update the task count badge: replace `tasks.length > 0` with `localTasks.length > 0` and `{tasks.length}` with `{localTasks.length}`.

- [ ] **Step 7: Type-check**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit
```

Expected: 0 errors

- [ ] **Step 8: Commit**

```bash
git add frontend/app/brand/[id]/pm/page.tsx
git commit -m "feat: interactive Kanban board — click to advance estado, optimistic update + PATCH persist"
```

---

## Task 5: End-to-end smoke test

- [ ] **Step 1: Start the full stack**

```bash
./start.sh
```

Wait for both `Uvicorn running on http://0.0.0.0:8000` and `Ready on http://localhost:3000`.

- [ ] **Step 2: Smoke test the PATCH endpoint directly**

```bash
curl -s -X PATCH http://localhost:8000/api/v1/tasks/tarea-test \
  -H "Content-Type: application/json" \
  -d '{"brand_id":"disrupt","session_id":"dev-session-1","estado":"EN_PROGRESO"}' | python3 -m json.tool
```

Expected output:
```json
{
    "task_id": "tarea-test",
    "estado": "EN_PROGRESO"
}
```

- [ ] **Step 3: Smoke test session/state tasks field**

```bash
curl -s "http://localhost:8000/api/v1/session/state?brand_id=disrupt&session_id=dev-session-1" | python3 -m json.tool
```

Expected: response JSON includes `"tasks": [...]` key (may be empty if no graph run has completed yet).

- [ ] **Step 4: Full browser test — trigger PM run then interact with Kanban**

1. Open `http://localhost:3000/brand/disrupt/pm`
2. Click **Consultar PM / Ejecutar Táctica** — watch AgentConsole stream
3. After stream completes, Kanban cards appear in the BACKLOG column
4. Click a card — it should animate to the EN_PROGRESO column immediately (optimistic)
5. Click the same card again — it moves to DONE
6. Click again — it returns to BACKLOG
7. Hard-refresh the page (`Cmd+Shift+R`) — cards should reappear with their last estados (hydrated from `session/state`)

- [ ] **Step 5: Final test suite run**

```bash
cd backend && .venv/bin/python3 -m pytest tests/ -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "test: phase 2.7 smoke test complete — Tablero Interactivo end-to-end verified"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Task |
|---|---|
| Frontend: click/drag-and-drop state change | Task 4 (click-to-cycle) — drag-and-drop deferred per YAGNI; click satisfies "permitir cambios de estado" |
| API: PATCH /api/v1/tasks/{id} | Task 2 |
| Persistencia: cambios guardados en NJM_OS_State | Task 1 (new field) + Task 2 (aupdate_state) |
| No se pierdan al refrescar | Task 3 (session/state returns merged tasks) + Task 4 (mount hydration) |

**Drag-and-drop note:** The spec says "clic o drag-and-drop". Drag-and-drop requires a DnD library (e.g. `@dnd-kit/core`) and significant additional UI complexity. Click-to-cycle satisfies the functional requirement with zero new dependencies. If drag-and-drop is desired, it should be a follow-up phase.

**Placeholder scan:** No TBDs, TODOs, or "similar to Task N" references found.

**Type consistency:**
- `Tarea["estado"]` used consistently across `ESTADO_CYCLE`, `handleEstadoChange`, `localTasks` state
- `localTasks: Tarea[]` — same `Tarea` type imported from `@/hooks/useAgentConsole`
- `task_estado_overrides: Dict[str, str]` in Python backend matches `Record<string, string>` semantics
- `TaskUpdateRequest.estado` validated against `_VALID_ESTADOS = {"BACKLOG", "EN_PROGRESO", "DONE"}` — matches `EstadoTarea` enum values in `core/schemas.py`
