"""
NJM OS — CEO Auditor Graph (LangGraph)

Minimal StateGraph wired for real-time SSE streaming via astream_events.

State:
  messages      — conversation history (add_messages reducer)
  brand_context — raw brand info string injected per request
  risk_flag     — set True when CEO detects a blocking risk

Graph:  START → ceo_auditor_node → END
"""

from __future__ import annotations

from typing import Annotated, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# ══════════════════════════════════════════════════════════════════
# STATE
# ══════════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    brand_context: str
    risk_flag: bool


# ══════════════════════════════════════════════════════════════════
# MODEL
# ══════════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = (
    "Eres el CEO de NJM OS evaluando una marca. "
    "Tu rol es auditar la coherencia estratégica, identificar riesgos críticos "
    "y validar los vectores del Libro Vivo. "
    "Sé directo, analítico y preciso. Sin cortesías innecesarias. "
    "Si detectas riesgos financieros, operativos o de reputación, señálalos explícitamente."
)

# claude-3-5-haiku: fast, cheap, streaming-capable — ideal for SSE
_LLM = ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    temperature=0,
    streaming=True,
)


# ══════════════════════════════════════════════════════════════════
# NODE
# ══════════════════════════════════════════════════════════════════

def ceo_auditor_node(state: AgentState) -> dict[str, Any]:
    """
    Injects the CEO system prompt + brand_context, then invokes the LLM.
    Returns only the new AI message so add_messages can append it cleanly.
    """
    context_note = (
        f"\n\n[CONTEXTO DE MARCA INYECTADO]\n{state['brand_context']}"
        if state.get("brand_context")
        else ""
    )
    system = SystemMessage(content=_SYSTEM_PROMPT + context_note)
    history = [system] + list(state["messages"])
    response = _LLM.invoke(history)
    return {"messages": [response]}


# ══════════════════════════════════════════════════════════════════
# GRAPH
# ══════════════════════════════════════════════════════════════════

_builder: StateGraph = StateGraph(AgentState)
_builder.add_node("ceo_auditor", ceo_auditor_node)
_builder.add_edge(START, "ceo_auditor")
_builder.add_edge("ceo_auditor", END)

# Compiled once at import time — reused across all requests.
ceo_graph = _builder.compile()
