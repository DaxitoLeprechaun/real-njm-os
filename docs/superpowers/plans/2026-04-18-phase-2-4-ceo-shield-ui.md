# Phase 2.4 — CEO Shield UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing `CEOShield` component to the `BLOQUEO_CEO` SSE event so the CEO sees a blocking approval dialog with Approve/Reject actions that resume or cancel the LangGraph execution.

**Architecture:** Three surgical file edits — no new files, no new abstractions. `CEOShield` gets a `submitting` prop to disable buttons during network I/O. `AgentConsole` gets an optional `exitMessage` prop to show "SESIÓN CERRADA — RECHAZADA POR CEO" instead of the generic footer. `ceo/page.tsx` gets the wiring: state, handlers, and CEOShield render. `useAgentConsole.ts` is complete — zero changes there.

**Tech Stack:** Next.js 14 App Router, React 18, TypeScript strict, `@base-ui/react` Dialog (portal-based, auto z-index above AgentConsole), Sonner toasts.

---

## File Map

| File | Change type | What changes |
|---|---|---|
| `frontend/components/njm/CEOShield.tsx` | Modify | Add `submitting?: boolean` prop; disable + dim buttons when true |
| `frontend/components/njm/AgentConsole.tsx` | Modify | Add `exitMessage?: string` prop; render it (rose-600, bold) instead of generic footer |
| `frontend/app/brand/[id]/ceo/page.tsx` | Modify | Import CEOShield; add `submitting` + `terminalExitMessage` state; add concurrency useEffect; add `handleApprove`/`handleReject`; render `<CEOShield>` |

---

## Task 1: Add `submitting` prop to `CEOShield`

**Files:**
- Modify: `frontend/components/njm/CEOShield.tsx`

> **Context:** CEOShield is a brutalist rose-600 Dialog. Both action buttons (`APROBAR ASUMIENDO RIESGO` and `RECHAZAR Y RE-PLANIFICAR`) must be disabled when the parent page is awaiting a network response. No loading spinners — just opacity + `disabled` attribute.

- [ ] **Step 1: Read the current file**

```bash
cat frontend/components/njm/CEOShield.tsx
```

Verify the `CEOShieldProps` interface and both button elements before editing.

- [ ] **Step 2: Add `submitting` to `CEOShieldProps`**

In `frontend/components/njm/CEOShield.tsx`, find:

```ts
export interface CEOShieldProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  riskMessage?: string;
  onApprove?: () => void;
  onReject?: () => void;
}
```

Replace with:

```ts
export interface CEOShieldProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  riskMessage?: string;
  onApprove?: () => void;
  onReject?: () => void;
  submitting?: boolean;
}
```

- [ ] **Step 3: Destructure `submitting` in the component**

Find:

```ts
export default function CEOShield({
  open,
  onOpenChange,
  riskMessage = "El presupuesto propuesto excede el límite del Vector 5.",
  onApprove,
  onReject,
}: CEOShieldProps) {
```

Replace with:

```ts
export default function CEOShield({
  open,
  onOpenChange,
  riskMessage = "El presupuesto propuesto excede el límite del Vector 5.",
  onApprove,
  onReject,
  submitting = false,
}: CEOShieldProps) {
```

- [ ] **Step 4: Disable the APPROVE button when submitting**

Find the approve button (the one with `onClick={handleApprove}`):

```tsx
<button
  onClick={handleApprove}
  className="flex-1 px-4 py-2.5 rounded-lg text-sm font-bold uppercase tracking-widest transition-all duration-150 active:scale-[0.97]"
  style={{
    background: "transparent",
    border: "1.5px solid rgb(225 29 72)",
    color: "rgb(251 113 133)", // rose-400
  }}
  onMouseEnter={(e) => {
    (e.currentTarget as HTMLButtonElement).style.background =
      "rgb(225 29 72 / 0.15)";
  }}
  onMouseLeave={(e) => {
    (e.currentTarget as HTMLButtonElement).style.background =
      "transparent";
  }}
>
  APROBAR ASUMIENDO RIESGO
</button>
```

Replace with:

```tsx
<button
  onClick={handleApprove}
  disabled={submitting}
  className="flex-1 px-4 py-2.5 rounded-lg text-sm font-bold uppercase tracking-widest transition-all duration-150 active:scale-[0.97] disabled:opacity-40 disabled:cursor-not-allowed"
  style={{
    background: "transparent",
    border: "1.5px solid rgb(225 29 72)",
    color: "rgb(251 113 133)", // rose-400
  }}
  onMouseEnter={(e) => {
    if (!submitting)
      (e.currentTarget as HTMLButtonElement).style.background =
        "rgb(225 29 72 / 0.15)";
  }}
  onMouseLeave={(e) => {
    (e.currentTarget as HTMLButtonElement).style.background =
      "transparent";
  }}
>
  {submitting ? "PROCESANDO..." : "APROBAR ASUMIENDO RIESGO"}
</button>
```

- [ ] **Step 5: Disable the REJECT button when submitting**

Find the reject button (the one with `onClick={handleReject}`):

```tsx
<button
  onClick={handleReject}
  className="flex-1 px-4 py-2.5 rounded-lg text-sm font-bold uppercase tracking-widest bg-slate-100 text-slate-900 hover:bg-white transition-all duration-150 active:scale-[0.97]"
>
  RECHAZAR Y RE-PLANIFICAR
</button>
```

Replace with:

```tsx
<button
  onClick={handleReject}
  disabled={submitting}
  className="flex-1 px-4 py-2.5 rounded-lg text-sm font-bold uppercase tracking-widest bg-slate-100 text-slate-900 hover:bg-white transition-all duration-150 active:scale-[0.97] disabled:opacity-40 disabled:cursor-not-allowed"
>
  RECHAZAR Y RE-PLANIFICAR
</button>
```

- [ ] **Step 6: Type-check**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit
```

Expected: zero errors. If you see `Property 'submitting' does not exist`, verify Step 2 was saved correctly.

- [ ] **Step 7: Commit**

```bash
git add frontend/components/njm/CEOShield.tsx
git commit -m "feat: add submitting prop to CEOShield — disable buttons during network I/O"
```

---

## Task 2: Add `exitMessage` prop to `AgentConsole`

**Files:**
- Modify: `frontend/components/njm/AgentConsole.tsx`

> **Context:** After a CEO rejection, the `ceo-reject` SSE sequence ends with `running=false`. The current footer reads "Process exited with code 0" in muted slate. We need to swap that for "SESIÓN CERRADA — RECHAZADA POR CEO" in rose-600 to create the "silent witness" visual state the user specified.

- [ ] **Step 1: Read the current file**

```bash
cat frontend/components/njm/AgentConsole.tsx
```

Confirm the `AgentConsoleProps` interface and the `!running && logs.length > 0` footer block.

- [ ] **Step 2: Add `exitMessage` to `AgentConsoleProps`**

Find:

```ts
export interface AgentConsoleProps {
  open: boolean;
  onClose: () => void;
  agentLabel: string;
  logs: string[];
  /** When true the simulation is still running (shows blinking cursor) */
  running: boolean;
}
```

Replace with:

```ts
export interface AgentConsoleProps {
  open: boolean;
  onClose: () => void;
  agentLabel: string;
  logs: string[];
  running: boolean;
  exitMessage?: string;
}
```

- [ ] **Step 3: Destructure `exitMessage` in the component**

Find:

```ts
export default function AgentConsole({
  open,
  onClose,
  agentLabel,
  logs,
  running,
}: AgentConsoleProps) {
```

Replace with:

```ts
export default function AgentConsole({
  open,
  onClose,
  agentLabel,
  logs,
  running,
  exitMessage,
}: AgentConsoleProps) {
```

- [ ] **Step 4: Update the footer to use `exitMessage`**

Find:

```tsx
{!running && logs.length > 0 && (
  <div
    className="text-xs font-mono text-slate-600 mt-2 pt-2"
    style={{
      fontFamily: "'Fira Code', monospace",
      borderTop: "1px solid rgb(30 41 59)",
    }}
  >
    Process exited with code 0
  </div>
)}
```

Replace with:

```tsx
{!running && logs.length > 0 && (
  <div
    className={`text-xs font-mono mt-2 pt-2 ${
      exitMessage
        ? "text-rose-600 font-semibold tracking-wide"
        : "text-slate-600"
    }`}
    style={{
      fontFamily: "'Fira Code', monospace",
      borderTop: "1px solid rgb(30 41 59)",
    }}
  >
    {exitMessage ?? "Process exited with code 0"}
  </div>
)}
```

- [ ] **Step 5: Type-check**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/njm/AgentConsole.tsx
git commit -m "feat: add exitMessage prop to AgentConsole — shows rejection status in terminal footer"
```

---

## Task 3: Wire CEOShield into `ceo/page.tsx`

**Files:**
- Modify: `frontend/app/brand/[id]/ceo/page.tsx`

> **Context:** This is the main wiring task. Surgeon approach: insert new lines; do not restructure existing code. The file already has `useRef`, `useState`, `useEffect` imported from React and `agentConsole` from `useAgentConsole`. `sessionIdRef` is already initialized with `crypto.randomUUID()` fallback. No imports will be removed.

- [ ] **Step 1: Read the current file**

```bash
cat "frontend/app/brand/[id]/ceo/page.tsx"
```

Confirm line numbers for: the import block, the existing `useState` declarations, and the `<AgentConsole>` render.

- [ ] **Step 2: Add CEOShield import**

Find the import block at the top. After:

```ts
import { useAgentConsole } from "@/hooks/useAgentConsole";
```

Add:

```ts
import CEOShield from "@/components/njm/CEOShield";
```

- [ ] **Step 3: Add `submitting` and `terminalExitMessage` state**

In the component body, after the existing state declarations (after `const fileInputRef = useRef...`), add these two lines:

```ts
const [submitting, setSubmitting] = useState(false);
const [terminalExitMessage, setTerminalExitMessage] = useState<string | undefined>(undefined);
```

- [ ] **Step 4: Add concurrency lock useEffect**

After the two new state lines, add:

```ts
useEffect(() => {
  if (agentConsole.logs.length > 0) {
    setSubmitting(false);
  }
}, [agentConsole.logs.length]);
```

> **Why:** This releases the `submitting` lock the moment the first SSE log arrives after resume — not when the network promise resolves. This is "Optimistic UI Inversion": the stream arriving is the real proof the agent restarted.

- [ ] **Step 5: Add `shieldOpen` derived value**

After the `useEffect`, add:

```ts
const shieldOpen =
  (agentConsole.actionRequired?.trigger === "BLOQUEO_CEO") ?? false;
```

- [ ] **Step 6: Add `handleApprove`**

After `shieldOpen`, add:

```ts
async function handleApprove() {
  setSubmitting(true);
  setTerminalExitMessage(undefined);
  try {
    await agentConsole.resume("APPROVED", {
      brand_id: params.id,
      session_id: sessionIdRef.current,
    });
    agentConsole.invoke("ceo-audit", {
      brand_id: params.id,
      session_id: sessionIdRef.current,
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Error desconocido";
    toast.error(`Error al aprobar: ${msg}`);
    setSubmitting(false);
  }
}
```

- [ ] **Step 7: Add `handleReject`**

Directly after `handleApprove`, add:

```ts
async function handleReject() {
  setSubmitting(true);
  setTerminalExitMessage("SESIÓN CERRADA — RECHAZADA POR CEO");
  try {
    await agentConsole.resume("REJECTED", {
      brand_id: params.id,
      session_id: sessionIdRef.current,
    });
    agentConsole.invoke("ceo-reject", {
      brand_id: params.id,
      session_id: sessionIdRef.current,
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Error desconocido";
    toast.error(`Error al rechazar: ${msg}`);
    setSubmitting(false);
  }
}
```

- [ ] **Step 8: Update `<AgentConsole>` render to pass `exitMessage`**

Find:

```tsx
<AgentConsole
  open={agentConsole.open}
  onClose={agentConsole.close}
  agentLabel="CEO Audit"
  logs={agentConsole.logs}
  running={agentConsole.running}
/>
```

Replace with:

```tsx
<AgentConsole
  open={agentConsole.open}
  onClose={agentConsole.close}
  agentLabel="CEO Audit"
  logs={agentConsole.logs}
  running={agentConsole.running}
  exitMessage={terminalExitMessage}
/>
```

- [ ] **Step 9: Render `<CEOShield>` after `<AgentConsole>`**

Find the closing `</div>` of the outermost `<div className="p-8 pb-28 relative">`. Just before it, add:

```tsx
<CEOShield
  open={shieldOpen}
  onOpenChange={() => {}}
  riskMessage={agentConsole.actionRequired?.risk_message}
  onApprove={handleApprove}
  onReject={handleReject}
  submitting={submitting}
/>
```

> **Note on `onOpenChange={() => {}`:** The shield is controlled entirely by `shieldOpen` (derived from `actionRequired`). Passing a no-op prevents Escape key from closing it mid-decision. It closes automatically when `invoke()` clears `actionRequired`.

- [ ] **Step 10: Type-check**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit
```

Expected: zero errors. Common failure: `Property 'exitMessage' does not exist on type 'AgentConsoleProps'` — means Task 2 wasn't saved.

- [ ] **Step 11: Commit**

```bash
git add "frontend/app/brand/[id]/ceo/page.tsx"
git commit -m "feat: wire CEOShield to BLOQUEO_CEO — approve/reject with concurrency lock"
```

---

## Task 4: Manual smoke test

> **No automated tests in this phase.** TypeScript is the safety net. This task verifies the golden path and both failure branches manually.

- [ ] **Step 1: Start dev server**

```bash
cd frontend && npm run dev
```

Navigate to `http://localhost:3000/brand/disrupt/ceo`.

- [ ] **Step 2: Verify baseline — no CEOShield on load**

Page loads. `CEOShield` is not visible. `AgentConsole` is closed. Floating "Invocar CEO" button is visible.

- [ ] **Step 3: Trigger CEO audit**

Click "Invocar CEO para Auditoría". `AgentConsole` opens, blinking cursor visible, logs streaming.

- [ ] **Step 4: Simulate BLOQUEO_CEO (backend required)**

If the real backend is running and emits `action_required` with trigger `BLOQUEO_CEO`, `CEOShield` should appear over the `AgentConsole`. Verify:
- Rose-600 border dialog is visible
- `risk_message` from the event is shown in the "Riesgo Detectado" block
- Both buttons are enabled (not gray, not "PROCESANDO...")

If backend is not running in this session: skip to Step 7 (reject path uses mock).

- [ ] **Step 5: Test approve path**

Click "APROBAR ASUMIENDO RIESGO". Verify:
- Both buttons immediately change to "PROCESANDO..." and dim (disabled)
- `CEOShield` stays open until first SSE log arrives
- Once logs start: `CEOShield` closes, `AgentConsole` shows new streaming logs
- No toast errors

- [ ] **Step 6: Test reject path**

Invoke CEO audit again (wait for `BLOQUEO_CEO`). Click "RECHAZAR Y RE-PLANIFICAR". Verify:
- Buttons disable immediately
- `CEOShield` closes when `ceo-reject` SSE starts
- Terminal shows `[!]`-prefixed logs in rose-400
- Terminal footer reads **"SESIÓN CERRADA — RECHAZADA POR CEO"** in rose-600 bold
- No toast errors

- [ ] **Step 7: Test error path (network failure)**

Stop the backend. Click either action button. Verify:
- `toast.error(...)` appears with the error message
- `submitting` resets to false (buttons re-enable)
- `CEOShield` stays open (shield not closed on error)

- [ ] **Step 8: Test double-click protection**

Click "APROBAR ASUMIENDO RIESGO" twice quickly. Verify only one POST is sent (second click is a no-op — button is `disabled`).

---

## Self-Review

**Spec coverage:**
- ✅ Hook unchanged — no edits to `useAgentConsole.ts`
- ✅ `submitting` state with concurrency lock via `useEffect` on `logs.length`
- ✅ `handleApprove` → `resume("APPROVED")` → `invoke("ceo-audit")`
- ✅ `handleReject` → `resume("REJECTED")` → `invoke("ceo-reject")`
- ✅ `shieldOpen` derived from `actionRequired.trigger === "BLOQUEO_CEO"`
- ✅ CEOShield buttons disabled when `submitting=true`
- ✅ Terminal footer shows "SESIÓN CERRADA — RECHAZADA POR CEO" after reject
- ✅ Error handling: `toast.error` + `setSubmitting(false)` on throw
- ✅ `sessionIdRef.current` already initialized with UUID fallback — never undefined
- ✅ Z-index: Dialog portal handles stacking automatically
- ✅ `onOpenChange={() => {}}` prevents Escape-close during decision

**Placeholder scan:** None found — all code blocks are complete.

**Type consistency:**
- `submitting: boolean` defined in Task 1, consumed in Task 3 Step 9 ✅
- `exitMessage?: string` defined in Task 2, consumed in Task 3 Step 8 ✅
- `ActionRequiredEvent.trigger` narrowed to `"BLOQUEO_CEO"` in `shieldOpen` derivation ✅
- `resume(answers: string, params: AgentParams)` — "APPROVED"/"REJECTED" match `string` ✅
