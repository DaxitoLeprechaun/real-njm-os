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
