"""
Tests for Phase 2.7 — Tablero Interactivo

Covers:
  - NJM_OS_State has task_estado_overrides field
  - PATCH /api/v1/tasks/{task_id} — persists override
  - PATCH validates estado enum (422 on invalid)
  - PATCH merges with existing overrides
  - GET /api/v1/session/state — returns merged tasks list
  - GET /api/v1/session/state — returns tasks: [] when no tareas_generadas
"""

import asyncio
import typing
import pytest
from core.estado import NJM_OS_State


def test_njm_os_state_has_task_estado_overrides():
    hints = typing.get_type_hints(NJM_OS_State, include_extras=True)
    assert "task_estado_overrides" in hints


@pytest.fixture(scope="module")
def client():
    import os
    os.environ.setdefault("OPENAI_API_KEY", "test")
    from agent.njm_graph import init_graph
    asyncio.run(init_graph())
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        yield c


def test_patch_task_updates_override(client, monkeypatch):
    from agent.njm_graph import njm_graph

    class FakeSnapshot:
        values = {"task_estado_overrides": {}}
        next = []

    captured = {}

    async def fake_aget_state(config):
        return FakeSnapshot()

    async def fake_aupdate_state(config, values, **kwargs):
        captured.update(values)

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)
    monkeypatch.setattr(njm_graph, "aupdate_state", fake_aupdate_state)

    res = client.patch(
        "/api/v1/tasks/tarea-001",
        json={"brand_id": "disrupt", "session_id": "dev-session-1", "estado": "EN_PROGRESO"},
    )
    assert res.status_code == 200
    assert res.json()["task_id"] == "tarea-001"
    assert res.json()["estado"] == "EN_PROGRESO"
    assert captured["task_estado_overrides"] == {"tarea-001": "EN_PROGRESO"}


def test_patch_task_invalid_estado(client):
    res = client.patch(
        "/api/v1/tasks/tarea-001",
        json={"brand_id": "disrupt", "session_id": "dev-session-1", "estado": "INVALID"},
    )
    assert res.status_code == 422


def test_patch_task_merges_existing_overrides(client, monkeypatch):
    from agent.njm_graph import njm_graph

    class FakeSnapshotWithExisting:
        values = {"task_estado_overrides": {"tarea-001": "EN_PROGRESO"}}
        next = []

    captured = {}

    async def fake_aget_state(config):
        return FakeSnapshotWithExisting()

    async def fake_aupdate_state(config, values, **kwargs):
        captured.update(values)

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)
    monkeypatch.setattr(njm_graph, "aupdate_state", fake_aupdate_state)

    res = client.patch(
        "/api/v1/tasks/tarea-002",
        json={"brand_id": "disrupt", "session_id": "dev-session-1", "estado": "DONE"},
    )
    assert res.status_code == 200
    assert captured["task_estado_overrides"] == {
        "tarea-001": "EN_PROGRESO",
        "tarea-002": "DONE",
    }


def test_session_state_returns_merged_tasks(client, monkeypatch):
    from agent.njm_graph import njm_graph

    class FakeSnapshot:
        values = {
            "audit_status": "COMPLETE",
            "tareas_generadas": [
                {"id": "tarea-001", "titulo": "Validar CAC", "descripcion": "desc",
                 "responsable": "PM", "prioridad": "ALTA", "estado": "BACKLOG",
                 "skill_origen": "generar_business_case"},
                {"id": "tarea-002", "titulo": "Presentar a CEO", "descripcion": "desc2",
                 "responsable": "CEO", "prioridad": "MEDIA", "estado": "BACKLOG",
                 "skill_origen": "generar_business_case"},
            ],
            "task_estado_overrides": {"tarea-001": "EN_PROGRESO"},
        }
        next = []

    async def fake_aget_state(config):
        return FakeSnapshot()

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)

    res = client.get("/api/v1/session/state?brand_id=disrupt&session_id=dev-session-1")
    assert res.status_code == 200
    data = res.json()
    assert "tasks" in data
    t1 = next(t for t in data["tasks"] if t["id"] == "tarea-001")
    assert t1["estado"] == "EN_PROGRESO"
    t2 = next(t for t in data["tasks"] if t["id"] == "tarea-002")
    assert t2["estado"] == "BACKLOG"


def test_session_state_tasks_empty_when_no_tareas(client, monkeypatch):
    from agent.njm_graph import njm_graph

    class FakeSnapshot:
        values = {"audit_status": "PENDING"}
        next = []

    async def fake_aget_state(config):
        return FakeSnapshot()

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)

    res = client.get("/api/v1/session/state?brand_id=disrupt&session_id=dev-session-1")
    assert res.status_code == 200
    assert res.json()["tasks"] == []
