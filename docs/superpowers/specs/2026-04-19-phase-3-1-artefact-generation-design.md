# Phase 3.1 — Artefact Generation Engine: Design Spec

**Date:** 2026-04-19
**Status:** Approved

---

## Goal

When a Kanban task reaches DONE, the PM operator can generate a full strategic document for that task via a direct LLM call (Option A), stream it live into an `ArtefactViewer` Sheet panel, and persist the result to the LangGraph checkpointer so it survives page refresh. If the artefact already exists in state, the UI shows an Eye icon for instant read-only access without re-invoking the stream.

---

## File Map

| File | Action | Change |
|---|---|---|
| `backend/core/estado.py` | Modify | Add `artefactos_generados: Dict[str, str]` |
| `backend/api/v1_router.py` | Modify | `_sse_artefact_stream` generator + dispatch branch + extend `get_session_state` |
| `backend/tests/test_artefact_generation.py` | Create | TDD tests for new field, stream, persistence, hydration |
| `frontend/hooks/useAgentConsole.ts` | Modify | Add `task_id?`, `task_title?` to `AgentParams` |
| `frontend/components/njm/ArtefactViewer.tsx` | Create | Shadcn Sheet with streaming markdown body |
| `frontend/app/brand/[id]/pm/page.tsx` | Modify | `artefactConsole` instance, hydration, Play/Eye icons, ArtefactViewer mount |

---

## Architecture Overview

```
DONE card (no artefact) → Play button
  → setArtefactTarget({id, titulo})
  → artefactConsole.invoke("pm-generate-artefact", {...agentParams, task_id, task_title})
  → GET /api/v1/agent/stream?sequenceId=pm-generate-artefact&task_id=...&task_title=...
  → _sse_artefact_stream(brand_id, session_id, task_id, task_title)
      1. buscar_contexto_marca(brand_id, task_title) → context string
      2. ChatOpenAI("gpt-4o").astream([SystemMessage, HumanMessage]) → token chunks
      3. yield {"type":"log","text": chunk} per token
      4. aupdate_state({artefactos_generados: {task_id: full_text}})  ← merge, not overwrite
      5. yield {"type":"done"}
  → artefactConsole.logs.join("") → ArtefactViewer Sheet body (streams live)
  → useEffect(running→false) → setArtefactos(prev + {task_id: content})

DONE card (artefact exists) → Eye button
  → setArtefactTarget({id, titulo})  (no invoke)
  → artefactContent = artefactos[task_id]  (local state, zero network)
  → Sheet opens instantly with full persisted content

Mount → GET /session/state → data.artefactos_generados → setArtefactos(data)
                           → data.tasks → setLocalTasks(data.tasks)
                           → data.last_tarjeta → setTarjeta(data.last_tarjeta)
```

**Key isolation decision:** `pm/page.tsx` uses two independent `useAgentConsole()` instances.
- `agentConsole` — existing, drives AgentConsole terminal + Kanban task hydration.
- `artefactConsole` — new, drives only the ArtefactViewer Sheet.

This prevents artefact generation from clearing Kanban tasks or hijacking the terminal.

---

## Backend Design

### 1. `core/estado.py` — new field

```python
artefactos_generados: Dict[str, str]
# Maps task_id → full markdown content string.
# No reducer: PATCH-style — endpoint fetches current dict, merges, calls aupdate_state().
```

`Dict` import already present. Field is optional in TypedDict — no breakage to existing state.

### 2. `api/v1_router.py` — `_sse_artefact_stream` generator

```python
async def _sse_artefact_stream(
    brand_id: str,
    session_id: str,
    task_id: str,
    task_title: str,
) -> AsyncGenerator[str, None]:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    from core.rag import query_brand  # direct function call, not via @tool dispatch
    from agent.njm_graph import njm_graph

    thread_id = f"{brand_id}:{session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # 1. Libro Vivo context
    try:
        context = query_brand(brand_id, task_title, n_results=5)
    except Exception:
        context = "Contexto no disponible."

    # 2. Focused prompt
    system_prompt = (
        "Eres el PM estratégico de NJM OS. "
        "Genera un documento en Markdown completo y ejecutable para la tarea dada. "
        "Estructura obligatoria: # Título, ## Resumen Ejecutivo, ## Análisis, "
        "## Plan de Acción (5-7 pasos numerados), ## Métricas de Éxito, ## Riesgos. "
        "Usa el contexto del Libro Vivo para anclar las propuestas a la realidad de la marca."
    )
    human_prompt = f"Tarea: {task_title}\n\nContexto del Libro Vivo:\n{context}"

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    full_text = ""

    # 3. Stream tokens
    try:
        async for chunk in llm.astream([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]):
            if chunk.content:
                full_text += chunk.content
                yield _sse_json({"type": "log", "text": chunk.content})
    except Exception as exc:
        yield _sse_json({"type": "log", "text": f"\n\n[Error de generación: {exc}]"})

    # 4. Persist to checkpointer (fetch-merge-write)
    try:
        snapshot = await njm_graph.aget_state(config)
        current: dict = {}
        if snapshot:
            current = dict(snapshot.values.get("artefactos_generados") or {})
        current[task_id] = full_text
        await njm_graph.aupdate_state(config, {"artefactos_generados": current})
    except Exception:
        pass  # stream delivered to user; persistence failure is non-fatal

    yield _sse_json({"type": "done"})
```

### 3. `api/v1_router.py` — dispatch branch

In the `_sse_agent_stream` route handler, add before the existing `if sequence_id == "ceo-audit":` chain:

```python
elif sequence_id == "pm-generate-artefact":
    task_id = request.query_params.get("task_id", "")
    task_title = request.query_params.get("task_title", "")
    if not task_id or not task_title:
        raise HTTPException(status_code=422, detail="task_id and task_title required")
    return EventSourceResponse(
        _sse_artefact_stream(brand_id, session_id, task_id, task_title)
    )
```

### 4. `api/v1_router.py` — extend `get_session_state`

Add `artefactos_generados` to the return dict:

```python
return {
    "audit_status": values.get("audit_status", "PENDING"),
    "interview_questions": values.get("interview_questions"),
    "last_tarjeta": values.get("payload_tarjeta_sugerencia"),
    "documentos_count": len(values.get("documentos_generados", [])),
    "next_interrupt": list(snapshot.next) if snapshot else [],
    "tasks": merged_tasks,
    "artefactos_generados": values.get("artefactos_generados") or {},  # NEW
}
```

### 5. Tests (`test_artefact_generation.py`)

| Test | Assertion |
|---|---|
| `test_artefactos_generados_field_in_state` | Field in `NJM_OS_State` type hints, is `Dict` type |
| `test_sse_artefact_stream_emits_log_events` | Mock LLM + aget_state/aupdate_state; assert `log` events arrive with text |
| `test_sse_artefact_stream_emits_done_event` | Last event type is `done` |
| `test_sse_artefact_stream_persists_content` | `aupdate_state` called with `{"artefactos_generados": {"tarea-001": <content>}}` |
| `test_sse_artefact_stream_merges_existing_artefacts` | Pre-existing `{"tarea-000": "old"}` preserved alongside new entry |
| `test_session_state_returns_artefactos_generados` | `GET /session/state` response includes `artefactos_generados` key |

---

## Frontend Design

### 1. `useAgentConsole.ts` — `AgentParams` extension

```typescript
export interface AgentParams {
  brand_id: string;
  session_id: string;
  task_id?: string;     // for pm-generate-artefact
  task_title?: string;  // for pm-generate-artefact
}
```

In `invoke`, forward optional params to URL if defined:
```typescript
if (params.task_id)    url.searchParams.set("task_id", params.task_id);
if (params.task_title) url.searchParams.set("task_title", params.task_title);
```

Fully backward compatible — no existing callers affected.

### 2. `ArtefactViewer.tsx` (`components/njm/`)

```tsx
interface ArtefactViewerProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  taskTitle: string;
  running: boolean;
  content: string;
}

export default function ArtefactViewer({
  open, onOpenChange, taskTitle, running, content,
}: ArtefactViewerProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-[580px] sm:w-[640px] flex flex-col gap-0 p-0"
        onInteractOutside={(e) => { if (running) e.preventDefault(); }}
      >
        <SheetHeader className="px-6 py-4 border-b border-white/[0.06]">
          <div className="flex items-start justify-between gap-3">
            <SheetTitle className="text-sm font-mono text-foreground/90 leading-snug">
              {taskTitle}
            </SheetTitle>
            <span className={`shrink-0 text-[10px] px-2 py-0.5 rounded-full border font-mono
              ${running
                ? "text-amber-400 border-amber-500/30 bg-amber-500/10"
                : "text-pm border-pm/30 bg-pm/10"}`}>
              {running ? "Generando..." : "Completado"}
            </span>
          </div>
        </SheetHeader>
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="font-mono text-xs text-foreground/80 bg-slate-900/50 rounded-lg
                          p-4 whitespace-pre-wrap leading-relaxed min-h-[200px]">
            {content || (
              <span className="text-muted-foreground/30">
                {running ? "Iniciando generación..." : "Sin contenido."}
              </span>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
```

**No new npm dependencies.** `Sheet`/`SheetContent`/`SheetHeader`/`SheetTitle` are already in `components/ui/sheet.tsx` (Shadcn). `Eye` and `PlayCircle` are already in Lucide.

### 3. `pm/page.tsx` changes

**New state (add after existing declarations):**
```typescript
const artefactConsole = useAgentConsole();
const [artefactTarget, setArtefactTarget] = useState<{ id: string; titulo: string } | null>(null);
const [artefactos, setArtefactos] = useState<Record<string, string>>({});
```

**Mount hydration** — extend existing `useEffect([], [])` fetch `.then()`:
```typescript
if (data.artefactos_generados) {
  setArtefactos(data.artefactos_generados as Record<string, string>);
}
```

**Post-stream hydration** — new `useEffect`:
```typescript
useEffect(() => {
  if (artefactConsole.running || !artefactTarget) return;
  const content = artefactConsole.logs.join("");
  if (content) {
    setArtefactos((prev) => ({ ...prev, [artefactTarget.id]: content }));
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [artefactConsole.running]);
```

**Resolved content:**
```typescript
const artefactContent =
  artefactConsole.logs.join("") ||
  (artefactTarget ? artefactos[artefactTarget.id] ?? "" : "");
```

**Play/Eye button on DONE cards** (inside `col.map`, after `PRIORIDAD_BADGE` span):
```tsx
{tarea.estado === "DONE" && (
  <button
    onClick={(e) => {
      e.stopPropagation();
      setArtefactTarget({ id: tarea.id, titulo: tarea.titulo });
      if (!artefactos[tarea.id]) {
        artefactConsole.invoke("pm-generate-artefact", {
          ...agentParams,
          task_id: tarea.id,
          task_title: tarea.titulo,
        });
      }
    }}
    disabled={patchingTaskIds.has(tarea.id)}
    className="ml-auto text-muted-foreground/30 hover:text-pm transition-colors"
    title={artefactos[tarea.id] ? "Ver artefacto" : "Generar documento"}
  >
    {artefactos[tarea.id]
      ? <Eye size={11} />
      : <PlayCircle size={11} />}
  </button>
)}
```

**ArtefactViewer mount** (at bottom of JSX, alongside `<CEOShield>` and `<AgentConsole>`):
```tsx
<ArtefactViewer
  open={artefactTarget !== null}
  onOpenChange={(v) => { if (!v) setArtefactTarget(null); }}
  taskTitle={artefactTarget?.titulo ?? ""}
  running={artefactConsole.running}
  content={artefactContent}
/>
```

---

## Data Flow Summary

```
Mount
  └─ GET /session/state
      ├─ tasks             → setLocalTasks
      ├─ last_tarjeta      → setTarjeta
      └─ artefactos_generados → setArtefactos

DONE card — artefact NOT in state
  ├─ Eye absent, Play icon shown
  └─ Play click
      ├─ setArtefactTarget({id, titulo})
      ├─ artefactConsole.invoke("pm-generate-artefact", {...})
      ├─ SSE chunks → artefactConsole.logs[] → Sheet streams live
      ├─ SSE done → artefactConsole.running = false
      ├─ useEffect → setArtefactos(prev + {id: content})
      └─ backend: aupdate_state({artefactos_generados: merged})

DONE card — artefact IN state
  ├─ Play absent, Eye icon shown
  └─ Eye click
      ├─ setArtefactTarget({id, titulo}) only — NO invoke
      └─ artefactContent = artefactos[id] → Sheet opens instantly
```

---

## Constraints

- No new npm dependencies.
- No file I/O — artefact content lives entirely in LangGraph state (SQLite checkpointer).
- `buscar_contexto_marca`'s underlying `query_brand` called directly as Python function — not via agent tool dispatch.
- Markdown rendered as `whitespace-pre-wrap` in `font-mono` — no `react-markdown`.
- ArtefactViewer Sheet cannot be dismissed (click-outside blocked) while `running === true`.
- `_sse_artefact_stream` persistence failure (step 4) is non-fatal — user already received the stream; a console warning is acceptable.
- The `artefact_console` in `pm/page.tsx` does NOT feed the `<AgentConsole>` terminal — that component stays wired to `agentConsole` only.

---

## Execution Plan

**Subagent-driven (5 tasks):**

| Task | Scope | Files |
|---|---|---|
| Task 1 | Backend state + tests | `estado.py`, `test_artefact_generation.py` |
| Task 2 | `_sse_artefact_stream` + dispatch + tests | `v1_router.py`, `test_artefact_generation.py` |
| Task 3 | `get_session_state` extension + tests | `v1_router.py`, `test_artefact_generation.py` |
| Task 4 | Frontend — `AgentParams` + `ArtefactViewer.tsx` | `useAgentConsole.ts`, new component |
| Task 5 | Frontend — `pm/page.tsx` wiring + E2E smoke | `pm/page.tsx` |
