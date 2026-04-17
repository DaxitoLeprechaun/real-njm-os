"""
NJM OS — Router FastAPI: /api/ejecutar-tarea

Orquesta la ejecución del grafo unificado njm_graph, devuelve la
Tarjeta de Sugerencia UI lista para ser consumida por el frontend Next.js.

Flujo:
  POST /api/ejecutar-tarea
    → Resuelve brand_id / session_id (dev fallback si vienen vacíos)
    → Construye thread_id = f"{brand_id}:{session_id}"
    → Inicializa NJM_OS_State con dev fixtures si brand_id == "disrupt"
    → Invoca njm_graph (async via asyncio.to_thread)
    → Devuelve payload_tarjeta_sugerencia (TarjetaSugerenciaUI JSON)

Dev fallback (Phase 2.1):
  brand_id vacío  → "disrupt"
  session_id vacío → "dev-session-1"
  brand_id == "disrupt" → libro_vivo pre-inyectado desde core/dev_fixtures.py
                          audit_status = "COMPLETE" (skip CEO, corre PM directo)

Phase 2.3: el frontend pasará brand_id y session_id reales;
  el dev fallback puede eliminarse en ese punto.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from agent.njm_graph import njm_graph
from core.schemas import EstadoValidacion

router = APIRouter()

# ══════════════════════════════════════════════════════════════════
# SCHEMAS DE REQUEST / RESPONSE
# ══════════════════════════════════════════════════════════════════


class EjecutarTareaRequest(BaseModel):
    peticion: str
    modo: str = "auditoria"
    nombre_marca: str = "Disrupt"
    ruta_espacio_trabajo: str = "/NJM_OS/Marcas/Disrupt/Q2_Campaign/"
    # Phase 2.1: opcionales con dev fallback
    brand_id: Optional[str] = None
    session_id: Optional[str] = None
    thread_id: Optional[str] = None  # override manual del thread (deprecado; usar brand_id+session_id)


class ErrorResponse(BaseModel):
    error: str
    detalle: str
    id_transaccion: str


# ══════════════════════════════════════════════════════════════════
# HELPER: PAYLOAD FALLBACK
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
    summary="Ejecutar tarea del Agente PM vía grafo unificado",
    description=(
        "Recibe la petición del Encargado Real, inicializa NJM_OS_State, "
        "ejecuta njm_graph con checkpointer SqliteSaver y devuelve la "
        "Tarjeta de Sugerencia UI lista para renderizar en el frontend."
    ),
    responses={
        200: {"description": "Tarjeta de Sugerencia generada exitosamente."},
        422: {"description": "Petición inválida."},
        500: {"description": "Error interno del grafo o de la API de Anthropic."},
    },
)
async def ejecutar_tarea(req: EjecutarTareaRequest) -> Dict[str, Any]:
    # ── Guardia: API Key ──────────────────────────────────────────
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

    # ── Resolver brand_id / session_id con dev fallback ──────────
    brand_id = req.brand_id or "disrupt"
    session_id = req.session_id or "dev-session-1"
    thread_id = req.thread_id or f"{brand_id}:{session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # ── Dev fixtures: inyectar libro_vivo para sesión de prueba ──
    # Phase 2.3: esto se elimina cuando el frontend pase brand_id real
    # y el CEO haya completado el onboarding del thread en el checkpointer.
    libro_vivo_inicial: Dict[str, Any] = {}
    audit_status_inicial = "PENDING"

    if brand_id == "disrupt":
        from core.dev_fixtures import _LIBRO_VIVO_DISRUPT
        libro_vivo_inicial = _LIBRO_VIVO_DISRUPT
        audit_status_inicial = "COMPLETE"  # skip CEO, corre PM directamente

    # ── Inicializar estado completo ───────────────────────────────
    estado_inicial: Dict[str, Any] = {
        # Identidad
        "brand_id": brand_id,
        "session_id": session_id,
        # Mensajes
        "messages": [HumanMessage(content=req.peticion)],
        # Onboarding
        "brand_context_raw": "",
        "uploaded_doc_paths": [],
        # CEO
        "audit_status": audit_status_inicial,
        "gap_report_path": None,
        "interview_questions": None,
        "human_interview_answers": None,
        "libro_vivo": libro_vivo_inicial or None,
        # Riesgo
        "risk_flag": False,
        "risk_details": None,
        "ceo_review_decision": None,
        # PM
        "peticion_humano": req.peticion,
        "ruta_espacio_trabajo": req.ruta_espacio_trabajo,
        "skill_activa": None,
        "documentos_generados": [],
        "estado_validacion": EstadoValidacion.EN_PROGRESO.value,
        "alertas_internas": [],
        # Output
        "payload_tarjeta_sugerencia": None,
        # Routing
        "next_node": None,
        # Compat
        "modo": req.modo,
        "nombre_marca": req.nombre_marca,
    }

    # ── Ejecutar grafo con checkpointer ──────────────────────────
    try:
        estado_final: Dict[str, Any] = await asyncio.to_thread(
            njm_graph.invoke, estado_inicial, config
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error al ejecutar njm_graph.",
                "detalle": str(exc),
                "id_transaccion": str(uuid4()),
            },
        ) from exc

    # ── Extraer payload ───────────────────────────────────────────
    payload = estado_final.get("payload_tarjeta_sugerencia")
    if payload is None:
        payload = _payload_sin_documentos(req.peticion)

    payload["thread_id"] = thread_id
    return payload
