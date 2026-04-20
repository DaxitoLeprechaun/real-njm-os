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
