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
**Venv gotcha:** The `.venv` shebang encodes the absolute path at creation time. If the repo was moved or cloned, the venv is broken. Fix: `python3 -m venv .venv --clear && .venv/bin/pip install -r requirements.txt`.

Use `.venv/bin/python3` (not `source .venv/bin/activate`) to avoid shell state issues. Always run from `backend/` so relative imports resolve correctly.

Requires `backend/.env` with `OPENAI_API_KEY=sk-...`

### Run tests
```bash
cd backend
.venv/bin/python3 -m pytest tests/ -v               # all tests
.venv/bin/python3 -m pytest tests/test_rag.py -v    # single file
.venv/bin/python3 -m pytest tests/test_v1_sse.py -v # SSE endpoint tests (no real API calls — monkeypatched)
```
Tests that call `upsert_chunks` or `query_brand` make real OpenAI embedding API calls — requires a valid key in `backend/.env`. SSE tests mock `njm_graph` fully and run without a key.

### Smoke test (verify graph compiles and agents load)
```bash
cd backend
.venv/bin/python3 -c "
import os, asyncio; os.environ.setdefault('OPENAI_API_KEY','test')
from agent.njm_graph import init_graph, ceo_graph
from agentes.agente_ceo import nodo_ceo, CEO_TOOLS
from agentes.agente_pm import nodo_pm
asyncio.run(init_graph())
from agent.njm_graph import njm_graph
print([n for n in njm_graph.get_graph().nodes])
print('CEO tools:', [t.name for t in CEO_TOOLS])
"
```
**Note:** `njm_graph` is `None` at import time — it is initialized by `await init_graph()` inside the FastAPI lifespan (or `asyncio.run(init_graph())` for scripts/tests). Do not import and use `njm_graph` without first calling `init_graph()`.

### Live smoke test (real API call — Phase 2.1 end-to-end)
```bash
cd backend && .venv/bin/python3 test_graph.py
```
Invokes `njm_graph` with `brand_id="disrupt"`, skips CEO (dev fallback), runs PM with gpt-4o, checks SQLite checkpoint. Allow 30–120 s.

### Test RAG ingest + retrieval (Phase 2.2 end-to-end)
```bash
# Start server first, then:
echo "CAC objetivo: $120. LTV: $2400." > /tmp/test_brief.txt
curl -X POST http://localhost:8000/api/v1/ingest \
  -F "file=@/tmp/test_brief.txt" \
  -F "brand_id=my-brand"

# Verify retrieval:
cd backend && .venv/bin/python3 -c "
from dotenv import load_dotenv; load_dotenv('.env')
from core.rag import query_brand
print(query_brand('my-brand', 'CAC objetivo', n_results=3))
"
```

### Frontend (Next.js)
```bash
cd frontend
npm install              # first time
npm run dev              # :3000
npm run build            # production build (also type-checks)
./node_modules/.bin/tsc --noEmit   # type-check only
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
| `main.py` | FastAPI app entry point — calls `load_dotenv()` first, then mounts both routers. Has `@asynccontextmanager lifespan` that calls `await init_graph()` on startup and closes the aiosqlite connection on shutdown. `load_dotenv()` **must run before any agent module is imported** — agents instantiate `ChatOpenAI` at module level. |
| `api/main.py` | `POST /api/ejecutar-tarea` — invokes `njm_graph` via `await njm_graph.ainvoke(...)`. Resolves `brand_id`/`session_id` with dev fallback (see below). Imports `njm_graph` lazily inside the function body (not at module level). |
| `api/v1_router.py` | `POST /api/v1/ingest` + `GET /api/v1/agent/stream` (SSE, unified via `njm_graph`) + `GET /api/v1/session/state` (checkpointer hydration) + `POST /api/v1/agent/resume` (graph resumption after interrupt). All `njm_graph` imports are lazy (inside function bodies). |
| `agent/njm_graph.py` | **Single source of graphs.** Exports `njm_graph` (starts as `None`), `init_graph()` async coroutine, `ceo_graph`, and `AgentState`. `njm_graph` is set by `await init_graph()` — called from lifespan on startup. Also contains `aiosqlite.Connection.is_alive` compatibility shim (see Dependency Pitfalls below). |
| `agentes/agente_ceo.py` | `nodo_ceo` — CEO node with 6 tools (5 original + `buscar_contexto_marca`), agentic loop (max 10 iters). Singleton `_LLM = ChatOpenAI(model="gpt-4o", temperature=0)`. |
| `agentes/agente_pm.py` | `nodo_pm` — PM node with 15 tools (14 PM skills + `buscar_contexto_marca`), max 12 iters. Singleton `_LLM = ChatOpenAI(model="gpt-4o", temperature=0)`. |
| `core/estado.py` | `NJM_OS_State` TypedDict — 23-field unified LangGraph state. `NJM_PM_State` is an alias (deprecated). |
| `core/rag.py` | ChromaDB singleton client + collection manager. `get_collection(brand_id)`, `upsert_chunks(brand_id, chunks, source)`, `query_brand(brand_id, query, n_results)`. Persistent store at `backend/chroma_db/` (gitignored). Thread-safe via double-checked locking. |
| `core/ingest.py` | RAG ingestion pipeline: `extract_text(bytes, filename)` (PDF via PyMuPDF, text via UTF-8 decode) → `chunk_text(text, chunk_size=500, overlap=80)` → `upsert_chunks`. Top-level `ingest_document(brand_id, file_bytes, filename) -> int`. |
| `core/schemas.py` | Pydantic v2: `LibroVivo` (9 vectors), `TarjetaSugerenciaUI`, `EstadoValidacion` enum |
| `core/dev_fixtures.py` | `_LIBRO_VIVO_DISRUPT` mock. Only imported in dev fallback paths — never in production. |
| `tools/pm_skills.py` | 14 `@tool`-decorated PM skills (business case, Ansoff, PRD, etc.) |
| `tools/retrieval_tool.py` | `buscar_contexto_marca` `@tool` — semantic search over ChromaDB for a brand. Used by both CEO and PM agents. |

### RAG pipeline (Phase 2.2)

```
POST /api/v1/ingest
  → extract_text (PyMuPDF for PDF, UTF-8 for text)
  → chunk_text (500-char chunks, 80-char overlap)
  → upsert_chunks → ChromaDB collection (one per brand_id)

Agent tool call: buscar_contexto_marca(brand_id, consulta)
  → query_brand → ChromaDB semantic search
  → formatted string of ranked fragments
```

**ChromaDB collection naming:** `brand_id` is sanitised (spaces/slashes → underscores, max 63 chars). Re-ingesting the same file is idempotent — chunk IDs are `{filename}::{index}`.

**Embedding model:** `text-embedding-3-small` via `chromadb.utils.embedding_functions.OpenAIEmbeddingFunction`. Called at upsert and query time — requires a live `OPENAI_API_KEY`.

**`buscar_contexto_marca` is now registered in both `CEO_TOOLS` and `_ALL_PM_TOOLS`.** The PM node uses `_PM_TOOL_MAP = {**_SKILL_MAP, _buscar_contexto.name: _buscar_contexto}` for dispatch (defined once per `nodo_pm` call, before the agentic loop).

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
- `ingest` — passthrough. Real ingestion now available via `POST /api/v1/ingest`; graph node still stub until Phase 2.3.
- `human_in_loop` — auto-sets `audit_status="COMPLETE"` + injects `_LIBRO_VIVO_DISRUPT`. Real `interrupt()` in Phase 2.3.
- `ceo_review` — auto-sets `ceo_review_decision="REJECTED"` → routes to output. Real CEOShield in Phase 2.5.

**CEO skip guard:** `ceo_auditor_node` returns `{}` immediately if `state["audit_status"] == "COMPLETE"`.

**Graph initialization:** `njm_graph` is `None` at import time. `await init_graph()` builds the graph and sets the module global — called once from the FastAPI lifespan in `main.py`. All callers import `njm_graph` lazily inside their function bodies (`from agent.njm_graph import njm_graph  # noqa: PLC0415`) to avoid capturing `None` at import time. The `init_graph()` coroutine is idempotent (guarded by `asyncio.Lock`) — safe to call multiple times.

**Test initialization:** `tests/conftest.py` has a session-scoped autouse fixture that calls `asyncio.run(init_graph())` before any test runs. This ensures `njm_graph` is a real object when tests monkeypatch its methods.

**Checkpointer:** `AsyncSqliteSaver` on `./njm_sessions.db`. `thread_id = f"{brand_id}:{session_id}"`. Pass `{"configurable": {"thread_id": thread_id}}` to every `ainvoke`/`astream_events`/`aget_state` call. Never use the sync `invoke`/`get_state` — they raise `NotImplementedError` with an async checkpointer.

**Dev fallback** (`api/main.py`): if `brand_id` is empty → `"disrupt"`, `session_id` empty → `"dev-session-1"`. When `brand_id == "disrupt"`, injects `_LIBRO_VIVO_DISRUPT` and sets `audit_status="COMPLETE"` so CEO is skipped and PM runs directly.

**CEO tools side-effects on state:**
- `escribir_libro_vivo` → `audit_status="COMPLETE"`, `libro_vivo={...}`
- `levantar_tarjeta_roja` → `audit_status="RISK_BLOCKED"`, `risk_flag=True`, `risk_details`
- `generar_reporte_brechas` → `audit_status="GAP_DETECTED"`, `gap_report_path`
- `iniciar_entrevista_profundidad` → `interview_questions=[...]`

**SSE endpoint (`GET /api/v1/agent/stream?sequenceId=...&brand_id=...&session_id=...`):**
- `ceo-audit` → streams full `njm_graph` via `astream_events(version="v2")`. Emits JSON events: `{"type":"log","text":"..."}`, `{"type":"action_required","trigger":"BLOQUEO_CEO"|"GAP_DETECTED",...}`, `{"type":"done"}`. Dev fallback: `brand_id="disrupt"` injects `_LIBRO_VIVO_DISRUPT` + skips CEO.
- `pm-execution`, `ceo-approve`, `ceo-reject` → hardcoded mock scripts (plain-text, legacy `[DONE]` sentinel — Phase 2.4 will wire real PM streaming)
- Post-stream: calls `await njm_graph.aget_state()` to detect `BLOQUEO_CEO` or graph interrupt (`snapshot.next` truthy) and emit `action_required` event before `done`.

**Session endpoints (Phase 2.3):**
- `GET /api/v1/session/state?brand_id=&session_id=` → returns `{audit_status, interview_questions, last_tarjeta, documentos_count, next_interrupt}` from checkpointer
- `POST /api/v1/agent/resume` body `{brand_id, session_id, answers}` → resumes graph paused at `human_in_loop_node` via `njm_graph.ainvoke({"human_interview_answers": answers}, config)`

**Thread ID convention:** `thread_id = f"{brand_id}:{session_id}"` — used consistently across all three endpoints and the SSE generator.

**Models:** `gpt-4o` (both agent nodes). All `temperature=0`.

**Data contract flow:**
```
NJM_OS_State.libro_vivo (9 vectors, CEO-validated JSON)
  → nodo_pm reads libro_vivo to build dynamic system prompt
  → PM agentic loop with 15 tools (14 skills + buscar_contexto_marca)
  → payload_tarjeta_sugerencia (TarjetaSugerenciaUI JSON → Next.js)
```

### Dependency Pitfalls

**aiosqlite / langgraph-checkpoint-sqlite incompatibility:** `langgraph-checkpoint-sqlite 2.0.x` calls `conn.is_alive()` inside `AsyncSqliteSaver.setup()`. `aiosqlite 0.22+` removed `is_alive()` from `Connection` (it's now on `Connection._thread`). A compatibility shim in `agent/njm_graph.py` patches the missing method at import time:
```python
if not hasattr(aiosqlite.Connection, "is_alive"):
    aiosqlite.Connection.is_alive = lambda self: self._thread.is_alive()
```
If this assertion fires on startup, the aiosqlite internal API changed — revisit the shim. Do not remove it without checking the installed versions of both packages.

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
- `components/ui/` — Shadcn UI primitives — **do not modify**. Uses `@base-ui/react` internally (not standard Radix); `Dialog` controlled mode: `<Dialog open={bool} onOpenChange={setFn}>`.
- `hooks/useAgentConsole` — `invoke(sequenceId, params?)` opens SSE with optional `{brand_id, session_id}`; exposes `open`, `logs`, `running`, `close`, `actionRequired: ActionRequiredEvent | null` (set on `action_required` JSON event, cleared by next `invoke()` call), `resume(answers, params)` (calls `POST /api/v1/agent/resume`). Handles both JSON events (new `ceo-audit`) and legacy plain-text (mock sequences). Hook is complete — do not modify.
- `CEOShield` — brutalist Dialog modal (2px rose-600 border). Accepts `submitting?: boolean` to disable buttons during network I/O. Approve path: `resume("APPROVED", params)` → `invoke("ceo-audit", params)`. Reject path: `resume("REJECTED", params)` → `invoke("ceo-reject", params)`. Controlled via `shieldOpen = actionRequired?.trigger === "BLOQUEO_CEO"` — pass `onOpenChange={() => {}}` to prevent Escape-close.
- `AgentConsole` — accepts optional `exitMessage?: string` to override the "Process exited with code 0" footer (shown in rose-600 bold after rejection).

**Concurrency pattern (CEO Shield):** After `resume()` + `invoke()`, use `useEffect` watching `agentConsole.logs.length > 0` to release the `submitting` lock — not the network promise. This ensures the shield stays blocked until the first SSE log proves the stream restarted ("Optimistic UI Inversion").

**Frontend testing:** No Jest/RTL infrastructure. TypeScript strict mode is the primary safety net. Integration tests deferred to Phase 2.6.

**Mock data state:** `ceo/page.tsx` (`MOCK_VECTORES`) and `pm/page.tsx` (`MOCK_ARTEFACTOS`) render hardcoded data. Neither connected to real backend state. "Consultar PM" invokes mock `pm-execution` SSE script.

**Toast:** `import { toast } from "sonner"` — `<Toaster>` mounted in root layout.

**Tailwind tokens:**

| Class | Value |
|---|---|
| `text-agency` / `bg-agency` | blue `210 100% 52%` |
| `text-ceo` / `bg-ceo` | purple `271 81% 56%` |
| `text-pm` / `bg-pm` | emerald `160 84% 39%` |
| `surface-{0-3}` | layered dark backgrounds |

When Tailwind JIT can't resolve dynamic HSL strings, use CSS variables: `hsl(var(--ceo-accent))`. Always HSL — never oklch. Glass utilities in `globals.css`: `.glass`, `.glass-subtle`, `.glass-strong`.

**Design constraints:** Never use chat bubble interfaces. `nature-bg.jpg` lives in `frontend/public/`.

**Not yet built (see ARCHITECTURE_ROADMAP_PHASE2.md):**
- Phase 2.3 partial: `interrupt()` in `human_in_loop_node` (stub auto-completes), DayCeroView wizard in CEO Workspace
- Phase 2.4 — CEO Shield UI **[implementation plan written]**: Wire `CEOShield` + `AgentConsole` into `ceo/page.tsx` to react to `BLOQUEO_CEO`. Plan: `docs/superpowers/plans/2026-04-18-phase-2-4-ceo-shield-ui.md`. Three files: `CEOShield.tsx` (submitting prop), `AgentConsole.tsx` (exitMessage prop), `ceo/page.tsx` (wiring).
- Phase 2.5: PM SSE streaming real (eliminate `pm-execution` mock), connect "Consultar PM" to real graph
- Phase 2.6: retry/tenacity, structured PM output, `Last-Event-ID` SSE reconnect, CORS env var, Jest/RTL frontend test infrastructure
- Frontend contexts: `AgencyContext`, `BrandContext`, `data/brands.ts`
- Graph `ingest` node wired to real ChromaDB pipeline (currently passthrough stub)
- `MOCK_VECTORES` (`ceo/page.tsx`) and `MOCK_ARTEFACTOS` (`pm/page.tsx`) still hardcoded — not yet connected to real backend state

**Planning artifacts:** `docs/superpowers/specs/` holds approved design specs; `docs/superpowers/plans/` holds step-by-step implementation plans. Read the relevant plan before implementing any pending phase.
