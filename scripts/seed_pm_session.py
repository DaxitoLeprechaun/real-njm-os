#!/usr/bin/env python3
"""
Seed dev-session-1 with a CEO-approved PM state for Kanban testing.

Usage:
    cd /path/to/real-njm-os
    python3 scripts/seed_pm_session.py

After running, start the backend and open /brand/disrupt/pm to test the
interactive Kanban board without needing a live OpenAI key.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# ── Path setup ─────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")
os.environ.setdefault("OPENAI_API_KEY", "seed-script-no-api-call")

# ── Seed data ───────────────────────────────────────────────────────────────

BRAND_ID = "disrupt"
SESSION_ID = "dev-session-1"
THREAD_ID = f"{BRAND_ID}:{SESSION_ID}"
DB_PATH = BACKEND_DIR / "njm_sessions.db"

_TARJETA = {
    "id_transaccion": "00000000-seed-0000-0000-dev000000001",
    "estado_ejecucion": "LISTO_PARA_FIRMA",
    "metadata": {
        "skill_utilizada": "generar_business_case",
        "timestamp_generacion": datetime.now().isoformat(),
    },
    "contenido_tarjeta": {
        "propuesta_principal": (
            "Pivotar a estrategia de retención: reducir CAC 40% "
            "vía lifecycle marketing y upsell a clientes existentes."
        ),
        "framework_metodologico": "Business Model Canvas + CLV Optimization",
        "check_coherencia_adn": {
            "aprobado": True,
            "justificacion": (
                "Alineado con North Star Metric del Vector 7 "
                "(retención > adquisición en fase de consolidación)."
            ),
        },
        "archivos_locales_cowork": [],
        "log_errores_escalamiento": [],
    },
    "acciones_ui_disponibles": [
        {
            "label": "Aprobar y Ejecutar",
            "accion_backend": "/api/v1/agent/resume",
            "variante_visual": "primario_success",
        }
    ],
}

_TAREAS = [
    {
        "id": "tarea-001",
        "titulo": "Auditar CAC actual vs benchmark $120",
        "descripcion": "Cruzar datos de CRM con el techo de CAC del Libro Vivo y calcular brecha.",
        "responsable": "Encargado Real",
        "prioridad": "ALTA",
        "estado": "BACKLOG",
        "skill_origen": "generar_business_case",
    },
    {
        "id": "tarea-002",
        "titulo": "Diseñar secuencia de lifecycle emails",
        "descripcion": "Crear flujo de 5 emails post-compra alineado con el buyer journey del Vector 3.",
        "responsable": "PM",
        "prioridad": "ALTA",
        "estado": "BACKLOG",
        "skill_origen": "generar_business_case",
    },
    {
        "id": "tarea-003",
        "titulo": "Identificar top 20% clientes por LTV",
        "descripcion": "Segmentar base de clientes y extraer cohorte de alto valor para upsell.",
        "responsable": "Encargado Real",
        "prioridad": "MEDIA",
        "estado": "BACKLOG",
        "skill_origen": "generar_business_case",
    },
    {
        "id": "tarea-004",
        "titulo": "Configurar dashboard de retención en CRM",
        "descripcion": "Habilitar métricas de churn rate y NPS en el panel de operaciones.",
        "responsable": "PM",
        "prioridad": "MEDIA",
        "estado": "BACKLOG",
        "skill_origen": "generar_business_case",
    },
    {
        "id": "tarea-005",
        "titulo": "Revisar contrato con partner de referidos",
        "descripcion": "Validar cláusulas de revenue share antes del lanzamiento del programa.",
        "responsable": "CEO",
        "prioridad": "BAJA",
        "estado": "BACKLOG",
        "skill_origen": "generar_business_case",
    },
]


# ── Main ────────────────────────────────────────────────────────────────────

async def main() -> None:
    os.chdir(BACKEND_DIR)  # ensure njm_graph opens backend/njm_sessions.db
    import aiosqlite
    from agent.njm_graph import init_graph

    await init_graph()
    from agent.njm_graph import njm_graph  # noqa: PLC0415

    # Clear existing checkpoint so re-runs don't accumulate tasks
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM checkpoints WHERE thread_id = ?", (THREAD_ID,))
        # checkpoint_writes table exists in langgraph-checkpoint-sqlite >= 1.x
        try:
            await db.execute(
                "DELETE FROM checkpoint_writes WHERE thread_id = ?", (THREAD_ID,)
            )
        except Exception as exc:
            print(f"  (checkpoint_writes not cleared: {exc})", file=sys.stderr)
        await db.commit()

    config = {"configurable": {"thread_id": THREAD_ID}}

    await njm_graph.aupdate_state(
        config,
        {
            "brand_id": BRAND_ID,
            "session_id": SESSION_ID,
            "audit_status": "COMPLETE",
            "estado_validacion": "LISTO_PARA_FIRMA",
            "payload_tarjeta_sugerencia": _TARJETA,
            "tareas_generadas": _TAREAS,
            "messages": [],
            "uploaded_doc_paths": [],
            "documentos_generados": [],
            "alertas_internas": [],
            "task_estado_overrides": {},
            "risk_flag": False,
            "ruta_espacio_trabajo": f"~/NJM_OS/Marcas/{BRAND_ID}/workspace/",
            "modo": "ejecucion",
            "nombre_marca": "Disrupt",
        },
        as_node="output",  # terminal node → snapshot.next=[] → no pending interrupt
    )

    print(f"\n✓ Seeded thread: {THREAD_ID}")
    print(f"  → {len(_TAREAS)} tareas en BACKLOG:")
    for t in _TAREAS:
        print(f"     [{t['prioridad']:5s}] {t['id']} — {t['titulo']}")
    print(
        f"\n  → last_tarjeta: \"{_TARJETA['contenido_tarjeta']['propuesta_principal'][:60]}...\""
    )
    print("\nInicia el backend y abre http://localhost:3000/brand/disrupt/pm")


if __name__ == "__main__":
    asyncio.run(main())
