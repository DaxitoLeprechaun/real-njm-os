# Phase 2.6 — El Motor de Desglose Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Backend emits structured `Tarea` objects via SSE that the frontend Kanban board consumes to fill with real tasks from the PM agent.

**Architecture:** The PM prompt's `[FORMATO DE SALIDA ESTRICTO]` section is extended with a `TAREAS:` block. After the agentic loop, `_parsear_tareas()` extracts the list. `tareas_generadas` is added to `NJM_OS_State`. The SSE generator emits `{"type": "task_ready", "tarea": {...}}` events before `done`. `useAgentConsole` accumulates them in `tasks[]`. The Kanban placeholder in `pm/page.tsx` is replaced with a 3-column board (BACKLOG / EN_PROGRESO / DONE).

**Tech Stack:** Python Pydantic v2 (backend schema), regex parser (no new deps), FastAPI SSE, React useState, Tailwind glassmorphism

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/core/schemas.py` | Modify | Add `PrioridadTarea`, `EstadoTarea` enums + `Tarea` Pydantic model |
| `backend/core/estado.py` | Modify | Add `tareas_generadas: Annotated[List[Dict[str, Any]], operator.add]` |
| `backend/agentes/agente_pm.py` | Modify | Extend prompt with TAREAS block + add `_parsear_tareas()` + update `nodo_pm` |
| `backend/api/v1_router.py` | Modify | Emit `task_ready` SSE events from `tareas_generadas` after graph completes |
| `frontend/hooks/useAgentConsole.ts` | Modify | Add `tasks: Tarea[]` state, parse `task_ready` events, expose in return type |
| `frontend/app/brand/[id]/pm/page.tsx` | Modify | Replace placeholder with real 3-column Kanban wired to `agentConsole.tasks` |
| `backend/tests/test_motor_desglose.py` | Create | Unit tests for `_parsear_tareas` and `Tarea` schema |

---

### Task 1: Add `Tarea` Pydantic schema to `core/schemas.py`

**Files:**
- Modify: `backend/core/schemas.py` (append after `TarjetaSugerenciaUI`)
- Create: `backend/tests/test_motor_desglose.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_motor_desglose.py
import pytest
from core.schemas import Tarea, PrioridadTarea, EstadoTarea


def test_tarea_schema_valid():
    t = Tarea(
        id="tarea-001",
        titulo="Definir estrategia de captación LinkedIn",
        descripcion="Crear matriz de contenido Q3 con presupuesto $3,000 USD.",
        responsable="PM",
        prioridad=PrioridadTarea.ALTA,
        estado=EstadoTarea.BACKLOG,
        skill_origen="generar_plan_demanda",
    )
    assert t.id == "tarea-001"
    assert t.prioridad == PrioridadTarea.ALTA


def test_tarea_titulo_max_length():
    with pytest.raises(Exception):
        Tarea(
            id="tarea-002",
            titulo="A" * 61,
            descripcion="desc",
            responsable="CEO",
            prioridad=PrioridadTarea.BAJA,
            estado=EstadoTarea.BACKLOG,
            skill_origen="generar_prd",
        )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py -v
```
Expected: `ImportError: cannot import name 'Tarea' from 'core.schemas'`

- [ ] **Step 3: Add enums and `Tarea` model to `backend/core/schemas.py`**

Append after the `TarjetaSugerenciaUI` class (end of file):

```python
# ══════════════════════════════════════════════════════════════════
# TAREA — Unidad atómica del Tablero Táctico
# Generada por el Agente PM al finalizar cada skill execution.
# Consumida por el frontend Kanban via SSE event "task_ready".
# ══════════════════════════════════════════════════════════════════


class PrioridadTarea(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class EstadoTarea(str, Enum):
    BACKLOG = "BACKLOG"
    EN_PROGRESO = "EN_PROGRESO"
    DONE = "DONE"


class Tarea(BaseModel):
    """
    Unidad de trabajo táctica emitida por el PM al finalizar.
    El PM genera mínimo 3 y máximo 10 tareas por ejecución.
    """

    id: str = Field(..., description="Ej.: 'tarea-001'. Único por sesión.")
    titulo: str = Field(..., max_length=60, description="Título accionable corto.")
    descripcion: str = Field(..., description="Descripción ejecutable de 1 oración.")
    responsable: str = Field(..., description="PM | CEO | Encargado Real")
    prioridad: PrioridadTarea
    estado: EstadoTarea = Field(default=EstadoTarea.BACKLOG)
    skill_origen: str = Field(..., description="Skill PM que generó esta tarea.")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py::test_tarea_schema_valid tests/test_motor_desglose.py::test_tarea_titulo_max_length -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
cd backend
git add core/schemas.py tests/test_motor_desglose.py
git commit -m "feat: add Tarea Pydantic schema — PrioridadTarea, EstadoTarea, Tarea model"
```

---

### Task 2: Add `tareas_generadas` field to `NJM_OS_State`

**Files:**
- Modify: `backend/core/estado.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_motor_desglose.py`:

```python
def test_njm_os_state_has_tareas_generadas():
    from core.estado import NJM_OS_State
    import typing
    hints = typing.get_type_hints(NJM_OS_State, include_extras=True)
    assert "tareas_generadas" in hints
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py::test_njm_os_state_has_tareas_generadas -v
```
Expected: `AssertionError` — `tareas_generadas` not in hints

- [ ] **Step 3: Add field to `NJM_OS_State` in `backend/core/estado.py`**

After the `alertas_internas` field (around line 98), add:

```python
    tareas_generadas: Annotated[List[Dict[str, Any]], operator.add]
    # Tareas tácticas generadas por el PM al finalizar cada ejecución.
    # Acumulativo entre runs. Consumidas por el frontend Kanban via SSE.
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py::test_njm_os_state_has_tareas_generadas -v
```
Expected: PASSED

- [ ] **Step 5: Smoke test graph still compiles**

```bash
cd backend && .venv/bin/python3 -c "
import os, asyncio
os.environ.setdefault('OPENAI_API_KEY','test')
from agent.njm_graph import init_graph
asyncio.run(init_graph())
from agent.njm_graph import njm_graph
print('nodes:', [n for n in njm_graph.get_graph().nodes])
print('OK')
"
```
Expected: prints node list and `OK` — no crash

- [ ] **Step 6: Commit**

```bash
git add backend/core/estado.py backend/tests/test_motor_desglose.py
git commit -m "feat: add tareas_generadas field to NJM_OS_State — operator.add accumulator"
```

---

### Task 3: Add `_parsear_tareas()` parser to `agente_pm.py`

This is the most critical task. The parser extracts the `TAREAS:` YAML-like block from the PM's final response.

**Files:**
- Modify: `backend/agentes/agente_pm.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_motor_desglose.py`:

```python
def test_parsear_tareas_full_block():
    from agentes.agente_pm import _parsear_tareas

    texto = """
RESUMEN_PM:
  skill_utilizada: generar_plan_demanda
  propuesta_principal: Plan de demanda Q3 generado.
  framework_metodologico: AIDA + CAC optimization
  check_adn_aprobado: true
  justificacion_adn: Coherente con Vector 5

TAREAS:
- id: tarea-001
  titulo: Crear matriz de contenido LinkedIn Q3
  descripcion: Diseñar 12 posts mensuales alineados con buyer personas validados.
  responsable: PM
  prioridad: ALTA
  estado: BACKLOG
  skill_origen: generar_plan_demanda
- id: tarea-002
  titulo: Auditar CAC actual vs benchmark
  descripcion: Comparar CAC real con el techo de $120 USD del Libro Vivo.
  responsable: Encargado Real
  prioridad: MEDIA
  estado: BACKLOG
  skill_origen: generar_plan_demanda
"""
    tareas = _parsear_tareas(texto)
    assert len(tareas) == 2
    assert tareas[0]["id"] == "tarea-001"
    assert tareas[0]["prioridad"] == "ALTA"
    assert tareas[1]["responsable"] == "Encargado Real"


def test_parsear_tareas_no_block():
    from agentes.agente_pm import _parsear_tareas

    texto = "RESUMEN_PM:\n  skill_utilizada: generar_prd\n  propuesta_principal: PRD generado."
    tareas = _parsear_tareas(texto)
    assert tareas == []


def test_parsear_tareas_malformed_item_skipped():
    from agentes.agente_pm import _parsear_tareas

    texto = """TAREAS:
- id: tarea-001
  titulo: Tarea válida
  descripcion: desc
  responsable: PM
  prioridad: ALTA
  estado: BACKLOG
  skill_origen: generar_prd
- titulo: Sin ID — debe ignorarse
  descripcion: desc sin id
  responsable: CEO
  prioridad: BAJA
  estado: BACKLOG
  skill_origen: generar_prd
"""
    tareas = _parsear_tareas(texto)
    assert len(tareas) == 1
    assert tareas[0]["id"] == "tarea-001"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py::test_parsear_tareas_full_block tests/test_motor_desglose.py::test_parsear_tareas_no_block tests/test_motor_desglose.py::test_parsear_tareas_malformed_item_skipped -v
```
Expected: `ImportError: cannot import name '_parsear_tareas' from 'agentes.agente_pm'`

- [ ] **Step 3: Add `_parsear_tareas()` to `backend/agentes/agente_pm.py`**

Add after the `_parsear_resumen_pm` function (around line 312):

```python
def _parsear_tareas(texto: str) -> List[Dict[str, Any]]:
    """
    Extrae el bloque TAREAS: de la respuesta final del PM.

    Formato esperado:
        TAREAS:
        - id: tarea-001
          titulo: ...
          descripcion: ...
          responsable: PM | CEO | Encargado Real
          prioridad: ALTA | MEDIA | BAJA
          estado: BACKLOG
          skill_origen: <nombre_skill>

    Items sin 'id' o sin 'titulo' se descartan silenciosamente.
    Retorna [] si el bloque TAREAS: no está presente o está malformado.
    """
    section_match = re.search(r"TAREAS:\n((?:[ \t]*[-\w].*\n?)+)", texto, re.MULTILINE)
    if not section_match:
        return []

    raw = section_match.group(1)
    tareas: List[Dict[str, Any]] = []

    # Split on lines starting with "- id:"
    items = re.split(r"(?m)^- (?=id:)", raw)
    for item in items:
        if not item.strip():
            continue
        t: Dict[str, Any] = {}
        for line in item.splitlines():
            line = line.strip()
            if ":" in line:
                key, _, val = line.partition(":")
                t[key.strip()] = val.strip()
        if t.get("id") and t.get("titulo"):
            tareas.append(t)

    return tareas
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py::test_parsear_tareas_full_block tests/test_motor_desglose.py::test_parsear_tareas_no_block tests/test_motor_desglose.py::test_parsear_tareas_malformed_item_skipped -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/agentes/agente_pm.py backend/tests/test_motor_desglose.py
git commit -m "feat: add _parsear_tareas() — extracts TAREAS: block from PM final response"
```

---

### Task 4: Extend PM prompt and wire `nodo_pm` to extract tareas

**Files:**
- Modify: `backend/agentes/agente_pm.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_motor_desglose.py`:

```python
def test_nodo_pm_patch_includes_tareas(monkeypatch):
    """nodo_pm debe incluir tareas_generadas en el parche cuando el LLM las emite."""
    import os
    os.environ.setdefault("OPENAI_API_KEY", "test")
    
    from langchain_core.messages import AIMessage
    from agentes.agente_pm import nodo_pm
    from core.dev_fixtures import _LIBRO_VIVO_DISRUPT

    fake_response_with_tareas = AIMessage(content="""
RESUMEN_PM:
  skill_utilizada: generar_business_case
  propuesta_principal: Business case Q3 generado con ROI estimado 3.2x.
  framework_metodologico: Business Model Canvas
  check_adn_aprobado: true
  justificacion_adn: Alineado con Vector 7 North Star Metric

TAREAS:
- id: tarea-001
  titulo: Validar supuestos de CAC con datos reales
  descripcion: Cruzar benchmark de $120 USD CAC con datos históricos de CRM.
  responsable: Encargado Real
  prioridad: ALTA
  estado: BACKLOG
  skill_origen: generar_business_case
- id: tarea-002
  titulo: Presentar Business Case al CEO
  descripcion: Agendar sesión de 30 min para revisión con stakeholders.
  responsable: PM
  prioridad: MEDIA
  estado: BACKLOG
  skill_origen: generar_business_case
""")

    # Monkeypatch LLM to return fake response without tool calls
    monkeypatch.setattr(
        "agentes.agente_pm._LLM",
        type("FakeLLM", (), {
            "bind_tools": lambda self, tools: type("Bound", (), {
                "invoke": lambda self, msgs: fake_response_with_tareas
            })()
        })()
    )

    state = {
        "messages": [],
        "libro_vivo": _LIBRO_VIVO_DISRUPT,
        "alertas_internas": [],
        "documentos_generados": [],
        "estado_validacion": "EN_PROGRESO",
        "ruta_espacio_trabajo": "/tmp/test_workspace",
        "tareas_generadas": [],
    }

    parche = nodo_pm(state)

    assert "tareas_generadas" in parche
    assert len(parche["tareas_generadas"]) == 2
    assert parche["tareas_generadas"][0]["id"] == "tarea-001"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py::test_nodo_pm_patch_includes_tareas -v
```
Expected: FAILED — parche does not contain `tareas_generadas`

- [ ] **Step 3: Extend `_PROMPT_TEMPLATE_PM` with TAREAS block**

In `backend/agentes/agente_pm.py`, replace the `[FORMATO DE SALIDA ESTRICTO]` section of `_PROMPT_TEMPLATE_PM` (lines 130–144):

```python
[FORMATO DE SALIDA ESTRICTO (OUTPUT SCHEMA)]
NUNCA respondas con texto libre al finalizar. Cuando termines de ejecutar herramientas, \
resume tu trabajo en este formato estructurado exacto:

RESUMEN_PM:
  skill_utilizada: <nombre de la skill principal ejecutada>
  propuesta_principal: <1 oración de qué hiciste y por qué>
  framework_metodologico: <marco teórico que fundamenta la decisión>
  check_adn_aprobado: <true o false>
  justificacion_adn: <por qué la propuesta es coherente con el Libro Vivo>

TAREAS:
- id: tarea-001
  titulo: <título accionable, máx 60 caracteres>
  descripcion: <descripción ejecutable de 1 oración>
  responsable: <PM | CEO | Encargado Real>
  prioridad: <ALTA | MEDIA | BAJA>
  estado: BACKLOG
  skill_origen: <nombre de la skill que originó esta tarea>
- id: tarea-002
  titulo: <siguiente tarea>
  descripcion: <descripción>
  responsable: <PM | CEO | Encargado Real>
  prioridad: <ALTA | MEDIA | BAJA>
  estado: BACKLOG
  skill_origen: <nombre skill>

Reglas del bloque TAREAS:
- Genera MÍNIMO 3 y MÁXIMO 10 tareas derivadas de la skill ejecutada.
- Cada tarea debe ser una acción concreta y verificable.
- El campo 'responsable' debe asignarse según quién ejecuta realmente: \
  PM para tareas del agente, CEO para validaciones estratégicas, \
  Encargado Real para acciones humanas.
- Mantén 'estado: BACKLOG' en todas — el humano actualiza el estado.

Si entraste en bloqueo, en vez del resumen y tareas, escribe:
BLOQUEO_CEO:
  motivo: <qué restricción del Libro Vivo no se puede satisfacer>
  intentos_realizados: <número>
```

- [ ] **Step 4: Update `nodo_pm` to extract and store tareas**

In `backend/agentes/agente_pm.py`, in the `nodo_pm` function, after the `elif nuevos_documentos:` block (around line 446), before the `# Si no hay documentos...` comment:

Find this block:
```python
    elif nuevos_documentos:
        # Ejecución exitosa: documentos generados y sin bloqueo.
        parche["estado_validacion"] = EstadoValidacion.LISTO_PARA_FIRMA.value
        resumen = _parsear_resumen_pm(respuesta_final_texto)
        parche["payload_tarjeta_sugerencia"] = _construir_payload_exito(
            skill=skill_utilizada or "desconocida",
            documentos=nuevos_documentos,
            resumen=resumen,
        )
```

Replace with:
```python
    elif nuevos_documentos:
        # Ejecución exitosa: documentos generados y sin bloqueo.
        parche["estado_validacion"] = EstadoValidacion.LISTO_PARA_FIRMA.value
        resumen = _parsear_resumen_pm(respuesta_final_texto)
        parche["payload_tarjeta_sugerencia"] = _construir_payload_exito(
            skill=skill_utilizada or "desconocida",
            documentos=nuevos_documentos,
            resumen=resumen,
        )

    # Extract tareas regardless of outcome (success or non-blocking partial run).
    nuevas_tareas = _parsear_tareas(respuesta_final_texto)
    if nuevas_tareas:
        parche["tareas_generadas"] = nuevas_tareas
```

Also add the extraction after the `motivo_bloqueo` block so tareas are also captured even when there's a BLOQUEO (partial tareas before the block was hit). Find:

```python
    if motivo_bloqueo:
        # El PM declaró explícitamente que no puede resolver la petición.
        nuevas_alertas.append(f"BLOQUEO declarado por el PM: {motivo_bloqueo}")
        parche["estado_validacion"] = EstadoValidacion.BLOQUEO_CEO.value
        parche["payload_tarjeta_sugerencia"] = _construir_payload_bloqueo(
            motivo=motivo_bloqueo,
            skill=skill_utilizada or "ninguna",
            alertas=list(state.get("alertas_internas", [])) + nuevas_alertas,
        )

    elif nuevos_documentos:
```

Replace with:
```python
    if motivo_bloqueo:
        # El PM declaró explícitamente que no puede resolver la petición.
        nuevas_alertas.append(f"BLOQUEO declarado por el PM: {motivo_bloqueo}")
        parche["estado_validacion"] = EstadoValidacion.BLOQUEO_CEO.value
        parche["payload_tarjeta_sugerencia"] = _construir_payload_bloqueo(
            motivo=motivo_bloqueo,
            skill=skill_utilizada or "ninguna",
            alertas=list(state.get("alertas_internas", [])) + nuevas_alertas,
        )

    elif nuevos_documentos:
        # Ejecución exitosa: documentos generados y sin bloqueo.
        parche["estado_validacion"] = EstadoValidacion.LISTO_PARA_FIRMA.value
        resumen = _parsear_resumen_pm(respuesta_final_texto)
        parche["payload_tarjeta_sugerencia"] = _construir_payload_exito(
            skill=skill_utilizada or "desconocida",
            documentos=nuevos_documentos,
            resumen=resumen,
        )

    # Extract tareas regardless of outcome (present in both success and bloqueo).
    nuevas_tareas = _parsear_tareas(respuesta_final_texto)
    if nuevas_tareas:
        parche["tareas_generadas"] = nuevas_tareas
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py::test_nodo_pm_patch_includes_tareas -v
```
Expected: PASSED

- [ ] **Step 6: Run full test suite to verify no regressions**

```bash
cd backend && .venv/bin/python3 -m pytest tests/ -v
```
Expected: all previously passing tests still PASS

- [ ] **Step 7: Commit**

```bash
git add backend/agentes/agente_pm.py backend/tests/test_motor_desglose.py
git commit -m "feat: wire PM nodo to extract tareas_generadas — extend prompt + _parsear_tareas"
```

---

### Task 5: Emit `task_ready` SSE events from `_sse_njm_stream`

**Files:**
- Modify: `backend/api/v1_router.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_motor_desglose.py`:

```python
import asyncio
import json


def test_sse_emits_task_ready_events(monkeypatch):
    """_sse_njm_stream must emit task_ready events for each tarea in final state."""
    import os
    os.environ.setdefault("OPENAI_API_KEY", "test")

    from agent.njm_graph import init_graph
    asyncio.run(init_graph())
    from agent.njm_graph import njm_graph

    fake_tareas = [
        {
            "id": "tarea-001",
            "titulo": "Validar CAC",
            "descripcion": "Cruzar datos de CRM.",
            "responsable": "PM",
            "prioridad": "ALTA",
            "estado": "BACKLOG",
            "skill_origen": "generar_business_case",
        }
    ]

    class FakeSnapshot:
        values = {
            "estado_validacion": "LISTO_PARA_FIRMA",
            "tareas_generadas": fake_tareas,
        }
        next = []

    async def fake_astream_events(state, config, version):
        yield {"event": "on_chain_end", "name": "pm_execution", "data": {}}

    monkeypatch.setattr(njm_graph, "astream_events", fake_astream_events)
    monkeypatch.setattr(njm_graph, "aget_state", lambda config: FakeSnapshot())

    from api.v1_router import _sse_njm_stream

    async def collect():
        events = []
        async for chunk in _sse_njm_stream("disrupt", "test-session"):
            # chunk is "data: <json>\n\n"
            raw = chunk.replace("data: ", "").strip()
            if raw:
                events.append(json.loads(raw))
        return events

    events = asyncio.run(collect())
    types = [e["type"] for e in events]
    assert "task_ready" in types
    task_events = [e for e in events if e["type"] == "task_ready"]
    assert task_events[0]["tarea"]["id"] == "tarea-001"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py::test_sse_emits_task_ready_events -v
```
Expected: FAILED — no `task_ready` events in output

- [ ] **Step 3: Add `task_ready` emission to `_sse_njm_stream` in `backend/api/v1_router.py`**

In `_sse_njm_stream`, find the post-stream block that calls `aget_state` and emits `action_required`. It looks like:

```python
    # ── Post-stream state check ──────────────────────────────────────
    try:
        snapshot = await njm_graph.aget_state(config)
        ...
        yield _sse_json({"type": "done"})
    except Exception:
        yield _sse_json({"type": "done"})
```

Read the exact current code first with the Read tool (lines ~280–340 of `v1_router.py`), then add task_ready emission. The pattern to add is:

After the `action_required` check and before `yield _sse_json({"type": "done"})`, insert:

```python
        # Emit task_ready events for each tarea in final state.
        tareas = snapshot.values.get("tareas_generadas", []) or []
        for tarea in tareas:
            yield _sse_json({"type": "task_ready", "tarea": tarea})
```

The full post-stream block after the change should look like:

```python
    # ── Post-stream state check ──────────────────────────────────────
    try:
        snapshot = await njm_graph.aget_state(config)
        estado_validacion = snapshot.values.get("estado_validacion", "")
        has_interrupt = bool(snapshot.next)

        if estado_validacion == EstadoValidacion.BLOQUEO_CEO.value or has_interrupt:
            yield _sse_json({
                "type": "action_required",
                "trigger": "BLOQUEO_CEO",
                "risk_message": snapshot.values.get("risk_details", ""),
                "session_id": session_id,
                "brand_id": brand_id,
            })
        else:
            # Emit task_ready events for each tarea in final state.
            tareas = snapshot.values.get("tareas_generadas", []) or []
            for tarea in tareas:
                yield _sse_json({"type": "task_ready", "tarea": tarea})

            yield _sse_json({"type": "done"})

    except Exception:
        yield _sse_json({"type": "done"})
```

**IMPORTANT:** Read the actual current post-stream block in `v1_router.py` before editing — use the Read tool on lines 260–350 to get the exact current code. The structure above is the target; adapt to match actual line numbers.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && .venv/bin/python3 -m pytest tests/test_motor_desglose.py::test_sse_emits_task_ready_events -v
```
Expected: PASSED

- [ ] **Step 5: Run full test suite**

```bash
cd backend && .venv/bin/python3 -m pytest tests/ -v
```
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/v1_router.py backend/tests/test_motor_desglose.py
git commit -m "feat: emit task_ready SSE events from tareas_generadas after graph completes"
```

---

### Task 6: Add `tasks` state to `useAgentConsole`

**Files:**
- Modify: `frontend/hooks/useAgentConsole.ts`

- [ ] **Step 1: Add `Tarea` interface and `tasks` to the hook**

In `frontend/hooks/useAgentConsole.ts`, add after the `ActionRequiredEvent` interface:

```typescript
export interface Tarea {
  id: string;
  titulo: string;
  descripcion: string;
  responsable: "PM" | "CEO" | "Encargado Real";
  prioridad: "ALTA" | "MEDIA" | "BAJA";
  estado: "BACKLOG" | "EN_PROGRESO" | "DONE";
  skill_origen: string;
}
```

Add `tasks: Tarea[]` to `UseAgentConsoleReturn`:

```typescript
export interface UseAgentConsoleReturn {
  open: boolean;
  logs: string[];
  running: boolean;
  tasks: Tarea[];                         // NEW
  actionRequired: ActionRequiredEvent | null;
  invoke: (sequenceId: string, params?: Partial<AgentParams>) => void;
  resume: (answers: string, params: AgentParams) => Promise<void>;
  close: () => void;
}
```

Add `tasks` state inside the hook function:

```typescript
const [tasks, setTasks] = useState<Tarea[]>([]);
```

Reset `tasks` in `invoke` (after `setActionRequired(null)`):

```typescript
setTasks([]);
```

Add `task_ready` handler in `es.onmessage` (after the `action_required` handler):

```typescript
} else if (parsed.type === "task_ready") {
  const tarea = parsed.tarea as Tarea;
  if (tarea?.id && tarea?.titulo) {
    setTasks((prev) => [...prev, tarea]);
  }
}
```

Add `tasks` to the return statement:

```typescript
return { open, logs, running, tasks, actionRequired, invoke, close, resume };
```

Also reset tasks in `close`:
```typescript
const close = useCallback(() => {
  closeStream();
  setOpen(false);
  setRunning(false);
  setActionRequired(null);
  setTasks([]);
}, []);
```

- [ ] **Step 2: Type-check**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit
```
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add frontend/hooks/useAgentConsole.ts
git commit -m "feat: add tasks[] state to useAgentConsole — parses task_ready SSE events"
```

---

### Task 7: Wire Kanban board in `pm/page.tsx`

Replace the `Tablero Táctico` placeholder with a real 3-column Kanban.

**Files:**
- Modify: `frontend/app/brand/[id]/pm/page.tsx`

- [ ] **Step 1: Import `Tarea` type and define Kanban columns**

At the top of `pm/page.tsx`, add the import:

```typescript
import type { Tarea } from "@/hooks/useAgentConsole";
```

Add the column config constant (after `const SESSION_ID = ...`):

```typescript
const KANBAN_COLUMNS: { estado: Tarea["estado"]; label: string }[] = [
  { estado: "BACKLOG", label: "Backlog" },
  { estado: "EN_PROGRESO", label: "En Progreso" },
  { estado: "DONE", label: "Done" },
];

const PRIORIDAD_BADGE: Record<Tarea["prioridad"], string> = {
  ALTA:  "bg-rose-500/20 text-rose-400 border-rose-500/30",
  MEDIA: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  BAJA:  "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
};
```

- [ ] **Step 2: Destructure `tasks` from `agentConsole`**

Find:
```typescript
const agentConsole = useAgentConsole();
```

Replace with:
```typescript
const agentConsole = useAgentConsole();
const { tasks } = agentConsole;
```

- [ ] **Step 3: Replace the placeholder with the Kanban**

Find (around line 405):
```tsx
      {/* Tablero Táctico — Phase 2.6 placeholder */}
      <div className="mt-12">
        <div className="flex items-center gap-3 mb-4">
          <p
            className="text-xs uppercase tracking-widest font-semibold"
            style={{ color: "hsl(var(--pm-accent))" }}
          >
            Tablero Táctico
          </p>
          <span className="text-[10px] px-2 py-0.5 rounded-full font-mono text-muted-foreground/50 border border-white/[0.06]">
            Phase 2.6
          </span>
        </div>
        <div className="glass-subtle rounded-xl p-6 border border-white/[0.04] flex items-center gap-3">
          <span className="text-muted-foreground/30 text-lg" aria-hidden>⏳</span>
          <p className="text-sm text-muted-foreground/40 font-mono">
            Esperando desglose táctico del PM...
          </p>
        </div>
      </div>
```

Replace with:
```tsx
      {/* Tablero Táctico — Phase 2.6 */}
      <div className="mt-12">
        <div className="flex items-center gap-3 mb-4">
          <p
            className="text-xs uppercase tracking-widest font-semibold"
            style={{ color: "hsl(var(--pm-accent))" }}
          >
            Tablero Táctico
          </p>
          {tasks.length > 0 && (
            <span className="text-[10px] px-2 py-0.5 rounded-full font-mono text-pm/60 border border-pm/20">
              {tasks.length} tarea{tasks.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {tasks.length === 0 ? (
          <div className="glass-subtle rounded-xl p-6 border border-white/[0.04] flex items-center gap-3">
            <span className="text-muted-foreground/30 text-lg" aria-hidden>⏳</span>
            <p className="text-sm text-muted-foreground/40 font-mono">
              Esperando desglose táctico del PM...
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {KANBAN_COLUMNS.map(({ estado, label }) => {
              const col = tasks.filter((t) => t.estado === estado);
              return (
                <div key={estado} className="flex flex-col gap-2">
                  {/* Column header */}
                  <div className="flex items-center justify-between px-1 mb-1">
                    <span className="text-[10px] uppercase tracking-widest font-semibold text-muted-foreground/50">
                      {label}
                    </span>
                    <span className="text-[10px] font-mono text-muted-foreground/30">
                      {col.length}
                    </span>
                  </div>
                  {/* Cards */}
                  <div className="flex flex-col gap-2 min-h-[80px]">
                    {col.length === 0 ? (
                      <div className="rounded-lg border border-white/[0.04] border-dashed p-3 flex items-center justify-center">
                        <span className="text-[10px] text-muted-foreground/20 font-mono">vacío</span>
                      </div>
                    ) : (
                      col.map((tarea) => (
                        <div
                          key={tarea.id}
                          className="glass-subtle rounded-lg p-3 border border-white/[0.06] flex flex-col gap-1.5"
                        >
                          <p className="text-xs font-medium text-foreground/80 leading-snug">
                            {tarea.titulo}
                          </p>
                          <p className="text-[10px] text-muted-foreground/50 leading-relaxed">
                            {tarea.descripcion}
                          </p>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span
                              className={`text-[9px] px-1.5 py-0.5 rounded border font-mono uppercase tracking-wide ${PRIORIDAD_BADGE[tarea.prioridad as Tarea["prioridad"]] ?? ""}`}
                            >
                              {tarea.prioridad}
                            </span>
                            <span className="text-[9px] text-muted-foreground/30 font-mono">
                              {tarea.responsable}
                            </span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
```

- [ ] **Step 4: Type-check**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit
```
Expected: 0 errors

- [ ] **Step 5: Start dev server and verify Kanban renders**

```bash
cd frontend && npm run dev
```

Open `http://localhost:3000/brand/disrupt/pm` and verify:
- Placeholder text "Esperando desglose táctico del PM..." shown when `tasks` is empty
- After clicking "Consultar PM" and stream completes: Kanban fills with 3 columns
- BACKLOG column shows task cards with titulo, descripcion, prioridad badge, responsable
- EN_PROGRESO and DONE columns show "vacío" dashed placeholders
- Prioridad badges render correct colors: ALTA=rose, MEDIA=amber, BAJA=emerald
- No layout breakage in the artefactos grid above

- [ ] **Step 6: Commit**

```bash
git add frontend/app/brand/\[id\]/pm/page.tsx
git commit -m "feat: replace Tablero Táctico placeholder with live Kanban wired to tasks[]"
```

---

## Self-Review

### Spec coverage

| Requirement | Task |
|-------------|------|
| Backend sends `Tarea` objects, not strings | Task 1 (schema) + Task 4 (nodo_pm extract) |
| `tareas_generadas` in graph state | Task 2 |
| Parser for TAREAS: block | Task 3 |
| SSE emits `task_ready` per tarea | Task 5 |
| Hook accumulates tasks[] | Task 6 |
| Kanban fills with real data | Task 7 |
| PM prompt tells LLM to emit TAREAS: block | Task 4, Step 3 |

### Placeholder scan

No TBDs, TODOs, or "implement later" patterns. All code blocks complete.

### Type consistency

- `Tarea` interface in `useAgentConsole.ts` matches `Tarea` Pydantic model fields exactly (same field names, compatible types)
- `tareas_generadas: List[Dict[str, Any]]` in state — dicts serialize to JSON cleanly for SSE
- `PRIORIDAD_BADGE` record uses `Tarea["prioridad"]` key — type-safe
- `tasks.filter((t) => t.estado === estado)` — `estado` is `Tarea["estado"]` — type-safe

### Edge cases covered

- PM emits no TAREAS: block → `_parsear_tareas` returns `[]` → no `tareas_generadas` in patch → `tasks` stays `[]` → placeholder shown
- Malformed item (no id/titulo) → skipped silently by parser
- BLOQUEO_CEO path → tareas extracted if partially present before bloqueo declaration
- `tasks` reset on every `invoke()` call — no stale data from previous run

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-18-phase-2-6-motor-desglose.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** — Fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
