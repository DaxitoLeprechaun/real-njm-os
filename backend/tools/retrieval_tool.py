"""
Retrieval tool for NJM OS agents.

buscar_contexto_marca: semantic search over ChromaDB for a given brand.
Usable by both nodo_ceo and nodo_pm.
"""
from __future__ import annotations

from langchain_core.tools import tool

from core import rag as _rag


@tool
def buscar_contexto_marca(
    brand_id: str,
    consulta: str,
    n_resultados: int = 5,
) -> str:
    """
    Busca fragmentos relevantes del material de onboarding de una marca
    en la base de datos vectorial (ChromaDB).

    Úsala antes de auditar o generar entregables para obtener contexto
    real de los documentos subidos por el Encargado Real.

    Args:
        brand_id: Identificador de la marca. Ej.: "disrupt".
        consulta: Pregunta o tema a buscar. Ej.: "¿Cuál es el CAC objetivo?".
        n_resultados: Número de fragmentos a recuperar (1–10). Default: 5.
    """
    n_resultados = max(1, min(n_resultados, 10))
    chunks = _rag.query_brand(brand_id, consulta, n_results=n_resultados)

    if not chunks:
        return (
            f"No se encontró contexto para la marca '{brand_id}'. "
            "El Encargado Real aún no ha subido documentos de onboarding. "
            "Procede con la entrevista de profundidad para obtener la información."
        )

    lines = [f"CONTEXTO RECUPERADO — Marca: {brand_id} | Consulta: '{consulta}'\n"]
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"--- Fragmento {i} ---")
        lines.append(chunk.strip())
        lines.append("")

    return "\n".join(lines)
