"""
NJM OS — Router FastAPI: /api/ejecutar-tarea

Orquesta la ejecución del grafo LangGraph del Agente PM, devuelve la
Tarjeta de Sugerencia UI lista para ser consumida por el frontend Next.js.

Flujo:
  POST /api/ejecutar-tarea
    → Inicializa NJM_PM_State con un LIBRO_VIVO de prueba (Disrupt / Technical_PM)
    → Invoca el grafo compilado (START → nodo_pm → END)
    → Devuelve payload_tarjeta_sugerencia (TarjetaSugerenciaUI JSON)
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from agentes.agente_ceo import nodo_ceo
from agentes.agente_pm import nodo_pm
from core.estado import NJM_PM_State
from core.schemas import EstadoValidacion

router = APIRouter()

# ══════════════════════════════════════════════════════════════════
# CHECKPOINTER — SqliteSaver para persistencia entre sesiones
# ══════════════════════════════════════════════════════════════════

_DB_PATH = os.environ.get("NJM_CHECKPOINT_DB", "/tmp/njm_checkpoints.sqlite")
_CHECKPOINTER = SqliteSaver(sqlite3.connect(_DB_PATH, check_same_thread=False))

# ══════════════════════════════════════════════════════════════════
# ROUTER — Decide qué nodo ejecutar según modo_operacion
# ══════════════════════════════════════════════════════════════════


def _router(state: NJM_PM_State) -> str:
    modo = state.get("modo_operacion", "ejecucion")
    if modo in ("onboarding", "auditoria"):
        return "nodo_ceo"
    return "nodo_pm"


def _ceo_post_router(state: NJM_PM_State) -> str:
    """Tras CEO en modo auditoria: continúa al PM si no hay bloqueo."""
    if (
        state.get("modo_operacion") == "auditoria"
        and state.get("estado_validacion") != EstadoValidacion.BLOQUEO_CEO.value
    ):
        return "nodo_pm"
    return END


# ══════════════════════════════════════════════════════════════════
# GRAFO LANGGRAPH — compilado una sola vez al iniciar el módulo
# ══════════════════════════════════════════════════════════════════


def _compilar_grafo():
    """
    Topología unificada CEO + PM:

      START → router → nodo_ceo → (auditoria sin bloqueo) → nodo_pm → END
                     ↘ nodo_pm → END          (modo ejecucion)
                       nodo_ceo → END          (onboarding / bloqueo)
    """
    grafo = StateGraph(NJM_PM_State)
    grafo.add_node("nodo_ceo", nodo_ceo)
    grafo.add_node("nodo_pm", nodo_pm)
    grafo.add_conditional_edges(START, _router, {"nodo_ceo": "nodo_ceo", "nodo_pm": "nodo_pm"})
    grafo.add_conditional_edges("nodo_ceo", _ceo_post_router, {"nodo_pm": "nodo_pm", END: END})
    grafo.add_edge("nodo_pm", END)
    return grafo.compile(checkpointer=_CHECKPOINTER)


_GRAFO = _compilar_grafo()

# ══════════════════════════════════════════════════════════════════
# LIBRO VIVO DE PRUEBA — Marca "Disrupt" (B2B SaaS / Technical_PM)
# Fuente: ARCHITECTURE.md § "La Lógica de Asignación del Agente CEO"
#
# Este dict simula el output del Agente CEO tras completar el onboarding.
# En producción, se leería del archivo LIBRO_VIVO_Disrupt.json en Cowork.
# ══════════════════════════════════════════════════════════════════

_LIBRO_VIVO_DISRUPT: Dict[str, Any] = {
    "metadata": {
        "nombre_marca": "Disrupt",
        "fecha_ultima_firma": "2026-04-13T00:00:00Z",
        "estado_auditoria": "COMPLETO_100%",
    },
    "vector_1_nucleo": {
        "uvp": "La única agencia B2B que garantiza ROI medible en 90 días o devuelve el fee.",
        "posicionamiento": "Eje X: Precio vs. Especialización — territorio: Alta especialización / Precio medio-alto.",
        "arquetipo_comunicacion": "Consultor Senior: directo, basado en datos, sin rodeos.",
        "lineas_rojas_marca": [
            "No hacer claims de ROI garantizado sin datos reales",
            "No comparar con competencia por precio",
            "No usar lenguaje informal o emojis en comunicación corporativa",
        ],
    },
    "vector_2_negocio": {
        "unit_economics": {
            "ticket_promedio_usd": 4500.0,
            "ltv_proyectado_usd": 27000.0,
            "cac_maximo_tolerable_usd": 900.0,
        },
        "cash_conversion_cycle_dias": 38,
        "modelo_pricing": "premium",
        "producto_estrella_bcg": "Consultoría de Demand Generation B2B",
        "producto_vaca_lechera_bcg": "Reportes mensuales de performance",
        "moats_economicos": [
            "Metodología propietaria de atribución multi-touch",
            "Base de datos de benchmarks B2B por industria",
        ],
    },
    "vector_3_audiencia": {
        "jtbd_funcional": "Generar leads B2B calificados sin contratar un equipo de marketing interno.",
        "jtbd_socioemocional": "Llegar a la reunión de directorio con métricas que justifiquen el gasto de marketing.",
        "friccion_transaccional": "No tienen claridad sobre qué canales generan ROI real — confunden actividad con resultados.",
        "trigger_event": "La empresa acaba de cerrar una ronda de inversión o tiene presión para escalar revenue en el Q.",
        "criterio_desempate": "Casos de estudio con métricas reales de empresas similares en su industria.",
    },
    "vector_4_competencia": {
        "competidores_directos": [
            {"nombre": "GrowthAgency MX", "vulnerabilidad_tactica": "No tiene especialización técnica — vende volumen, no calidad."},
            {"nombre": "Digital Pros", "vulnerabilidad_tactica": "Reporting manual y sin atribución real."},
            {"nombre": "ScaleB2B", "vulnerabilidad_tactica": "Precios más bajos pero sin metodología probada."},
        ],
        "amenaza_sustitutos": "Contratar un Head of Growth interno ($8k/mes) en vez de externalizar.",
        "tactica_a_disrumpir": "Todos usan casos de éxito anónimos — nosotros publicamos métricas reales con nombre de cliente (con permiso).",
    },
    "vector_5_infraestructura": {
        "arquitectura_funnel": "LinkedIn Ads / Google Search → Landing page → Demo call → Propuesta → Cierre. Ciclo promedio: 21 días.",
        "cuello_botella_funnel": "La tasa de conversión Demo-to-Propuesta es del 40% — hay fricción en la llamada de discovery.",
        "presupuesto_pauta_mensual_usd": 6000.0,
        "punto_quiebre_operativo": "Más de 80 leads/mes colapsa el equipo de ventas de 3 personas — máximo 20 demos/semana.",
        "deuda_tecnica_adquisicion": "Los leads de LinkedIn se pasan manualmente a HubSpot — requiere automatización con Zapier.",
        "activo_first_party_data": "Lista de 2,400 CMOs y VPs de Growth en LATAM con email verificado.",
    },
    "vector_6_historico": {
        "campañas_exitosas": [
            {"descripcion": "Campaña ABM Q4 2025 para sector Fintech", "roi_observado": "4.2x en 60 días", "diagnostico": "Segmentación ultra-específica + contenido de thought leadership funcionó."},
        ],
        "campañas_fallidas": [
            {"descripcion": "Meta Ads B2C Q1 2025", "roi_observado": "0.3x", "diagnostico": "El producto es B2B puro — audiencia de Meta incompatible con el ICP."},
        ],
        "practicas_obsoletas": ["Reportes en PDF estáticos que nadie lee", "Reuniones de status semanales de 2 horas sin agenda"],
    },
    "vector_7_objetivos": {
        "north_star_metric": "MQLs calificados (score > 70 en HubSpot) generados por mes.",
        "objetivo_negocio_12_meses": "Escalar de $180k a $360k ARR cerrando 4 nuevas cuentas enterprise.",
        "objetivo_tactico_trimestre": "Generar 60 MQLs calificados en Q2 con un CPA ≤ $100 USD usando principalmente LinkedIn Ads y contenido SEO.",
    },
    "vector_8_gobernanza": {
        "zonas_rojas_compliance": [
            "No usar datos de contactos sin opt-in explícito (GDPR/LGPD)",
            "No hacer promesas de resultados garantizados en materiales publicitarios",
            "No publicar casos de estudio sin autorización escrita del cliente",
        ],
        "riesgo_pr": "Cualquier campaña que parezca spam masivo destruye la credibilidad de thought leadership que tomó 3 años construir.",
        "propiedad_intelectual_confidencial": "Metodología de atribución multi-touch y base de datos de benchmarks B2B.",
    },
    "vector_9_perfil_pm": {
        "arquetipo_principal": "Technical_PM",
        "matriz_habilidades": {
            "enfoque_tecnico": 9,
            "enfoque_negocio": 8,
            "enfoque_usuario_ux": 5,
        },
        "sesgo_metodologico": (
            "Basar TODAS las decisiones en LTV y reducción de Churn. "
            "Priorizar retención sobre adquisición. "
            "Nunca proponer tácticas sin sustento matemático de CAC vs. LTV."
        ),
        "skills_especificas_activas": [
            "generar_business_case",
            "generar_analisis_ansoff",
            "generar_prd",
            "generar_plan_demanda",
            "evaluar_preparacion_lanzamiento",
        ],
    },
}

# ══════════════════════════════════════════════════════════════════
# SCHEMAS DE REQUEST / RESPONSE
# ══════════════════════════════════════════════════════════════════


class EjecutarTareaRequest(BaseModel):
    peticion: str
    nombre_marca: str = "Disrupt"
    ruta_espacio_trabajo: str = "/NJM_OS/Marcas/Disrupt/Q2_Campaign/"
    modo: str = "ejecucion"  # "onboarding" | "ejecucion" | "auditoria"
    thread_id: Optional[str] = None  # Si None, se genera uno nuevo


class ErrorResponse(BaseModel):
    error: str
    detalle: str
    id_transaccion: str


# ══════════════════════════════════════════════════════════════════
# HELPER: PAYLOAD FALLBACK
# Se usa cuando el PM termina sin generar documentos ni bloqueo explícito
# (respuesta puramente conversacional). No debería ocurrir en producción
# pero protege el contrato de la API.
# ══════════════════════════════════════════════════════════════════


def _payload_sin_documentos(peticion: str) -> Dict[str, Any]:
    return {
        "id_transaccion": str(uuid4()),
        "estado_ejecucion": EstadoValidacion.BLOQUEO_CEO.value,
        "metadata": {
            "skill_utilizada": "ninguna",
            "timestamp_generacion": datetime.now(timezone.utc).isoformat(),
        },
        "contenido_tarjeta": {
            "propuesta_principal": "El PM no ejecutó ninguna skill para esta petición.",
            "framework_metodologico": "N/A",
            "check_coherencia_adn": {
                "aprobado": False,
                "justificacion": (
                    f"La petición '{peticion[:80]}' no activó ninguna de las 14 skills. "
                    "Intenta ser más específico sobre qué entregable necesitas."
                ),
            },
            "archivos_locales_cowork": [],
            "log_errores_escalamiento": [
                "El Agente PM completó su razonamiento sin invocar ninguna herramienta.",
                "Reformula la petición indicando el tipo de entregable (ej: 'Genera un Business Case para...').",
            ],
        },
        "acciones_ui_disponibles": [
            {
                "label": "Reformular Petición",
                "accion_backend": "/api/v1/tarjeta/ajustar",
                "variante_visual": "secundario_outline",
            },
        ],
    }


# ══════════════════════════════════════════════════════════════════
# ENDPOINT
# ══════════════════════════════════════════════════════════════════


@router.post(
    "/api/ejecutar-tarea",
    summary="Ejecutar tarea del Agente PM",
    description=(
        "Recibe la petición del Encargado Real, inicializa el NJM_PM_State "
        "con el Libro Vivo de la marca, ejecuta el grafo LangGraph y devuelve "
        "la Tarjeta de Sugerencia UI lista para renderizar en el frontend."
    ),
    responses={
        200: {"description": "Tarjeta de Sugerencia generada exitosamente."},
        422: {"description": "Petición inválida."},
        500: {"description": "Error interno del grafo o de la API de Anthropic."},
    },
)
async def ejecutar_tarea(req: EjecutarTareaRequest) -> Dict[str, Any]:
    """
    Endpoint principal de ejecución del Agente PM.

    1. Valida que ANTHROPIC_API_KEY esté configurada.
    2. Inicializa el NJM_PM_State con el Libro Vivo de prueba (Disrupt).
    3. Invoca el grafo compilado en un thread separado (no bloquea el event loop).
    4. Extrae y devuelve el payload_tarjeta_sugerencia del estado final.
    """
    # ── Guardia: API Key ──────────────────────────────────────────
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ANTHROPIC_API_KEY no configurada.",
                "detalle": (
                    "Crea el archivo backend/.env con ANTHROPIC_API_KEY=sk-ant-... "
                    "y reinicia el servidor con 'uvicorn main:app --reload'."
                ),
                "id_transaccion": str(uuid4()),
            },
        )

    # ── Inicializar estado ────────────────────────────────────────
    tid = req.thread_id or str(uuid4())
    estado_inicial: NJM_PM_State = {
        "thread_id": tid,
        "modo_operacion": req.modo,
        "messages": [HumanMessage(content=req.peticion)],
        "libro_vivo": _LIBRO_VIVO_DISRUPT,
        "ruta_espacio_trabajo": req.ruta_espacio_trabajo,
        "peticion_humano": req.peticion,
        "skill_activa": None,
        "documentos_generados": [],
        "estado_validacion": EstadoValidacion.EN_PROGRESO.value,
        "alertas_internas": [],
        "payload_tarjeta_sugerencia": None,
    }
    config = {"configurable": {"thread_id": tid}}

    # ── Ejecutar grafo (en thread para no bloquear el event loop) ─
    try:
        estado_final: Dict[str, Any] = await asyncio.to_thread(
            _GRAFO.invoke, estado_inicial, config
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error al ejecutar el grafo LangGraph.",
                "detalle": str(exc),
                "id_transaccion": str(uuid4()),
            },
        ) from exc

    # ── Extraer payload ───────────────────────────────────────────
    payload = estado_final.get("payload_tarjeta_sugerencia")

    if payload is None:
        payload = _payload_sin_documentos(req.peticion)

    payload["thread_id"] = tid
    return payload


@router.post("/api/upload-documento", summary="Indexar PDF en ChromaDB")
async def upload_documento(file: UploadFile = File(...)) -> Dict[str, Any]:
    from core.document_processor import pdf_to_docs
    from core.vector_store import vector_store

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")

    contents = await file.read()
    docs = pdf_to_docs(contents, file.filename)
    if not docs:
        raise HTTPException(status_code=422, detail="El PDF no contiene texto extraíble.")

    vector_store.add_documents(docs)
    return {"status": "ok", "chunks_indexados": len(docs), "filename": file.filename}
