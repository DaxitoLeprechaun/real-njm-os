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

## Dev Commands

### Start both servers (recommended)
```bash
./start.sh
```

### Backend only
```bash
cd backend
.venv/bin/python3 -m uvicorn main:app --reload --port 8000
```

### Frontend only
```bash
cd frontend
npm run dev        # port 3000
npm run build
npm run lint
```

### First-time setup
```bash
# Backend
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### Required env files
- `backend/.env` — `ANTHROPIC_API_KEY=sk-ant-...` (never commit)
- `frontend/.env.local` — `NEXT_PUBLIC_API_URL=http://localhost:8000`

### API introspection
- Swagger UI: `http://localhost:8000/docs`
- Health: `GET http://localhost:8000/health`

## Architecture

### Stack
- **Frontend**: Next.js 14 App Router, React 18, TypeScript 5, Tailwind CSS
- **Backend**: FastAPI + Uvicorn, Python 3.11+, LangGraph 0.2.60, Anthropic SDK
- **Persistence**: SQLite (LangGraph checkpointer at `/tmp/njm_checkpoints.sqlite`)
- **RAG**: ChromaDB + PyPDF (`backend/core/vector_store.py`)

### Multi-Agent LangGraph topology

```
POST /api/ejecutar-tarea
  → NJM_PM_State initialized
  → START → _router (mode) → nodo_ceo or nodo_pm
                nodo_ceo → _ceo_post_router → nodo_pm (auditoria, no block) or END
                nodo_pm → END
  ← TarjetaSugerenciaUI JSON
```

Three `modo_operacion` values:
- `"ejecucion"` — skips CEO, PM runs skill directly
- `"onboarding"` — CEO only (interviews brand, builds Libro Vivo)
- `"auditoria"` — CEO validates first, then PM executes if no red card

Graph is compiled once at module load (`_GRAFO = _compilar_grafo()` in `backend/api/main.py`). Thread-based resumability via `thread_id` + SqliteSaver.

### State: NJM_PM_State (`backend/core/estado.py`)

Key fields:
- `libro_vivo` — immutable 9-vector brand capsule set by CEO; PM reads but never writes
- `messages` — LangChain messages, append-only (`add_messages` reducer)
- `documentos_generados` — file paths, append-only (`operator.add` reducer)
- `estado_validacion` — `EN_PROGRESO` | `BLOQUEO_CEO` | `LISTO_PARA_FIRMA`
- `payload_tarjeta_sugerencia` — final UI JSON, only set at graph END

### Agent files

| File | Role |
|------|------|
| `backend/agentes/agente_ceo.py` | Brand governance; 6 tools (scan, interview, gap report, red card, libro vivo, search) |
| `backend/agentes/agente_pm.py` | Task execution; 14 PM skills across 3 phases (ideation, planning, validation) |
| `backend/api/main.py` | Router, graph compilation, `/api/ejecutar-tarea`, `/api/upload-documento` |
| `backend/tools/pm_skills.py` | All 14 skill implementations |
| `backend/core/schemas.py` | Pydantic models: `LibroVivo`, `TarjetaSugerenciaUI`, `EstadoValidacion` |

### Test data

`_LIBRO_VIVO_DISRUPT` in `backend/api/main.py` is a hardcoded brand capsule (Disrupt, B2B SaaS, Technical_PM) used as the default `libro_vivo` for all test requests. Production will load this from a JSON file.

### Frontend → Backend contract

Frontend posts to `POST /api/ejecutar-tarea` with `{ peticion, nombre_marca, modo, ruta_espacio_trabajo }` and receives `TarjetaSugerenciaUI`:

```ts
{
  id_transaccion, estado_ejecucion, metadata,
  contenido_tarjeta: { propuesta, framework, check_coherencia_adn, archivos, logs },
  acciones_ui_disponibles: [{ label, ruta_backend }]
}
```

Key frontend components: `AgentLogStream` (streaming step visualization), `StateOrchestrator` (PM/CEO flow), `CEOShield` (human-in-the-loop approval gate).
