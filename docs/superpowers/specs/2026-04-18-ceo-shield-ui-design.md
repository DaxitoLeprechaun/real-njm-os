# CEO Shield UI — Phase 2.4 Design Spec

**Date:** 2026-04-18  
**Phase:** 2.4 — CEO Shield Interface  
**Status:** Approved

---

## Problem

The backend SSE stream already emits `{"type": "action_required", "trigger": "BLOQUEO_CEO", "risk_message": "...", "session_id": "..."}` when the PM agent raises a strategic risk. The frontend ignores this event — `agentConsole.actionRequired` is set in the hook but never consumed by any page component.

---

## Scope

Wire the existing `CEOShield` component and `useAgentConsole` hook into `ceo/page.tsx`. No new abstractions. No backend changes. No test infrastructure (deferred to Phase 2.6).

**Out of scope:** GAP_DETECTED trigger handling, human_in_loop interview flow, PM workspace shield, test setup.

---

## Existing Pieces (no changes)

| File | Relevant state |
|---|---|
| `hooks/useAgentConsole.ts` | `actionRequired: ActionRequiredEvent \| null`, `resume(answers, params)`, `invoke(sequenceId, params)` |
| `components/njm/CEOShield.tsx` | `open`, `riskMessage`, `onApprove`, `onReject` props. Brutalist rose-600 Dialog. |
| `api/v1_router.py` | `POST /api/v1/agent/resume` accepts `{brand_id, session_id, answers: string}` |
| `GET /api/v1/agent/stream?sequenceId=ceo-reject` | Mock SSE sequence emitting `[!]`-prefixed log lines + `done` event |

---

## Data Flow

```
invoke("ceo-audit") → SSE stream
  → "action_required" event
  → hook: actionRequired set, running=false, stream closed

page detects actionRequired?.trigger === "BLOQUEO_CEO"
  → shieldOpen = true
  → CEOShield renders over everything (z-index > AgentConsole)

[APPROVE]
  setSubmitting(true)
  POST /resume {answers: "APPROVED"}
  invoke("ceo-audit", params)          ← re-opens real SSE, graph resumes from PM
  useEffect: logs.length > 0 → setSubmitting(false)
  actionRequired cleared by invoke()   ← shieldOpen becomes false

[REJECT]
  setSubmitting(true)
  POST /resume {answers: "REJECTED"}
  invoke("ceo-reject", params)         ← opens mock rejection SSE
  [!] logs appear in rose-400
  "done" event → running=false, terminal read-only
  actionRequired cleared by invoke()   ← shieldOpen becomes false
```

---

## Changes to `ceo/page.tsx`

### New imports
```ts
import CEOShield from "@/components/njm/CEOShield";
```

### New state
```ts
const [submitting, setSubmitting] = useState(false);
```

### Derived value (no new state)
```ts
const shieldOpen = agentConsole.actionRequired?.trigger === "BLOQUEO_CEO" ?? false;
```

### Concurrency lock release — useEffect
```ts
useEffect(() => {
  if (agentConsole.logs.length > 0) {
    setSubmitting(false);
  }
}, [agentConsole.logs.length]);
```

Technique: **Optimistic UI Inversion** — lock releases when reality (first SSE log) arrives, not when the network promise resolves. Prevents double-clicks and premature UI unlock before the agent stream begins.

### handleApprove
```ts
async function handleApprove() {
  setSubmitting(true);
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

### handleReject
```ts
async function handleReject() {
  setSubmitting(true);
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

### CEOShield render
Placed as the last element before the outer `</div>`, after AgentConsole. Uses `DialogContent` from `@base-ui/react` internally — renders in a portal by default, so z-index stacking is automatic and correct.

```tsx
<CEOShield
  open={shieldOpen}
  onOpenChange={() => {}} // non-closeable during submitting
  riskMessage={agentConsole.actionRequired?.risk_message}
  onApprove={handleApprove}
  onReject={handleReject}
/>
```

**Z-index note:** `CEOShield` uses `Dialog` from `components/ui/dialog` which renders in a portal (`document.body`). It stacks above `AgentConsole` (z-50) by default. No manual z-index override needed.

### `sessionIdRef` initialization
Already present in the page:
```ts
const sessionIdRef = useRef<string>(
  typeof crypto !== "undefined" ? crypto.randomUUID() : "dev-session-1"
);
```
Stable across renders. Never undefined — falls back to `"dev-session-1"` in SSR context.

---

## Visual Behavior

| State | CEOShield | AgentConsole | CTA Button |
|---|---|---|---|
| Running (ceo-audit) | hidden | open, blinking cursor | disabled |
| BLOQUEO_CEO received | **open** | open, static logs | visible |
| submitting=true | open, buttons disabled | — | — |
| Resume in progress | open (until first log) | opens, blinking | — |
| Post-approve | hidden | streaming PM logs | visible |
| Post-reject | hidden | `[!]` red logs, read-only | visible |

---

## Error Handling

| Failure | Behavior |
|---|---|
| `resume()` throws (network/backend) | `toast.error(...)`, `setSubmitting(false)`, shield stays open |
| `invoke()` stream error | Existing `es.onerror` appends `[!] Error de conexión`, sets `running=false` |
| Backend rejects `answers` value | Surface as `toast.error` via resume catch |

---

## TypeScript Contracts

`ActionRequiredEvent.trigger` is typed as `"BLOQUEO_CEO" | "GAP_DETECTED"` — narrowing to `BLOQUEO_CEO` before rendering shield prevents accidental firing on future triggers. `resume()` `answers` param is `string` — semantic values `"APPROVED"` / `"REJECTED"` are enforced by convention (consider narrowing to a union type in Phase 2.6).

---

## Not Addressed Here

- `GAP_DETECTED` trigger → DayCeroView wizard (Phase 2.3)
- Shield on PM workspace (Phase 2.5)
- Jest/RTL integration tests (Phase 2.6)
- `Last-Event-ID` SSE reconnect (Phase 2.6)
