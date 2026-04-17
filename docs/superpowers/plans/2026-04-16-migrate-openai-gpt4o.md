# Migrate LLM Provider Anthropic → OpenAI (gpt-4o) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every `ChatAnthropic` instance in the NJM OS backend with `ChatOpenAI` (gpt-4o for agents, gpt-4o-mini for SSE streaming), keeping tool calling, agentic loops, and SSE streaming fully intact.

**Architecture:** LangChain's `ChatOpenAI` exposes the same `bind_tools()`, `invoke()`, and `astream_events()` interface as `ChatAnthropic`, so no logic changes are needed — only import swaps, model name updates, and env var references. The SSE `_extract_text()` helper already handles OpenAI's `str`-only chunk format via its first branch (`isinstance(content, str)`).

**Tech Stack:** `langchain-openai==0.2.14`, FastAPI, LangGraph 0.2.60, Python 3.11+.

---

## File Structure — Changes

| File | Action | What changes |
|------|--------|--------------|
| `backend/requirements.txt` | **Modify** | Remove `langchain-anthropic`, add `langchain-openai==0.2.14` |
| `backend/agentes/agente_ceo.py` | **Modify** | Import, MODEL_NAME, `_LLM` singleton |
| `backend/agentes/agente_pm.py` | **Modify** | Import, MODEL_NAME, `_LLM` singleton |
| `backend/agent/njm_graph.py` | **Modify** | Import, `_SSE_LLM` singleton, model name |
| `backend/api/main.py` | **Modify** | API key guard: `ANTHROPIC_API_KEY` → `OPENAI_API_KEY` |
| `backend/api/v1_router.py` | **Modify** | `_extract_text()` comment — remove Anthropic-specific note |
| `backend/.env` | **Modify** (user) | User adds `OPENAI_API_KEY=sk-...` before execution |

No schema, state, tool logic, routing, or frontend files change.

---

### Task 1: Swap dependency in requirements.txt

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Edit requirements.txt**

Open `backend/requirements.txt`. Remove line:
```
langchain-anthropic==0.3.3
```
Add in its place:
```
langchain-openai==0.2.14
```

The complete LangChain block should read:
```
# LangChain / LangGraph
langgraph==0.2.60
langgraph-checkpoint-sqlite==2.0.11
langchain==0.3.13
langchain-openai==0.2.14
langchain-core>=0.3.30,<0.4.0
```

- [ ] **Step 2: Reinstall the venv**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend
.venv/bin/pip install -r requirements.txt
```

Expected: pip installs `langchain-openai` and its `openai` dependency. Should see `Successfully installed openai-...` and `langchain-openai-0.2.14`. `langchain-anthropic` will be uninstalled or simply not present.

- [ ] **Step 3: Verify import works**

```bash
.venv/bin/python3 -c "from langchain_openai import ChatOpenAI; print('ChatOpenAI import OK')"
```

Expected:
```
ChatOpenAI import OK
```

- [ ] **Step 4: Commit**

```bash
cd /Users/juanduran/Downloads/real-njm-os
git add backend/requirements.txt
git commit -m "chore: swap langchain-anthropic for langchain-openai==0.2.14"
```

---

### Task 2: Migrate agente_ceo.py

**Files:**
- Modify: `backend/agentes/agente_ceo.py:22,35,561`

Three lines change. Everything else — tools, agentic loop, state side-effects — stays identical.

- [ ] **Step 1: Replace import (line 22)**

Old:
```python
from langchain_anthropic import ChatAnthropic
```

New:
```python
from langchain_openai import ChatOpenAI
```

- [ ] **Step 2: Replace MODEL_NAME (line 35)**

Old:
```python
MODEL_NAME = "claude-3-5-sonnet-20241022"
```

New:
```python
MODEL_NAME = "gpt-4o"
```

- [ ] **Step 3: Replace _LLM singleton (line 561)**

Old:
```python
_LLM = ChatAnthropic(model=MODEL_NAME, temperature=0)
```

New:
```python
_LLM = ChatOpenAI(model=MODEL_NAME, temperature=0)
```

- [ ] **Step 4: Verify compile (no API call)**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend
OPENAI_API_KEY=test .venv/bin/python3 -c "
from agentes.agente_ceo import nodo_ceo, CEO_TOOLS, _LLM
print('CEO LLM model:', _LLM.model_name)
print('CEO tools:', [t.name for t in CEO_TOOLS])
print('agente_ceo compile OK')
"
```

Expected:
```
CEO LLM model: gpt-4o
CEO tools: ['escanear_directorio_onboarding', 'generar_reporte_brechas', 'iniciar_entrevista_profundidad', 'escribir_libro_vivo', 'levantar_tarjeta_roja']
agente_ceo compile OK
```

- [ ] **Step 5: Commit**

```bash
cd /Users/juanduran/Downloads/real-njm-os
git add backend/agentes/agente_ceo.py
git commit -m "feat: migrate agente_ceo from ChatAnthropic to ChatOpenAI (gpt-4o)"
```

---

### Task 3: Migrate agente_pm.py

**Files:**
- Modify: `backend/agentes/agente_pm.py:21,39,43`
  (line numbers approximate — search for the three Anthropic references)

Same three-line change as Task 2.

- [ ] **Step 1: Replace import**

Find:
```python
from langchain_anthropic import ChatAnthropic
```
Replace with:
```python
from langchain_openai import ChatOpenAI
```

- [ ] **Step 2: Replace MODEL_NAME**

Find:
```python
MODEL_NAME = "claude-3-5-sonnet-20241022"
```
Replace with:
```python
MODEL_NAME = "gpt-4o"
```

- [ ] **Step 3: Replace _LLM singleton**

Find:
```python
_LLM = ChatAnthropic(model=MODEL_NAME, temperature=0)
```
Replace with:
```python
_LLM = ChatOpenAI(model=MODEL_NAME, temperature=0)
```

- [ ] **Step 4: Verify compile (no API call)**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend
OPENAI_API_KEY=test .venv/bin/python3 -c "
from agentes.agente_pm import nodo_pm, PM_SKILLS, _LLM
print('PM LLM model:', _LLM.model_name)
print('PM skills count:', len(PM_SKILLS))
print('agente_pm compile OK')
"
```

Expected:
```
PM LLM model: gpt-4o
PM skills count: 14
agente_pm compile OK
```

- [ ] **Step 5: Commit**

```bash
cd /Users/juanduran/Downloads/real-njm-os
git add backend/agentes/agente_pm.py
git commit -m "feat: migrate agente_pm from ChatAnthropic to ChatOpenAI (gpt-4o)"
```

---

### Task 4: Migrate njm_graph.py (SSE streaming LLM)

**Files:**
- Modify: `backend/agent/njm_graph.py:29,229-233`

The main `njm_graph` (used by `POST /api/ejecutar-tarea`) only imports `nodo_ceo` and `nodo_pm` — those singletons are already migrated in Tasks 2–3. The only direct Anthropic usage here is `_SSE_LLM` which drives the `GET /api/v1/agent/stream?sequenceId=ceo-audit` SSE endpoint.

- [ ] **Step 1: Replace import (line 29)**

Find:
```python
from langchain_anthropic import ChatAnthropic
```
Replace with:
```python
from langchain_openai import ChatOpenAI
```

- [ ] **Step 2: Replace _SSE_LLM (lines 229–233)**

Find:
```python
_SSE_LLM = ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    temperature=0,
    streaming=True,
)
```
Replace with:
```python
_SSE_LLM = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    streaming=True,
)
```

- [ ] **Step 3: Verify full graph compile (no API call)**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend
OPENAI_API_KEY=test .venv/bin/python3 -c "
from agent.njm_graph import njm_graph, ceo_graph
from agentes.agente_ceo import nodo_ceo
from agentes.agente_pm import nodo_pm
nodes = list(njm_graph.get_graph().nodes)
print('Graph nodes:', nodes)
print('njm_graph compile OK')
"
```

Expected:
```
Graph nodes: ['__start__', 'ingest', 'ceo_auditor', 'human_in_loop', 'pm_execution', 'ceo_review', 'output', '__end__']
njm_graph compile OK
```

- [ ] **Step 4: Commit**

```bash
cd /Users/juanduran/Downloads/real-njm-os
git add backend/agent/njm_graph.py
git commit -m "feat: migrate njm_graph SSE LLM from Claude Haiku to gpt-4o-mini"
```

---

### Task 5: Update API key guard + _extract_text() cleanup

**Files:**
- Modify: `backend/api/main.py:124-135`
- Modify: `backend/api/v1_router.py:89-100`

- [ ] **Step 1: Update API key guard in api/main.py**

Find the block starting at line 124:
```python
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ANTHROPIC_API_KEY no configurada.",
                "detalle": (
                    "Crea el archivo backend/.env con ANTHROPIC_API_KEY=sk-ant-... "
                    "y reinicia el servidor."
                ),
                "id_transaccion": str(uuid4()),
            },
        )
```

Replace with:
```python
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "OPENAI_API_KEY no configurada.",
                "detalle": (
                    "Crea el archivo backend/.env con OPENAI_API_KEY=sk-... "
                    "y reinicia el servidor."
                ),
                "id_transaccion": str(uuid4()),
            },
        )
```

- [ ] **Step 2: Update _extract_text() in api/v1_router.py**

Find (lines 89–100):
```python
def _extract_text(content: str | list) -> str:
    """Normalize Anthropic streaming content blocks to plain text."""
    if isinstance(content, str):
        return content
    # Anthropic returns list of dicts: [{"type": "text", "text": "...", "index": 0}]
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text", "")
            if text:
                parts.append(text)
    return "".join(parts)
```

Replace with:
```python
def _extract_text(content: str | list) -> str:
    """Normalize LLM streaming chunk content to plain text."""
    if isinstance(content, str):
        return content
    # Fallback for non-str content (unused with OpenAI; kept for safety)
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text", "")
            if text:
                parts.append(text)
    return "".join(parts)
```

- [ ] **Step 3: Verify api modules load cleanly**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend
OPENAI_API_KEY=test .venv/bin/python3 -c "
from api.main import router
from api.v1_router import router as v1, _extract_text
print('_extract_text str:', _extract_text('hello'))
print('_extract_text list:', _extract_text([{'type': 'text', 'text': 'hi'}]))
print('api modules OK')
"
```

Expected:
```
_extract_text str: hello
_extract_text list: hi
api modules OK
```

- [ ] **Step 4: Commit**

```bash
cd /Users/juanduran/Downloads/real-njm-os
git add backend/api/main.py backend/api/v1_router.py
git commit -m "chore: update API key guard to OPENAI_API_KEY, clean up _extract_text comment"
```

---

### Task 6: Set OPENAI_API_KEY + full compile smoke test

**Files:**
- Modify: `backend/.env` (user action)
- Modify: `backend/test_graph.py` — update env var reference

**Prerequisites:** User must add `OPENAI_API_KEY=sk-...` to `backend/.env` before Step 2.

- [ ] **Step 1: Update test_graph.py env var reference**

In `backend/test_graph.py`, find:
```python
if not os.getenv("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY not set. Create backend/.env with the key.")
    sys.exit(1)
```
Replace with:
```python
if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not set. Create backend/.env with the key.")
    sys.exit(1)
```

- [ ] **Step 2: Add OPENAI_API_KEY to backend/.env**

This is a user action — not automated. The file at `backend/.env` must contain:
```
OPENAI_API_KEY=sk-...your-real-key-here...
```
(Remove or leave the old `ANTHROPIC_API_KEY` line — it is no longer read.)

Wait for user confirmation before proceeding to Step 3.

- [ ] **Step 3: Run compile-only smoke test (zero API calls)**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend
.venv/bin/python3 -c "
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')
from agent.njm_graph import njm_graph, ceo_graph
from agentes.agente_ceo import nodo_ceo, _LLM as ceo_llm
from agentes.agente_pm import nodo_pm, _LLM as pm_llm
nodes = list(njm_graph.get_graph().nodes)
print('CEO model:', ceo_llm.model_name)
print('PM  model:', pm_llm.model_name)
print('Nodes:', nodes)
print('Full compile OK')
"
```

Expected:
```
CEO model: gpt-4o
PM  model: gpt-4o
Nodes: ['__start__', 'ingest', 'ceo_auditor', 'human_in_loop', 'pm_execution', 'ceo_review', 'output', '__end__']
Full compile OK
```

- [ ] **Step 4: Run live smoke test (makes real OpenAI API calls)**

```bash
cd /Users/juanduran/Downloads/real-njm-os/backend && .venv/bin/python3 test_graph.py
```

Allow 30–120 seconds for PM to call `generar_business_case` via gpt-4o.

All 4 postconditions must pass:
```
[✓] CEO skip guard OK — audit_status: COMPLETE
[✓] skill_activa        : generar_business_case
[✓] payload presente    — id: <uuid>
[✓] SQLite OK — N checkpoint(s) para thread_id=disrupt:test-001
Smoke Test PASÓ ✓ — Fase 2.1 completada
```

- [ ] **Step 5: Commit everything**

```bash
cd /Users/juanduran/Downloads/real-njm-os
git add backend/test_graph.py docs/superpowers/plans/2026-04-16-migrate-openai-gpt4o.md
git commit -m "test: update smoke test for OpenAI provider, add migration plan doc"
```

---

## Self-Review

**Spec coverage:**
- ✅ Replace `ChatAnthropic` → `ChatOpenAI` in `agente_ceo.py` (Task 2)
- ✅ Replace `ChatAnthropic` → `ChatOpenAI` in `agente_pm.py` (Task 3)
- ✅ SSE streaming in `api/v1_router.py` + `njm_graph.py` intact (Task 4 + 5)
- ✅ Tool calling (`bind_tools`, 5 CEO tools, 14 PM skills) unchanged — same LangChain API
- ✅ `_extract_text()` works with OpenAI str chunks via existing `isinstance(str)` branch (Task 5)
- ✅ API key guard updated (Task 5)
- ✅ Smoke test confirms gpt-4o runs end-to-end through the graph (Task 6)

**Placeholder scan:** No TBDs. All code blocks are complete. Step 6.2 explicitly marks the user action and says to wait.

**Type consistency:** `_LLM.model_name` is `"gpt-4o"` in both agents. `_SSE_LLM` uses `"gpt-4o-mini"`. `bind_tools()` signature unchanged. No type mismatches introduced.
