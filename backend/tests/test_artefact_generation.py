import typing


def test_artefactos_generados_field_in_state():
    from core.estado import NJM_OS_State

    hints = typing.get_type_hints(NJM_OS_State, include_extras=True)
    assert "artefactos_generados" in hints, (
        f"artefactos_generados not in NJM_OS_State. Keys: {list(hints)}"
    )
    raw = hints["artefactos_generados"]
    origin = getattr(raw, "__origin__", None)
    assert origin is dict or str(raw).startswith("typing.Dict"), (
        f"artefactos_generados must be Dict[str, str], got {raw}"
    )
    args = getattr(raw, "__args__", None)
    assert args == (str, str), f"artefactos_generados must be Dict[str, str], got args={args}"


# ── Task 2 tests: _sse_artefact_stream ────────────────────────────────────


import asyncio
import json
import os
import pytest


# ── helpers ───────────────────────────────────────────────────────────────


def _parse_events(chunks: list) -> list:
    """Parse raw SSE chunks into dicts."""
    events = []
    for chunk in chunks:
        raw = chunk.strip()
        if raw.startswith("data: "):
            raw = raw[6:]
        if raw:
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError:
                pass
    return events


async def _collect(gen) -> list:
    chunks = []
    async for chunk in gen:
        chunks.append(chunk)
    return chunks


# ── fixtures ──────────────────────────────────────────────────────────────


def _init():
    os.environ.setdefault("OPENAI_API_KEY", "test")
    from agent.njm_graph import init_graph
    asyncio.run(init_graph())


# ── tests ─────────────────────────────────────────────────────────────────


def test_sse_artefact_stream_emits_log_events(monkeypatch):
    _init()
    from agent.njm_graph import njm_graph

    # Mock query_brand (sync)
    monkeypatch.setattr(
        "core.rag.query_brand",
        lambda brand_id, query, n_results=5: "CAC objetivo: $120. LTV: $2,400.",
    )

    # Mock ChatOpenAI to return one chunk
    async def fake_astream(messages):
        class FakeChunk:
            content = "# Plan Estratégico\n\nContenido de prueba."
        yield FakeChunk()

    class FakeLLM:
        def astream(self, messages):
            return fake_astream(messages)

    monkeypatch.setattr("langchain_openai.ChatOpenAI", lambda **kwargs: FakeLLM())

    # Mock aget_state / aupdate_state
    class FakeSnapshot:
        values = {"artefactos_generados": {}}
        next = []

    async def fake_aget_state(config):
        return FakeSnapshot()

    async def fake_aupdate_state(config, values):
        pass

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)
    monkeypatch.setattr(njm_graph, "aupdate_state", fake_aupdate_state)

    from api.v1_router import _sse_artefact_stream

    chunks = asyncio.run(_collect(_sse_artefact_stream(
        "disrupt", "dev-session-1", "tarea-001", "Validar CAC"
    )))
    events = _parse_events(chunks)

    log_events = [e for e in events if e.get("type") == "log"]
    assert len(log_events) >= 1
    assert any("Plan" in e.get("text", "") or "prueba" in e.get("text", "") for e in log_events)


def test_sse_artefact_stream_emits_done_event(monkeypatch):
    _init()
    from agent.njm_graph import njm_graph

    monkeypatch.setattr(
        "core.rag.query_brand",
        lambda brand_id, query, n_results=5: "contexto",
    )

    async def fake_astream(messages):
        class FakeChunk:
            content = "texto"
        yield FakeChunk()

    monkeypatch.setattr(
        "langchain_openai.ChatOpenAI",
        lambda **kwargs: type("LLM", (), {"astream": lambda self, m: fake_astream(m)})(),
    )

    class FakeSnapshot:
        values = {}
        next = []

    async def fake_aget_state(config):
        return FakeSnapshot()

    async def fake_aupdate_state(config, values):
        pass

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)
    monkeypatch.setattr(njm_graph, "aupdate_state", fake_aupdate_state)

    from api.v1_router import _sse_artefact_stream

    chunks = asyncio.run(_collect(_sse_artefact_stream(
        "disrupt", "dev-session-1", "tarea-001", "Validar CAC"
    )))
    events = _parse_events(chunks)

    assert events[-1]["type"] == "done"


def test_sse_artefact_stream_persists_content(monkeypatch):
    _init()
    from agent.njm_graph import njm_graph

    monkeypatch.setattr(
        "core.rag.query_brand",
        lambda brand_id, query, n_results=5: "contexto",
    )

    async def fake_astream(messages):
        class FakeChunk:
            content = "# Mi Documento\n\nContenido."
        yield FakeChunk()

    monkeypatch.setattr(
        "langchain_openai.ChatOpenAI",
        lambda **kwargs: type("LLM", (), {"astream": lambda self, m: fake_astream(m)})(),
    )

    class FakeSnapshot:
        values = {
            "artefactos_generados": {},
            "libro_vivo": {"posicionamiento": "Marca premium", "cac_objetivo": 120},
        }
        next = []

    captured = {}

    async def fake_aget_state(config):
        return FakeSnapshot()

    async def fake_aupdate_state(config, values):
        captured.update(values)

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)
    monkeypatch.setattr(njm_graph, "aupdate_state", fake_aupdate_state)

    from api.v1_router import _sse_artefact_stream

    asyncio.run(_collect(_sse_artefact_stream(
        "disrupt", "dev-session-1", "tarea-001", "Validar CAC"
    )))

    assert "artefactos_generados" in captured
    assert "tarea-001" in captured["artefactos_generados"]
    assert "Mi Documento" in captured["artefactos_generados"]["tarea-001"]


def test_sse_artefact_stream_merges_existing_artefacts(monkeypatch):
    _init()
    from agent.njm_graph import njm_graph

    monkeypatch.setattr(
        "core.rag.query_brand",
        lambda brand_id, query, n_results=5: "ctx",
    )

    async def fake_astream(messages):
        class FakeChunk:
            content = "nuevo contenido"
        yield FakeChunk()

    monkeypatch.setattr(
        "langchain_openai.ChatOpenAI",
        lambda **kwargs: type("LLM", (), {"astream": lambda self, m: fake_astream(m)})(),
    )

    class FakeSnapshotWithExisting:
        values = {
            "artefactos_generados": {"tarea-000": "contenido viejo"},
            "libro_vivo": {"posicionamiento": "Marca premium", "cac_objetivo": 120},
        }
        next = []

    captured = {}

    async def fake_aget_state(config):
        return FakeSnapshotWithExisting()

    async def fake_aupdate_state(config, values):
        captured.update(values)

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)
    monkeypatch.setattr(njm_graph, "aupdate_state", fake_aupdate_state)

    from api.v1_router import _sse_artefact_stream

    asyncio.run(_collect(_sse_artefact_stream(
        "disrupt", "dev-session-1", "tarea-001", "Nueva Tarea"
    )))

    assert "tarea-000" in captured["artefactos_generados"]
    assert captured["artefactos_generados"]["tarea-000"] == "contenido viejo"
    assert "tarea-001" in captured["artefactos_generados"]


def test_session_state_returns_artefactos_generados(monkeypatch):
    _init()
    from agent.njm_graph import njm_graph

    class FakeSnapshot:
        values = {
            "audit_status": "COMPLETE",
            "tareas_generadas": [],
            "task_estado_overrides": {},
            "artefactos_generados": {"tarea-001": "# Documento\n\nContenido guardado."},
        }
        next = []

    async def fake_aget_state(config):
        return FakeSnapshot()

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)

    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as client:
        res = client.get("/api/v1/session/state?brand_id=disrupt&session_id=dev-session-1")
    assert res.status_code == 200
    data = res.json()
    assert "artefactos_generados" in data
    assert data["artefactos_generados"]["tarea-001"] == "# Documento\n\nContenido guardado."


def test_session_state_artefactos_empty_when_none(monkeypatch):
    _init()
    from agent.njm_graph import njm_graph

    class FakeSnapshot:
        values = {"audit_status": "PENDING"}
        next = []

    async def fake_aget_state(config):
        return FakeSnapshot()

    monkeypatch.setattr(njm_graph, "aget_state", fake_aget_state)

    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as client:
        res = client.get("/api/v1/session/state?brand_id=disrupt&session_id=dev-session-1")
    assert res.status_code == 200
    data = res.json()
    assert data["artefactos_generados"] == {}
