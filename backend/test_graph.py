"""
Smoke test Phase 2.1 — verifies four postconditions:
  1. CEO skip guard fires (audit_status stays COMPLETE)
  2. PM executes at least one skill
  3. payload_tarjeta_sugerencia is populated
  4. SQLite checkpointer persists the session
Run from backend/:
  .venv/bin/python3 test_graph.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

# load_dotenv MUST run before any agent module import — agents instantiate
# ChatAnthropic at module level and read ANTHROPIC_API_KEY immediately.
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not set. Create backend/.env with the key.")
    sys.exit(1)

from langchain_core.messages import HumanMessage

from agent.njm_graph import njm_graph
from core.dev_fixtures import _LIBRO_VIVO_DISRUPT
from core.schemas import EstadoValidacion

BRAND_ID = "disrupt"
SESSION_ID = "test-001"
THREAD_ID = f"{BRAND_ID}:{SESSION_ID}"
PETICION = "Generar Business Case para campaña de Demand Generation Q2 2026"

config = {"configurable": {"thread_id": THREAD_ID}}

estado_inicial = {
    # Identity
    "brand_id": BRAND_ID,
    "session_id": SESSION_ID,
    # Messages
    "messages": [HumanMessage(content=PETICION)],
    # Onboarding
    "brand_context_raw": "",
    "uploaded_doc_paths": [],
    # CEO — pre-set COMPLETE so ceo_auditor_node skip guard fires
    "audit_status": "COMPLETE",
    "gap_report_path": None,
    "interview_questions": None,
    "human_interview_answers": None,
    "libro_vivo": _LIBRO_VIVO_DISRUPT,
    # Risk
    "risk_flag": False,
    "risk_details": None,
    "ceo_review_decision": None,
    # PM
    "peticion_humano": PETICION,
    "ruta_espacio_trabajo": "/NJM_OS/Marcas/Disrupt/Q2_Campaign/",
    "skill_activa": None,
    "documentos_generados": [],
    "estado_validacion": EstadoValidacion.EN_PROGRESO.value,
    "alertas_internas": [],
    # Output
    "payload_tarjeta_sugerencia": None,
    # Routing
    "next_node": None,
    # Compat
    "modo": "auditoria",
    "nombre_marca": "Disrupt",
}

SEP = "=" * 60

print(SEP)
print("NJM OS — Smoke Test Fase 2.1")
print(f"thread_id : {THREAD_ID}")
print(f"peticion  : {PETICION}")
print(SEP)

print("\n[GRAPH] Invocando njm_graph.invoke() ...")
estado_final = njm_graph.invoke(estado_inicial, config)
print("[GRAPH] Ejecución completa.\n")

failures: list[str] = []

# ── Postcondition 1: CEO skip guard fired ─────────────────────────
audit_final = estado_final.get("audit_status")
if audit_final == "COMPLETE":
    print(f"[✓] CEO skip guard OK — audit_status: {audit_final}")
else:
    msg = f"[✗] CEO skip guard FAIL — audit_status esperado=COMPLETE, obtenido={audit_final}"
    print(msg)
    failures.append(msg)

# ── Postcondition 2: PM ejecutó (documentos_generados o skill_activa) ─
documentos = estado_final.get("documentos_generados", [])
skill_activa = estado_final.get("skill_activa")
estado_validacion = estado_final.get("estado_validacion")
print(f"[✓] skill_activa        : {skill_activa}")
print(f"[✓] estado_validacion   : {estado_validacion}")
print(f"[✓] documentos_generados ({len(documentos)}):")
for doc in documentos:
    print(f"     • {doc}")
if skill_activa is None and not documentos:
    msg = "[✗] PM no ejecutó ninguna skill — skill_activa es None y documentos_generados vacío"
    print(msg)
    failures.append(msg)

# ── Postcondition 3: payload_tarjeta_sugerencia existe ────────────
payload = estado_final.get("payload_tarjeta_sugerencia")
if payload is not None:
    print(f"[✓] payload presente    — id: {payload.get('id_transaccion')}")
    print(f"    estado_ejecucion    : {payload.get('estado_ejecucion')}")
else:
    msg = "[✗] payload_tarjeta_sugerencia es None"
    print(msg)
    failures.append(msg)

# ── Postcondition 4: SQLite tiene el checkpoint ───────────────────
print("\n[SQLite] Verificando checkpointer ...")
try:
    conn = sqlite3.connect("njm_sessions.db")
    (count,) = conn.execute(
        "SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?",
        (THREAD_ID,),
    ).fetchone()
    conn.close()
    if count > 0:
        print(f"[✓] SQLite OK — {count} checkpoint(s) para thread_id={THREAD_ID}")
    else:
        msg = f"[✗] SQLite FAIL — 0 checkpoints para thread_id={THREAD_ID}"
        print(msg)
        failures.append(msg)
except Exception as exc:
    msg = f"[✗] SQLite error: {exc}"
    print(msg)
    failures.append(msg)

# ── Resultado final ───────────────────────────────────────────────
print("\n" + SEP)
if failures:
    print(f"Smoke Test FALLÓ — {len(failures)} postcondition(s) no cumplida(s):")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
else:
    print("Smoke Test PASÓ ✓ — Fase 2.1 completada")
print(SEP)
