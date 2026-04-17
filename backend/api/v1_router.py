"""
NJM OS — v1 API router

Endpoints:
  POST /api/v1/ingest          — document ingestion (multipart)
  GET  /api/v1/agent/stream    — SSE agent stream
    ?sequenceId=ceo-audit      → real LangGraph + Claude streaming
    ?sequenceId=<other>        → mock script (pm-execution, ceo-approve, ceo-reject)
    ?brand_context=<text>      — optional brand context for ceo-audit (default: demo brand)
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/api/v1")

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "temp_uploads"


# ══════════════════════════════════════════════════════════════════
# POST /api/v1/ingest
# ══════════════════════════════════════════════════════════════════

@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    context: str = Form(default=""),
    vectorId: str = Form(default=""),
):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    dest = UPLOAD_DIR / file.filename
    contents = await file.read()
    dest.write_bytes(contents)

    return {
        "status": "success",
        "message": "Documento procesado",
        "filename": file.filename,
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

_DEFAULT_BRAND_CONTEXT = (
    "Marca: Disrupt Agency — Agencia de marketing B2B enfocada en SaaS latinoamericano. "
    "Etapa: Serie A. CAC objetivo: $120. LTV objetivo: $2,400. "
    "Mercados: México, Colombia, Argentina. "
    "Diferenciador: integración de IA en campañas de demanda."
)


def _extract_text(content: str | list) -> str:
    """Normalize Anthropic streaming content blocks to plain text."""
    if isinstance(content, str):
        return content
    # Anthropic returns list of dicts: [{"type": "text", "text": "...", "index": 0}]
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text", "")
            if text:
                parts.append(text)
    return "".join(parts)


async def _sse_ceo_audit(brand_context: str) -> AsyncGenerator[str, None]:
    """Stream real CEO auditor tokens from LangGraph via astream_events."""
    # Import here to avoid circular imports and keep graph load lazy.
    from agent.njm_graph import AgentState, ceo_graph  # noqa: PLC0415

    initial_state: AgentState = {
        "messages": [
            HumanMessage(
                content=(
                    "Inicia la auditoría CEO. Analiza el contexto de marca provisto, "
                    "evalúa riesgos estratégicos y emite tu diagnóstico ejecutivo."
                )
            )
        ],
        "brand_context": brand_context,
        "risk_flag": False,
    }

    yield "data: [⏳] Conectando con Agente CEO real (Claude)...\n\n"
    await asyncio.sleep(0.1)

    buffer: str = ""

    async for event in ceo_graph.astream_events(initial_state, version="v2"):
        if event["event"] != "on_chat_model_stream":
            continue

        chunk = event["data"].get("chunk")
        if chunk is None:
            continue

        text = _extract_text(chunk.content)
        if not text:
            continue

        # Buffer tokens until we have a natural flush point (newline or ~80 chars).
        buffer += text
        while "\n" in buffer or len(buffer) >= 80:
            if "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    yield f"data: {line.strip()}\n\n"
            else:
                yield f"data: {buffer}\n\n"
                buffer = ""
                break

    # Flush remaining buffer
    if buffer.strip():
        yield f"data: {buffer.strip()}\n\n"

    yield "data: [✓] Auditoría CEO completada.\n\n"
    yield "data: [DONE]\n\n"


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
    brand_context: str = _DEFAULT_BRAND_CONTEXT,
):
    if sequenceId == "ceo-audit":
        generator = _sse_ceo_audit(brand_context)
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
