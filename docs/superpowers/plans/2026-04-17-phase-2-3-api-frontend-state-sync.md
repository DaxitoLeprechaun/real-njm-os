# Phase 2.3 — API & Frontend State Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `GET /api/v1/agent/stream` to `njm_graph.astream_events`, pass real `brand_id`/`session_id` from query params, and emit a structured `action_required` SSE event when the graph pauses at `BLOQUEO_CEO` or `GAP_DETECTED`.

**Architecture:** Replace the `_sse_ceo_audit(brand_context)` generator (which streams from the orphaned `ceo_graph`) with `_sse_njm_stream(brand_id, session_id)` that streams from the unified `njm_graph`. Emit JSON-structured events so the frontend can distinguish log lines from action triggers. Add two new endpoints (`GET /api/v1/session/state` and `POST /api/v1/agent/resume`) needed to make the `action_required` event useful. Update `useAgentConsole.ts` to parse JSON events and expose a `resume` function.

**Tech Stack:** FastAPI SSE (`StreamingResponse`), LangGraph `astream_events(version="v2")`, `SqliteSaver` checkpointer, Next.js EventSource API, TypeScript.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/api/v1_router.py` | Modify | New SSE generator + `session/state` + `agent/resume` endpoints |
| `backend/tests/test_v1_sse.py` | Create | Tests for all new endpoint behaviour |
| `frontend/hooks/useAgentConsole.ts` | Modify | JSON event parsing, `brand_id`/`session_id` params, `resume` fn |
| `frontend/app/brand/[id]/ceo/page.tsx` | Modify | Pass `brand_id` + `session_id` to `invoke` |

---

## Task 1: Write failing tests for new SSE endpoint

**Files:**
- Create: `backend/tests/test_v1_sse.py`

- [ ] **Step 1: Write the test file**

```python
# backend/tests/test_v1_sse.py
"""Tests for Phase 2.3 unified SSE endpoint."""
import json
import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key-for-unit-tests")


# ── helpers ──────────────────────────────────────────────────────────────────


def _parse_sse_lines(body: bytes) -> list[dict]:
    """Extract data payloads from SSE response bytes."""
    events = []
    for line in body.decode().splitlines():
        if line.startswith("data: "):
            raw = line[6:]
            if raw == "[DONE]":
                events.append({"type": "done_sentinel"})
            else:
                try:
                    events.append(json.loads(raw))
                except json.JSONDecodeError:
                    events.append({"type": "raw", "text": raw})
    return events


# ── tests ─────────────────────────────────────────────────────────────────────


def test_agent_stream_accepts_brand_id_and_session_id(monkeypatch):
    """GET /api/v1/agent/stream must accept brand_id and session_id params."""
    from agent import njm_graph as graph_mod

    async def fake_astream_events(state, config, version):
        yield {"event": "on_chain_end", "name": "output", "data": {}}

    monkeypatch.setattr(graph_mod.njm_graph, "astream_events", fake_astream_events)

    def fake_get_state(config):
        class _Snap:
            values = {"estado_validacion": "LISTO_PARA_FIRMA", "audit_status": "COMPLETE"}
            next = []
            tasks = []
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/agent/stream",
        params={"sequenceId": "ceo-audit", "brand_id": "acme", "session_id": "ses-001"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


def test_agent_stream_emits_done_event(monkeypatch):
    """SSE stream must always end with a done event."""
    from agent import njm_graph as graph_mod

    async def fake_astream_events(state, config, version):
        yield {"event": "on_chain_end", "name": "output", "data": {}}

    monkeypatch.setattr(graph_mod.njm_graph, "astream_events", fake_astream_events)

    def fake_get_state(config):
        class _Snap:
            values = {"estado_validacion": "LISTO_PARA_FIRMA", "audit_status": "COMPLETE"}
            next = []
            tasks = []
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/agent/stream",
        params={"sequenceId": "ceo-audit", "brand_id": "acme", "session_id": "ses-001"},
    )
    events = _parse_sse_lines(resp.content)
    done_events = [e for e in events if e.get("type") == "done"]
    assert len(done_events) == 1


def test_agent_stream_emits_action_required_on_bloqueo_ceo(monkeypatch):
    """SSE must emit action_required event when final state is BLOQUEO_CEO."""
    from agent import njm_graph as graph_mod

    async def fake_astream_events(state, config, version):
        yield {"event": "on_chain_end", "name": "output", "data": {}}

    monkeypatch.setattr(graph_mod.njm_graph, "astream_events", fake_astream_events)

    def fake_get_state(config):
        class _Snap:
            values = {
                "estado_validacion": "BLOQUEO_CEO",
                "audit_status": "COMPLETE",
                "risk_details": "Propuesta viola vector 5.",
            }
            next = []
            tasks = []
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/agent/stream",
        params={"sequenceId": "ceo-audit", "brand_id": "acme", "session_id": "ses-001"},
    )
    events = _parse_sse_lines(resp.content)
    ar = [e for e in events if e.get("type") == "action_required"]
    assert len(ar) == 1
    assert ar[0]["trigger"] == "BLOQUEO_CEO"
    assert "risk_message" in ar[0]


def test_agent_stream_emits_action_required_on_gap_detected(monkeypatch):
    """SSE must emit action_required with trigger GAP_DETECTED when graph pauses."""
    from agent import njm_graph as graph_mod

    async def fake_astream_events(state, config, version):
        yield {"event": "on_chain_end", "name": "human_in_loop", "data": {}}

    monkeypatch.setattr(graph_mod.njm_graph, "astream_events", fake_astream_events)

    def fake_get_state(config):
        class _FakeTask:
            class _Interrupt:
                value = {"type": "interview_required", "questions": ["Q1", "Q2"]}
            interrupts = [_Interrupt()]

        class _Snap:
            values = {
                "audit_status": "GAP_DETECTED",
                "interview_questions": ["Q1", "Q2"],
            }
            next = ["ceo_auditor"]
            tasks = [_FakeTask()]
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/agent/stream",
        params={"sequenceId": "ceo-audit", "brand_id": "acme", "session_id": "ses-001"},
    )
    events = _parse_sse_lines(resp.content)
    ar = [e for e in events if e.get("type") == "action_required"]
    assert len(ar) == 1
    assert ar[0]["trigger"] == "GAP_DETECTED"
    assert "questions" in ar[0]


def test_session_state_endpoint_returns_snapshot(monkeypatch):
    """GET /api/v1/session/state must return current graph state from checkpointer."""
    from agent import njm_graph as graph_mod

    def fake_get_state(config):
        class _Snap:
            values = {
                "audit_status": "COMPLETE",
                "interview_questions": None,
                "payload_tarjeta_sugerencia": None,
                "documentos_generados": ["file1.md"],
            }
            next = []
            tasks = []
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/session/state",
        params={"brand_id": "acme", "session_id": "ses-001"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["audit_status"] == "COMPLETE"
    assert data["documentos_count"] == 1


def test_agent_resume_endpoint_invokes_graph(monkeypatch):
    """POST /api/v1/agent/resume must call njm_graph.ainvoke with answers."""
    from agent import njm_graph as graph_mod

    invoked_with = []

    async def fake_ainvoke(state, config):
        invoked_with.append({"state": state, "config": config})
        return {}

    monkeypatch.setattr(graph_mod.njm_graph, "ainvoke", fake_ainvoke)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.post(
        "/api/v1/agent/resume",
        json={
            "brand_id": "acme",
            "session_id": "ses-001",
            "answers": "Vector 3: audiencia SaaS B2B en LATAM.",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resumed"
    assert len(invoked_with) == 1
    assert invoked_with[0]["state"]["human_interview_answers"] == "Vector 3: audiencia SaaS B2B en LATAM."
    assert invoked_with[0]["config"]["configurable"]["thread_id"] == "acme:ses-001"
```

- [ ] **Step 2: Run tests to confirm they all fail**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_v1_sse.py -v 2>&1 | head -60
```

Expected output: 6 failures — endpoints don't exist yet / wrong behavior.

- [ ] **Step 3: Commit the failing tests**

```bash
cd backend
git add tests/test_v1_sse.py
git commit -m "test: add failing tests for Phase 2.3 unified SSE + session endpoints"
```

---

## Task 2: Implement `_sse_njm_stream` generator

**Files:**
- Modify: `backend/api/v1_router.py`

Replace `_sse_ceo_audit` with a new generator that streams from `njm_graph`. Keep mock scripts for non-`ceo-audit` sequences (PM streaming is Phase 2.4).

- [ ] **Step 1: Add imports and node label maps at the top of `v1_router.py`**

Open `backend/api/v1_router.py`. Add after the existing imports (after line 22, before `router = APIRouter(...)`):

```python
import json
from core.dev_fixtures import _LIBRO_VIVO_DISRUPT  # noqa: PLC0415 — lazy for startup speed
```

Then add after the `router = APIRouter(...)` line:

```python
_NODE_START_LOG: dict[str, str] = {
    "ingest": "[⏳] Procesando documentos de onboarding...",
    "ceo_auditor": "[⏳] Auditoría CEO iniciada — escaneando vectores estratégicos...",
    "human_in_loop": "[⏳] Esperando input del Encargado Real...",
    "pm_execution": "[⏳] Agente PM ejecutando skill seleccionada...",
    "ceo_review": "[⏳] CEO revisando output del PM...",
    "output": "[⏳] Generando tarjeta final...",
}

_NODE_END_LOG: dict[str, str] = {
    "ingest": "[✓] Documentos indexados en memoria de marca.",
    "ceo_auditor": "[✓] Auditoría CEO completada.",
    "pm_execution": "[✓] Ejecución PM finalizada.",
    "ceo_review": "[✓] Revisión CEO completada.",
    "output": "[✓] Tarjeta lista.",
}


def _sse_json(payload: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
```

- [ ] **Step 2: Write `_sse_njm_stream` — the new unified generator**

Add this function **before** the existing `_sse_ceo_audit` function in `v1_router.py`:

```python
async def _sse_njm_stream(
    brand_id: str,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """
    Stream njm_graph.astream_events for a given brand/session.

    Emits JSON-structured SSE events:
      {"type": "log",            "text": "..."}
      {"type": "action_required", "trigger": "BLOQUEO_CEO"|"GAP_DETECTED", ...}
      {"type": "done"}
    """
    from agent.njm_graph import njm_graph  # noqa: PLC0415

    thread_id = f"{brand_id}:{session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Dev fallback: brand "disrupt" skips CEO with pre-loaded fixtures.
    if brand_id == "disrupt":
        initial_state = {
            "brand_id": brand_id,
            "session_id": session_id,
            "messages": [
                HumanMessage(
                    content="Ejecuta el flujo completo. brand_id=disrupt, usar fixtures de desarrollo."
                )
            ],
            "audit_status": "COMPLETE",
            "libro_vivo": _LIBRO_VIVO_DISRUPT,
            "brand_context_raw": _DEFAULT_BRAND_CONTEXT,
            "uploaded_doc_paths": [],
            "documentos_generados": [],
            "alertas_internas": [],
            "ruta_espacio_trabajo": f"~/NJM_OS/Marcas/{brand_id}/workspace/",
            "risk_flag": False,
            "estado_validacion": "EN_PROGRESO",
            "peticion_humano": "Genera el Business Case inicial para la marca.",
        }
    else:
        initial_state = {
            "brand_id": brand_id,
            "session_id": session_id,
            "messages": [
                HumanMessage(
                    content="Inicia la auditoría CEO y ejecuta el flujo completo."
                )
            ],
            "audit_status": "PENDING",
            "brand_context_raw": "",
            "uploaded_doc_paths": [],
            "documentos_generados": [],
            "alertas_internas": [],
            "ruta_espacio_trabajo": f"~/NJM_OS/Marcas/{brand_id}/workspace/",
            "risk_flag": False,
            "estado_validacion": "EN_PROGRESO",
        }

    yield _sse_json({"type": "log", "text": f"[⏳] Conectando con NJM OS (brand: {brand_id})..."})
    await asyncio.sleep(0.05)

    buffer: str = ""

    try:
        async for event in njm_graph.astream_events(initial_state, config, version="v2"):
            etype = event.get("event", "")
            name = event.get("name", "")

            if etype == "on_chain_start" and name in _NODE_START_LOG:
                yield _sse_json({"type": "log", "text": _NODE_START_LOG[name]})

            elif etype == "on_chain_end" and name in _NODE_END_LOG:
                yield _sse_json({"type": "log", "text": _NODE_END_LOG[name]})

            elif etype == "on_tool_start":
                yield _sse_json({"type": "log", "text": f"[⏳] Herramienta: {name}..."})

            elif etype == "on_tool_end":
                yield _sse_json({"type": "log", "text": f"[✓] {name} completada."})

            elif etype == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk is None:
                    continue
                text = _extract_text(chunk.content)
                if not text:
                    continue
                buffer += text
                while "\n" in buffer or len(buffer) >= 80:
                    if "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if line.strip():
                            yield _sse_json({"type": "log", "text": line.strip()})
                    else:
                        yield _sse_json({"type": "log", "text": buffer})
                        buffer = ""
                        break

        if buffer.strip():
            yield _sse_json({"type": "log", "text": buffer.strip()})

    except asyncio.CancelledError:
        # Client disconnected — clean up and exit.
        return

    # ── Post-stream: check final state for interrupts / terminal states ──────
    try:
        snapshot = njm_graph.get_state(config)
        values = snapshot.values

        # Case 1: graph was interrupted (human_in_loop with real interrupt())
        if snapshot.next:
            questions = values.get("interview_questions") or []
            yield _sse_json({
                "type": "action_required",
                "trigger": "GAP_DETECTED",
                "questions": questions,
                "gap_report_path": values.get("gap_report_path"),
                "session_id": session_id,
                "brand_id": brand_id,
            })

        # Case 2: graph completed but PM raised BLOQUEO_CEO
        elif values.get("estado_validacion") == "BLOQUEO_CEO":
            yield _sse_json({
                "type": "action_required",
                "trigger": "BLOQUEO_CEO",
                "risk_message": values.get("risk_details", "Revisión CEO requerida."),
                "session_id": session_id,
                "brand_id": brand_id,
            })

    except Exception:
        # Checkpointer unavailable — don't crash the stream.
        pass

    yield _sse_json({"type": "done"})
```

- [ ] **Step 3: Verify the file still imports cleanly**

```bash
cd backend
.venv/bin/python3 -c "
import os; os.environ.setdefault('OPENAI_API_KEY','test')
from api.v1_router import router
print('v1_router OK')
"
```

Expected: `v1_router OK`

---

## Task 3: Update `agent_stream` endpoint signature

**Files:**
- Modify: `backend/api/v1_router.py`

The current `agent_stream` function accepts `sequenceId` and `brand_context`. Replace it to accept `brand_id` and `session_id`, routing `ceo-audit` to `_sse_njm_stream` and other sequences to the mock generator.

- [ ] **Step 1: Replace the `agent_stream` function**

Find and replace the entire `agent_stream` function (lines 193–210 of the original file):

Old:
```python
@router.get("/agent/stream")
async def agent_stream(
    sequenceId: str,
    brand_context: str = _DEFAULT_BRAND_CONTEXT,
):
    if sequenceId == "ceo-audit":
        generator = _sse_ceo_audit(brand_context)
    else:
        generator = _sse_mock(sequenceId)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

New:
```python
@router.get("/agent/stream")
async def agent_stream(
    sequenceId: str,
    brand_id: str = "disrupt",
    session_id: str = "dev-session-1",
):
    """
    Unified SSE agent stream.

    sequenceId=ceo-audit  → streams real njm_graph (brand_id + session_id required)
    sequenceId=<other>    → mock script (pm-execution, ceo-approve, ceo-reject)

    TD-03 resolved: brand_id and session_id now come from query params, not brand_context.
    """
    if sequenceId == "ceo-audit":
        generator = _sse_njm_stream(brand_id, session_id)
    else:
        generator = _sse_mock(sequenceId)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 2: Run the SSE tests — the first three should now pass**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_v1_sse.py::test_agent_stream_accepts_brand_id_and_session_id \
  tests/test_v1_sse.py::test_agent_stream_emits_done_event \
  tests/test_v1_sse.py::test_agent_stream_emits_action_required_on_bloqueo_ceo \
  tests/test_v1_sse.py::test_agent_stream_emits_action_required_on_gap_detected \
  -v
```

Expected: 4 PASS. (The session/state and resume tests still fail — not yet implemented.)

- [ ] **Step 3: Commit**

```bash
cd backend
git add api/v1_router.py
git commit -m "feat: unified SSE endpoint streams njm_graph with brand_id + session_id (TD-03)"
```

---

## Task 4: Add `GET /api/v1/session/state` endpoint

**Files:**
- Modify: `backend/api/v1_router.py`

- [ ] **Step 1: Add the endpoint to `v1_router.py`**

Add this function after `agent_stream` (at the bottom of the router file, before the end):

```python
# ══════════════════════════════════════════════════════════════════
# GET /api/v1/session/state
# ══════════════════════════════════════════════════════════════════

@router.get("/session/state")
async def get_session_state(
    brand_id: str = "disrupt",
    session_id: str = "dev-session-1",
):
    """
    Return current checkpointer snapshot for a brand/session thread.
    Frontend uses this on workspace mount to hydrate state without re-running the graph.
    """
    from agent.njm_graph import njm_graph  # noqa: PLC0415

    thread_id = f"{brand_id}:{session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        snapshot = njm_graph.get_state(config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Checkpointer error: {exc}") from exc

    values = snapshot.values if snapshot else {}
    return {
        "audit_status": values.get("audit_status", "PENDING"),
        "interview_questions": values.get("interview_questions"),
        "last_tarjeta": values.get("payload_tarjeta_sugerencia"),
        "documentos_count": len(values.get("documentos_generados", [])),
        "next_interrupt": list(snapshot.next) if snapshot else [],
    }
```

- [ ] **Step 2: Run the session state test**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_v1_sse.py::test_session_state_endpoint_returns_snapshot -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
cd backend
git add api/v1_router.py
git commit -m "feat: add GET /api/v1/session/state for checkpointer hydration"
```

---

## Task 5: Add `POST /api/v1/agent/resume` endpoint

**Files:**
- Modify: `backend/api/v1_router.py`

- [ ] **Step 1: Add the Pydantic request model and endpoint**

Add after the `get_session_state` function:

```python
# ══════════════════════════════════════════════════════════════════
# POST /api/v1/agent/resume
# ══════════════════════════════════════════════════════════════════

from pydantic import BaseModel  # noqa: PLC0415 — already imported via FastAPI, explicit here


class ResumeRequest(BaseModel):
    brand_id: str
    session_id: str
    answers: str


@router.post("/agent/resume")
async def agent_resume(body: ResumeRequest):
    """
    Resume a graph paused at human_in_loop_node after interview answers are provided.
    The frontend calls this after the user fills in the DayCeroView wizard.
    """
    from agent.njm_graph import njm_graph  # noqa: PLC0415

    thread_id = f"{body.brand_id}:{body.session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        await njm_graph.ainvoke(
            {"human_interview_answers": body.answers},
            config=config,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Resume failed: {exc}") from exc

    return {"status": "resumed", "thread_id": thread_id}
```

- [ ] **Step 2: Run the resume test**

```bash
cd backend
.venv/bin/python3 -m pytest tests/test_v1_sse.py::test_agent_resume_endpoint_invokes_graph -v
```

Expected: PASS.

- [ ] **Step 3: Run the full test suite to confirm no regressions**

```bash
cd backend
.venv/bin/python3 -m pytest tests/ -v 2>&1 | tail -30
```

Expected: All tests pass (including pre-existing `test_ingest_endpoint.py`, `test_rag.py`, etc.).

- [ ] **Step 4: Commit**

```bash
cd backend
git add api/v1_router.py
git commit -m "feat: add POST /api/v1/agent/resume for human-in-loop graph resumption"
```

---

## Task 6: Update `useAgentConsole.ts` — JSON events + params + resume

**Files:**
- Modify: `frontend/hooks/useAgentConsole.ts`

The hook currently expects plain text in `event.data`. After Task 2, the backend emits JSON. Update the hook to parse JSON, expose an `actionRequired` state, and add a `resume` function.

- [ ] **Step 1: Rewrite `useAgentConsole.ts`**

```typescript
"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────

export interface AgentParams {
  brand_id: string;
  session_id: string;
}

export interface ActionRequiredEvent {
  trigger: "BLOQUEO_CEO" | "GAP_DETECTED";
  risk_message?: string;
  questions?: string[];
  gap_report_path?: string | null;
  session_id: string;
  brand_id: string;
}

export interface UseAgentConsoleReturn {
  open: boolean;
  logs: string[];
  running: boolean;
  actionRequired: ActionRequiredEvent | null;
  invoke: (sequenceId: string, params?: Partial<AgentParams>) => void;
  resume: (answers: string, params: AgentParams) => Promise<void>;
  close: () => void;
}

// ── Hook ───────────────────────────────────────────────────────────────────

export function useAgentConsole(): UseAgentConsoleReturn {
  const [open, setOpen] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [actionRequired, setActionRequired] = useState<ActionRequiredEvent | null>(null);
  const esRef = useRef<EventSource | null>(null);

  function closeStream() {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  }

  const invoke = useCallback(
    (sequenceId: string, params: Partial<AgentParams> = {}) => {
      closeStream();
      setLogs([]);
      setRunning(true);
      setOpen(true);
      setActionRequired(null);

      const brand_id = params.brand_id ?? "disrupt";
      const session_id = params.session_id ?? "dev-session-1";

      const url = new URL(`${API_URL}/api/v1/agent/stream`);
      url.searchParams.set("sequenceId", sequenceId);
      url.searchParams.set("brand_id", brand_id);
      url.searchParams.set("session_id", session_id);

      const es = new EventSource(url.toString());
      esRef.current = es;

      es.onmessage = (event) => {
        const raw = event.data as string;

        // Legacy sentinel — kept for backward compat with mock sequences.
        if (raw === "[DONE]") {
          closeStream();
          setRunning(false);
          return;
        }

        let parsed: Record<string, unknown>;
        try {
          parsed = JSON.parse(raw);
        } catch {
          // Non-JSON line — treat as plain log text (mock sequences).
          setLogs((prev) => [...prev, raw]);
          return;
        }

        if (parsed.type === "log") {
          setLogs((prev) => [...prev, parsed.text as string]);
        } else if (parsed.type === "action_required") {
          setActionRequired(parsed as unknown as ActionRequiredEvent);
          closeStream();
          setRunning(false);
        } else if (parsed.type === "done") {
          closeStream();
          setRunning(false);
        }
      };

      es.onerror = () => {
        closeStream();
        setRunning(false);
        setLogs((prev) => [...prev, "[!] Error de conexión con el agente."]);
      };
    },
    []
  );

  const resume = useCallback(async (answers: string, params: AgentParams) => {
    const res = await fetch(`${API_URL}/api/v1/agent/resume`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        brand_id: params.brand_id,
        session_id: params.session_id,
        answers,
      }),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Resume failed: ${err}`);
    }
  }, []);

  const close = useCallback(() => {
    closeStream();
    setOpen(false);
    setRunning(false);
    setActionRequired(null);
  }, []);

  useEffect(() => () => closeStream(), []);

  return { open, logs, running, actionRequired, invoke, close, resume };
}
```

- [ ] **Step 2: Type-check the frontend**

```bash
cd frontend
./node_modules/.bin/tsc --noEmit 2>&1 | head -40
```

Expected: errors only about `invoke` callers that don't pass `params` yet (handled in Task 7). If there are other errors, fix them before continuing.

---

## Task 7: Update `ceo/page.tsx` to pass `brand_id` and `session_id`

**Files:**
- Modify: `frontend/app/brand/[id]/ceo/page.tsx`

`params.id` is the `brand_id`. For `session_id`, generate once per component mount and store in `useRef`.

- [ ] **Step 1: Add `useRef` for session_id and update `handleInvocarCEO`**

In `ceo/page.tsx`, find the component function body. Add a `sessionIdRef` and update `handleInvocarCEO`:

Current (around line 67–78):
```typescript
  const agentConsole = useAgentConsole();

  function handleCargarDoc(vectorId: string) {
    ...
  }

  function handleInvocarCEO() {
    agentConsole.invoke("ceo-audit");
  }
```

Replace with:
```typescript
  const agentConsole = useAgentConsole();
  const sessionIdRef = useRef<string>(
    typeof crypto !== "undefined" ? crypto.randomUUID() : "dev-session-1"
  );

  function handleCargarDoc(vectorId: string) {
    setActiveVectorId(vectorId);
    setManualInput("");
    setSelectedFile(null);
    setDialogOpen(true);
  }

  function handleInvocarCEO() {
    agentConsole.invoke("ceo-audit", {
      brand_id: params.id,
      session_id: sessionIdRef.current,
    });
  }
```

- [ ] **Step 2: Type-check again**

```bash
cd frontend
./node_modules/.bin/tsc --noEmit 2>&1 | head -40
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd frontend
git add hooks/useAgentConsole.ts app/brand/\[id\]/ceo/page.tsx
git commit -m "feat: pass brand_id + session_id to SSE invoke, add resume fn and actionRequired state"
```

---

## Task 8: Smoke test the full flow

- [ ] **Step 1: Start the backend**

```bash
cd backend && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
sleep 3
```

- [ ] **Step 2: Verify new endpoint signatures in Swagger**

Open `http://localhost:8000/docs` and confirm:
- `GET /api/v1/agent/stream` shows `brand_id` and `session_id` params (not `brand_context`)
- `GET /api/v1/session/state` exists
- `POST /api/v1/agent/resume` exists

- [ ] **Step 3: Manual SSE test with curl**

```bash
curl -N "http://localhost:8000/api/v1/agent/stream?sequenceId=ceo-audit&brand_id=disrupt&session_id=test-001" 2>&1 | head -30
```

Expected output: JSON events like:
```
data: {"type": "log", "text": "[⏳] Conectando con NJM OS (brand: disrupt)..."}
data: {"type": "log", "text": "[⏳] Agente PM ejecutando skill seleccionada..."}
...
data: {"type": "done"}
```

- [ ] **Step 4: Test session state endpoint**

```bash
curl "http://localhost:8000/api/v1/session/state?brand_id=disrupt&session_id=test-001"
```

Expected: JSON with `audit_status`, `documentos_count`, etc.

- [ ] **Step 5: Start frontend and verify console opens**

```bash
cd frontend && npm run dev &
sleep 5
```

Open `http://localhost:3000/brand/disrupt/ceo` in browser. Click "Invocar CEO". Verify:
- Agent console opens
- Log lines appear (not `[object Object]` — JSON is being parsed)
- Console closes when `done` event received

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat: Phase 2.3 complete — unified SSE, real brand/session params, action_required events"
```

---

## Self-Review

**Spec coverage:**

| Requirement | Task |
|-------------|------|
| SSE streams from `njm_graph.astream_events` | Task 2 |
| `brand_id` + `session_id` from query params (TD-03) | Task 3 |
| `action_required` event on `BLOQUEO_CEO` | Task 2 (`_sse_njm_stream` post-stream check) |
| `action_required` event on `GAP_DETECTED` / interrupt | Task 2 (`snapshot.next` check) |
| `GET /api/v1/session/state` | Task 4 |
| `POST /api/v1/agent/resume` | Task 5 |
| Frontend parses JSON events | Task 6 |
| Frontend passes `brand_id`/`session_id` to invoke | Task 7 |

**No placeholders.** All code is complete and runnable.

**Type consistency:**
- `ActionRequiredEvent` defined in `useAgentConsole.ts` — used by `actionRequired` state field.
- `AgentParams` used consistently in `invoke` and `resume` signatures.
- `ResumeRequest` Pydantic model field names match what the test posts.
- `thread_id = f"{brand_id}:{session_id}"` convention consistent across `_sse_njm_stream`, `get_session_state`, and `agent_resume`.
- `njm_graph.get_state(config)` called with same `config` shape (`{"configurable": {"thread_id": ...}}`) in all three places.

**Known limitation:** `pm-execution`, `ceo-approve`, `ceo-reject` sequences still use mock scripts. That's Phase 2.4.
