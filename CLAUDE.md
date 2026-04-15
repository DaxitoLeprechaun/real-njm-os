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
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Requires `backend/.env` with `ANTHROPIC_API_KEY=sk-ant-...`

### Frontend (Next.js)
```bash
cd frontend
npm install              # first time
npm run dev              # :3000
npm run build            # production build (also type-checks)
npx tsc --noEmit         # type-check only (must run from frontend/)
```

### API docs
```
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/health    # health check
```

---

## Architecture

NJM OS is a monorepo with two independent services. `ARCHITECTURE.md` is the full system design source of truth.

```
real-njm-os/
├── backend/        FastAPI + LangGraph agent engine
├── frontend/       Next.js 14 App Router
└── start.sh        runs both in parallel
```

### Backend: Agent Engine

Two AI agents orchestrated with **LangGraph**, both using `claude-3-5-sonnet-20241022` at `temperature=0`.

**Data contract flow:**
```
LibroVivo (9 strategic vectors, CEO-validated)
  → NJM_PM_State (LangGraph TypedDict)
  → POST /api/ejecutar-tarea
  → TarjetaSugerenciaUI (JSON → Next.js)
```

**Modules:**
- `backend/main.py` — FastAPI app, CORS for `localhost:3000`
- `backend/api/main.py` — single router `POST /api/ejecutar-tarea`. Compiles `_GRAFO_PM` at module load, invokes via `asyncio.to_thread`.
- `backend/core/estado.py` — `NJM_PM_State` TypedDict. `messages` reducer: `add_messages`; `documentos_generados` and `alertas_internas`: `operator.add` (append-only).
- `backend/core/schemas.py` — Pydantic v2: `LibroVivo` (9 Vector sub-models), `TarjetaSugerenciaUI`, `EstadoValidacion` enum (`EN_PROGRESO` → `LISTO_PARA_FIRMA` | `BLOQUEO_CEO`).
- `backend/agentes/agente_pm.py` — `nodo_pm`: builds system prompt dynamically from `libro_vivo` vectors, internal agentic loop (max 12 iterations, max 2 autocorrection alerts before `BLOQUEO_CEO`).
- `backend/agentes/agente_ceo.py` — CEO agent: scans onboarding docs, maps to 8 business vectors, compiles Libro Vivo when all 9 vectors are 100%, acts as background ADN arbitrator.
- `backend/tools/pm_skills.py` — 14 PM skill tools (e.g. `generar_business_case`, `generar_analisis_ansoff`, `generar_prd`). Active skills are set in `vector_9_perfil_pm.skills_especificas_activas`.

**`TarjetaSugerenciaUI` states:**
- `LISTO_PARA_FIRMA` → green card, file attachments, approve button
- `BLOQUEO_CEO` → red banner, error log, escalation buttons

### Frontend: Next.js 14 App Router

Design system: **glassmorphism** ("Clear Crystal") — dark mode only, nature background at ~8% opacity, three agent color themes.

**Current route structure:**
```
frontend/app/
├── layout.tsx                  # RootLayout: Sidebar + nature-bg layers
├── page.tsx                    # Agency Hub (dashboard root)
├── settings/page.tsx           # Global settings
└── brand/[id]/
    ├── layout.tsx              # Injects brandId via data-brand-id attr
    ├── ceo/page.tsx            # CEO Workspace
    ├── pm/page.tsx             # PM Workspace
    └── libro-vivo/page.tsx     # Libro Vivo viewer (read-only)
```

**Component hierarchy:**
- `components/njm/` — business components. Currently: `Sidebar`, `BrandCard`, `VectorCard`, `SlideOver`
- `components/ui/` — Shadcn UI primitives — **do not modify**. Internally uses `@base-ui/react` (not standard Radix); the exported component APIs are identical to standard Shadcn.

**Tailwind color aliases** (use instead of raw HSL):
- `text-agency` / `bg-agency` → blue `210 100% 52%`
- `text-ceo` / `bg-ceo` → purple `271 81% 56%`
- `text-pm` / `bg-pm` → emerald `160 84% 39%`
- `surface-0` through `surface-3` → layered dark backgrounds

**Key design constraints:**
- Never use chat bubble interfaces — this is a dashboard/workspace.
- Glass utilities: `.glass`, `.glass-subtle`, `.glass-strong` (defined in `globals.css`).
- Agent accent colors are also available as CSS variables: `hsl(var(--agency-accent))`, `hsl(var(--ceo-accent))`, `hsl(var(--pm-accent))`. Always use HSL format, not oklch.
- `nature-bg.jpg` lives in `frontend/public/`.
- Auth (not yet built): mock `localStorage.getItem("njm-auth") === "true"`.
- PM Workspace is gated: only accessible after CEO validates all vectors and signs the Libro Vivo.

**State flow (planned):**
```
AgencyContext.isSetupComplete
  false → DayCeroView (4-step onboarding wizard)
  true  → AgencyHubView → brand/[id]/ceo
            ├── CEO: validateAllVectors() → signLibroVivo() → unlocks PM
            └── PM: gated by isLibroVivoComplete(brandId)
```

`context/` (not yet built) will hold `AgencyContext` and `BrandContext`.  
`data/` (not yet built) will hold mock data: `brands.ts`, `ceoManagement.ts`, `pmManagement.ts`.
