"""
NJM OS — Estado Global del Agente PM (LangGraph GraphState)

Fuente de verdad: ARCHITECTURE.md § "PM. Memoria / NJM_PM_State"

Reglas de reducción:
- messages            → add_messages (LangGraph acumula, nunca sobrescribe)
- documentos_generados → operator.add  (array acumulativo de rutas locales)
- alertas_internas    → operator.add  (array acumulativo para el loop de autocorrección)
"""

import operator
from typing import Annotated, Any, Dict, List, Optional

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class NJM_PM_State(TypedDict):
    """
    Estado global del grafo NJM OS (CEO + PM).
    Instanciado por LangGraph al inicio de cada petición del Encargado Real.
    """

    # ─────────────────────────────────────────────────────────────
    # 1. MEMORIA CORE Y RUTEO
    # ─────────────────────────────────────────────────────────────
    thread_id: str
    # Identificador de sesión para SqliteSaver — permite retomar conversaciones.

    modo_operacion: str
    # Modo de ejecución del grafo: "onboarding" | "ejecucion" | "auditoria"

    messages: Annotated[list, add_messages]
    # Historial de conversación y llamadas a herramientas (ToolCalls/ToolMessages).
    # add_messages concatena entradas nuevas sin sobrescribir el historial previo.

    # ─────────────────────────────────────────────────────────────
    # 2. CONTEXTO INMUTABLE — Handoff del CEO
    # ─────────────────────────────────────────────────────────────
    libro_vivo: Dict[str, Any]
    # JSON completo validado por el Agente CEO (LIBRO_VIVO_SCHEMA).
    # REGLA: el PM tiene permisos READ-ONLY. Si está vacío, el grafo falla en el nodo de guardia.

    ruta_espacio_trabajo: str
    # Ruta local absoluta en Claude Cowork donde el agente puede leer/escribir archivos.
    # Ej.: "/NJM_OS/Marcas/Disrupt/Q3_Campaign/"

    # ─────────────────────────────────────────────────────────────
    # 3. CONTEXTO DE LA TAREA ACTUAL
    # ─────────────────────────────────────────────────────────────
    peticion_humano: str
    # Instrucción cruda del Encargado Real. Ej.: "Arma la campaña para Q3."

    skill_activa: Optional[str]
    # Skill metodológica en uso durante este ciclo.
    # Ej.: "generar_analisis_ansoff". None si el agente aún está razonando.

    # ─────────────────────────────────────────────────────────────
    # 4. TRAZABILIDAD DE ARTEFACTOS LOCALES — Claude Cowork
    # ─────────────────────────────────────────────────────────────
    documentos_generados: Annotated[List[str], operator.add]
    # Rutas absolutas de los archivos (.docx, .xlsx, .md) creados en este run.
    # operator.add garantiza que cada nodo annexe su salida sin borrar la del anterior.
    # La Tarjeta de Sugerencia usará este array para mostrar links clicables al humano.

    # ─────────────────────────────────────────────────────────────
    # 5. CONTROL DE CALIDAD Y GOBERNANZA
    # ─────────────────────────────────────────────────────────────
    estado_validacion: str
    # Semáforo de gobernanza. Valores válidos (ver schemas.EstadoValidacion):
    #   "EN_PROGRESO"      → el loop de LangGraph sigue activo.
    #   "BLOQUEO_CEO"      → el PM falló autocorrección; se detiene y escala.
    #   "LISTO_PARA_FIRMA" → trabajo validado; payload listo para el frontend.

    alertas_internas: Annotated[List[str], operator.add]
    # Advertencias inyectadas por el Nodo Evaluador durante el loop de autocorrección.
    # Ej.: "Error Financiero: Presupuesto propuesto ($5k) excede Vector 5 ($2k)".
    # Max 2 alertas antes de cambiar estado_validacion a BLOQUEO_CEO.

    # ─────────────────────────────────────────────────────────────
    # 6. OUTPUT HACIA NEXT.JS — Interfaz
    # ─────────────────────────────────────────────────────────────
    payload_tarjeta_sugerencia: Optional[Dict[str, Any]]
    # JSON final (TARJETA_SUGERENCIA_UI) que el frontend lee para renderizar botones.
    # Empieza como None. Solo se popula en el último nodo del grafo, garantizando
    # que Next.js no renderice nada hasta que el trabajo esté 100% validado.
