# ARCHITECTURE ROADMAP — PHASE 2
## NJM OS: Multi-Agent Brain

**Fecha:** 2026-04-16  
**Autor:** Principal AI Systems Architect (Auditoría de Código Base)  
**Fuente de verdad de producto:** `ARCHITECTURE.md`  
**Estado:** BORRADOR — Revisión requerida antes de implementación

---

## ÍNDICE

1. [Auditoría del Estado Actual (AS-IS)](#1-auditoría-del-estado-actual-as-is)
2. [Deuda Técnica y Puntos Críticos](#2-deuda-técnica-y-puntos-críticos)
3. [Diseño del Grafo Multi-Agente (TO-BE)](#3-diseño-del-grafo-multi-agente-to-be)
4. [AgentState Unificado](#4-agentstate-unificado)
5. [Nodos y Edges — Flujo Exacto](#5-nodos-y-edges--flujo-exacto)
6. [Persistencia: Checkpointer Strategy](#6-persistencia-checkpointer-strategy)
7. [Memoria Semántica: RAG Pipeline](#7-memoria-semántica-rag-pipeline)
8. [Error Handling & Fallbacks](#8-error-handling--fallbacks)
9. [Contrato de Integración Frontend ↔ Backend](#9-contrato-de-integración-frontend--backend)
10. [Hoja de Ruta de Implementación](#10-hoja-de-ruta-de-implementación)

---

## 1. Auditoría del Estado Actual (AS-IS)

### 1.1 Topología de Grafos Actual

El sistema **NO tiene un grafo multi-agente real**. Tiene dos grafos independientes y desconectados:

| Grafo | Archivo | State | Trigger | Streaming |
|-------|---------|-------|---------|-----------|
| `ceo_graph` | `agent/graph.py` | `AgentState` (3 keys) | `GET /api/v1/agent/stream?sequenceId=ceo-audit` | Sí — SSE via `astream_events` |
| `_GRAFO_PM` | `api/main.py` | `NJM_PM_State` (9 keys) | `POST /api/ejecutar-tarea` | No — sync via `asyncio.to_thread` |

**El handoff CEO → PM no existe.** El `_LIBRO_VIVO_DISRUPT` está hardcodeado en `api/main.py:65`. El CEO nunca escribe el Libro Vivo al estado que el PM lee.

### 1.2 El Problema de los Dos CEOs

Existe un `nodo_ceo` completamente implementado en `agentes/agente_ceo.py` con las 5 herramientas CEO, el agentic loop de 10 iteraciones, y manejo de side-effects. **Este nodo nunca es invocado.** El `ceo_graph` en `agent/graph.py` usa `ceo_auditor_node`, un nodo distinto y simplificado que solo llama al LLM sin herramientas.

```
agente_ceo.py::nodo_ceo    ← IMPLEMENTADO PERO HUÉRFANO
agent/graph.py::ceo_auditor_node  ← WIRED pero sin herramientas CEO
```

### 1.3 El Problema del Ingest

`POST /api/v1/ingest` guarda archivos en `backend/temp_uploads/`. El CEO tool `escanear_directorio_onboarding` lee desde `~/NJM_OS/`. **Estos dos paths nunca se conectan.** Los documentos subidos desde el frontend no llegan al CEO.

### 1.4 Estado del Frontend

| Componente | Estado real | Estado aparente |
|-----------|-------------|-----------------|
| CEO Workspace — vectores | Mock estático (`MOCK_VECTORES`) | Parece dinámico |
| PM Workspace — artefactos | Mock estático (`MOCK_ARTEFACTOS`) | Parece dinámico |
| SSE `ceo-audit` | Real (Claude streaming) | ✓ |
| SSE `pm-execution` | Mock script hardcodeado | Parece real |
| `POST /api/ejecutar-tarea` | **Nunca llamado desde frontend** | — |
| CEOShield trigger | Dev button manual | No conectado a BLOQUEO_CEO real |

---

## 2. Deuda Técnica y Puntos Críticos

### 2.1 CRÍTICO — Sin Session/Brand Context Threading

`useAgentConsole.invoke(sequenceId)` pasa solo `sequenceId`. No pasa `brand_id`, `session_id`, ni contexto de usuario. Cada request SSE es **stateless** desde el frontend.

**Consecuencia:** Imposible construir sesiones multi-turno ni multi-marca sin refactorizar el hook.

**Fix requerido en Phase 2:**
```typescript
// useAgentConsole debe aceptar params adicionales
invoke(sequenceId: string, params?: Record<string, string>): void
// URL: /api/v1/agent/stream?sequenceId=ceo-audit&brand_id=disrupt&session_id=uuid
```

### 2.2 CRÍTICO — URL Length Limit en SSE con brand_context

`GET /api/v1/agent/stream?sequenceId=ceo-audit&brand_context=<texto>` pasa el contexto de marca como query param. El `_DEFAULT_BRAND_CONTEXT` actual tiene ~230 chars. Un `LibroVivo` real tiene ~3,000–8,000 chars. **Los proxies y browsers truncan URLs > 2,048 chars.**

**Fix requerido:** Cambiar a `POST` con `ReadableStream` o usar un `session_id` que el backend resuelve a contexto desde el checkpointer.

### 2.3 ALTO — nodo_ceo Huérfano

`agentes/agente_ceo.py::nodo_ceo` tiene las 5 herramientas CEO (`escanear_directorio_onboarding`, `generar_reporte_brechas`, `iniciar_entrevista_profundidad`, `escribir_libro_vivo`, `levantar_tarjeta_roja`), el agentic loop y el side-effect handling. Es el código real del CEO. Debe ser wired al grafo unificado.

### 2.4 ALTO — Output Parsing Frágil del PM

`_parsear_resumen_pm()` usa regex sobre texto libre. Si el LLM omite indentación exacta o cambia el formato, retorna `{}` silenciosamente. El payload de éxito usa defaults genéricos sin error visible.

**Fix:** Usar `model.with_structured_output(ResumenPM)` de LangChain con un Pydantic model, con retry en caso de fallo de parsing.

### 2.5 ALTO — Sin Persistencia

Restart del server = pérdida de todo el estado de conversación. Sin checkpointer, Human-in-the-Loop es imposible (el grafo no puede pausar y reanudarse).

### 2.6 MEDIO — Doble Instanciación de ChatAnthropic

`nodo_pm` y `nodo_ceo` instancian `ChatAnthropic(...)` en cada invocación del nodo. Con concurrencia o sesiones largas esto crea N clientes HTTP por run. Debe moverse a nivel de módulo como `_LLM` singleton (ya implementado en `agent/graph.py`, no en los agentes).

### 2.7 MEDIO — temp_uploads sin TTL ni Procesamiento

`POST /api/v1/ingest` guarda archivos y retorna `"success"` sin procesarlos. No hay extracción de texto, no hay embedding, no hay conexión al CEO scan. Es un endpoint placeholder.

### 2.8 BAJO — `asyncio.to_thread` como Parche Temporal

`_GRAFO_PM.invoke()` es síncrono. `api/main.py` usa `asyncio.to_thread()` para no bloquear el event loop. Funciona pero no es escalable. En Phase 2 migrar al grafo unificado con `astream_events` completo.

### 2.9 BAJO — CORS Hardcodeado a localhost:3000

`main.py:14` permite solo `http://localhost:3000`. En staging/prod esto rompe. Debe parametrizarse vía env var `ALLOWED_ORIGINS`.

---

## 3. Diseño del Grafo Multi-Agente (TO-BE)

### 3.1 Principio de Diseño

Un **único grafo compilado** (`njm_graph`) reemplaza los dos grafos actuales. La arquitectura sigue el patrón **Supervisor + Specialized Agents** de LangGraph:

- El grafo orquesta el flujo completo: Ingest → CEO Audit → Human-in-Loop → PM Execution → CEO Review → Output.
- Los nodos CEO y PM son **nodos especializados** dentro del mismo grafo, compartiendo el mismo state.
- El checkpointer permite suspender y reanudar el grafo en cualquier `interrupt()`.

### 3.2 Diagrama de Flujo

```
START
  │
  ▼
[ingest_node]
  │  Guarda docs en vector store, prepara brand_context_raw
  │
  ▼
[ceo_auditor_node]  ← nodo_ceo de agente_ceo.py (ahora wired)
  │  Escanea docs, mapea 9 vectores, escribe libro_vivo o genera gap report
  │
  ├─→ audit_status == "COMPLETE"
  │     │
  │     ▼
  │   [pm_execution_node]
  │     │  Ejecuta skill, genera artefactos
  │     │
  │     ├─→ estado_validacion == "LISTO_PARA_FIRMA"
  │     │     │
  │     │     ▼
  │     │   [output_node]  →  END
  │     │
  │     └─→ estado_validacion == "BLOQUEO_CEO"
  │           │
  │           ▼
  │         [ceo_review_node]
  │           │
  │           ├─→ ceo_decision == "APPROVED" → [pm_execution_node]  (retry)
  │           ├─→ ceo_decision == "REJECTED" → [output_node] → END
  │           └─→ ceo_decision == "ESCALATE" → [human_in_loop_node] ⏸️ INTERRUPT
  │
  └─→ audit_status == "GAP_DETECTED"
        │
        ▼
      [human_in_loop_node]  ⏸️ INTERRUPT
        │  Pausa grafo. Frontend muestra preguntas de entrevista.
        │  Humano responde. Frontend reanuda con `invoke(thread_id, human_response)`.
        │
        ▼
      [ceo_auditor_node]  (re-audit con nueva info)
```

---

## 4. AgentState Unificado

El estado actual tiene dos schemas incompatibles (`AgentState` y `NJM_PM_State`). Phase 2 usa un único TypedDict:

```python
# backend/core/estado.py — REEMPLAZA el NJM_PM_State actual

import operator
from typing import Annotated, Any, Dict, List, Literal, Optional
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class NJM_OS_State(TypedDict):
    """
    Estado unificado del grafo multi-agente NJM OS.
    
    Ciclo de vida:
      ingest_node → ceo_auditor_node → [human_in_loop?] → pm_execution_node
      → [ceo_review?] → output_node
    """

    # ── IDENTIDAD DE SESIÓN ────────────────────────────────────────
    brand_id: str
    # Slug de la marca. Ej.: "disrupt". Clave del thread del checkpointer.
    
    session_id: str
    # UUID v4 por sesión de usuario. Combinado con brand_id forma el thread_id.
    # thread_id = f"{brand_id}:{session_id}"

    # ── HISTORIAL DE CONVERSACIÓN ──────────────────────────────────
    messages: Annotated[list, add_messages]
    # Acumula HumanMessage, AIMessage y ToolMessage de AMBOS agentes.
    # add_messages nunca sobrescribe — solo appends.

    # ── INPUT DE ONBOARDING ────────────────────────────────────────
    brand_context_raw: str
    # Texto crudo extraído de los docs subidos por el frontend vía /api/v1/ingest.
    # El CEO lo lee para iniciar la auditoría.

    uploaded_doc_paths: Annotated[List[str], operator.add]
    # Rutas en temp_uploads/ o vector store de docs ingeridos.
    # Acumulativo: cada ingest añade sin borrar.

    # ── CEO — AUDITORÍA ────────────────────────────────────────────
    audit_status: Literal["PENDING", "IN_PROGRESS", "GAP_DETECTED", "COMPLETE", "RISK_BLOCKED"]
    # PENDING: CEO no ha corrido. GAP_DETECTED: pausa HITL activa.
    # COMPLETE: libro_vivo escrito y validado. RISK_BLOCKED: tarjeta roja activa.

    gap_report_path: Optional[str]
    # Ruta del archivo 00_GAP_ANALYSIS_*.md generado por CEO si hay brechas.
    
    interview_questions: Optional[List[str]]
    # Preguntas C-Suite generadas por CEO para el Encargado Real.
    # El frontend las renderiza en el DayCeroView wizard (aún no construido).

    human_interview_answers: Optional[str]
    # Respuestas del humano al cuestionario CEO. Input para el re-audit.

    libro_vivo: Optional[Dict[str, Any]]
    # JSON final validado por CEO. LibroVivo Pydantic schema.
    # READ-ONLY para el PM. Escrito por ceo_auditor_node::escribir_libro_vivo tool.

    # ── CONTROL DE RIESGO ──────────────────────────────────────────
    risk_flag: bool
    # True cuando CEO activa levantar_tarjeta_roja o PM activa BLOQUEO_CEO.
    
    risk_details: Optional[str]
    # Descripción del riesgo activo. Enviada al frontend como riskMessage del CEOShield.

    ceo_review_decision: Optional[Literal["APPROVED", "REJECTED", "ESCALATE"]]
    # Decisión del CEO al revisar output del PM.

    # ── PM — EJECUCIÓN ─────────────────────────────────────────────
    peticion_humano: Optional[str]
    # Instrucción cruda del Encargado Real para el PM.

    ruta_espacio_trabajo: str
    # Ruta local donde el PM guarda artefactos.
    # Default: f"~/NJM_OS/Marcas/{brand_id}/workspace/"

    skill_activa: Optional[str]
    # Última skill PM ejecutada. Ej.: "generar_business_case".

    documentos_generados: Annotated[List[str], operator.add]
    # Rutas absolutas de artefactos generados por el PM en este run.

    estado_validacion: Literal["EN_PROGRESO", "LISTO_PARA_FIRMA", "BLOQUEO_CEO"]
    # Semáforo de gobernanza del PM.

    alertas_internas: Annotated[List[str], operator.add]
    # Alertas de autocorrección del PM. Max 2 antes de escalar.

    # ── OUTPUT ─────────────────────────────────────────────────────
    payload_tarjeta_sugerencia: Optional[Dict[str, Any]]
    # TarjetaSugerenciaUI JSON. Emitido por output_node.
    # None hasta que el grafo finalice. Frontend hace GET para obtenerlo.

    # ── ROUTING INTERNO ────────────────────────────────────────────
    next_node: Optional[str]
    # Hint de routing para conditional edges.
    # Valores: "pm_execution" | "human_in_loop" | "ceo_review" | "output"
```

### 4.1 Reductores y Reglas de Escritura

| Key | Reductor | Quién escribe | Quién lee |
|-----|----------|--------------|-----------|
| `messages` | `add_messages` (append) | Todos los nodos | Todos |
| `documentos_generados` | `operator.add` (append) | `pm_execution_node` | `output_node`, frontend |
| `alertas_internas` | `operator.add` (append) | `pm_execution_node` | `pm_execution_node` (autocorrección) |
| `uploaded_doc_paths` | `operator.add` (append) | `ingest_node` | `ceo_auditor_node` |
| `libro_vivo` | Overwrite (last-write-wins) | `ceo_auditor_node` | `pm_execution_node` (read-only) |
| `audit_status` | Overwrite | `ceo_auditor_node` | Router edges |
| `estado_validacion` | Overwrite | `pm_execution_node` | Router edges |
| `risk_flag` | Overwrite | `ceo_auditor_node`, `pm_execution_node` | Frontend (SSE event) |
| `payload_tarjeta_sugerencia` | Overwrite | `output_node` | Frontend (GET endpoint) |

---

## 5. Nodos y Edges — Flujo Exacto

### 5.1 `ingest_node`

**Responsabilidad:** Recibir docs del frontend, extraer texto, almacenar en vector store, actualizar `brand_context_raw`.

**Inputs del state:** `uploaded_doc_paths`, `brand_id`  
**Outputs al state:** `brand_context_raw` (texto concatenado de todos los docs)

**Implementación:**
```python
async def ingest_node(state: NJM_OS_State) -> Dict[str, Any]:
    # 1. Leer todos los docs en uploaded_doc_paths
    # 2. Extraer texto (pypdf para PDFs, read_text para .md/.txt)
    # 3. Hacer chunk (RecursiveCharacterTextSplitter, chunk_size=1000)
    # 4. Embed y upsert en ChromaDB collection f"brand_{state['brand_id']}"
    # 5. Concatenar texto crudo para brand_context_raw (≤ 8,000 chars para CEO prompt)
    return {"brand_context_raw": extracted_text}
```

**Nota:** Este nodo corre solo cuando hay `uploaded_doc_paths` nuevos. Si el `libro_vivo` ya existe en el checkpointer, el grafo puede saltar directamente a `pm_execution_node`.

### 5.2 `ceo_auditor_node`

**Responsabilidad:** Auditar los 9 vectores, escribir libro_vivo o detectar gaps.

**Cambio clave respecto al estado actual:** Usar `nodo_ceo` de `agentes/agente_ceo.py` (el nodo con las 5 herramientas), NO el `ceo_auditor_node` actual de `agent/graph.py`. Adaptar la firma para usar `NJM_OS_State`.

**Inputs del state:** `brand_context_raw`, `human_interview_answers` (si re-audit), `messages`  
**Outputs al state:** `libro_vivo`, `audit_status`, `gap_report_path`, `interview_questions`, `risk_flag`, `messages`

**Lógica de routing interna:**
```python
def route_after_ceo(state: NJM_OS_State) -> str:
    if state["audit_status"] == "COMPLETE":
        return "pm_execution"
    elif state["audit_status"] == "GAP_DETECTED":
        return "human_in_loop"
    elif state["audit_status"] == "RISK_BLOCKED":
        return "output"     # Emitir tarjeta roja directamente
    return "human_in_loop"  # Default seguro
```

### 5.3 `human_in_loop_node` (INTERRUPT)

**Responsabilidad:** Suspender el grafo para input humano. El frontend recibe las preguntas vía SSE event `"type": "interview_start"` y renderiza el DayCeroView wizard.

```python
from langgraph.types import interrupt

def human_in_loop_node(state: NJM_OS_State) -> Dict[str, Any]:
    # Suspend graph execution here.
    # Frontend must call POST /api/v1/agent/resume with:
    #   { thread_id, human_answers: "Vector 1.1: ..." }
    human_response = interrupt({
        "type": "interview_required",
        "questions": state["interview_questions"],
        "gap_report_path": state["gap_report_path"],
    })
    return {"human_interview_answers": human_response["answers"]}
```

**Reanudación:** `POST /api/v1/agent/resume` recibe `{ thread_id, answers }` y llama `njm_graph.invoke({"human_interview_answers": answers}, config)`.

### 5.4 `pm_execution_node`

**Responsabilidad:** Ejecutar skill del PM, generar artefactos.

**Cambio respecto al estado actual:** Misma lógica de `nodo_pm` de `agentes/agente_pm.py`, adaptada para usar `NJM_OS_State`. Sin cambios en las 14 skills.

**Inputs del state:** `libro_vivo`, `peticion_humano`, `ruta_espacio_trabajo`, `alertas_internas`  
**Outputs al state:** `documentos_generados`, `estado_validacion`, `alertas_internas`, `skill_activa`, `messages`

**Lógica de routing:**
```python
def route_after_pm(state: NJM_OS_State) -> str:
    if state["estado_validacion"] == "LISTO_PARA_FIRMA":
        return "output"
    elif state["estado_validacion"] == "BLOQUEO_CEO":
        return "ceo_review"
    return "output"  # EN_PROGRESO no debería llegar aquí
```

### 5.5 `ceo_review_node` (INTERRUPT opcional)

**Responsabilidad:** CEO revisa el output del PM cuando hay BLOQUEO_CEO. Puede aprobar (con condiciones), rechazar o escalar al humano.

**Implementación:**
```python
def ceo_review_node(state: NJM_OS_State) -> Dict[str, Any]:
    # CEO analiza alertas_internas y payload del PM
    # Usa el mismo LLM del CEO con un prompt de revisión
    # Resultado: ceo_review_decision = "APPROVED" | "REJECTED" | "ESCALATE"
    
    if needs_human_approval:
        # Escalar al humano vía interrupt
        decision = interrupt({
            "type": "ceo_shield_required",
            "risk_message": state["risk_details"],
            "pm_output": state["payload_tarjeta_sugerencia"],
        })
        return {"ceo_review_decision": decision["choice"]}
    
    return {"ceo_review_decision": auto_decision}
```

**Lógica de routing:**
```python
def route_after_ceo_review(state: NJM_OS_State) -> str:
    decision = state.get("ceo_review_decision")
    if decision == "APPROVED":
        return "pm_execution"   # Retry con instrucciones de corrección
    elif decision == "REJECTED":
        return "output"         # Emitir tarjeta de bloqueo
    else:  # ESCALATE
        return "human_in_loop"
```

### 5.6 `output_node`

**Responsabilidad:** Construir el payload `TarjetaSugerenciaUI` final. Registrar en DB si hay persistencia.

```python
def output_node(state: NJM_OS_State) -> Dict[str, Any]:
    # Build final TarjetaSugerenciaUI based on estado_validacion
    # Store result keyed by (brand_id, session_id) for frontend polling
    # Emit SSE event "type": "done" con el payload completo
    return {"payload_tarjeta_sugerencia": payload}
```

### 5.7 Compilación del Grafo

```python
# backend/agent/njm_graph.py

builder = StateGraph(NJM_OS_State)

# Nodos
builder.add_node("ingest", ingest_node)
builder.add_node("ceo_auditor", ceo_auditor_node)       # usa nodo_ceo
builder.add_node("human_in_loop", human_in_loop_node)
builder.add_node("pm_execution", pm_execution_node)     # usa nodo_pm
builder.add_node("ceo_review", ceo_review_node)
builder.add_node("output", output_node)

# Edges
builder.add_edge(START, "ingest")
builder.add_edge("ingest", "ceo_auditor")

builder.add_conditional_edges(
    "ceo_auditor",
    route_after_ceo,
    {
        "pm_execution": "pm_execution",
        "human_in_loop": "human_in_loop",
        "output": "output",
    }
)

builder.add_edge("human_in_loop", "ceo_auditor")  # Re-audit after answers

builder.add_conditional_edges(
    "pm_execution",
    route_after_pm,
    {
        "output": "output",
        "ceo_review": "ceo_review",
    }
)

builder.add_conditional_edges(
    "ceo_review",
    route_after_ceo_review,
    {
        "pm_execution": "pm_execution",
        "output": "output",
        "human_in_loop": "human_in_loop",
    }
)

builder.add_edge("output", END)

# Compilar CON checkpointer
from langgraph.checkpoint.sqlite import SqliteSaver
memory = SqliteSaver.from_conn_string("./njm_sessions.db")
njm_graph = builder.compile(checkpointer=memory)
```

---

## 6. Persistencia: Checkpointer Strategy

### 6.1 Problema

Sin checkpointer, `interrupt()` en `human_in_loop_node` y `ceo_review_node` no funciona. El grafo no puede pausar. Restart del servidor = pérdida de sesión.

### 6.2 Thread ID Convention

```python
# Cada sesión de marca es un thread único en el checkpointer.
thread_id = f"{brand_id}:{session_id}"

# Config que se pasa en cada invocación del grafo:
config = {"configurable": {"thread_id": thread_id}}

# Invocar:
await njm_graph.ainvoke(initial_state, config=config)

# Reanudar (tras interrupt):
await njm_graph.ainvoke({"human_interview_answers": answers}, config=config)
```

### 6.3 Implementación por Ambiente

| Ambiente | Checkpointer | Driver | Notas |
|----------|-------------|--------|-------|
| **Desarrollo** | `SqliteSaver` | `aiosqlite` | Archivo local `./njm_sessions.db`. Zero config. |
| **Staging** | `AsyncSqliteSaver` | `aiosqlite` | Mismo esquema, async-native. |
| **Producción** | `PostgresSaver` | `asyncpg` | Connection pool. Env var `DATABASE_URL`. |

```python
# backend/core/checkpointer.py
import os
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def get_checkpointer():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return await AsyncPostgresSaver.from_conn_string(db_url)
    return await AsyncSqliteSaver.from_conn_string("./njm_sessions.db")
```

### 6.4 Session Lifecycle

```
Frontend genera session_id (uuid v4) al cargar brand workspace.
  │
  ├─ Guarda en localStorage: "njm_session_{brand_id}" = session_id
  │
  └─ Pasa session_id en headers o params a todos los endpoints del backend.

Backend usa (brand_id, session_id) → thread_id → checkpointer.get_state(thread_id)
  │
  ├─ Si existe snapshot → reanudar desde último checkpoint
  └─ Si no existe → iniciar nuevo grafo
```

### 6.5 TTL y Limpieza

- Sessions sin actividad por >7 días: marcar como `ARCHIVED` en metadata del thread.
- Implementar job diario (FastAPI lifespan event) que purga threads archivados.
- `libro_vivo` y `documentos_generados` **no se borran** con la sesión — son datos de marca permanentes.

---

## 7. Memoria Semántica: RAG Pipeline

### 7.1 Arquitectura

```
[Frontend Upload]
      │
      ▼
POST /api/v1/ingest
      │
      ├─ Guardar raw file → temp_uploads/
      ├─ Extraer texto (pypdf / plain read)
      ├─ Chunk text (RecursiveCharacterTextSplitter, chunk_size=1000, overlap=100)
      ├─ Embed (claude-3-haiku via /messages o text-embedding via OpenAI compat)
      └─ Upsert → ChromaDB collection: f"brand_{brand_id}_onboarding"
             │
             └─ Metadata: { brand_id, filename, upload_ts, vector_hint }

[ceo_auditor_node]
      │
      ├─ Query ChromaDB: "¿Qué dice este doc sobre [vector_N_name]?"
      ├─ Top-k chunks (k=5) por vector
      └─ Inyectar en CEO prompt como contexto aumentado

[pm_execution_node]
      │
      ├─ Query ChromaDB collection: f"brand_{brand_id}_artifacts"
      ├─ Recuperar artefactos similares de ejecuciones previas
      └─ Usar como few-shot examples en el PM prompt
```

### 7.2 Colecciones ChromaDB

| Colección | Contenido | Escrito por | Leído por |
|-----------|-----------|-------------|-----------|
| `brand_{id}_onboarding` | Chunks de docs subidos por el cliente | `ingest_node` | `ceo_auditor_node` |
| `brand_{id}_libro_vivo` | Chunks del LibroVivo validado (9 vectores como documentos) | `ceo_auditor_node` tras escribir libro | `pm_execution_node` |
| `brand_{id}_artifacts` | Artefactos PM previos (Business Cases, PRDs, etc.) | `output_node` | `pm_execution_node` (few-shot) |

### 7.3 Implementación Mínima (Phase 2)

```python
# backend/core/vector_store.py
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_anthropic import AnthropicEmbeddings  # o usar OpenAI text-embedding

_client = chromadb.PersistentClient(path="./chroma_db")

def get_collection(brand_id: str, suffix: str):
    return _client.get_or_create_collection(f"brand_{brand_id}_{suffix}")

async def ingest_document(brand_id: str, text: str, filename: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(text)
    collection = get_collection(brand_id, "onboarding")
    # Upsert con IDs únicos (filename + chunk_index)
    collection.add(
        documents=chunks,
        ids=[f"{filename}:{i}" for i in range(len(chunks))],
        metadatas=[{"filename": filename, "chunk_idx": i} for i in range(len(chunks))],
    )

def query_brand_context(brand_id: str, query: str, n_results: int = 5) -> str:
    collection = get_collection(brand_id, "onboarding")
    results = collection.query(query_texts=[query], n_results=n_results)
    return "\n\n".join(results["documents"][0])
```

### 7.4 Nota sobre Embeddings

ChromaDB por defecto usa `all-MiniLM-L6-v2` (local, no necesita API key). Para Phase 2 esto es suficiente. En producción, migrar a `text-embedding-3-small` de OpenAI o el endpoint de embeddings de Anthropic cuando esté disponible.

### 7.5 CEO Prompt Augmentation

```python
# En ceo_auditor_node, antes de invocar el LLM:
retrieved_context = query_brand_context(
    brand_id=state["brand_id"],
    query=f"información sobre {vector_name}",
    n_results=5
)
context_note = f"\n\n[CONTEXTO RAG — DOCUMENTOS DE ONBOARDING]\n{retrieved_context}"
# Inyectar en system prompt, antes del brand_context_raw
```

---

## 8. Error Handling & Fallbacks

### 8.1 LLM Failures (Network / Rate Limit / Timeout)

**Estrategia:** Retry con exponential backoff usando `tenacity`.

```python
# backend/core/llm_utils.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from anthropic import APIConnectionError, RateLimitError, APITimeoutError

@retry(
    retry=retry_if_exception_type((APIConnectionError, RateLimitError, APITimeoutError)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
def invoke_with_retry(model, messages):
    return model.invoke(messages)
```

**Fallback si los 3 intentos fallan:** Emitir `payload_tarjeta_sugerencia` con `estado_ejecucion: BLOQUEO_CEO`, `motivo: "Error de conexión con el modelo de lenguaje. Reintenta en unos minutos."`. No crashear el endpoint.

### 8.2 Output Parsing Failures

**Problema:** `_parsear_resumen_pm()` retorna `{}` sin error si el LLM no sigue el formato `RESUMEN_PM:`.

**Fix — Structured Output con fallback:**
```python
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

class ResumenPM(BaseModel):
    skill_utilizada: str = Field(default="desconocida")
    propuesta_principal: str = Field(default="Ver documento generado.")
    framework_metodologico: str = Field(default="N/A")
    check_adn_aprobado: bool = Field(default=True)
    justificacion_adn: str = Field(default="Pendiente de revisión.")

# En pm_execution_node, para el output final:
structured_llm = llm.with_structured_output(ResumenPM, include_raw=True)
result = structured_llm.invoke(final_messages)
if result["parsing_error"]:
    # Log el error, usar defaults del modelo Pydantic
    resumen = ResumenPM()
else:
    resumen = result["parsed"]
```

### 8.3 SSE Disconnection

**Problema:** Si el browser cierra la conexión SSE a mitad del stream, el generador sigue corriendo en el servidor (gastando tokens). Cuando el cliente reconecta, no recupera los tokens ya emitidos.

**Fix:**
1. **Server-side:** Detectar `CancelledError` en el generador SSE y hacer cleanup del grafo.
```python
async def _sse_agent_stream(...):
    try:
        async for event in njm_graph.astream_events(...):
            yield f"data: {event_data}\n\n"
    except asyncio.CancelledError:
        # Client disconnected. Cleanup gracefully.
        return
```

2. **`Last-Event-ID` support:** El frontend debe pasar `Last-Event-ID` en la reconexión. El backend consulta el checkpointer para encontrar el último estado guardado y retransmite desde ahí.

3. **Frontend retry logic:**
```typescript
// En useAgentConsole: si SSE cierra con error, reintentar con exponential backoff
// usando el mismo session_id (el backend puede reanudad desde checkpoint)
```

### 8.4 Graph Execution Timeout

**Problema:** Un nodo con herramientas puede quedarse bloqueado (ej: `escanear_directorio_onboarding` en un directorio con miles de archivos).

**Fix:** `asyncio.wait_for` con timeout configurable:
```python
# En cada nodo que invoca herramientas externas:
try:
    resultado = await asyncio.wait_for(
        asyncio.to_thread(herramienta.invoke, args),
        timeout=60.0  # 60 segundos máximo por tool call
    )
except asyncio.TimeoutError:
    resultado = f"ERROR: La herramienta tardó más de 60 segundos. Reintenta con menos datos."
```

**Timeout global del endpoint:** FastAPI `asyncio.wait_for` de 300s en `agent_stream`. Si excede, emitir `[DONE]` con error en los logs.

### 8.5 PM Skill Tool Failures

El mecanismo actual ya maneja errores por skill con `try/except` y registra alertas. Falta:

1. **Circuit breaker:** Si la misma skill falla 2 veces consecutivas, no reintentar. Emitir `BLOQUEO_CEO` directamente.
2. **Distinguir error types:** `FileNotFoundError` (ruta_espacio_trabajo no existe) es diferente a `LLM parsing error`. Mensaje al humano debe ser específico.

### 8.6 Human-in-the-Loop Timeout

Si el humano no responde al cuestionario CEO después de N horas, el thread del checkpointer queda en estado `interrupted`. El frontend debe:
1. Detectar estado `"audit_status": "GAP_DETECTED"` al cargar la página (polling del estado del thread).
2. Mostrar el wizard de entrevista aunque la página se haya recargado.

```python
# Nuevo endpoint:
# GET /api/v1/session/state?brand_id=disrupt&session_id=uuid
# Retorna el snapshot actual del checkpointer para este thread
async def get_session_state(brand_id: str, session_id: str):
    thread_id = f"{brand_id}:{session_id}"
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = await njm_graph.aget_state(config)
    return {
        "audit_status": snapshot.values.get("audit_status"),
        "interview_questions": snapshot.values.get("interview_questions"),
        "next_interrupt": snapshot.next,  # Qué nodo pausó el grafo
    }
```

---

## 9. Contrato de Integración Frontend ↔ Backend

### 9.1 Cambios Requeridos en useAgentConsole

```typescript
// hooks/useAgentConsole.ts — Phase 2

export interface UseAgentConsoleReturn {
  open: boolean;
  logs: string[];
  running: boolean;
  sessionState: SessionState | null;   // NUEVO: estado del checkpointer
  invoke: (sequenceId: string, params: AgentParams) => void;
  resume: (answers: string) => void;   // NUEVO: reanudar tras interrupt
  close: () => void;
}

interface AgentParams {
  brand_id: string;
  session_id: string;
  peticion?: string;          // Para PM execution
  brand_context?: string;     // Para CEO audit (texto corto, < 500 chars)
  // Context largo se pasa vía session_id → checkpointer lookup en backend
}

// SSE URL: GET /api/v1/agent/stream?sequenceId=ceo-audit&brand_id=...&session_id=...
// Sin brand_context en URL. El backend lo lee del checkpointer por session_id.
```

### 9.2 Eventos SSE Estructurados (Phase 2)

El stream actual emite texto plano. Phase 2 requiere eventos tipados:

```
// Tipos de eventos SSE emitidos por el backend:

data: {"type": "log", "text": "[✓] CEO Audit iniciada...", "ts": 1234567890}

data: {"type": "vector_update", "vector_id": 3, "status": "COMPLETE", "ts": ...}

data: {"type": "interview_start", "questions": [...], "gap_report_path": "..."}

data: {"type": "ceo_shield", "risk_message": "...", "risk_level": "financiero"}

data: {"type": "artifact_ready", "filename": "Business_Case_Q2.md", "path": "file://..."}

data: {"type": "tarjeta_ready", "payload": { ...TarjetaSugerenciaUI... }}

data: {"type": "error", "message": "LLM timeout after 3 retries"}

data: [DONE]
```

**Frontend** parsea `JSON.parse(event.data)` y actúa según `type`:
- `vector_update` → actualiza VectorCard estado (elimina mocks)
- `interview_start` → abre DayCeroView wizard con preguntas
- `ceo_shield` → abre CEOShield modal automáticamente
- `tarjeta_ready` → actualiza PM Workspace con artefactos reales
- `artifact_ready` → añade archivo a `documentos_generados` list

### 9.3 Nuevo Endpoint: Resume

```
POST /api/v1/agent/resume
Body: { brand_id: string, session_id: string, answers: string }
Response: { status: "resumed" | "error", message?: string }

→ Backend: njm_graph.ainvoke({"human_interview_answers": answers}, config=config)
→ Esto reanuda el grafo desde el interrupt point (human_in_loop_node)
→ Dispara nuevo stream SSE al cliente
```

### 9.4 Nuevo Endpoint: Session State

```
GET /api/v1/session/state?brand_id={id}&session_id={uuid}
Response: {
  audit_status: "PENDING" | "GAP_DETECTED" | "COMPLETE" | ...,
  interview_questions: string[] | null,
  last_tarjeta: TarjetaSugerenciaUI | null,
  documentos_count: number,
}

→ Frontend llama esto al montar CEO Workspace y PM Workspace.
→ Elimina la necesidad de MOCK_VECTORES y MOCK_ARTEFACTOS.
→ Hidrata el estado real desde el checkpointer.
```

---

## 10. Hoja de Ruta de Implementación

Las fases están ordenadas por dependencias. No reordenar.

### Fase 2.1 — Estado Unificado y Grafo Base (Fundación)
**Objetivo:** Un solo grafo con el CEO real wired y checkpointer funcional.

- [ ] Crear `backend/core/estado.py` con `NJM_OS_State` (reemplaza `NJM_PM_State`)
- [ ] Adaptar `agentes/agente_ceo.py::nodo_ceo` para `NJM_OS_State`
- [ ] Adaptar `agentes/agente_pm.py::nodo_pm` para `NJM_OS_State`
- [ ] Crear `backend/agent/njm_graph.py` con todos los nodos y edges del §5
- [ ] Integrar `SqliteSaver` como checkpointer dev
- [ ] Actualizar `api/v1_router.py` para usar `njm_graph` en lugar de `ceo_graph`
- [ ] Actualizar `api/main.py::ejecutar_tarea` para usar `njm_graph` en lugar de `_GRAFO_PM`
- [ ] Tests de humo: invocar grafo completo para brand "disrupt" con Libro Vivo hardcodeado

### Fase 2.2 — Ingest Real + RAG MVP
**Objetivo:** Documentos subidos desde el frontend llegan al CEO.

- [ ] Añadir `pypdf` a `requirements.txt`
- [ ] Crear `backend/core/vector_store.py` con ChromaDB
- [ ] Implementar `ingest_node` con extracción de texto y upsert a ChromaDB
- [ ] Conectar `POST /api/v1/ingest` a `ingest_node` (reemplaza el placeholder actual)
- [ ] Modificar `ceo_auditor_node` para query ChromaDB antes de invocar el LLM
- [ ] Test: subir un PDF de onboarding desde el frontend y verificar que el CEO lo lee

### Fase 2.3 — Human-in-the-Loop
**Objetivo:** CEO puede pausar y pedir información al humano.

- [ ] Implementar `human_in_loop_node` con `interrupt()`
- [ ] Crear `GET /api/v1/session/state` endpoint
- [ ] Crear `POST /api/v1/agent/resume` endpoint
- [ ] Añadir tipos de eventos SSE estructurados al generador (§9.2)
- [ ] Actualizar `useAgentConsole` para parsear eventos tipados
- [ ] Implementar DayCeroView wizard en el CEO Workspace (4-step, ya en backlog)
- [ ] Test: CEO detecta gap en Vector 3, frontend muestra wizard, humano responde, CEO re-audita

### Fase 2.4 — Streaming PM Real
**Objetivo:** PM execution con SSE real (eliminar mocks).

- [ ] Implementar `pm_execution_node` con `astream_events` (igual que CEO)
- [ ] Conectar boton "Consultar PM" en `pm/page.tsx` al grafo real (no al mock)
- [ ] Frontend parsea `artifact_ready` events para hidratar la grilla de artefactos
- [ ] Implementar SlideOver para leer artefactos desde rutas reales (file:// protocol o endpoint dedicado)
- [ ] Test: solicitar Business Case → ver stream real → ver artefacto en grilla

### Fase 2.5 — CEO Shield Real
**Objetivo:** CEOShield se dispara desde eventos de backend, no desde botón manual.

- [ ] `ceo_review_node` emite evento SSE `ceo_shield` cuando hay BLOQUEO_CEO
- [ ] `useAgentConsole` parsea `ceo_shield` event y abre CEOShield modal automáticamente
- [ ] `onApprove` / `onReject` en CEOShield llaman a `POST /api/v1/agent/resume` con decision
- [ ] Eliminar botón "Simular Bloqueo CEO" del PM Workspace
- [ ] Test: PM genera propuesta que viola Vector 5 → CEO Shield se abre automáticamente

### Fase 2.6 — Error Handling & Hardening
**Objetivo:** Sistema robusto para producción.

- [ ] Implementar retry con `tenacity` en todas las invocaciones LLM
- [ ] Migrar `_parsear_resumen_pm` a `model.with_structured_output(ResumenPM)`
- [ ] Añadir `asyncio.wait_for` en herramientas CEO y PM skills
- [ ] Detectar `CancelledError` en SSE generators
- [ ] Implementar `Last-Event-ID` support para reconexión SSE
- [ ] Parametrizar `ALLOWED_ORIGINS` con env var
- [ ] Migrar `ChatAnthropic` instantiation a singletons de módulo
- [ ] Test: simular timeout LLM, simular desconexión SSE, verificar recovery

---

## APÉNDICE A: Inventario de Deuda Técnica Priorizada

| ID | Archivo | Descripción | Prioridad | Fix en Fase |
|----|---------|-------------|-----------|-------------|
| TD-01 | `api/main.py:65` | `_LIBRO_VIVO_DISRUPT` hardcodeado | CRÍTICO | 2.1 |
| TD-02 | `agent/graph.py` | `ceo_auditor_node` sin herramientas CEO | CRÍTICO | 2.1 |
| TD-03 | `api/v1_router.py:180` | `brand_context` en URL query param | ALTO | 2.3 |
| TD-04 | `api/v1/ingest` | Guarda files pero no los procesa | ALTO | 2.2 |
| TD-05 | `agentes/agente_pm.py:297` | `_parsear_resumen_pm` regex frágil | ALTO | 2.6 |
| TD-06 | `main.py:14` | CORS solo `localhost:3000` | MEDIO | 2.6 |
| TD-07 | `agentes/agente_ceo.py:597` | `ChatAnthropic` instanciado por invocación | MEDIO | 2.1 |
| TD-08 | `agentes/agente_pm.py:357` | `ChatAnthropic` instanciado por invocación | MEDIO | 2.1 |
| TD-09 | `frontend/app/brand/[id]/ceo/page.tsx:26` | `MOCK_VECTORES` no conectado a CEO state | MEDIO | 2.4 |
| TD-10 | `frontend/app/brand/[id]/pm/page.tsx:18` | `MOCK_ARTEFACTOS` no conectado a PM output | MEDIO | 2.4 |
| TD-11 | `frontend/hooks/useAgentConsole.ts:28` | No pasa `brand_id`/`session_id` al SSE | ALTO | 2.3 |

---

## APÉNDICE B: Variables de Entorno Requeridas en Phase 2

```bash
# backend/.env

# Existentes
ANTHROPIC_API_KEY=sk-ant-...

# Nuevas en Phase 2
DATABASE_URL=                    # Vacío = SQLite dev. Prod: postgresql://...
CHROMA_DB_PATH=./chroma_db       # Directorio ChromaDB persistente
ALLOWED_ORIGINS=http://localhost:3000  # Comma-separated para prod
NJM_OS_ROOT=/Users/{user}/NJM_OS      # Raíz del Cowork local
SESSION_TTL_DAYS=7               # TTL de sesiones inactivas

# frontend/.env.local

# Existentes
NEXT_PUBLIC_API_URL=http://localhost:8000

# Nuevas en Phase 2
NEXT_PUBLIC_SESSION_STORAGE_KEY=njm_session  # Key para localStorage session_id
```

---

*Documento generado tras auditoría completa de: `backend/main.py`, `backend/api/main.py`, `backend/api/v1_router.py`, `backend/agent/graph.py`, `backend/agentes/agente_ceo.py`, `backend/agentes/agente_pm.py`, `backend/core/estado.py`, `backend/core/schemas.py`, `frontend/hooks/useAgentConsole.ts`, `frontend/app/brand/[id]/ceo/page.tsx`, `frontend/app/brand/[id]/pm/page.tsx`.*
