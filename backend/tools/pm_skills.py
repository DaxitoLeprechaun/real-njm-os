"""
NJM OS — Catálogo de Skills del Agente PM (14 herramientas)

Fuente de verdad: ARCHITECTURE.md §§ PM-Skills (Fases 1, 2 y 3)

Cada skill genera un archivo Markdown estructurado que simula el entregable
real (PRD, Business Case, Roadmap, etc.) en el entorno Claude Cowork local.

Convención de parámetros complejos:
  - Objetos anidados (analisis_financiero, epicas_estrategicas, etc.) se aceptan
    como JSON strings. El LLM los construye como strings; se parsean internamente.
  - Listas de strings simples se pasan con List[str] directamente.

Registro de herramientas al final del módulo: PM_SKILLS, _SKILL_MAP.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

# ══════════════════════════════════════════════════════════════════
# HELPER INTERNO
# ══════════════════════════════════════════════════════════════════

_TIMESTAMP_FMT = "%Y-%m-%d %H:%M UTC"


def _escribir_md(ruta_destino: str, contenido: str) -> str:
    """
    Escribe `contenido` en `ruta_destino` (crea directorios intermedios).
    Devuelve la ruta absoluta del archivo creado o un mensaje de error.
    """
    try:
        ruta = Path(ruta_destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(contenido, encoding="utf-8")
        return str(ruta.resolve())
    except PermissionError:
        return f"ERROR_PERMISOS:{ruta_destino}"
    except OSError as exc:
        return f"ERROR_OS:{exc}"


def _ts() -> str:
    return datetime.now(timezone.utc).strftime(_TIMESTAMP_FMT)


def _lista_md(items: List[str], prefijo: str = "-") -> str:
    return "\n".join(f"{prefijo} {item}" for item in items) if items else "_(sin datos)_"


def _parse_json_param(valor: Any, nombre_param: str) -> tuple[Any, Optional[str]]:
    """Parsea un JSON string; devuelve (datos, None) o (None, mensaje_error)."""
    if isinstance(valor, (dict, list)):
        return valor, None
    try:
        return json.loads(valor), None
    except (json.JSONDecodeError, TypeError) as exc:
        return None, (
            f"ERROR: El parámetro '{nombre_param}' no es un JSON válido. "
            f"Detalle: {exc}"
        )


def _confirmar(nombre_skill: str, ruta_absoluta: str) -> str:
    return (
        f"SKILL EJECUTADA: {nombre_skill}\n"
        f"  Archivo generado: {ruta_absoluta}\n"
        f"  Timestamp: {_ts()}"
    )


# ══════════════════════════════════════════════════════════════════
# FASE 1 — IDEACIÓN Y JUSTIFICACIÓN (Skills 1–5)
# ══════════════════════════════════════════════════════════════════


@tool
def generar_vision_producto(
    ruta_destino: str,
    target_audience: str,
    core_need: str,
    product_name_category: str,
    key_benefit: str,
    primary_differentiation: str,
) -> str:
    """
    Genera el documento de Visión de Producto (Elevator Pitch extendido)
    alineando el mercado objetivo con las necesidades no cubiertas.

    Anclaje en Libro Vivo: Vector 1 (UVP) y Vector 3 (JTBD).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo en Claude Cowork.
        target_audience: Descripción demográfica y psicográfica del usuario final.
        core_need: El 'Job-to-be-Done' o problema principal a resolver.
        product_name_category: Nombre de la iniciativa o categoría de mercado.
        key_benefit: La razón principal de compra (UVP).
        primary_differentiation: Qué lo separa de las alternativas (Vector 4).
    """
    contenido = f"""# Visión de Producto — {product_name_category}
> Generado por Agente PM | NJM OS | {_ts()}

---

## Elevator Pitch

**Para** {target_audience}
**que** {core_need},
**{product_name_category}** es una solución que
**{key_benefit}**.
**A diferencia de** las alternativas del mercado,
**nuestra ventaja única es** {primary_differentiation}.

---

## Desglose Analítico

### Audiencia Objetivo (Vector 3 — JTBD)
{target_audience}

### Necesidad Core / Job-to-be-Done
{core_need}

### Iniciativa / Categoría de Mercado
{product_name_category}

### Beneficio Principal (UVP — Vector 1)
{key_benefit}

### Diferenciación Primaria (Vector 4 — Competencia)
{primary_differentiation}

---

## Checklist de Coherencia con el ADN

- [ ] El target_audience está validado en el Vector 3 del Libro Vivo
- [ ] El core_need es consistente con el JTBD documentado
- [ ] El key_benefit no contradice las lineas_rojas_marca del Vector 1
- [ ] La diferenciación está verificada contra el Vector 4 (competidores directos)

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_vision_producto", ruta)


@tool
def generar_analisis_ansoff(
    ruta_destino: str,
    cuadrante_recomendado: str,
    justificacion_estrategica: str,
    tacticas_ejecucion: List[str],
) -> str:
    """
    Evalúa las 4 estrategias de crecimiento de la Matriz de Ansoff y documenta
    la selección óptima con justificación financiera.

    Anclaje en Libro Vivo: Vector 2 (Unit Economics) y Vector 7 (Objetivos Q).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        cuadrante_recomendado: Cuadrante seleccionado. Valores válidos:
            "Market Penetration" | "Market Development" |
            "Product Development" | "Diversification"
        justificacion_estrategica: Justificación basada en Unit Economics
            y riesgo financiero actual (Vector 2).
        tacticas_ejecucion: Lista con 3 acciones tácticas concretas
            para ejecutar en el cuadrante elegido.
    """
    cuadrantes_validos = {
        "Market Penetration", "Market Development",
        "Product Development", "Diversification",
    }
    if cuadrante_recomendado not in cuadrantes_validos:
        return (
            f"ERROR: cuadrante_recomendado '{cuadrante_recomendado}' no es válido. "
            f"Opciones: {sorted(cuadrantes_validos)}"
        )

    mapa_riesgo = {
        "Market Penetration": "BAJO — mercado y producto conocidos",
        "Market Development": "MEDIO — mercado nuevo, producto conocido",
        "Product Development": "MEDIO — mercado conocido, producto nuevo",
        "Diversification": "ALTO — mercado y producto nuevos",
    }

    contenido = f"""# Análisis de Matriz de Ansoff
> Generado por Agente PM | NJM OS | {_ts()}

---

## Cuadrante Recomendado

### ✅ {cuadrante_recomendado}
**Nivel de Riesgo:** {mapa_riesgo[cuadrante_recomendado]}

---

## Mapa Completo de Ansoff

|                        | **Mercado Existente**      | **Mercado Nuevo**          |
|------------------------|---------------------------|---------------------------|
| **Producto Existente** | Market Penetration {"← SELECCIONADO" if cuadrante_recomendado == "Market Penetration" else ""}         | Market Development {"← SELECCIONADO" if cuadrante_recomendado == "Market Development" else ""}         |
| **Producto Nuevo**     | Product Development {"← SELECCIONADO" if cuadrante_recomendado == "Product Development" else ""}       | Diversification {"← SELECCIONADO" if cuadrante_recomendado == "Diversification" else ""}            |

---

## Justificación Estratégica (Anclada en Vector 2)

{justificacion_estrategica}

---

## Plan Táctico de Ejecución

{_lista_md(tacticas_ejecucion, prefijo="1.")}

---

## Checklist de Coherencia con el ADN

- [ ] El cuadrante seleccionado es viable dado el CAC máximo tolerable (Vector 2)
- [ ] Las tácticas no superan el presupuesto de pauta mensual (Vector 5)
- [ ] El objetivo de crecimiento está alineado con la North Star Metric (Vector 7)
- [ ] Ninguna táctica usa canales prohibidos por las lineas_rojas_marca (Vector 1)

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_analisis_ansoff", ruta)


@tool
def generar_analisis_porter(
    ruta_destino: str,
    intensidad_rivalidad: str,
    poder_compradores: str,
    amenaza_sustitutos: str,
    conclusion_estrategica: str,
) -> str:
    """
    Genera un reporte de las 5 Fuerzas de Porter para auditar la resistencia
    del mercado competitivo antes de entrar a un nuevo canal o lanzar un servicio.

    Anclaje en Libro Vivo: Vector 4 (Ecosistema Competitivo).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        intensidad_rivalidad: Nivel de rivalidad entre competidores directos.
            Valores: "Alta" | "Media" | "Baja"
        poder_compradores: Capacidad de negociación de los clientes.
            Valores: "Alto" | "Medio" | "Bajo"
        amenaza_sustitutos: Descripción de productos que resuelven el mismo
            problema con un método distinto (riesgo de sustitución).
        conclusion_estrategica: Acción recomendada para mitigar las fuerzas
            más altas detectadas en el análisis.
    """
    niveles_rivalidad = {"Alta", "Media", "Baja"}
    niveles_compradores = {"Alto", "Medio", "Bajo"}

    if intensidad_rivalidad not in niveles_rivalidad:
        return f"ERROR: intensidad_rivalidad debe ser {sorted(niveles_rivalidad)}."
    if poder_compradores not in niveles_compradores:
        return f"ERROR: poder_compradores debe ser {sorted(niveles_compradores)}."

    def _semaforo(nivel: str) -> str:
        return {"Alta": "🔴", "Media": "🟡", "Baja": "🟢",
                "Alto": "🔴", "Medio": "🟡", "Bajo": "🟢"}.get(nivel, "⚪")

    contenido = f"""# Análisis de las 5 Fuerzas de Porter
> Generado por Agente PM | NJM OS | {_ts()}

---

## Resumen Ejecutivo del Ecosistema

| Fuerza                        | Nivel    | Señal |
|-------------------------------|----------|-------|
| Rivalidad entre competidores  | {intensidad_rivalidad}    | {_semaforo(intensidad_rivalidad)} |
| Poder de negociación (compradores) | {poder_compradores} | {_semaforo(poder_compradores)} |
| Amenaza de sustitutos         | (ver abajo) | — |
| Poder de proveedores          | _(requiere datos Vector 5)_ | — |
| Amenaza de nuevos entrantes   | _(requiere datos Vector 4)_ | — |

---

## Análisis Detallado

### 1. Rivalidad entre Competidores Existentes — {intensidad_rivalidad} {_semaforo(intensidad_rivalidad)}
Nivel derivado del Vector 4 (Ecosistema Competitivo) del Libro Vivo.

### 2. Poder de Negociación de los Compradores — {poder_compradores} {_semaforo(poder_compradores)}
Evaluado contra el criterio_desempate y la friccion_transaccional del Vector 3.

### 3. Amenaza de Productos/Servicios Sustitutos
{amenaza_sustitutos}

### 4. Poder de Negociación de Proveedores
_(Completar con datos del Vector 5 — Infraestructura de Canales)_

### 5. Amenaza de Nuevos Entrantes
_(Completar con barreras de entrada del Vector 4 — moats_economicos)_

---

## Conclusión Estratégica y Acción Recomendada

{conclusion_estrategica}

---

## Checklist de Coherencia con el ADN

- [ ] La rivalidad documentada coincide con los competidores del Vector 4
- [ ] Los sustitutos identificados están en el radar del Vector 4
- [ ] La conclusión estratégica no contradice el sesgo_metodologico del Vector 9

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_analisis_porter", ruta)


@tool
def generar_auditoria_foda(
    ruta_destino: str,
    fortalezas_core: List[str],
    debilidades_operativas: List[str],
    oportunidades_mercado: List[str],
    amenazas_externas: List[str],
    implicacion_estrategica_pm: str,
) -> str:
    """
    Redacta la Evaluación Interna y Externa (FODA) enfocada en la
    viabilidad operativa de la marca para el trimestre actual.

    Anclaje en Libro Vivo: Vector 5 (Infraestructura / Cuellos de botella)
    y Vector 6 (Histórico y Aprendizajes).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        fortalezas_core: Capacidades internas diferenciadoras de la marca.
        debilidades_operativas: Limitaciones de presupuesto o capacidad (Vector 5).
        oportunidades_mercado: Tendencias o ventanas externas aprovechables.
        amenazas_externas: Riesgos del entorno competitivo o macroeconómico.
        implicacion_estrategica_pm: Cómo las debilidades limitan las
            oportunidades tácticas del trimestre actual.
    """
    contenido = f"""# Auditoría FODA — Evaluación Interna y Externa
> Generado por Agente PM | NJM OS | {_ts()}

---

## Matriz FODA

|                    | **Positivo (Ayuda)**              | **Negativo (Obstaculiza)**           |
|--------------------|-----------------------------------|--------------------------------------|
| **Interno**        | **Fortalezas**                    | **Debilidades**                      |
|                    | {"; ".join(fortalezas_core[:2])} | {"; ".join(debilidades_operativas[:2])} |
| **Externo**        | **Oportunidades**                 | **Amenazas**                         |
|                    | {"; ".join(oportunidades_mercado[:2])} | {"; ".join(amenazas_externas[:2])} |

---

## Fortalezas Core (Ventajas Internas)

{_lista_md(fortalezas_core)}

## Debilidades Operativas (Vector 5 — Cuellos de Botella)

{_lista_md(debilidades_operativas)}

## Oportunidades de Mercado

{_lista_md(oportunidades_mercado)}

## Amenazas Externas

{_lista_md(amenazas_externas)}

---

## Implicación Estratégica para el Agente PM

> {implicacion_estrategica_pm}

Esta implicación define los límites operativos del PM para el trimestre actual.
Ninguna táctica propuesta puede ignorar las debilidades listadas arriba.

---

## Checklist de Coherencia con el ADN

- [ ] Las debilidades están validadas contra el punto_quiebre_operativo (Vector 5)
- [ ] Las fortalezas se alinean con los moats_economicos (Vector 2)
- [ ] Las oportunidades no contradicen las zonas_rojas_compliance (Vector 8)
- [ ] La implicación estratégica respeta el sesgo_metodologico del PM (Vector 9)

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_auditoria_foda", ruta)


@tool
def generar_concepto_producto(
    ruta_destino: str,
    customer_segment: str,
    problem_statement: str,
    solution_description: str,
    value_proposition: str,
    metricas_exito: str,
) -> str:
    """
    Estructura el Brief final de Concepto de Producto o Campaña listo para
    que el equipo de diseño, marketing o ventas ejecute sin ambigüedades.

    Anclaje en Libro Vivo: Síntesis del Vector 1 (UVP), Vector 3 (JTBD)
    y Vector 8 (Gobernanza — lo que no se debe hacer).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        customer_segment: Segmento de cliente objetivo.
        problem_statement: El problema formulado en una oración accionable.
        solution_description: Cómo funciona la campaña/producto paso a paso.
        value_proposition: La propuesta de valor diferencial.
        metricas_exito: North Star Metric afectada por esta iniciativa.
    """
    contenido = f"""# Brief de Concepto de Producto / Campaña
> Generado por Agente PM | NJM OS | {_ts()}

---

## Ficha del Concepto

| Campo                  | Contenido |
|------------------------|-----------|
| **Segmento Objetivo**  | {customer_segment} |
| **North Star Metric**  | {metricas_exito} |

---

## Problem Statement

> {problem_statement}

## Descripción de la Solución

{solution_description}

## Propuesta de Valor

> {value_proposition}

---

## Métrica de Éxito (North Star — Vector 7)

**KPI Principal:** {metricas_exito}

Define el único número que, si mejora como resultado de esta iniciativa,
confirma que el Encargado Real tomó la decisión correcta.

---

## Restricciones de Gobernanza (Vector 8)

- [ ] La solución no vulnera ninguna zona_roja_compliance
- [ ] El tono y lenguaje no infringe lineas_rojas_marca (Vector 1)
- [ ] El customer_segment coincide con los perfiles del Vector 3

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_concepto_producto", ruta)


# ══════════════════════════════════════════════════════════════════
# FASE 2 — PLANEACIÓN Y EJECUCIÓN (Skills 6–9)
# ══════════════════════════════════════════════════════════════════


@tool
def generar_business_case(
    ruta_destino: str,
    resumen_ejecutivo: str,
    alineacion_estrategica: str,
    analisis_financiero: str,
    riesgos_y_mitigacion: List[str],
) -> str:
    """
    Genera el formato de Caso de Negocio, evaluando la viabilidad financiera,
    el ROI proyectado y la alineación estratégica antes de aprobar el desarrollo.

    Anclaje en Libro Vivo: Vector 2 (Unit Economics & Cash Conversion Cycle),
    Vector 7 (Objetivos Macro) y Vector 8 (Mitigación de Riesgos).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        resumen_ejecutivo: Síntesis del problema y la solución.
        alineacion_estrategica: Cómo impacta directamente en la North Star Metric
            (Vector 7).
        analisis_financiero: JSON string con campos:
            - costo_estimado_implementacion (number)
            - beneficio_proyectado_mrr (number)
            - impacto_flujo_caja (string)
        riesgos_y_mitigacion: Lista de riesgos operativos y cómo se mitigan
            (referenciados en Vector 8).
    """
    financiero, err = _parse_json_param(analisis_financiero, "analisis_financiero")
    if err:
        return err

    costo = financiero.get("costo_estimado_implementacion", "N/D")
    mrr = financiero.get("beneficio_proyectado_mrr", "N/D")
    flujo = financiero.get("impacto_flujo_caja", "N/D")

    roi_str = "N/D"
    if isinstance(costo, (int, float)) and isinstance(mrr, (int, float)) and costo > 0:
        roi_meses = round(costo / mrr, 1) if mrr > 0 else float("inf")
        roi_str = f"{roi_meses} meses de recuperación"

    contenido = f"""# Business Case
> Generado por Agente PM | NJM OS | {_ts()}

---

## Resumen Ejecutivo

{resumen_ejecutivo}

---

## Alineación Estratégica (Vector 7 — North Star Metric)

{alineacion_estrategica}

---

## Análisis Financiero (Vector 2 — Unit Economics)

| Métrica                         | Valor |
|---------------------------------|-------|
| Costo estimado de implementación | ${costo:,.2f} USD |
| Beneficio proyectado (MRR)       | ${mrr:,.2f} USD/mes |
| Payback period estimado          | {roi_str} |
| Impacto en flujo de caja         | {flujo} |

> **Advertencia CEO:** Antes de aprobar, verifica que el costo_estimado no supere
> el presupuesto disponible del Vector 5 y que el Payback no comprometa el
> `cash_conversion_cycle_dias` del Vector 2.

---

## Riesgos y Plan de Mitigación (Vector 8)

{_lista_md(riesgos_y_mitigacion)}

---

## Decisión Requerida

- [ ] **APROBADO** — El caso de negocio es viable. El PM puede proceder con el PRD.
- [ ] **RECHAZADO** — Los números no cuadran con el Libro Vivo.
- [ ] **AJUSTE REQUERIDO** — Modificar presupuesto o alcance antes de continuar.

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_business_case", ruta)


@tool
def generar_prd(
    ruta_destino: str,
    objetivo_iniciativa: str,
    casos_uso_principales: List[str],
    requisitos_funcionales: List[str],
    restricciones_y_fuera_de_alcance: List[str],
    metricas_adopcion: Optional[List[str]] = None,
) -> str:
    """
    Redacta el Documento de Requisitos de Producto (PRD) como única fuente de
    verdad sobre qué se va a construir o lanzar.

    Anclaje en Libro Vivo: Vector 3 (JTBD — casos de uso) y Vector 5
    (Infraestructura — restricciones operativas).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        objetivo_iniciativa: Qué problema de negocio resuelve esta iniciativa.
        casos_uso_principales: Lista de casos de uso mapeados desde el JTBD
            del Vector 3.
        requisitos_funcionales: Características exactas que debe tener el
            producto o campaña.
        restricciones_y_fuera_de_alcance: Lo que NO se va a hacer, basado en
            el Vector 5 y cuellos de botella operativos.
        metricas_adopcion: KPIs para medir si el lanzamiento tuvo éxito
            (opcional, por defecto vacío).
    """
    metricas = metricas_adopcion or []
    contenido = f"""# Product Requirements Document (PRD)
> Generado por Agente PM | NJM OS | {_ts()}

---

## Objetivo de la Iniciativa

{objetivo_iniciativa}

---

## Casos de Uso Principales (Vector 3 — JTBD)

{_lista_md(casos_uso_principales, prefijo='**UC-' + str(0) + '.**') if False else chr(10).join(f'**UC-{i+1}.** {caso}' for i, caso in enumerate(casos_uso_principales))}

---

## Requisitos Funcionales

{chr(10).join(f'- **RF-{i+1}:** {req}' for i, req in enumerate(requisitos_funcionales))}

---

## Restricciones y Fuera de Alcance (Vector 5 — Cuellos de Botella)

> ⚠️ El Agente PM NO tiene autorización para implementar los siguientes items.

{_lista_md(restricciones_y_fuera_de_alcance, prefijo='❌')}

---

## Métricas de Adopción

{_lista_md(metricas) if metricas else '_No definidas en esta versión del PRD. El PM debe completarlas antes del Launch Readiness._'}

---

## Checklist de Coherencia con el ADN

- [ ] Todos los casos de uso están respaldados por el JTBD del Vector 3
- [ ] Los requisitos funcionales no violan zonas_rojas_compliance (Vector 8)
- [ ] Las restricciones reflejan el punto_quiebre_operativo (Vector 5)

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_prd", ruta)


@tool
def generar_roadmap(
    ruta_destino: str,
    formato_tiempo: str,
    epicas_estrategicas: str,
    dependencias_criticas: Optional[List[str]] = None,
) -> str:
    """
    Estructura el Roadmap estratégico dividiendo la ejecución en horizontes
    temporales para mantener el foco del equipo.

    Anclaje en Libro Vivo: Vector 5 (capacidad operativa instalada) y
    Vector 7 (objetivos a corto/largo plazo).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        formato_tiempo: Marco temporal del roadmap.
            Valores: "Now-Next-Later" | "Quarterly (Q1-Q4)"
        epicas_estrategicas: JSON string con lista de objetos:
            [{"nombre_epica": str, "horizonte": str, "vinculo_estrategico": str}]
        dependencias_criticas: Lista de dependencias o blockers entre épicas
            (opcional).
    """
    formatos_validos = {"Now-Next-Later", "Quarterly (Q1-Q4)"}
    if formato_tiempo not in formatos_validos:
        return f"ERROR: formato_tiempo debe ser {sorted(formatos_validos)}."

    epicas, err = _parse_json_param(epicas_estrategicas, "epicas_estrategicas")
    if err:
        return err
    if not isinstance(epicas, list):
        return "ERROR: epicas_estrategicas debe ser un array JSON de objetos."

    dependencias = dependencias_criticas or []

    # Agrupar épicas por horizonte
    por_horizonte: Dict[str, List[Dict]] = {}
    for epica in epicas:
        h = epica.get("horizonte", "Sin horizonte")
        por_horizonte.setdefault(h, []).append(epica)

    bloques_horizontes = []
    for horizonte, items in por_horizonte.items():
        bloque = [f"### {horizonte}"]
        for item in items:
            bloque.append(f"- **{item.get('nombre_epica', 'Sin nombre')}**")
            bloque.append(f"  - Vínculo estratégico: {item.get('vinculo_estrategico', 'N/D')}")
        bloques_horizontes.append("\n".join(bloque))

    contenido = f"""# Product Roadmap — {formato_tiempo}
> Generado por Agente PM | NJM OS | {_ts()}

---

## Marco Temporal: {formato_tiempo}

---

## Épicas Estratégicas

{chr(10).join(bloques_horizontes)}

---

## Tabla de Resumen

| Épica | Horizonte | Vínculo Estratégico |
|-------|-----------|---------------------|
{chr(10).join(f'| {e.get("nombre_epica","?")} | {e.get("horizonte","?")} | {e.get("vinculo_estrategico","?")} |' for e in epicas)}

---

## Dependencias Críticas

{_lista_md(dependencias) if dependencias else '_No se identificaron dependencias críticas en esta versión._'}

---

## Checklist de Coherencia con el ADN

- [ ] Los horizontes no saturan el punto_quiebre_operativo (Vector 5)
- [ ] Cada épica está vinculada a un objetivo del Vector 7
- [ ] Las dependencias no generan un cuello de botella que bloquee el Q actual

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_roadmap", ruta)


@tool
def generar_backlog_historias(
    ruta_destino: str,
    historias_usuario: str,
) -> str:
    """
    Desglosa las épicas del Roadmap en Historias de Usuario accionables
    con criterios de aceptación y priorización matemática (RICE Score).

    Anclaje en Libro Vivo: Vector 3 (fricción transaccional — dolores reales).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        historias_usuario: JSON string con lista de objetos:
            [{
              "rol_usuario": str,
              "accion_deseada": str,
              "beneficio_jtbd": str,
              "criterios_aceptacion": [str],
              "priorizacion_rice_score": number
            }]
    """
    historias, err = _parse_json_param(historias_usuario, "historias_usuario")
    if err:
        return err
    if not isinstance(historias, list):
        return "ERROR: historias_usuario debe ser un array JSON de objetos."

    # Ordenar por RICE score descendente
    historias_ordenadas = sorted(
        historias,
        key=lambda h: h.get("priorizacion_rice_score", 0),
        reverse=True,
    )

    bloques = []
    for i, historia in enumerate(historias_ordenadas, 1):
        rice = historia.get("priorizacion_rice_score", "N/D")
        criterios = historia.get("criterios_aceptacion", [])
        bloque = [
            f"### US-{i:02d} | RICE Score: {rice}",
            "",
            f"**Como** {historia.get('rol_usuario', 'N/D')},",
            f"**quiero** {historia.get('accion_deseada', 'N/D')},",
            f"**para** {historia.get('beneficio_jtbd', 'N/D')}",
            "",
            "**Criterios de Aceptación:**",
            _lista_md(criterios, prefijo="  - [ ]"),
            "",
        ]
        bloques.append("\n".join(bloque))

    tabla_resumen = "\n".join(
        f"| US-{i+1:02d} | {h.get('rol_usuario','')[:30]} | {h.get('priorizacion_rice_score','N/D')} |"
        for i, h in enumerate(historias_ordenadas)
    )

    contenido = f"""# Product Backlog — User Stories
> Generado por Agente PM | NJM OS | {_ts()}
> Ordenado por RICE Score (mayor prioridad primero)

---

## Resumen del Backlog

| Historia | Rol de Usuario | RICE Score |
|----------|----------------|------------|
{tabla_resumen}

---

## Historias de Usuario Detalladas

{chr(10).join(bloques)}

---

## Nota de Priorización (RICE Framework)

El RICE Score considera: **R**each × **I**mpact × **C**onfidence ÷ **E**ffort.
Scores calculados por el Agente PM en función del Unit Economics (Vector 2)
y la fricción transaccional del Vector 3.

---

## Checklist de Coherencia con el ADN

- [ ] Cada US está mapeada a un caso de uso del PRD (Vector 3 JTBD)
- [ ] Los criterios de aceptación son verificables y no subjetivos
- [ ] El backlog completo es ejecutable dentro del punto_quiebre_operativo (Vector 5)

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_backlog_historias", ruta)


# ══════════════════════════════════════════════════════════════════
# FASE 3 — VALIDACIÓN, LANZAMIENTO Y RETIRO (Skills 10–14)
# ══════════════════════════════════════════════════════════════════


@tool
def generar_plan_beta(
    ruta_destino: str,
    objetivos_beta: str,
    perfil_early_adopters: str,
    mecanismo_feedback: str,
    metricas_exito_para_ga: List[str],
) -> str:
    """
    Diseña la estrategia de pruebas Beta, definiendo el alcance, los usuarios
    objetivo y los criterios de éxito antes del lanzamiento oficial (General Availability).

    Anclaje en Libro Vivo: Vector 3 (Early Adopters del segmento) y
    Vector 8 (Mitigación de riesgos de PR).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        objetivos_beta: Qué hipótesis crítica se busca validar en el piloto.
        perfil_early_adopters: Segmento específico del Vector 3 dispuesto a
            tolerar fricción y dar feedback estructurado.
        mecanismo_feedback: Cómo se recolectarán los datos del piloto
            (entrevistas, telemetría, encuestas NPS, etc.).
        metricas_exito_para_ga: Condiciones innegociables para pasar a
            General Availability (ej. NPS > 40, Error rate < 2%).
    """
    contenido = f"""# Plan de Beta Testing
> Generado por Agente PM | NJM OS | {_ts()}

---

## Objetivos del Piloto

{objetivos_beta}

---

## Perfil de Early Adopters (Vector 3)

{perfil_early_adopters}

> Estos usuarios fueron seleccionados porque representan el segmento del Vector 3
> con mayor tolerancia a la fricción y mayor capacidad de retroalimentación estructurada.

---

## Mecanismo de Recolección de Feedback

{mecanismo_feedback}

---

## Criterios de Éxito para General Availability (Go/No-Go Gate)

Los siguientes criterios deben estar cumplidos al 100% antes de escalar:

{_lista_md(metricas_exito_para_ga, prefijo='- [ ]')}

---

## Protocolo de Riesgo (Vector 8)

Si durante el Beta se detecta:
- Daño reputacional potencial → Activar `levantar_tarjeta_roja` (nivel: reputacional)
- Violación de compliance → Detener la Beta inmediatamente y escalar al CEO

---

## Checklist de Coherencia con el ADN

- [ ] Los Early Adopters son un subconjunto real del Vector 3 (no usuarios genéricos)
- [ ] Los criterios de GA están alineados con la North Star Metric del Vector 7
- [ ] El mecanismo de feedback no almacena datos que violen el Vector 8 (privacidad)

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_plan_beta", ruta)


@tool
def generar_requisitos_usabilidad(
    ruta_destino: str,
    escenarios_prueba: List[str],
    perfil_tester: str,
    kpis_usabilidad: List[str],
) -> str:
    """
    Establece los parámetros y tareas para pruebas de usabilidad empíricas
    de un producto o funnel de conversión, eliminando suposiciones creativas.

    Anclaje en Libro Vivo: Vector 3 (Jobs-to-be-Done — base de los escenarios).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        escenarios_prueba: Tareas específicas que el usuario debe intentar
            completar, derivadas del JTBD del Vector 3.
        perfil_tester: Descripción del usuario reclutado para las pruebas
            (debe coincidir con el segmento del Vector 3).
        kpis_usabilidad: Métricas cuantitativas a medir.
            Ej.: ["Time-on-task < 3 min", "Completion rate > 80%", "Error rate < 5%"]
    """
    contenido = f"""# Requisitos de Pruebas de Usabilidad
> Generado por Agente PM | NJM OS | {_ts()}

---

## Perfil del Tester

{perfil_tester}

> Debe ser un representante real del segmento documentado en el Vector 3 del Libro Vivo.
> No usar testers internos que conocen el producto.

---

## Escenarios de Prueba (Derivados del Vector 3 — JTBD)

{chr(10).join(f'**Escenario {i+1}:** {escenario}' for i, escenario in enumerate(escenarios_prueba))}

---

## KPIs de Usabilidad (Benchmark Cuantitativo)

| KPI | Umbral de Éxito | Resultado (llenar en prueba) |
|-----|-----------------|------------------------------|
{chr(10).join(f'| {kpi} | (definir) | — |' for kpi in kpis_usabilidad)}

---

## Instrucciones para el Moderador

1. No guíes al tester — solo observa y registra.
2. Pide en voz alta ("Think Aloud Protocol") durante la ejecución.
3. Registra tiempos, errores y puntos de confusión por escenario.
4. Al finalizar, aplica encuesta de Satisfacción (CSAT o SUS Score).

---

## Checklist de Coherencia con el ADN

- [ ] Los escenarios cubren el flujo crítico del funnel (Vector 5)
- [ ] Los KPIs están conectados a la North Star Metric (Vector 7)
- [ ] El perfil del tester coincide con el trigger_event del Vector 3

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_requisitos_usabilidad", ruta)


@tool
def generar_plan_demanda(
    ruta_destino: str,
    kpis_demanda: List[str],
    tacticas_inbound_outbound: List[str],
    distribucion_presupuesto: str,
    alineacion_ventas: str,
) -> str:
    """
    Estructura la campaña de adquisición alineando canales, presupuesto y
    tácticas para generar leads cualificados (MQLs/SQLs).

    Anclaje en Libro Vivo: Vector 5 (Canales y Presupuesto),
    Vector 2 (CAC máximo tolerable) y Vector 4 (Evita tácticas saturadas).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        kpis_demanda: Objetivos de volumen y costo.
            Ej.: ["500 MQLs/mes", "CPA < $50 USD", "Tasa de conversión MQL→SQL > 25%"]
        tacticas_inbound_outbound: Estrategias de contenido, pauta o
            prospección directa a ejecutar.
        distribucion_presupuesto: JSON string con la asignación de capital
            por canal. Ej.: {"Google Ads": 2000, "LinkedIn": 1500, "Contenido": 500}
            Debe validarse contra el presupuesto_pauta_mensual_usd del Vector 5.
        alineacion_ventas: SLA entre marketing y ventas — cómo y cuándo se
            entregarán los leads cualificados.
    """
    presupuesto, err = _parse_json_param(distribucion_presupuesto, "distribucion_presupuesto")
    if err:
        return err

    total_presupuesto = sum(v for v in presupuesto.values() if isinstance(v, (int, float)))

    tabla_presupuesto = "\n".join(
        f"| {canal} | ${monto:,.2f} USD |"
        for canal, monto in presupuesto.items()
    )

    contenido = f"""# Plan de Demand Generation
> Generado por Agente PM | NJM OS | {_ts()}

---

## KPIs de Demanda

{_lista_md(kpis_demanda)}

---

## Tácticas Inbound y Outbound

{_lista_md(tacticas_inbound_outbound)}

---

## Distribución del Presupuesto (Vector 5 — presupuesto_pauta_mensual_usd)

| Canal | Inversión Mensual |
|-------|------------------|
{tabla_presupuesto}
| **TOTAL** | **${total_presupuesto:,.2f} USD** |

> ⚠️ **Validación CEO requerida:** El total debe ser ≤ presupuesto_pauta_mensual_usd del Vector 5.
> Si supera el límite, el Agente CEO levantará tarjeta roja antes del lanzamiento.

---

## SLA de Alineación con Ventas

{alineacion_ventas}

---

## Checklist de Coherencia con el ADN

- [ ] El presupuesto total ≤ presupuesto_pauta_mensual_usd (Vector 5)
- [ ] El CPA objetivo es ≤ cac_maximo_tolerable_usd (Vector 2)
- [ ] Los canales seleccionados no son tácticas saturadas del Vector 4
- [ ] Los canales seleccionados no incluyen tácticas prohibidas (Vector 1 / 8)

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_plan_demanda", ruta)


@tool
def evaluar_preparacion_lanzamiento(
    ruta_destino: str,
    estado_areas_criticas: str,
    riesgos_bloqueantes: List[str],
    recomendacion_go_no_go: str,
) -> str:
    """
    Genera el reporte de Go/No-Go, auditando si todas las áreas operativas
    están listas para soportar el lanzamiento sin colapso.

    Anclaje en Libro Vivo: Vector 5 (punto_quiebre_operativo) y
    Vector 8 (Compliance y Riesgos PR).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        estado_areas_criticas: JSON string con booleanos por área:
            {
              "marketing_y_pr": bool,
              "ventas_capacitacion": bool,
              "soporte_y_operaciones": bool,
              "tecnologia_infraestructura": bool
            }
        riesgos_bloqueantes: Lista de dependencias o fallos que impiden
            el lanzamiento (vacía si no hay blockers).
        recomendacion_go_no_go: Veredicto del PM.
            Valores: "GO" | "NO-GO" | "CONDITIONAL-GO"
    """
    veredictos_validos = {"GO", "NO-GO", "CONDITIONAL-GO"}
    if recomendacion_go_no_go not in veredictos_validos:
        return f"ERROR: recomendacion_go_no_go debe ser {sorted(veredictos_validos)}."

    areas, err = _parse_json_param(estado_areas_criticas, "estado_areas_criticas")
    if err:
        return err

    def _check(valor: Any) -> str:
        return "✅ LISTA" if valor else "❌ NO LISTA"

    icono_veredicto = {"GO": "✅", "NO-GO": "🚫", "CONDITIONAL-GO": "⚠️"}[recomendacion_go_no_go]

    contenido = f"""# Launch Readiness Assessment — Go/No-Go
> Generado por Agente PM | NJM OS | {_ts()}

---

## Veredicto Final

# {icono_veredicto} {recomendacion_go_no_go}

---

## Estado de Áreas Críticas

| Área | Estado |
|------|--------|
| Marketing y PR | {_check(areas.get('marketing_y_pr'))} |
| Ventas — Capacitación | {_check(areas.get('ventas_capacitacion'))} |
| Soporte y Operaciones | {_check(areas.get('soporte_y_operaciones'))} |
| Tecnología e Infraestructura | {_check(areas.get('tecnologia_infraestructura'))} |

---

## Riesgos Bloqueantes

{_lista_md(riesgos_bloqueantes, prefijo='🚧') if riesgos_bloqueantes else '✅ Sin riesgos bloqueantes identificados.'}

---

## Condiciones para Proceder (si CONDITIONAL-GO)

_El Encargado Real debe resolver los riesgos bloqueantes listados arriba
antes de proceder al lanzamiento._

---

## Checklist Final de Gobernanza (Vector 8)

- [ ] Ninguna zona_roja_compliance es violada por el lanzamiento
- [ ] El equipo de ventas está capacitado para absorber el volumen proyectado (Vector 5)
- [ ] El plan de PR está activo para manejar posibles crisis reputacionales

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("evaluar_preparacion_lanzamiento", ruta)


@tool
def generar_plan_eol(
    ruta_destino: str,
    justificacion_retiro: str,
    cronograma_apagado: str,
    plan_migracion_usuarios: str,
    estrategia_comunicacion: str,
) -> str:
    """
    Estructura el protocolo de retiro o 'Sunsetting' de un producto, servicio
    o campaña, gestionando la migración de usuarios y el cierre financiero
    de forma ordenada.

    Anclaje en Libro Vivo: Vector 6 (se documenta como aprendizaje histórico)
    y Vector 2 (impacto en el flujo de caja tras el cierre).

    Args:
        ruta_destino: Ruta local donde se guardará el archivo.
        justificacion_retiro: Razones financieras o estratégicas para detener
            la iniciativa (se documenta en el Vector 6 del Libro Vivo).
        cronograma_apagado: Fechas clave del proceso de cierre:
            aviso a clientes, fin de soporte, apagado final.
        plan_migracion_usuarios: A dónde se enviará a los clientes actuales
            (Upsell / Cross-sell / Offboarding).
        estrategia_comunicacion: Cómo se informará al mercado para evitar
            daños de reputación (Vector 8).
    """
    contenido = f"""# Plan de End of Life (EOL) — Sunsetting Protocol
> Generado por Agente PM | NJM OS | {_ts()}

---

## Justificación del Retiro (Vector 6 — Histórico)

{justificacion_retiro}

> Esta decisión debe quedar documentada en el Vector 6 del Libro Vivo como
> aprendizaje histórico para evitar repetir la inversión en el futuro.

---

## Cronograma de Apagado

{cronograma_apagado}

---

## Plan de Migración de Usuarios

{plan_migracion_usuarios}

> **Objetivo:** Retener el máximo de clientes actuales a través de Upsell o Cross-sell.
> El impacto en MRR debe re-evaluarse contra el Vector 2 (Unit Economics).

---

## Estrategia de Comunicación (Vector 8 — Gobernanza)

{estrategia_comunicacion}

---

## Impacto Financiero Post-Cierre (Vector 2)

| Métrica | Estado esperado post-EOL |
|---------|--------------------------|
| MRR afectado | _(calcular contra Unit Economics del Vector 2)_ |
| Usuarios migrados | _(registrar tasa de retención)_ |
| Costo de cierre | _(contabilizar en flujo de caja)_ |

---

## Checklist de Cierre

- [ ] Todos los usuarios han sido notificados con la anticipación requerida
- [ ] El plan de migración está activo y monitoreado
- [ ] La comunicación no genera riesgo de PR (Vector 8 validado)
- [ ] El aprendizaje está documentado en el Vector 6 del Libro Vivo
- [ ] El impacto financiero está modelado en el flujo de caja (Vector 2)

---
_Documento generado automáticamente. Requiere firma del Encargado Real._
"""
    ruta = _escribir_md(ruta_destino, contenido)
    if ruta.startswith("ERROR"):
        return ruta
    return _confirmar("generar_plan_eol", ruta)


# ══════════════════════════════════════════════════════════════════
# REGISTRO DE HERRAMIENTAS
# ══════════════════════════════════════════════════════════════════

PM_SKILLS: List[Any] = [
    # Fase 1 — Ideación y Justificación
    generar_vision_producto,        # Skill 1
    generar_analisis_ansoff,        # Skill 2
    generar_analisis_porter,        # Skill 3
    generar_auditoria_foda,         # Skill 4
    generar_concepto_producto,      # Skill 5
    # Fase 2 — Planeación y Ejecución
    generar_business_case,          # Skill 6
    generar_prd,                    # Skill 7
    generar_roadmap,                # Skill 8
    generar_backlog_historias,      # Skill 9
    # Fase 3 — Validación, Lanzamiento y Retiro
    generar_plan_beta,              # Skill 10
    generar_requisitos_usabilidad,  # Skill 11
    generar_plan_demanda,           # Skill 12
    evaluar_preparacion_lanzamiento,  # Skill 13
    generar_plan_eol,               # Skill 14
]

_SKILL_MAP: Dict[str, Any] = {skill.name: skill for skill in PM_SKILLS}
