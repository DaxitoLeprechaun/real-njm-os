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
