"""
NJM OS — Grafo Multi-Agente Unificado (Phase 2.1)

Topología completa (6 nodos):
  START
    → ingest_node          [STUB Phase 2.2 — passthrough]
    → ceo_auditor_node     [ACTIVO — nodo_ceo con 5 herramientas]
    → human_in_loop_node   [STUB Phase 2.3 — auto-completa con dev fixtures]
    → pm_execution_node    [ACTIVO — nodo_pm con 14 skills]
    → ceo_review_node      [STUB Phase 2.5 — auto-rechaza para ir a output]
    → output_node          [ACTIVO — construye TarjetaSugerenciaUI]
    → END

Routing condicional basado en audit_status y estado_validacion del NJM_OS_State.

Checkpointer: AsyncSqliteSaver en ./njm_sessions.db
  thread_id = f"{brand_id}:{session_id}"

SSE compat: también exporta AgentState + ceo_graph para /api/v1/agent/stream.
"""

from __future__ import annotations

import asyncio
import aiosqlite
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional
from uuid import uuid4

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from agentes.agente_ceo import nodo_ceo
from agentes.agente_pm import nodo_pm
from core.estado import NJM_OS_State
from core.schemas import EstadoValidacion

# ══════════════════════════════════════════════════════════════════
# NODOS STUB (Phase 2.1)
# ══════════════════════════════════════════════════════════════════


def ingest_node(state: NJM_OS_State) -> Dict[str, Any]:
    """Phase 2.2 stub — text extraction + ChromaDB upsert pendiente."""
    return {}


def ceo_auditor_node(state: NJM_OS_State) -> Dict[str, Any]:
    """
    Wrapper del nodo CEO real.

    Skip guard: si audit_status ya es COMPLETE (e.g. dev smoke test con
    libro_vivo pre-cargado), devuelve sin invocar el LLM para no gastar tokens.
    """
    if state.get("audit_status") == "COMPLETE":
        return {}
    return nodo_ceo(state)


def human_in_loop_stub_node(state: NJM_OS_State) -> Dict[str, Any]:
    """
    Phase 2.3 stub — simula respuesta humana con datos del fixture de desarrollo.
    En Phase 2.3 esto se reemplaza con interrupt() + POST /api/v1/agent/resume.
    """
    from core.dev_fixtures import _LIBRO_VIVO_DISRUPT
    return {
        "audit_status": "COMPLETE",
        "human_interview_answers": "[STUB Phase 2.1] Respuestas simuladas — integración real en Phase 2.3.",
        "libro_vivo": state.get("libro_vivo") or _LIBRO_VIVO_DISRUPT,
    }


def pm_execution_node(state: NJM_OS_State) -> Dict[str, Any]:
    """Wrapper directo del nodo PM real."""
    return nodo_pm(state)


def ceo_review_stub_node(state: NJM_OS_State) -> Dict[str, Any]:
    """
    Phase 2.5 stub — fuerza REJECTED para que el grafo fluya a output_node
    sin crear loops. En Phase 2.5 se reemplaza con CEOShield real + interrupt().
    """
    return {"ceo_review_decision": "REJECTED"}


def output_node(state: NJM_OS_State) -> Dict[str, Any]:
    """
    Nodo terminal — garantiza que payload_tarjeta_sugerencia esté poblado.
    nodo_pm ya construye el payload en la mayoría de los casos.
    Este nodo actúa como fallback si el grafo termina sin payload.
    """
    if state.get("payload_tarjeta_sugerencia"):
        return {}

    alertas = list(state.get("alertas_internas", []))
    audit_status = state.get("audit_status", "PENDING")

    if audit_status == "RISK_BLOCKED":
        propuesta = f"BLOQUEO CEO: {state.get('risk_details', 'Tarjeta roja activa.')}"
    else:
        propuesta = "El grafo completó la ejecución sin generar un payload de PM."

    return {
        "payload_tarjeta_sugerencia": {
            "id_transaccion": str(uuid4()),
            "estado_ejecucion": EstadoValidacion.BLOQUEO_CEO.value,
            "metadata": {
                "skill_utilizada": state.get("skill_activa", "ninguna"),
                "timestamp_generacion": datetime.now(timezone.utc).isoformat(),
            },
            "contenido_tarjeta": {
                "propuesta_principal": propuesta,
                "framework_metodologico": "N/A",
                "check_coherencia_adn": {"aprobado": False, "justificacion": propuesta},
                "archivos_locales_cowork": [],
                "log_errores_escalamiento": alertas,
            },
            "acciones_ui_disponibles": [],
        }
    }


# ══════════════════════════════════════════════════════════════════
# ROUTING CONDICIONAL
# ══════════════════════════════════════════════════════════════════


def _route_after_ceo(state: NJM_OS_State) -> str:
    status = state.get("audit_status", "PENDING")
    if status == "COMPLETE":
        return "pm_execution"
    elif status == "GAP_DETECTED":
        return "human_in_loop"
    elif status == "RISK_BLOCKED":
        return "output"
    return "human_in_loop"  # default seguro


def _route_after_pm(state: NJM_OS_State) -> str:
    estado = state.get("estado_validacion", EstadoValidacion.EN_PROGRESO.value)
    if estado == EstadoValidacion.LISTO_PARA_FIRMA.value:
        return "output"
    elif estado == EstadoValidacion.BLOQUEO_CEO.value:
        return "ceo_review"
    return "output"


def _route_after_ceo_review(state: NJM_OS_State) -> str:
    decision = state.get("ceo_review_decision")
    if decision == "APPROVED":
        return "pm_execution"
    elif decision == "ESCALATE":
        return "human_in_loop"
    return "output"  # REJECTED o None → output


# ══════════════════════════════════════════════════════════════════
# COMPILACIÓN — njm_graph
# ══════════════════════════════════════════════════════════════════


async def _build_njm_graph() -> Any:
    builder = StateGraph(NJM_OS_State)

    builder.add_node("ingest", ingest_node)
    builder.add_node("ceo_auditor", ceo_auditor_node)
    builder.add_node("human_in_loop", human_in_loop_stub_node)
    builder.add_node("pm_execution", pm_execution_node)
    builder.add_node("ceo_review", ceo_review_stub_node)
    builder.add_node("output", output_node)

    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "ceo_auditor")

    builder.add_conditional_edges(
        "ceo_auditor",
        _route_after_ceo,
        {"pm_execution": "pm_execution", "human_in_loop": "human_in_loop", "output": "output"},
    )

    builder.add_edge("human_in_loop", "ceo_auditor")

    builder.add_conditional_edges(
        "pm_execution",
        _route_after_pm,
        {"output": "output", "ceo_review": "ceo_review"},
    )

    builder.add_conditional_edges(
        "ceo_review",
        _route_after_ceo_review,
        {"pm_execution": "pm_execution", "output": "output", "human_in_loop": "human_in_loop"},
    )

    builder.add_edge("output", END)

    conn = await aiosqlite.connect("njm_sessions.db")
    checkpointer = AsyncSqliteSaver(conn)
    return builder.compile(checkpointer=checkpointer)


njm_graph = None  # initialized by init_graph() inside Uvicorn's event loop
_init_lock: asyncio.Lock | None = None


async def init_graph() -> None:
    """Call once from FastAPI lifespan (or test fixtures) to build njm_graph."""
    global njm_graph, _init_lock
    if _init_lock is None:
        _init_lock = asyncio.Lock()
    async with _init_lock:
        if njm_graph is not None:
            return
        njm_graph = await _build_njm_graph()


# ══════════════════════════════════════════════════════════════════
# SSE STREAMING GRAPH — backward compat con /api/v1/agent/stream
# ══════════════════════════════════════════════════════════════════


class AgentState(TypedDict):
    """Estado mínimo para el grafo de streaming SSE del CEO (v1_router)."""
    messages: Annotated[list, add_messages]
    brand_context: str
    risk_flag: bool


_SSE_SYSTEM_PROMPT = (
    "Eres el CEO de NJM OS evaluando una marca. "
    "Tu rol es auditar la coherencia estratégica, identificar riesgos críticos "
    "y validar los vectores del Libro Vivo. "
    "Sé directo, analítico y preciso. Sin cortesías innecesarias. "
    "Si detectas riesgos financieros, operativos o de reputación, señálalos explícitamente."
)

_SSE_LLM = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    streaming=True,
)


def _sse_ceo_auditor_node(state: AgentState) -> dict[str, Any]:
    context_note = (
        f"\n\n[CONTEXTO DE MARCA INYECTADO]\n{state['brand_context']}"
        if state.get("brand_context")
        else ""
    )
    system = SystemMessage(content=_SSE_SYSTEM_PROMPT + context_note)
    history = [system] + list(state["messages"])
    response = _SSE_LLM.invoke(history)
    return {"messages": [response]}


_sse_builder: StateGraph = StateGraph(AgentState)
_sse_builder.add_node("ceo_auditor", _sse_ceo_auditor_node)
_sse_builder.add_edge(START, "ceo_auditor")
_sse_builder.add_edge("ceo_auditor", END)

ceo_graph = _sse_builder.compile()
