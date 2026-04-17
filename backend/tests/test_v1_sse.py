"""Tests for Phase 2.3 unified SSE endpoint."""
import json
import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key-for-unit-tests")


# ── helpers ──────────────────────────────────────────────────────────────────


def _parse_sse_lines(body: bytes) -> list[dict]:
    """Extract data payloads from SSE response bytes."""
    events = []
    for line in body.decode().splitlines():
        if line.startswith("data: "):
            raw = line[6:]
            if raw == "[DONE]":
                events.append({"type": "done_sentinel"})
            else:
                try:
                    events.append(json.loads(raw))
                except json.JSONDecodeError:
                    events.append({"type": "raw", "text": raw})
    return events


# ── tests ─────────────────────────────────────────────────────────────────────


def test_agent_stream_accepts_brand_id_and_session_id(monkeypatch):
    """GET /api/v1/agent/stream must accept brand_id and session_id params."""
    from agent import njm_graph as graph_mod

    async def fake_astream_events(state, config, version="v2", **_kwargs):
        yield {"event": "on_chain_end", "name": "output", "data": {}}

    monkeypatch.setattr(graph_mod.njm_graph, "astream_events", fake_astream_events)

    def fake_get_state(config):
        class _Snap:
            values = {"estado_validacion": "LISTO_PARA_FIRMA", "audit_status": "COMPLETE"}
            next = []
            tasks = []
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/agent/stream",
        params={"sequenceId": "ceo-audit", "brand_id": "acme", "session_id": "ses-001"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


def test_agent_stream_emits_done_event(monkeypatch):
    """SSE stream must always end with a done event."""
    from agent import njm_graph as graph_mod

    async def fake_astream_events(state, config, version="v2", **_kwargs):
        yield {"event": "on_chain_end", "name": "output", "data": {}}

    monkeypatch.setattr(graph_mod.njm_graph, "astream_events", fake_astream_events)

    def fake_get_state(config):
        class _Snap:
            values = {"estado_validacion": "LISTO_PARA_FIRMA", "audit_status": "COMPLETE"}
            next = []
            tasks = []
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/agent/stream",
        params={"sequenceId": "ceo-audit", "brand_id": "acme", "session_id": "ses-001"},
    )
    events = _parse_sse_lines(resp.content)
    done_events = [e for e in events if e.get("type") == "done"]
    assert len(done_events) == 1


def test_agent_stream_emits_action_required_on_bloqueo_ceo(monkeypatch):
    """SSE must emit action_required event when final state is BLOQUEO_CEO."""
    from agent import njm_graph as graph_mod

    async def fake_astream_events(state, config, version="v2", **_kwargs):
        yield {"event": "on_chain_end", "name": "output", "data": {}}

    monkeypatch.setattr(graph_mod.njm_graph, "astream_events", fake_astream_events)

    def fake_get_state(config):
        class _Snap:
            values = {
                "estado_validacion": "BLOQUEO_CEO",
                "audit_status": "COMPLETE",
                "risk_details": "Propuesta viola vector 5.",
            }
            next = []
            tasks = []
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/agent/stream",
        params={"sequenceId": "ceo-audit", "brand_id": "acme", "session_id": "ses-001"},
    )
    events = _parse_sse_lines(resp.content)
    ar = [e for e in events if e.get("type") == "action_required"]
    assert len(ar) == 1
    assert ar[0]["trigger"] == "BLOQUEO_CEO"
    assert "risk_message" in ar[0]


def test_agent_stream_emits_action_required_on_gap_detected(monkeypatch):
    """SSE must emit action_required with trigger GAP_DETECTED when graph pauses."""
    from agent import njm_graph as graph_mod

    async def fake_astream_events(state, config, version="v2", **_kwargs):
        yield {"event": "on_chain_end", "name": "human_in_loop", "data": {}}

    monkeypatch.setattr(graph_mod.njm_graph, "astream_events", fake_astream_events)

    def fake_get_state(config):
        class _Snap:
            values = {
                "audit_status": "GAP_DETECTED",
                "interview_questions": ["Q1", "Q2"],
            }
            next = ["ceo_auditor"]
            tasks = []
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/agent/stream",
        params={"sequenceId": "ceo-audit", "brand_id": "acme", "session_id": "ses-001"},
    )
    events = _parse_sse_lines(resp.content)
    ar = [e for e in events if e.get("type") == "action_required"]
    assert len(ar) == 1
    assert ar[0]["trigger"] == "GAP_DETECTED"
    assert "questions" in ar[0]


def test_session_state_endpoint_returns_snapshot(monkeypatch):
    """GET /api/v1/session/state must return current graph state from checkpointer."""
    from agent import njm_graph as graph_mod

    def fake_get_state(config):
        class _Snap:
            values = {
                "audit_status": "COMPLETE",
                "interview_questions": None,
                "payload_tarjeta_sugerencia": None,
                "documentos_generados": ["file1.md"],
            }
            next = []
            tasks = []
        return _Snap()

    monkeypatch.setattr(graph_mod.njm_graph, "get_state", fake_get_state)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/api/v1/session/state",
        params={"brand_id": "acme", "session_id": "ses-001"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["audit_status"] == "COMPLETE"
    assert data["documentos_count"] == 1


def test_agent_resume_endpoint_invokes_graph(monkeypatch):
    """POST /api/v1/agent/resume must call njm_graph.ainvoke with answers."""
    from agent import njm_graph as graph_mod

    invoked_with = []

    async def fake_ainvoke(state, *, config=None):
        invoked_with.append({"state": state, "config": config})
        return {}

    monkeypatch.setattr(graph_mod.njm_graph, "ainvoke", fake_ainvoke)

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.post(
        "/api/v1/agent/resume",
        json={
            "brand_id": "acme",
            "session_id": "ses-001",
            "answers": "Vector 3: audiencia SaaS B2B en LATAM.",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resumed"
    assert len(invoked_with) == 1
    assert invoked_with[0]["state"]["human_interview_answers"] == "Vector 3: audiencia SaaS B2B en LATAM."
    assert invoked_with[0]["config"]["configurable"]["thread_id"] == "acme:ses-001"
