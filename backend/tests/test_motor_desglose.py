import pytest
from pydantic import ValidationError
from core.schemas import Tarea, PrioridadTarea, EstadoTarea


def test_tarea_schema_valid():
    t = Tarea(
        id="tarea-001",
        titulo="Definir estrategia de captación LinkedIn",
        descripcion="Crear matriz de contenido Q3 con presupuesto $3,000 USD.",
        responsable="PM",
        prioridad=PrioridadTarea.ALTA,
        estado=EstadoTarea.BACKLOG,
        skill_origen="generar_plan_demanda",
    )
    assert t.id == "tarea-001"
    assert t.prioridad == PrioridadTarea.ALTA


def test_tarea_titulo_max_length():
    with pytest.raises(ValidationError):
        Tarea(
            id="tarea-002",
            titulo="A" * 61,
            descripcion="desc",
            responsable="CEO",
            prioridad=PrioridadTarea.BAJA,
            estado=EstadoTarea.BACKLOG,
            skill_origen="generar_prd",
        )


def test_njm_os_state_has_tareas_generadas():
    from core.estado import NJM_OS_State
    import typing
    hints = typing.get_type_hints(NJM_OS_State, include_extras=True)
    assert "tareas_generadas" in hints


def test_parsear_tareas_full_block():
    from agentes.agente_pm import _parsear_tareas

    texto = """
RESUMEN_PM:
  skill_utilizada: generar_plan_demanda
  propuesta_principal: Plan de demanda Q3 generado.
  framework_metodologico: AIDA + CAC optimization
  check_adn_aprobado: true
  justificacion_adn: Coherente con Vector 5

TAREAS:
- id: tarea-001
  titulo: Crear matriz de contenido LinkedIn Q3
  descripcion: Diseñar 12 posts mensuales alineados con buyer personas validados.
  responsable: PM
  prioridad: ALTA
  estado: BACKLOG
  skill_origen: generar_plan_demanda
- id: tarea-002
  titulo: Auditar CAC actual vs benchmark
  descripcion: Comparar CAC real con el techo de $120 USD del Libro Vivo.
  responsable: Encargado Real
  prioridad: MEDIA
  estado: BACKLOG
  skill_origen: generar_plan_demanda
"""
    tareas = _parsear_tareas(texto)
    assert len(tareas) == 2
    assert tareas[0]["id"] == "tarea-001"
    assert tareas[0]["prioridad"] == "ALTA"
    assert tareas[1]["responsable"] == "Encargado Real"


def test_parsear_tareas_no_block():
    from agentes.agente_pm import _parsear_tareas

    texto = "RESUMEN_PM:\n  skill_utilizada: generar_prd\n  propuesta_principal: PRD generado."
    tareas = _parsear_tareas(texto)
    assert tareas == []


def test_parsear_tareas_malformed_item_skipped():
    from agentes.agente_pm import _parsear_tareas

    texto = """TAREAS:
- id: tarea-001
  titulo: Tarea válida
  descripcion: desc
  responsable: PM
  prioridad: ALTA
  estado: BACKLOG
  skill_origen: generar_prd
- titulo: Sin ID — debe ignorarse
  descripcion: desc sin id
  responsable: CEO
  prioridad: BAJA
  estado: BACKLOG
  skill_origen: generar_prd
"""
    tareas = _parsear_tareas(texto)
    assert len(tareas) == 1
    assert tareas[0]["id"] == "tarea-001"


def test_nodo_pm_patch_includes_tareas(monkeypatch):
    """nodo_pm debe incluir tareas_generadas en el parche cuando el LLM las emite."""
    import os
    os.environ.setdefault("OPENAI_API_KEY", "test")

    from langchain_core.messages import AIMessage
    from agentes.agente_pm import nodo_pm
    from core.dev_fixtures import _LIBRO_VIVO_DISRUPT

    fake_response_with_tareas = AIMessage(content="""
RESUMEN_PM:
  skill_utilizada: generar_business_case
  propuesta_principal: Business case Q3 generado con ROI estimado 3.2x.
  framework_metodologico: Business Model Canvas
  check_adn_aprobado: true
  justificacion_adn: Alineado con Vector 7 North Star Metric

TAREAS:
- id: tarea-001
  titulo: Validar supuestos de CAC con datos reales
  descripcion: Cruzar benchmark de $120 USD CAC con datos históricos de CRM.
  responsable: Encargado Real
  prioridad: ALTA
  estado: BACKLOG
  skill_origen: generar_business_case
- id: tarea-002
  titulo: Presentar Business Case al CEO
  descripcion: Agendar sesión de 30 min para revisión con stakeholders.
  responsable: PM
  prioridad: MEDIA
  estado: BACKLOG
  skill_origen: generar_business_case
""")

    monkeypatch.setattr(
        "agentes.agente_pm._LLM",
        type("FakeLLM", (), {
            "bind_tools": lambda self, tools: type("Bound", (), {
                "invoke": lambda self, msgs: fake_response_with_tareas
            })()
        })()
    )

    state = {
        "messages": [],
        "libro_vivo": _LIBRO_VIVO_DISRUPT,
        "alertas_internas": [],
        "documentos_generados": [],
        "estado_validacion": "EN_PROGRESO",
        "ruta_espacio_trabajo": "/tmp/test_workspace",
        "tareas_generadas": [],
    }

    parche = nodo_pm(state)

    assert "tareas_generadas" in parche
    assert len(parche["tareas_generadas"]) == 2
    assert parche["tareas_generadas"][0]["id"] == "tarea-001"
