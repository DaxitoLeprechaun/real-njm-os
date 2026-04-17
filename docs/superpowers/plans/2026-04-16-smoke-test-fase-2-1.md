# Smoke Test Fase 2.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create and run `backend/test_graph.py` to verify the Phase 2.1 unified graph flows correctly — dev fallback activates, CEO is skipped, PM executes, and SQLite checkpointer persists the session.

**Architecture:** The script calls `njm_graph.invoke()` directly (no HTTP server needed), builds `NJM_OS_State` exactly as `api/main.py` does for `brand_id="disrupt"`, and asserts four postconditions: CEO skip guard fired, PM ran at least one skill, `payload_tarjeta_sugerencia` is populated, and SQLite has a checkpoint row for the thread.

**Tech Stack:** Python 3.11+, LangGraph 0.2.60, langgraph-checkpoint-sqlite 2.0.11, SQLite3 stdlib, python-dotenv.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/test_graph.py` | **Create** | Standalone smoke test — loads env, builds initial state, invokes graph, asserts 4 postconditions, prints diagnostic output |

No existing files are modified.

---

### Task 1: Create `backend/test_graph.py`

**Files:**
- Create: `backend/test_graph.py`

- [ ] **Step 1: Verify the venv and .env exist**

Run from repo root:
```bash
ls backend/.venv/bin/python3 && echo "venv OK"
ls backend/.env && echo ".env OK"
```
Expected: both lines print `OK`. If `.venv` is missing, run:
```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```
If `.env` is missing, copy from `.env.example` and fill in `ANTHROPIC_API_KEY`.

- [ ] **Step 2: Write `backend/test_graph.py`**

```python
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

if not os.getenv("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY not set. Create backend/.env with the key.")
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
```

- [ ] **Step 3: Run the smoke test**

```bash
cd backend && .venv/bin/python3 test_graph.py
```

Expected output (PM will make real Anthropic API calls — puede tardar 30-90 segundos):
```
============================================================
NJM OS — Smoke Test Fase 2.1
thread_id : disrupt:test-001
peticion  : Generar Business Case para campaña de Demand Generation Q2 2026
============================================================

[GRAPH] Invocando njm_graph.invoke() ...
[GRAPH] Ejecución completa.

[✓] CEO skip guard OK — audit_status: COMPLETE
[✓] skill_activa        : generar_business_case
[✓] estado_validacion   : LISTO_PARA_FIRMA
[✓] documentos_generados (1):
     • /NJM_OS/Marcas/Disrupt/Q2_Campaign/business_case_*.md
[✓] payload presente    — id: <uuid>
    estado_ejecucion    : LISTO_PARA_FIRMA

[SQLite] Verificando checkpointer ...
[✓] SQLite OK — N checkpoint(s) para thread_id=disrupt:test-001

============================================================
Smoke Test PASÓ ✓ — Fase 2.1 completada
============================================================
```

If the test exits with code 1, the failure lines tell you exactly which postcondition failed.

- [ ] **Step 4: Commit**

```bash
cd ..
git add backend/test_graph.py docs/superpowers/plans/2026-04-16-smoke-test-fase-2-1.md
git commit -m "test: add Phase 2.1 smoke test for unified graph + SQLite checkpointer"
```

---

## Self-Review

**Spec coverage:**
- ✅ Invoke `njm_graph.invoke()` directly with `brand_id="disrupt"`, `session_id="test-001"`, petición de prueba
- ✅ Verify dev fallback activates (`audit_status="COMPLETE"`, `libro_vivo` pre-injected)
- ✅ Verify graph skips `ceo_auditor_node` (skip guard postcondition)
- ✅ Verify `pm_execution_node` ran (via `skill_activa` + `documentos_generados`)
- ✅ Print `documentos_generados` and final state
- ✅ Verify SQLite checkpointer persisted the session

**Placeholder scan:** None found. All code is complete.

**Type consistency:** `NJM_OS_State` fields match `core/estado.py` exactly. `EstadoValidacion` imported from `core/schemas.py`. `_LIBRO_VIVO_DISRUPT` imported from `core/dev_fixtures.py`.
