# Phase 2.5 — PM Real Streaming & Kanban Connection

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the PM Workspace "Consultar PM" button to the real LangGraph pipeline, display `payload_tarjeta_sugerencia` as a live artefact card, and replace the disconnected CEOShield state with `useAgentConsole.actionRequired`.

**Architecture:** The PM page calls `agentConsole.invoke("ceo-audit", {brand_id, session_id})` — for the `disrupt` brand this skips the CEO node (audit_status=COMPLETE guard) and runs PM directly. After the SSE stream closes (`running → false`, no `actionRequired`), the page fetches `GET /api/v1/session/state` to pull `last_tarjeta` (the `TarjetaSugerenciaUI` JSON) and renders it as a live card above the static mock artefacts. The CEOShield is wired to `agentConsole.actionRequired` instead of a local `shieldOpen` boolean, using the Optimistic UI Inversion submitting lock pattern already established in the CEO page.

**Tech Stack:** Next.js 14 App Router, React hooks, `useAgentConsole` (complete — do not modify), FastAPI `GET /api/v1/session/state` endpoint (already built).

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Modify | `backend/api/v1_router.py` | Remove stale Phase 2.4 test comment around `_TEST_BLOQUEO_CEO` |
| Modify | `frontend/app/brand/[id]/pm/page.tsx` | All Phase 2.5 logic lives here — wire real SSE, fetch tarjeta, fix CEOShield |

---

## Task 1: Clean up `_TEST_BLOQUEO_CEO` comment in backend

Phase 2.4 is complete. The flag is already `False` but the surrounding comment still references "once Phase 2.4 testing is done." Remove the stale comment so the file is clean.

**Files:**
- Modify: `backend/api/v1_router.py:124-127`

- [ ] **Step 1: Edit the comment block**

In `backend/api/v1_router.py`, replace lines 124–127:

```python
# ── Dev testing toggle ────────────────────────────────────────────
# Set True to short-circuit ceo-audit with a BLOQUEO_CEO mock sequence.
# Flip back to False (or delete) once Phase 2.4 frontend testing is done.
_TEST_BLOQUEO_CEO = False
```

With:

```python
# Set True to short-circuit ceo-audit with a hardcoded BLOQUEO_CEO sequence
# for frontend testing without a live OpenAI key.
_TEST_BLOQUEO_CEO = False
```

- [ ] **Step 2: Verify no change to runtime behavior**

```bash
cd backend && grep "_TEST_BLOQUEO_CEO" api/v1_router.py
```

Expected: exactly two lines — the comment line and the assignment `_TEST_BLOQUEO_CEO = False`.

- [ ] **Step 3: Commit**

```bash
git add backend/api/v1_router.py
git commit -m "chore: remove stale Phase 2.4 test comment from _TEST_BLOQUEO_CEO"
```

---

## Task 2: Wire "Consultar PM" to real graph SSE

Replace the old `handleConsultarPM` (which calls the deprecated `POST /api/ejecutar-tarea` endpoint and mocks `pm-execution`) with `agentConsole.invoke("ceo-audit", ...)`. Remove the now-unused `executing`, `threadId`, `shieldOpen`, and `shieldMessage` states.

**Files:**
- Modify: `frontend/app/brand/[id]/pm/page.tsx`

- [ ] **Step 1: Add SESSION_ID constant and TarjetaResultado type**

At the top of `frontend/app/brand/[id]/pm/page.tsx`, after the `API_URL` line and before the `Artefacto` interface, add:

```typescript
const SESSION_ID = "dev-session-1";

interface TarjetaResultado {
  id_transaccion: string;
  estado_ejecucion: "LISTO_PARA_FIRMA" | "BLOQUEO_CEO";
  metadata: {
    skill_utilizada: string;
    timestamp_generacion: string;
  };
  contenido_tarjeta: {
    propuesta_principal: string;
    framework_metodologico: string;
    check_coherencia_adn: { aprobado: boolean; justificacion: string };
    archivos_locales_cowork: Array<{ nombre_archivo: string; ruta_absoluta: string }>;
    log_errores_escalamiento: string[];
  };
}
```

- [ ] **Step 2: Replace state declarations in the component**

In `PMWorkspacePage`, replace the existing state declarations:

```typescript
const [activeArtefacto, setActiveArtefacto] = useState<Artefacto | null>(null);
const [shieldOpen, setShieldOpen] = useState(false);
const [shieldMessage, setShieldMessage] = useState("");
const [threadId, setThreadId] = useState<string | null>(null);
const [executing, setExecuting] = useState(false);

const agentConsole = useAgentConsole();
```

With:

```typescript
const [activeArtefacto, setActiveArtefacto] = useState<Artefacto | null>(null);
const [tarjeta, setTarjeta] = useState<TarjetaResultado | null>(null);
const [submitting, setSubmitting] = useState(false);
const [terminalExitMessage, setTerminalExitMessage] = useState<string | null>(null);
const prevRunningRef = useRef(false);

const agentConsole = useAgentConsole();

const agentParams = { brand_id: params.id, session_id: SESSION_ID };
const shieldOpen = agentConsole.actionRequired?.trigger === "BLOQUEO_CEO";
const shieldMessage =
  agentConsole.actionRequired?.risk_message ??
  "El PM detectó un riesgo que requiere revisión del CEO.";
```

- [ ] **Step 3: Add `useRef` to imports**

At the top of the file, update the React import:

```typescript
import { useEffect, useRef, useState } from "react";
```

- [ ] **Step 4: Replace `handleConsultarPM`**

Replace the entire `handleConsultarPM` function:

```typescript
async function handleConsultarPM() {
  setExecuting(true);
  agentConsole.invoke("pm-execution");
  try {
    const res = await fetch(`${API_URL}/api/ejecutar-tarea`, {
      // ... old body
    });
    const data = await res.json();
    if (data.thread_id) setThreadId(data.thread_id);
    if (data.estado_ejecucion === "BLOQUEO_CEO") {
      const msg =
        data.contenido_tarjeta?.check_coherencia_adn?.justificacion ||
        data.contenido_tarjeta?.log_errores_escalamiento?.[0] ||
        "El CEO bloqueó la ejecución por riesgo estratégico.";
      setShieldMessage(msg);
      setShieldOpen(true);
    } else if (!res.ok) {
      toast.error("Error al consultar el PM");
    }
  } catch {
    toast.error("No se pudo conectar con el backend");
  } finally {
    setExecuting(false);
  }
}
```

With:

```typescript
function handleConsultarPM() {
  setTarjeta(null);
  setTerminalExitMessage(null);
  agentConsole.invoke("ceo-audit", agentParams);
}
```

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit 2>&1 | head -40
```

Expected: zero errors related to `pm/page.tsx`. If `useEffect` is unused (added in next task), ignore that for now.

---

## Task 3: Fetch session state after stream completes

When the SSE stream finishes normally (no `actionRequired`), call `GET /api/v1/session/state` and store `last_tarjeta` in component state. Uses a `prevRunningRef` to detect the `running: true → false` transition without firing on mount.

**Files:**
- Modify: `frontend/app/brand/[id]/pm/page.tsx`

- [ ] **Step 1: Add session-state fetch effect**

Inside `PMWorkspacePage`, after the state declarations, add:

```typescript
useEffect(() => {
  if (prevRunningRef.current && !agentConsole.running && !agentConsole.actionRequired) {
    fetch(
      `${API_URL}/api/v1/session/state?brand_id=${params.id}&session_id=${SESSION_ID}`
    )
      .then((r) => r.json())
      .then((data) => {
        if (data.last_tarjeta) setTarjeta(data.last_tarjeta as TarjetaResultado);
      })
      .catch(() => {});
  }
  prevRunningRef.current = agentConsole.running;
}, [agentConsole.running, agentConsole.actionRequired, params.id]);
```

- [ ] **Step 2: Add submitting lock release effect**

Immediately after the fetch effect, add:

```typescript
useEffect(() => {
  if (agentConsole.logs.length > 0) setSubmitting(false);
}, [agentConsole.logs.length]);
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit 2>&1 | head -40
```

Expected: zero errors.

---

## Task 4: Render real `TarjetaResultado` card

Display the live PM output above the mock artefacts grid. Color-coded by `estado_ejecucion`. Clicking opens the SlideOver with the full proposal and framework details.

**Files:**
- Modify: `frontend/app/brand/[id]/pm/page.tsx`

- [ ] **Step 1: Add tarjeta artefact click handler**

Inside `PMWorkspacePage`, add a helper to convert a `TarjetaResultado` into an `Artefacto` for the SlideOver:

```typescript
function tarjetaToArtefacto(t: TarjetaResultado): Artefacto {
  const date = new Date(t.metadata.timestamp_generacion).toLocaleDateString("es-MX");
  const files =
    t.contenido_tarjeta.archivos_locales_cowork
      .map((f) => `- ${f.nombre_archivo}`)
      .join("\n") || "— sin archivos adjuntos —";
  const errors =
    t.contenido_tarjeta.log_errores_escalamiento.length
      ? "\n\n## Errores de escalamiento\n" +
        t.contenido_tarjeta.log_errores_escalamiento.map((e) => `- ${e}`).join("\n")
      : "";
  return {
    id: t.id_transaccion,
    titulo: t.contenido_tarjeta.propuesta_principal,
    framework: t.contenido_tarjeta.framework_metodologico,
    tipo: t.estado_ejecucion === "LISTO_PARA_FIRMA" ? "Resultado PM" : "Bloqueado CEO",
    fecha: date,
    contenidoMd:
      `# ${t.contenido_tarjeta.propuesta_principal}\n\n` +
      `**Framework:** ${t.contenido_tarjeta.framework_metodologico}\n\n` +
      `**Coherencia ADN:** ${t.contenido_tarjeta.check_coherencia_adn.aprobado ? "✓" : "✗"} ${t.contenido_tarjeta.check_coherencia_adn.justificacion}\n\n` +
      `## Archivos entregables\n${files}` +
      errors,
  };
}
```

- [ ] **Step 2: Add tarjeta card to JSX**

In the JSX, between the `{/* Header */}` block and `{/* Artifacts Grid */}`, insert:

```tsx
{/* Live PM Result Card */}
{tarjeta && (
  <div className="mb-8">
    <p className="text-xs uppercase tracking-widest mb-3 font-semibold text-muted-foreground">
      Resultado PM
    </p>
    <button
      onClick={() => setActiveArtefacto(tarjetaToArtefacto(tarjeta))}
      className="w-full glass rounded-xl p-5 text-left group hover:scale-[1.01] active:scale-[0.99] transition-all duration-150 cursor-pointer relative overflow-hidden"
    >
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{
          background:
            tarjeta.estado_ejecucion === "LISTO_PARA_FIRMA"
              ? "hsl(var(--pm-accent))"
              : "rgb(225 29 72)",
        }}
      />
      <span
        className="inline-block text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded-full mb-3"
        style={{
          color:
            tarjeta.estado_ejecucion === "LISTO_PARA_FIRMA"
              ? "hsl(var(--pm-accent))"
              : "rgb(251 113 133)",
          background:
            tarjeta.estado_ejecucion === "LISTO_PARA_FIRMA"
              ? "hsl(var(--pm-accent) / 0.12)"
              : "rgb(225 29 72 / 0.12)",
        }}
      >
        {tarjeta.estado_ejecucion === "LISTO_PARA_FIRMA" ? "Listo para firma" : "Bloqueado CEO"}
      </span>
      <h3 className="font-semibold text-foreground text-sm leading-snug">
        {tarjeta.contenido_tarjeta.propuesta_principal}
      </h3>
      <div className="grid grid-rows-[0fr] group-hover:grid-rows-[1fr] transition-all duration-300 ease-out">
        <div className="overflow-hidden">
          <div className="mt-3 pt-3 border-t border-white/[0.06]">
            <p className="text-xs text-muted-foreground">
              <span className="text-muted-foreground/60">Framework:</span>{" "}
              {tarjeta.contenido_tarjeta.framework_metodologico}
            </p>
            <p className="text-[11px] text-muted-foreground/40 mt-0.5">
              {tarjeta.metadata.skill_utilizada} ·{" "}
              {new Date(tarjeta.metadata.timestamp_generacion).toLocaleDateString("es-MX")}
            </p>
          </div>
        </div>
      </div>
      <p className="text-[10px] text-muted-foreground/30 mt-3 uppercase tracking-wider group-hover:opacity-0 transition-opacity duration-200">
        {tarjeta.contenido_tarjeta.framework_metodologico}
      </p>
    </button>
  </div>
)}
```

- [ ] **Step 3: Update artefacts count in header**

Replace:

```tsx
<p className="text-muted-foreground mt-1 text-sm">
  {MOCK_ARTEFACTOS.length} artefactos generados
</p>
```

With:

```tsx
<p className="text-muted-foreground mt-1 text-sm">
  {MOCK_ARTEFACTOS.length + (tarjeta ? 1 : 0)} artefactos generados
</p>
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit 2>&1 | head -40
```

Expected: zero errors.

---

## Task 5: Wire CEOShield to `agentConsole.actionRequired`

Replace the disconnected local `shieldOpen`/`shieldMessage` booleans with `agentConsole.actionRequired`. The `shieldOpen` and `shieldMessage` derived values were already set up in Task 2 as computed values — now wire them into the CEOShield and add the approve/reject handlers with the submitting lock pattern.

**Files:**
- Modify: `frontend/app/brand/[id]/pm/page.tsx`

- [ ] **Step 1: Add approve and reject handlers**

Inside `PMWorkspacePage`, after the effects, add:

```typescript
async function handleApprove() {
  setSubmitting(true);
  try {
    await agentConsole.resume("APPROVED", agentParams);
    agentConsole.invoke("ceo-audit", agentParams);
  } catch {
    setSubmitting(false);
    toast.error("No se pudo aprobar la decisión");
  }
}

async function handleReject() {
  setSubmitting(true);
  setTerminalExitMessage(null);
  try {
    await agentConsole.resume("REJECTED", agentParams);
    agentConsole.invoke("ceo-reject", agentParams);
    setTerminalExitMessage("CEO bloqueó el entregable. PM notificado para reformulación.");
  } catch {
    setSubmitting(false);
    setTerminalExitMessage(null);
    toast.error("No se pudo registrar el rechazo");
  }
}
```

- [ ] **Step 2: Replace the CEOShield JSX**

Find the `{/* CEO Shield Modal */}` block and replace it entirely:

```tsx
{/* CEO Shield Modal */}
<CEOShield
  open={shieldOpen}
  onOpenChange={() => {}}
  riskMessage={shieldMessage}
  submitting={submitting}
  onApprove={handleApprove}
  onReject={handleReject}
/>
```

- [ ] **Step 3: Remove the "Simular Bloqueo CEO" dev button**

Remove the entire `{/* Simulate CEO Block button */}` div from the JSX (lines ~317–331 in the original file):

```tsx
{/* Simulate CEO Block button — dev/test helper */}
<div className="mt-8 flex justify-center">
  <button
    onClick={() => setShieldOpen(true)}
    ...
  >
    <span aria-hidden>🛡</span>
    Simular Bloqueo CEO
  </button>
</div>
```

This button is replaced by real SSE detection via `agentConsole.actionRequired`.

- [ ] **Step 4: Update AgentConsole to show exitMessage**

Replace the `{/* Agent Console */}` block:

```tsx
{/* Agent Console */}
<AgentConsole
  open={agentConsole.open}
  onClose={agentConsole.close}
  agentLabel="PM Agent"
  logs={agentConsole.logs}
  running={agentConsole.running}
/>
```

With:

```tsx
{/* Agent Console */}
<AgentConsole
  open={agentConsole.open}
  onClose={agentConsole.close}
  agentLabel="PM Agent"
  logs={agentConsole.logs}
  running={agentConsole.running}
  exitMessage={terminalExitMessage ?? undefined}
/>
```

- [ ] **Step 5: Update the floating CTA button**

Replace the `disabled={executing}` logic:

```tsx
<button
  onClick={handleConsultarPM}
  disabled={executing}
  ...
>
```

With:

```tsx
<button
  onClick={handleConsultarPM}
  disabled={agentConsole.running}
  ...
>
```

- [ ] **Step 6: Verify TypeScript compiles**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit 2>&1 | head -40
```

Expected: zero errors.

---

## Task 6: Integration smoke test and commit

Verify the full flow works end-to-end without a live OpenAI key using the dev fixtures, then commit.

**Files:** none (test only, then commit)

- [ ] **Step 1: Start the backend**

```bash
cd backend && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Leave running in background.

- [ ] **Step 2: Start the frontend**

```bash
cd frontend && npm run dev
```

Leave running in background.

- [ ] **Step 3: Verify SSE stream for ceo-audit reaches PM node**

```bash
curl -N "http://localhost:8000/api/v1/agent/stream?sequenceId=ceo-audit&brand_id=disrupt&session_id=dev-session-1" 2>/dev/null | head -30
```

Expected output (JSON lines):
```
data: {"type": "log", "text": "[⏳] Conectando con NJM OS (brand: disrupt)..."}
data: {"type": "log", "text": "[⏳] Agente PM ejecutando skill seleccionada..."}
...
data: {"type": "done"}
```

If the stream hangs without PM logs, check that `audit_status="COMPLETE"` is set in the `disrupt` initial_state path in `_sse_njm_stream`.

- [ ] **Step 4: Verify session state endpoint returns last_tarjeta**

After the stream above completes:

```bash
curl "http://localhost:8000/api/v1/session/state?brand_id=disrupt&session_id=dev-session-1" | python3 -m json.tool | head -20
```

Expected: JSON with `"last_tarjeta": { "id_transaccion": "...", "estado_ejecucion": "LISTO_PARA_FIRMA", ... }`.

If `last_tarjeta` is `null`, check `output_node` in `agent/njm_graph.py` — the PM may have returned without populating `payload_tarjeta_sugerencia`.

- [ ] **Step 5: Open PM workspace in browser**

Navigate to `http://localhost:3000/brand/disrupt/pm`.

1. Click "Consultar PM / Ejecutar Táctica" — AgentConsole should open and stream real logs.
2. After stream closes, a "Resultado PM" card should appear above the mock artefacts.
3. Clicking the card should open the SlideOver with proposal details.

If no card appears, open browser DevTools → Network → look for `session/state` request → check its response.

- [ ] **Step 6: Commit all Phase 2.5 changes**

```bash
git add frontend/app/brand/\[id\]/pm/page.tsx
git commit -m "feat: wire PM workspace to real graph SSE — Phase 2.5

- Replace mock pm-execution with ceo-audit SSE stream
- Fetch payload_tarjeta_sugerencia from session state after stream done
- Render live TarjetaResultado card above static mock artefacts
- Wire CEOShield to agentConsole.actionRequired (eliminates local shieldOpen state)
- Add submitting lock + exitMessage on CEO rejection path
- Remove Simular Bloqueo CEO dev button (replaced by real SSE detection)"
```

---

## Self-Review

**Spec coverage:**
- ✅ Cleanup `_TEST_BLOQUEO_CEO` comment — Task 1
- ✅ Eliminate `pm-execution` mock — Task 2 (invoke `ceo-audit` instead)
- ✅ Connect "Consultar PM" to real graph — Task 2
- ✅ Display `payload_tarjeta_sugerencia` as artefact — Tasks 3 + 4
- ✅ Wire CEOShield to `actionRequired` — Task 5
- ✅ Submitting lock (Optimistic UI Inversion) — Task 5
- ✅ `exitMessage` on rejection — Task 5
- ✅ Integration smoke test — Task 6

**Placeholder scan:** None. All code blocks are complete and self-contained.

**Type consistency:**
- `TarjetaResultado` defined once in Task 2, used in Task 3 (effect), Task 4 (card render), Task 4 (tarjetaToArtefacto).
- `agentParams: { brand_id: string; session_id: string }` defined once in Task 2, used in Tasks 5 handlers.
- `SESSION_ID` constant used in Task 2 (agentParams), Task 3 (fetch URL). Consistent.
- `tarjetaToArtefacto` returns `Artefacto` — same shape as `MOCK_ARTEFACTOS` items. SlideOver accepts `Artefacto`. Consistent.
