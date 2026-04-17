# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Rules

1. Think before acting. Read existing files before writing code.
2. Be concise in output but thorough in reasoning.
3. Prefer editing over rewriting whole files.
4. Do not re-read files you have already read unless the file may have changed.
5. Test your code before declaring done.
6. No sycophantic openers or closing fluff.
7. Keep solutions simple and direct.
8. User instructions always override this file.

---

## Commands

### Run everything (recommended)
```bash
./start.sh          # Starts backend :8000 + frontend :3000 in parallel
```

### Backend (FastAPI + LangGraph)
```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # first time
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
**Venv gotcha:** The `.venv` shebang encodes the absolute path at creation time. If the repo was moved or cloned to a different path, the venv is broken. Fix: `python3 -m venv .venv --clear && .venv/bin/pip install -r requirements.txt`.

Use `.venv/bin/python3` (not `source .venv/bin/activate`) to avoid shell state issues. Always run from `backend/` so relative imports resolve correctly.

Requires `backend/.env` with `OPENAI_API_KEY=sk-...`

### Smoke test (verify graph compiles and agents load)
```bash
cd backend
.venv/bin/python3 -c "
import os; os.environ.setdefault('OPENAI_API_KEY','test')
from agent.njm_graph import njm_graph, ceo_graph
from agentes.agente_ceo import nodo_ceo
from agentes.agente_pm import nodo_pm
print([n for n in njm_graph.get_graph().nodes])
"
```

### Live smoke test (real API call — Phase 2.1 end-to-end)
```bash
cd backend && .venv/bin/python3 test_graph.py
```
Invokes `njm_graph` with `brand_id="disrupt"`, skips CEO (dev fallback), runs PM with gpt-4o, checks SQLite checkpoint. Allow 30–120 s.

### Frontend (Next.js)
```bash
cd frontend
npm install              # first time
npm run dev              # :3000
npm run build            # production build (also type-checks)
./node_modules/.bin/tsc --noEmit   # type-check only (run from frontend/)
```
Env: `frontend/.env.local` must have `NEXT_PUBLIC_API_URL=http://localhost:8000`

### API docs
```
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/health    # health check
```

---

## Architecture

NJM OS is a monorepo: FastAPI + LangGraph backend, Next.js 14 frontend.

- `ARCHITECTURE.md` — full product design source of truth (business logic, agent prompts, data schemas)
- `ARCHITECTURE_ROADMAP_PHASE2.md` — Phase 2 technical roadmap and audit. **Source of truth for what's built vs. pending.**

### Backend modules

| Module | Role |
|---|---|
| `main.py` | FastAPI app entry point — calls `load_dotenv()` first, then mounts both routers. `load_dotenv()` **must run before any agent module is imported** — agents instantiate `ChatOpenAI` at module level. |
| `api/main.py` | `POST /api/ejecutar-tarea` — invokes `njm_graph` (async via `asyncio.to_thread`). Resolves `brand_id`/`session_id` with dev fallback (see below). |
| `api/v1_router.py` | `POST /api/v1/ingest` (file upload placeholder) + `GET /api/v1/agent/stream` (SSE) |
| `agent/njm_graph.py` | **Single source of graphs.** Exports `njm_graph` (6-node full graph, `SqliteSaver` checkpointer on `njm_sessions.db`) and `ceo_graph` + `AgentState` (SSE streaming compat). `load_dotenv()` must precede import. |
| `agentes/agente_ceo.py` | `nodo_ceo` — CEO node with 5 tools, agentic loop (max 10 iters). Module-level singleton `_LLM = ChatOpenAI(model="gpt-4o", temperature=0)`. |
| `agentes/agente_pm.py` | `nodo_pm` — PM node with 14 skill tools, max 12 iters, max 2 autocorrection alerts. Module-level singleton `_LLM = ChatOpenAI(model="gpt-4o", temperature=0)`. |
| `core/estado.py` | `NJM_OS_State` TypedDict — 23-field unified LangGraph state. `NJM_PM_State` is an alias (deprecated). |
| `core/dev_fixtures.py` | `_LIBRO_VIVO_DISRUPT` mock + `DEV_BRAND_ID`/`DEV_SESSION_ID` constants. Only imported in dev fallback paths — never in production. |
| `core/schemas.py` | Pydantic v2: `LibroVivo` (9 vectors), `TarjetaSugerenciaUI`, `EstadoValidacion` enum |
| `tools/pm_skills.py` | 14 `@tool`-decorated PM skills (business case, Ansoff, PRD, etc.) |

### Graph topology (`njm_graph`) — Phase 2.1

```
START → ingest [STUB] → ceo_auditor → human_in_loop [STUB] → ceo_auditor (re-run)
                             ↓ COMPLETE
                       pm_execution → output → END
                             ↓ BLOQUEO_CEO
                        ceo_review [STUB] → output → END
```

Routing is driven by `audit_status` (set by CEO tools) and `estado_validacion` (set by PM):

| Condition | Route |
|---|---|
| `audit_status == "COMPLETE"` | `ceo_auditor → pm_execution` |
| `audit_status == "GAP_DETECTED"` | `ceo_auditor → human_in_loop` |
| `audit_status == "RISK_BLOCKED"` | `ceo_auditor → output` |
| `estado_validacion == "LISTO_PARA_FIRMA"` | `pm_execution → output` |
| `estado_validacion == "BLOQUEO_CEO"` | `pm_execution → ceo_review` |

**Stub nodes (Phase 2.1):**
- `ingest` — passthrough. Real ChromaDB ingestion in Phase 2.2.
- `human_in_loop` — auto-sets `audit_status="COMPLETE"` + injects `_LIBRO_VIVO_DISRUPT`. Real `interrupt()` in Phase 2.3.
- `ceo_review` — auto-sets `ceo_review_decision="REJECTED"` → routes to output. Real CEOShield in Phase 2.5.

**CEO skip guard:** `ceo_auditor_node` returns `{}` immediately if `state["audit_status"] == "COMPLETE"`, preventing redundant LLM calls after `human_in_loop` stub.

**Checkpointer:** `SqliteSaver` on `./njm_sessions.db`. `thread_id = f"{brand_id}:{session_id}"`. Pass `{"configurable": {"thread_id": thread_id}}` to every `invoke`/`astream_events` call.

**Dev fallback** (`api/main.py`): if `brand_id` is empty → `"disrupt"`, `session_id` empty → `"dev-session-1"`. When `brand_id == "disrupt"`, injects `_LIBRO_VIVO_DISRUPT` and sets `audit_status="COMPLETE"` so CEO is skipped and PM runs directly.

**CEO tools side-effects on state:**
- `escribir_libro_vivo` → `audit_status="COMPLETE"`, `libro_vivo={...}`
- `levantar_tarjeta_roja` → `audit_status="RISK_BLOCKED"`, `risk_flag=True`, `risk_details`
- `generar_reporte_brechas` → `audit_status="GAP_DETECTED"`, `gap_report_path`
- `iniciar_entrevista_profundidad` → `interview_questions=[...]`

**SSE endpoint (`GET /api/v1/agent/stream?sequenceId=...`):**
- `ceo-audit` → real LangGraph streaming via `astream_events(version="v2")`, filters `on_chat_model_stream`, uses `ceo_graph` from `njm_graph.py`
- `pm-execution`, `ceo-approve`, `ceo-reject` → hardcoded mock scripts with `asyncio.sleep` delays
- All sequences terminate with `data: [DONE]\n\n`
- OpenAI streaming returns `chunk.content` as `str` — `_extract_text()` normalizes to str (list fallback kept for safety)

**Models:** `gpt-4o-mini` (SSE `ceo_graph`), `gpt-4o` (both agent nodes). All `temperature=0`.

**`POST /api/v1/ingest` is a placeholder** — saves files to `backend/temp_uploads/` but does not extract text, embed, or connect to `escanear_directorio_onboarding` (which reads from `~/NJM_OS/`). Phase 2.2 work.

**Data contract flow:**
```
NJM_OS_State.libro_vivo (9 vectors, CEO-validated JSON)
  → nodo_pm reads libro_vivo to build dynamic system prompt
  → PM agentic loop with 14 skills
  → payload_tarjeta_sugerencia (TarjetaSugerenciaUI JSON → Next.js)
```

**`TarjetaSugerenciaUI` states:**
- `LISTO_PARA_FIRMA` → green card, file attachments, approve button
- `BLOQUEO_CEO` → red banner, error log, escalation buttons

**Active PM skills** are set per-brand in `vector_9_perfil_pm.skills_especificas_activas`. The dev brand (`_LIBRO_VIVO_DISRUPT`) activates: `generar_business_case`, `generar_analisis_ansoff`, `generar_prd`, `generar_plan_demanda`, `evaluar_preparacion_lanzamiento`.

### Frontend: Next.js 14 App Router

Design system: **glassmorphism** ("Clear Crystal") — dark mode only (`<html class="dark">` hardcoded), nature background at ~8% opacity, three agent color themes.

**Route structure:**
```
frontend/app/
├── layout.tsx                  # RootLayout: Sidebar (240px) + nature-bg layers + <Toaster>
├── page.tsx                    # Agency Hub (dashboard root)
├── settings/page.tsx           # Global settings
└── brand/[id]/
    ├── layout.tsx              # Injects brandId via data-brand-id attr
    ├── ceo/page.tsx            # CEO Workspace — vector grid + ingest dialog + agent console
    ├── pm/page.tsx             # PM Workspace — artifacts grid + SlideOver + CEOShield
    └── libro-vivo/page.tsx     # Libro Vivo viewer (read-only)
```

**Key components:**
- `components/njm/` — business components: `Sidebar`, `BrandCard`, `VectorCard`, `SlideOver`, `AgentConsole`, `CEOShield`
- `components/ui/` — Shadcn UI primitives — **do not modify**. Uses `@base-ui/react` internally (not standard Radix); exported APIs are identical to standard Shadcn. `Dialog` controlled mode: `<Dialog open={bool} onOpenChange={setFn}>`.
- `hooks/useAgentConsole` — call `invoke(sequenceId)` to open SSE to `${NEXT_PUBLIC_API_URL}/api/v1/agent/stream?sequenceId=...`; appends each `data:` line to `logs`; closes on `[DONE]` or error. Exposes `open`, `logs`, `running`, `close`.
- `AgentConsole` — terminal drawer (slate-950, Fira Code). Log prefix colors: `[✓]` emerald, `[⏳]` amber, `[✗]/[!]` rose. Always pair with `useAgentConsole`.
- `CEOShield` — brutalist Dialog modal (2px rose-600 border). Human-in-the-Loop gate for `BLOQUEO_CEO`. `onApprove` → `invoke("ceo-approve")`, `onReject` → `invoke("ceo-reject")`.

**Mock data state:** Both `ceo/page.tsx` (`MOCK_VECTORES`) and `pm/page.tsx` (`MOCK_ARTEFACTOS`) render hardcoded data. Neither is connected to real backend state. The "Consultar PM" button invokes the mock `pm-execution` SSE script, not `POST /api/ejecutar-tarea`. The CEOShield is triggered manually via a dev button, not from real `BLOQUEO_CEO` events.

**Toast:** `import { toast } from "sonner"` — `<Toaster>` mounted in root layout.

**Tailwind tokens — use these, not raw HSL:**

| Class | Value |
|---|---|
| `text-agency` / `bg-agency` | blue `210 100% 52%` |
| `text-ceo` / `bg-ceo` | purple `271 81% 56%` |
| `text-pm` / `bg-pm` | emerald `160 84% 39%` |
| `surface-{0-3}` | layered dark backgrounds |

When Tailwind JIT can't resolve dynamic HSL strings, use CSS variables: `hsl(var(--ceo-accent))`. Always HSL — never oklch.

**Glass utilities** (in `globals.css`): `.glass`, `.glass-subtle`, `.glass-strong`

**Fonts:** Body `Inter`, mono `Fira Code` (`font-mono` class).

**Design constraints:**
- Never use chat bubble interfaces — this is a workspace dashboard.
- `nature-bg.jpg` lives in `frontend/public/`.
- Auth mock: `localStorage.getItem("njm-auth") === "true"` (not yet built).
- PM Workspace gated: only accessible after CEO validates all vectors + signs Libro Vivo.

**Not yet built (see ARCHITECTURE_ROADMAP_PHASE2.md):**
- Phase 2.2: real ingest pipeline (text extraction + ChromaDB embedding)
- Phase 2.3: Human-in-the-Loop (`interrupt()`, `POST /api/v1/agent/resume`, `GET /api/v1/session/state`, `useAgentConsole` params, DayCeroView wizard)
- Phase 2.4: PM SSE streaming real (eliminate `pm-execution` mock)
- Phase 2.5: CEOShield wired to real `BLOQUEO_CEO` events
- Phase 2.6: retry/tenacity, structured PM output, `Last-Event-ID` SSE reconnect, CORS env var
- Frontend contexts: `AgencyContext`, `BrandContext`, `data/brands.ts`
