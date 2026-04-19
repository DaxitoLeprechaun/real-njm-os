"""
NJM OS — Estado Unificado del Grafo Multi-Agente

Fuente de verdad: ARCHITECTURE_ROADMAP_PHASE2.md § 4 "AgentState Unificado"

Ciclo de vida del estado:
  ingest_node → ceo_auditor_node → [human_in_loop_node?]
  → pm_execution_node → [ceo_review_node?] → output_node

Reductores:
  messages              → add_messages (append, nunca sobrescribe)
  documentos_generados  → operator.add  (acumulativo)
  alertas_internas      → operator.add  (acumulativo)
  uploaded_doc_paths    → operator.add  (acumulativo)
  Todos los demás       → overwrite (last-write-wins)
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Literal, Optional

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class NJM_OS_State(TypedDict):
    """Estado unificado del grafo multi-agente NJM OS (Phase 2)."""

    # ── IDENTIDAD DE SESIÓN ────────────────────────────────────────
    brand_id: str
    # Slug de la marca. Ej.: "disrupt".
    # Junto con session_id forma el thread_id: f"{brand_id}:{session_id}"

    session_id: str
    # UUID v4 por sesión de usuario.

    # ── HISTORIAL DE CONVERSACIÓN ──────────────────────────────────
    messages: Annotated[list, add_messages]
    # Acumula HumanMessage, AIMessage y ToolMessage de ambos agentes.
    # add_messages garantiza append — nunca sobrescribe.

    # ── INPUT DE ONBOARDING ────────────────────────────────────────
    brand_context_raw: str
    # Texto crudo extraído de los docs subidos vía /api/v1/ingest.
    # Fase 2.2: ingest_node lo popula desde ChromaDB. Hasta entonces: string vacío.

    uploaded_doc_paths: Annotated[List[str], operator.add]
    # Rutas en temp_uploads/ de docs ingeridos. Acumulativo entre sesiones.

    # ── CEO — AUDITORÍA ────────────────────────────────────────────
    audit_status: Literal["PENDING", "IN_PROGRESS", "GAP_DETECTED", "COMPLETE", "RISK_BLOCKED"]
    # PENDING      → CEO aún no corrió
    # GAP_DETECTED → pausa HITL activa (Fase 2.3)
    # COMPLETE     → libro_vivo escrito y validado
    # RISK_BLOCKED → tarjeta roja activa

    gap_report_path: Optional[str]
    # Ruta del 00_GAP_ANALYSIS_*.md generado por CEO si detecta brechas.

    interview_questions: Optional[List[str]]
    # Preguntas C-Suite generadas por CEO para el Encargado Real.
    # El frontend las renderiza en el DayCeroView wizard (Fase 2.3).

    human_interview_answers: Optional[str]
    # Respuestas del humano al cuestionario CEO. Input para el re-audit.

    libro_vivo: Optional[Dict[str, Any]]
    # JSON final validado por CEO (schema LibroVivo).
    # READ-ONLY para el PM. Escrito por ceo_auditor_node::escribir_libro_vivo.

    # ── CONTROL DE RIESGO ──────────────────────────────────────────
    risk_flag: bool
    # True cuando CEO activa levantar_tarjeta_roja o PM activa BLOQUEO_CEO.

    risk_details: Optional[str]
    # Descripción del riesgo activo. Enviada al frontend como riskMessage del CEOShield.

    ceo_review_decision: Optional[Literal["APPROVED", "REJECTED", "ESCALATE"]]
    # Decisión del CEO al revisar output del PM (Fase 2.5).

    # ── PM — EJECUCIÓN ─────────────────────────────────────────────
    peticion_humano: Optional[str]
    # Instrucción cruda del Encargado Real para el PM.

    ruta_espacio_trabajo: str
    # Ruta local donde el PM guarda artefactos.

    skill_activa: Optional[str]
    # Última skill PM ejecutada. Ej.: "generar_business_case".

    documentos_generados: Annotated[List[str], operator.add]
    # Rutas absolutas de artefactos generados por el PM. Acumulativo entre nodos.

    estado_validacion: Literal["EN_PROGRESO", "LISTO_PARA_FIRMA", "BLOQUEO_CEO"]
    # Semáforo de gobernanza del PM.

    alertas_internas: Annotated[List[str], operator.add]
    # Alertas de autocorrección del PM. Max 2 antes de escalar al CEO.

    tareas_generadas: Annotated[List[Dict[str, Any]], operator.add]
    # Tareas desglosadas por el PM durante la ejecución. Acumulativo entre nodos.
    # Cada elemento es un dict serializado de Tarea (Phase 2.6).

    # ── OUTPUT ─────────────────────────────────────────────────────
    payload_tarjeta_sugerencia: Optional[Dict[str, Any]]
    # TarjetaSugerenciaUI JSON. Emitido por output_node al finalizar el grafo.

    # ── ROUTING INTERNO ────────────────────────────────────────────
    next_node: Optional[str]
    # Hint de routing para conditional edges.

    # ── COMPATIBILIDAD DE DESARROLLO ──────────────────────────────
    modo: str
    # "auditoria" | "ejecucion" — heredado de la arquitectura anterior.

    nombre_marca: str
    # Nombre legible de la marca. Ej.: "Disrupt". Deprecated: usar brand_id.


# Alias de compatibilidad — eliminar en Fase 2.3.
NJM_PM_State = NJM_OS_State
