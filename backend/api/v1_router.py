"""
NJM OS — v1 API router

Endpoints:
  POST /api/v1/ingest          — document ingestion (multipart)
  GET  /api/v1/agent/stream    — SSE agent stream
    ?sequenceId=ceo-audit      → real LangGraph + Claude streaming
    ?sequenceId=<other>        → mock script (pm-execution, ceo-approve, ceo-reject)
    ?brand_id=<str>            — brand slug (default: disrupt)
    ?session_id=<str>          — session UUID (default: dev-session-1)
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import json

from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/api/v1")

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "temp_uploads"

_NODE_START_LOG: dict[str, str] = {
    "ingest": "[⏳] Procesando documentos de onboarding...",
    "ceo_auditor": "[⏳] Auditoría CEO iniciada — escaneando vectores estratégicos...",
    "human_in_loop": "[⏳] Esperando input del Encargado Real...",
    "pm_execution": "[⏳] Agente PM ejecutando skill seleccionada...",
    "ceo_review": "[⏳] CEO revisando output del PM...",
    "output": "[⏳] Generando tarjeta final...",
}

_NODE_END_LOG: dict[str, str] = {
    "ingest": "[✓] Documentos indexados en memoria de marca.",
    "ceo_auditor": "[✓] Auditoría CEO completada.",
    "pm_execution": "[✓] Ejecución PM finalizada.",
    "ceo_review": "[✓] Revisión CEO completada.",
    "output": "[✓] Tarjeta lista.",
}


def _sse_json(payload: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ══════════════════════════════════════════════════════════════════
# POST /api/v1/ingest
# ══════════════════════════════════════════════════════════════════

@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    brand_id: str = Form(default="disrupt"),
    context: str = Form(default=""),
    vectorId: str = Form(default=""),
):
    import asyncio
    from core import ingest as _ingest  # noqa: PLC0415

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(file.filename).name
    dest = UPLOAD_DIR / safe_filename
    contents = await file.read()
    dest.write_bytes(contents)

    try:
        chunks_stored = await asyncio.to_thread(
            _ingest.ingest_document, brand_id, contents, safe_filename
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error al indexar el documento: {exc}",
        ) from exc

    return {
        "status": "success",
        "message": "Documento procesado e indexado",
        "filename": safe_filename,
        "brand_id": brand_id,
        "chunks_stored": chunks_stored,
    }


# ══════════════════════════════════════════════════════════════════
# GET /api/v1/agent/stream — helpers
# ══════════════════════════════════════════════════════════════════

_MOCK_SCRIPTS: dict[str, list[str]] = {
    "pm-execution": [
        "[⏳] Agente PM inicializado — leyendo Libro Vivo...",
        "[⏳] Seleccionando skill óptima según petición...",
        "[✓] Skill activa: generar_business_case",
        "[⏳] Ejecutando análisis LTV / CAC contra vector_2_negocio...",
        "[✓] Business Case generado. Estado: LISTO_PARA_FIRMA",
    ],
    "ceo-approve": [
        "[⏳] CEO revisando tarjeta de sugerencia...",
        "[✓] Coherencia con ADN de marca confirmada.",
        "[✓] Entregable aprobado y firmado. Moviendo a Cowork.",
    ],
    "ceo-reject": [
        "[!] CEO solicitó revisión del entregable.",
        "[⏳] Registrando motivo de rechazo en log interno...",
        "[✓] Bloqueo registrado. PM notificado para reformulación.",
    ],
}

_DEFAULT_SCRIPT = [
    "[⏳] Inicializando agente...",
    "[⏳] Procesando solicitud...",
    "[✓] Secuencia completada.",
]

# Set True to short-circuit ceo-audit with a hardcoded BLOQUEO_CEO sequence
# for frontend testing without a live OpenAI key.
_TEST_BLOQUEO_CEO = False


async def _sse_bloqueo_ceo_test(
    brand_id: str, session_id: str
) -> AsyncGenerator[str, None]:
    """Hardcoded BLOQUEO_CEO sequence for frontend testing without a live OpenAI key."""
    logs = [
        f"[⏳] Conectando con NJM OS (brand: {brand_id})...",
        "[⏳] Auditoría CEO iniciada — escaneando vectores estratégicos...",
        "[⏳] Herramienta: buscar_contexto_marca...",
        "[✓] buscar_contexto_marca completada.",
        "[⏳] Analizando coherencia de narrativa de marca...",
        "[✓] Auditoría CEO completada.",
    ]
    for log in logs:
        yield _sse_json({"type": "log", "text": log})
        await asyncio.sleep(0.8)

    yield _sse_json({
        "type": "action_required",
        "trigger": "BLOQUEO_CEO",
        "risk_message": (
            "Se detectó un cambio crítico en la narrativa de marca "
            "que requiere validación manual."
        ),
        "session_id": session_id,
        "brand_id": brand_id,
    })
    # No "done" — stream closes here; shield stays open until CEO decides.



_DEFAULT_BRAND_CONTEXT = (
    "Marca: Disrupt Agency — Agencia de marketing B2B enfocada en SaaS latinoamericano. "
    "Etapa: Serie A. CAC objetivo: $120. LTV objetivo: $2,400. "
    "Mercados: México, Colombia, Argentina. "
    "Diferenciador: integración de IA en campañas de demanda."
)


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


async def _sse_njm_stream(
    brand_id: str,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """
    Stream njm_graph.astream_events for a given brand/session.

    Emits JSON-structured SSE events:
      {"type": "log",            "text": "..."}
      {"type": "action_required", "trigger": "BLOQUEO_CEO"|"GAP_DETECTED", ...}
      {"type": "done"}

    Note: {"type": "done"} is NOT emitted on client disconnect (CancelledError).
    """
    from agent.njm_graph import njm_graph  # noqa: PLC0415
    from core.dev_fixtures import _LIBRO_VIVO_DISRUPT  # noqa: PLC0415

    thread_id = f"{brand_id}:{session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    if brand_id == "disrupt":
        initial_state = {
            "brand_id": brand_id,
            "session_id": session_id,
            "messages": [
                HumanMessage(
                    content="Ejecuta el flujo completo. brand_id=disrupt, usar fixtures de desarrollo."
                )
            ],
            "audit_status": "COMPLETE",
            "libro_vivo": _LIBRO_VIVO_DISRUPT,
            "brand_context_raw": _DEFAULT_BRAND_CONTEXT,
            "uploaded_doc_paths": [],
            "documentos_generados": [],
            "alertas_internas": [],
            "ruta_espacio_trabajo": f"~/NJM_OS/Marcas/{brand_id}/workspace/",
            "risk_flag": False,
            "estado_validacion": "EN_PROGRESO",
            "peticion_humano": "Genera el Business Case inicial para la marca.",
        }
    else:
        initial_state = {
            "brand_id": brand_id,
            "session_id": session_id,
            "messages": [
                HumanMessage(
                    content="Inicia la auditoría CEO y ejecuta el flujo completo."
                )
            ],
            "audit_status": "PENDING",
            "brand_context_raw": "",
            "uploaded_doc_paths": [],
            "documentos_generados": [],
            "alertas_internas": [],
            "ruta_espacio_trabajo": f"~/NJM_OS/Marcas/{brand_id}/workspace/",
            "risk_flag": False,
            "estado_validacion": "EN_PROGRESO",
            "peticion_humano": None,
        }

    yield _sse_json({"type": "log", "text": f"[⏳] Conectando con NJM OS (brand: {brand_id})..."})

    buffer: str = ""

    try:
        async for event in njm_graph.astream_events(initial_state, config, version="v2"):
            etype = event.get("event", "")
            name = event.get("name", "")

            if etype == "on_chain_start" and name in _NODE_START_LOG:
                yield _sse_json({"type": "log", "text": _NODE_START_LOG[name]})

            elif etype == "on_chain_end" and name in _NODE_END_LOG:
                yield _sse_json({"type": "log", "text": _NODE_END_LOG[name]})

            elif etype == "on_tool_start":
                yield _sse_json({"type": "log", "text": f"[⏳] Herramienta: {name}..."})

            elif etype == "on_tool_end":
                yield _sse_json({"type": "log", "text": f"[✓] {name} completada."})

            elif etype == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk is None:
                    continue
                text = _extract_text(chunk.content)
                if not text:
                    continue
                buffer += text
                while "\n" in buffer or len(buffer) >= 80:
                    if "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if line.strip():
                            yield _sse_json({"type": "log", "text": line.strip()})
                    else:
                        yield _sse_json({"type": "log", "text": buffer})
                        buffer = ""
                        break

        if buffer.strip():
            yield _sse_json({"type": "log", "text": buffer.strip()})

    except asyncio.CancelledError:
        return

    # Post-stream: check final state for interrupts / terminal states
    try:
        snapshot = await njm_graph.aget_state(config)
        values = snapshot.values

        if snapshot.next:
            questions = values.get("interview_questions") or []
            yield _sse_json({
                "type": "action_required",
                "trigger": "GAP_DETECTED",
                "questions": questions,
                "gap_report_path": values.get("gap_report_path"),
                "session_id": session_id,
                "brand_id": brand_id,
            })

        elif values.get("estado_validacion") == "BLOQUEO_CEO":
            yield _sse_json({
                "type": "action_required",
                "trigger": "BLOQUEO_CEO",
                "risk_message": values.get("risk_details", "Revisión CEO requerida."),
                "session_id": session_id,
                "brand_id": brand_id,
            })

    except Exception as exc:
        yield _sse_json({"type": "log", "text": f"[!] No se pudo leer estado final: {exc}"})

    yield _sse_json({"type": "done"})


async def _sse_mock(sequence_id: str) -> AsyncGenerator[str, None]:
    script = _MOCK_SCRIPTS.get(sequence_id, _DEFAULT_SCRIPT)

    yield f"data: [⏳] Iniciando secuencia {sequence_id}\n\n"
    await asyncio.sleep(0.5)

    for line in script:
        yield f"data: {line}\n\n"
        await asyncio.sleep(1)

    yield "data: [DONE]\n\n"


# ══════════════════════════════════════════════════════════════════
# GET /api/v1/agent/stream
# ══════════════════════════════════════════════════════════════════

@router.get("/agent/stream")
async def agent_stream(
    sequenceId: str,
    brand_id: str = "disrupt",
    session_id: str = "dev-session-1",
):
    """
    Unified SSE agent stream.

    sequenceId=ceo-audit  → streams real njm_graph (brand_id + session_id required)
    sequenceId=<other>    → mock script (pm-execution, ceo-approve, ceo-reject)

    TD-03 resolved: brand_id and session_id now come from query params, not brand_context.
    """
    if sequenceId == "ceo-audit":
        if _TEST_BLOQUEO_CEO:
            generator = _sse_bloqueo_ceo_test(brand_id, session_id)
        else:
            generator = _sse_njm_stream(brand_id, session_id)
    else:
        generator = _sse_mock(sequenceId)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ══════════════════════════════════════════════════════════════════
# GET /api/v1/session/state
# ══════════════════════════════════════════════════════════════════

@router.get("/session/state")
async def get_session_state(
    brand_id: str = "disrupt",
    session_id: str = "dev-session-1",
):
    """Return current checkpointer snapshot for a brand/session thread."""
    from agent.njm_graph import njm_graph  # noqa: PLC0415

    thread_id = f"{brand_id}:{session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        snapshot = await njm_graph.aget_state(config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Checkpointer error: {exc}") from exc

    values = snapshot.values if snapshot else {}
    return {
        "audit_status": values.get("audit_status", "PENDING"),
        "interview_questions": values.get("interview_questions"),
        "last_tarjeta": values.get("payload_tarjeta_sugerencia"),
        "documentos_count": len(values.get("documentos_generados", [])),
        "next_interrupt": list(snapshot.next) if snapshot else [],
    }


# ══════════════════════════════════════════════════════════════════
# POST /api/v1/agent/resume
# ══════════════════════════════════════════════════════════════════

from pydantic import BaseModel as _BaseModel  # noqa: PLC0415


class ResumeRequest(_BaseModel):
    brand_id: str
    session_id: str
    answers: str


@router.post("/agent/resume")
async def agent_resume(body: ResumeRequest):
    """Resume a graph paused at human_in_loop_node after interview answers are provided."""
    from agent.njm_graph import njm_graph  # noqa: PLC0415

    thread_id = f"{body.brand_id}:{body.session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        await njm_graph.ainvoke(
            {"human_interview_answers": body.answers},
            config=config,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Resume failed: {exc}") from exc

    return {"status": "resumed", "thread_id": thread_id}
