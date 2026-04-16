"""
NJM OS — Unified Multi-Agent Graph (CEO + PM)

Topology:
  START → router_node → ceo_node  → [END | pm_node]
                      → pm_node   → END

Routing:
  - modo "auditoria" | "onboarding" | libro_vivo empty → CEO
  - modo "ejecucion" + libro_vivo populated             → PM

Post-CEO conditional edge:
  - BLOQUEO_CEO  → END  (PM never runs)
  - LISTO_PARA_FIRMA → pm_node
  - else         → END

Checkpointer: SqliteSaver — thread_id enables multi-turn memory.

SSE streaming graph (ceo_graph) kept as a separate export for v1_router.
"""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from agentes.agente_ceo import nodo_ceo
from agentes.agente_pm import nodo_pm
from core.estado import NJM_OS_State
from core.schemas import EstadoValidacion

# ══════════════════════════════════════════════════════════════════
# ROUTING LOGIC
# ══════════════════════════════════════════════════════════════════

def router_node(state: NJM_OS_State) -> dict[str, Any]:
    """Pass-through node — routing is done via conditional edges."""
    return {}


def _initial_route(state: NJM_OS_State) -> str:
    modo = state.get("modo", "auditoria")
    libro_vivo = state.get("libro_vivo") or {}
    if modo == "ejecucion" and libro_vivo:
        return "pm_node"
    return "ceo_node"


def _post_ceo_route(state: NJM_OS_State) -> str:
    estado = state.get("estado_validacion", EstadoValidacion.EN_PROGRESO.value)
    libro_vivo = state.get("libro_vivo") or {}
    if estado == EstadoValidacion.BLOQUEO_CEO.value:
        return END
    if estado == EstadoValidacion.LISTO_PARA_FIRMA.value and libro_vivo:
        return "pm_node"
    return END


# ══════════════════════════════════════════════════════════════════
# UNIFIED GRAPH
# ══════════════════════════════════════════════════════════════════

def _build_unified_graph() -> Any:
    builder = StateGraph(NJM_OS_State)

    builder.add_node("router_node", router_node)
    builder.add_node("ceo_node", nodo_ceo)
    builder.add_node("pm_node", nodo_pm)

    builder.add_edge(START, "router_node")
    builder.add_conditional_edges("router_node", _initial_route, {
        "ceo_node": "ceo_node",
        "pm_node": "pm_node",
    })
    builder.add_conditional_edges("ceo_node", _post_ceo_route, {
        "pm_node": "pm_node",
        END: END,
    })
    builder.add_edge("pm_node", END)

    conn = sqlite3.connect("njm_checkpoints.db", check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return builder.compile(checkpointer=checkpointer)


unified_graph = _build_unified_graph()


# ══════════════════════════════════════════════════════════════════
# SSE STREAMING GRAPH — kept for /api/v1/agent/stream (v1_router)
# ══════════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    brand_context: str
    risk_flag: bool


_SYSTEM_PROMPT = (
    "Eres el CEO de NJM OS evaluando una marca. "
    "Tu rol es auditar la coherencia estratégica, identificar riesgos críticos "
    "y validar los vectores del Libro Vivo. "
    "Sé directo, analítico y preciso. Sin cortesías innecesarias. "
    "Si detectas riesgos financieros, operativos o de reputación, señálalos explícitamente."
)

_LLM = ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    temperature=0,
    streaming=True,
)


def ceo_auditor_node(state: AgentState) -> dict[str, Any]:
    context_note = (
        f"\n\n[CONTEXTO DE MARCA INYECTADO]\n{state['brand_context']}"
        if state.get("brand_context")
        else ""
    )
    system = SystemMessage(content=_SYSTEM_PROMPT + context_note)
    history = [system] + list(state["messages"])
    response = _LLM.invoke(history)
    return {"messages": [response]}


_sse_builder: StateGraph = StateGraph(AgentState)
_sse_builder.add_node("ceo_auditor", ceo_auditor_node)
_sse_builder.add_edge(START, "ceo_auditor")
_sse_builder.add_edge("ceo_auditor", END)

ceo_graph = _sse_builder.compile()
