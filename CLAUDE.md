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

Requires `backend/.env` with `ANTHROPIC_API_KEY=sk-ant-...`

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
- `ARCHITECTURE_ROADMAP_PHASE2.md` — Phase 2 technical roadmap: unified multi-agent graph design, RAG pipeline, checkpointer strategy, and full audit of current technical debt

### Backend modules

| Module | Role |
|---|---|
| `main.py` | FastAPI app entry point — calls `load_dotenv()` first, then mounts both routers |
| `api/main.py` | `POST /api/ejecutar-tarea` — invokes `unified_graph` (async via `asyncio.to_thread`); hardcodes `_LIBRO_VIVO_DISRUPT` as the test brand |
| `api/v1_router.py` | `POST /api/v1/ingest` (file upload placeholder) + `GET /api/v1/agent/stream` (SSE) |
| `agent/graph.py` | Two compiled graphs: `unified_graph` (CEO+PM, SqliteSaver checkpointer) and `ceo_graph` (streaming-only CEO for SSE). `load_dotenv()` in `main.py` **must run before this module is imported** — it instantiates `ChatAnthropic` at module level (`_LLM`). |
| `agentes/agente_ceo.py` | `nodo_ceo` — CEO node with 5 tools, agentic loop (max 10 iters); wired into `unified_graph` |
| `agentes/agente_pm.py` | `nodo_pm` — PM node with 14 skill tools, max 12 iters, max 2 autocorrection alerts; wired into `unified_graph` |
| `core/estado.py` | `NJM_OS_State` TypedDict — LangGraph state contract |
| `core/schemas.py` | Pydantic v2: `LibroVivo` (9 vectors), `TarjetaSugerenciaUI`, `EstadoValidacion` enum |
| `tools/pm_skills.py` | 14 `@tool`-decorated PM skills (business case, Ansoff, PRD, etc.) |

**Graph topology** (`unified_graph`): `START → router_node → ceo_node → [END | pm_node] → END`. Routing: `modo="auditoria"` or empty `libro_vivo` → CEO first; `modo="ejecucion"` + populated `libro_vivo` → PM directly. Post-CEO edge: `BLOQUEO_CEO` → END, `LISTO_PARA_FIRMA` + libro_vivo → PM. Checkpointer: `SqliteSaver` on `njm_checkpoints.db`; pass `{"configurable": {"thread_id": "..."}}` to `invoke`/`astream_events` for multi-turn memory.

**SSE endpoint (`GET /api/v1/agent/stream?sequenceId=...`):**
- `ceo-audit` → real LangGraph streaming via `astream_events(version="v2")`, filters `on_chat_model_stream`
- `pm-execution`, `ceo-approve`, `ceo-reject` → hardcoded mock scripts with `asyncio.sleep` delays
- All sequences terminate with `data: [DONE]\n\n`
- Anthropic streaming returns `chunk.content` as either `str` or `list[dict]` — `_extract_text()` normalizes both

**`POST /api/v1/ingest` is a placeholder** — saves files to `backend/temp_uploads/` but does not extract text, embed, or connect to the CEO's `escanear_directorio_onboarding` tool (which reads from `~/NJM_OS/`).

**Models:** `claude-3-5-haiku-20241022` (streaming in `agent/graph.py`), `claude-3-5-sonnet-20241022` (both agent nodes). All at `temperature=0`.

**Data contract flow:**
```
LibroVivo (9 vectors, CEO-validated JSON)
  → NJM_PM_State (injected by api/main.py — currently hardcoded)
  → nodo_pm (agentes/agente_pm.py, agentic loop)
  → payload_tarjeta_sugerencia (TarjetaSugerenciaUI JSON → Next.js)
```

**`TarjetaSugerenciaUI` states:**
- `LISTO_PARA_FIRMA` → green card, file attachments, approve button
- `BLOQUEO_CEO` → red banner, error log, escalation buttons

**CEO tools** (in `agente_ceo.py`, currently orphaned): `escanear_directorio_onboarding`, `generar_reporte_brechas`, `iniciar_entrevista_profundidad`, `escribir_libro_vivo`, `levantar_tarjeta_roja`. Scans `~/NJM_OS/` for onboarding docs.

**Active PM skills** are set per-brand in `vector_9_perfil_pm.skills_especificas_activas`. The hardcoded test brand (`_LIBRO_VIVO_DISRUPT` in `api/main.py`) activates: `generar_business_case`, `generar_analisis_ansoff`, `generar_prd`, `generar_plan_demanda`, `evaluar_preparacion_lanzamiento`.

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

**Not yet built (see ARCHITECTURE_ROADMAP_PHASE2.md for implementation plan):**
- Unified multi-agent LangGraph (`njm_graph`) with `NJM_OS_State`, checkpointer, and real CEO → PM handoff
- Real ingest pipeline (text extraction + ChromaDB embedding)
- Typed SSE events (currently plain text — Phase 2 adds JSON events)
- `POST /api/v1/agent/resume` endpoint for Human-in-the-Loop graph resumption
- `GET /api/v1/session/state` endpoint to hydrate frontend from checkpointer
- `context/` — `AgencyContext` and `BrandContext`
- `data/` — `brands.ts`, `ceoManagement.ts`, `pmManagement.ts`
- DayCeroView onboarding wizard (4-step)
