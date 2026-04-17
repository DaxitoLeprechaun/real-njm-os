"""
NJM OS — Agente CEO (Guardián del ADN y Estratega)

Fuente de verdad: ARCHITECTURE.md §§ CEO-Sistema, CEO-Herramientas, CEO-EsquemaDatos

Responsabilidades:
  1. Escanear los documentos de onboarding de la marca.
  2. Mapear hallazgos a los 8 Vectores de Negocio.
  3. Generar reporte de brechas y lanzar entrevista de profundidad si falta información.
  4. Compilar y escribir el Libro Vivo cuando los 9 vectores están al 100%.
  5. Actuar como árbitro en background: levantar tarjetas rojas si el PM viola el ADN.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import ValidationError

from core.estado import NJM_OS_State
from core.schemas import EstadoValidacion, LibroVivo, NivelRiesgo
from tools.retrieval_tool import buscar_contexto_marca

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL MODELO
# ══════════════════════════════════════════════════════════════════

# Claude 3.5 Sonnet — especificado en ARCHITECTURE.md § "STACK TÉCNICO"
# temperature=0 garantiza determinismo máximo para un rol de auditoría.
MODEL_NAME = "gpt-4o"

# Extensiones que el CEO tiene permitido leer durante el escaneo.
_EXTENSIONES_TEXTO = {".txt", ".md", ".json", ".csv"}

# Directorio raíz del entorno Cowork (configurable vía variable de entorno en producción).
_COWORK_ROOT = Path.home() / "NJM_OS"

# ══════════════════════════════════════════════════════════════════
# PROMPT DE SISTEMA MAESTRO — Agente CEO
# Fuente: ARCHITECTURE.md § "Prompt de Sistema Maestro: Agente CEO (NJM OS)"
# ══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_CEO = """
[ROL Y PERSONA]
Eres el Agente CEO de NJM OS. Actúas como un C-Level Advisor implacable, Auditor de Negocios \
y Guardián del ADN de Marca. Tu objetivo principal no es ser un asistente servicial, \
sino proteger la rentabilidad, la identidad y la viabilidad estratégica de la empresa cliente. \
Piensas exclusivamente en términos de márgenes, mitigación de riesgos, escalabilidad \
y coherencia de marca. Tu tono es directo, corporativo, analítico y desprovisto de emociones \
o cortesías innecesarias.

Operas con tres capacidades cognitivas simultáneas:
1. Strategy Analyzer (Visión Sistémica): Detectas dependencias. Entiendes que una estrategia de \
   marketing agresiva no sirve de nada si el equipo de ventas no tiene un CRM configurado.
2. Financial Scenario Modeling (Asignación de Capital): Piensas en términos de Runway, flujo de caja \
   y protección de márgenes. No apruebas campañas por ser "creativas"; las apruebas si la \
   matemática de adquisición tiene sentido.
3. Board Governance & Risk Management: Actúas como el escudo de la empresa. Detectas riesgos \
   regulatorios, crisis de relaciones públicas potenciales y proteges los activos intangibles.

[DIRECTRIZ PRINCIPAL]
Tu función es auditar la documentación inicial de las marcas (Onboarding) y construir el \
"Libro Vivo" definitivo. El Libro Vivo está compuesto por 9 Vectores de Negocio estrictos \
(incluye el Vector 9: Perfil Operativo del Agente PM). Bajo ninguna circunstancia puedes \
permitir que el Agente PM u otro sistema opere si estos 9 vectores no están cubiertos al 100%.

[REGLAS INQUEBRANTABLES]
1. Cero Alucinación (Zero-Shot Constraint): Si al utilizar la herramienta \
   `escanear_directorio_onboarding` falta información para llenar cualquiera de los 9 vectores, \
   TIENES ESTRICTAMENTE PROHIBIDO inventar, inferir o rellenar los datos con suposiciones \
   o teoría general. Debes detenerte inmediatamente.

2. Protocolo de Bloqueo (Gatekeeper): Si detectas vacíos de información (Gap Analysis), \
   debes activar la herramienta `generar_reporte_brechas` y proceder a usar \
   `iniciar_entrevista_profundidad` para extraer los datos del usuario. No ejecutarás \
   la herramienta `escribir_libro_vivo` hasta que el humano responda y los datos \
   faltantes sean provistos.

3. Evaluación de Riesgo (Stress Test): Al revisar la documentación, debes buscar \
   proactivamente cuellos de botella operativos, deuda técnica, amenazas a la reputación \
   corporativa y riesgos de flujo de caja. Si durante la operación detectas tácticas del \
   Agente PM que comprometan el Cash Conversion Cycle, la coherencia del ADN o la estructura \
   de costos, debes activar `levantar_tarjeta_roja`.

4. Soberanía Humana: Reconoces que el "Encargado Real" (el humano) es el único con poder \
   de firma y veto. Tú recomiendas, auditas y bloqueas basándote en datos empíricos y \
   frameworks validados, pero si el humano decide forzar una acción asumiendo el riesgo \
   estratégico, debes permitirlo y documentarlo como una excepción en el Libro Vivo.

[FLUJO DE TRABAJO ESPERADO]
1. Escanea los documentos provistos en el directorio local con `escanear_directorio_onboarding`.
2. Mapea los hallazgos a los 9 Vectores de Negocio.
3. Si la información es insuficiente → Genera reporte de brechas con `generar_reporte_brechas` \
   y lanza preguntas C-Suite con `iniciar_entrevista_profundidad`.
4. Si la información está completa → Compila y genera el Libro Vivo con `escribir_libro_vivo`.
5. Durante la operación diaria → Monitorea las propuestas del Agente PM en background \
   y levanta alertas rojas con `levantar_tarjeta_roja` si rompen los parámetros del Libro Vivo.
"""

# ══════════════════════════════════════════════════════════════════
# BANCO DE PREGUNTAS DE ENTREVISTA POR VECTOR
# Fuente: ARCHITECTURE.md § "Banco de Ingesta del Agente CEO: Entrevista a Profundidad"
# ══════════════════════════════════════════════════════════════════

_PREGUNTAS_POR_VECTOR: Dict[int, List[str]] = {
    1: [
        "¿Cuál es la promesa exacta y cuantificable que la marca le hace al mercado, y por qué el cliente debería creerla por encima de la alternativa más barata?",
        "Si mapeamos a la marca en un eje cartesiano frente a la competencia, ¿cuáles son las dos variables principales que definen nuestro territorio?",
        "¿Cuáles son las líneas rojas innegociables? ¿Qué es lo que esta marca NUNCA haría o diría, incluso si eso significara perder una venta?",
    ],
    2: [
        "Si el CAC en nuestros canales principales sufriera una inflación del 30% el próximo trimestre, ¿la estructura de precios actual puede absorber el impacto?",
        "Del capital total disponible para crecimiento, ¿qué porcentaje exige ROI inmediato a 30 días y qué porcentaje tiene autorización para experimentación a largo plazo?",
        "Desde que invertimos un dólar en adquisición hasta que ese dólar regresa con utilidad, ¿cuántos días transcurren en promedio (Cash Conversion Cycle)?",
    ],
    3: [
        "¿Cuál es el 'trabajo' funcional y el 'trabajo' socioemocional para el cual el cliente 'contrata' a la marca (Jobs-to-be-Done)?",
        "¿Cuál es la principal objeción documentada que impide que los prospectos calificados cierren la compra hoy mismo?",
        "¿Cuál es el evento detonante (trigger event) que hace que el prospecto comience activamente a buscar nuestra solución?",
    ],
    4: [
        "Nombra a los tres competidores directos que están pujando por el mismo presupuesto del cliente y cuál es su principal vulnerabilidad táctica.",
        "¿Qué solución alternativa (diferente método) representa la mayor amenaza de sustitución a largo plazo?",
        "¿Cuál es el canal o táctica que toda la industria usa por defecto y que nosotros deberíamos disrumpir?",
    ],
    5: [
        "Si las tácticas del Agente PM triplicaran la demanda comercial mañana, ¿en qué punto exacto se rompe la operación actual?",
        "¿Existe algún proceso manual insostenible que debamos automatizar antes de inyectar más volumen al sistema?",
        "¿Cuál es el presupuesto mensual exacto asignado a pauta de adquisición?",
    ],
    6: [
        "En los últimos 18 meses, ¿cuál ha sido la campaña con mayor ROI y por qué funcionó?",
        "¿Existe alguna campaña reciente que haya consumido recursos sin generar tracción comercial? ¿Cuál fue el diagnóstico?",
        "¿Qué práctica obsoleta sigue viva en la operación de marketing por simple inercia corporativa?",
    ],
    7: [
        "¿Cuál es el único número que, si mejora sistemáticamente, garantiza que la marca está creciendo de forma saludable? (North Star Metric)",
        "En términos comerciales, ¿qué debe lograr esta marca en un año para considerarse un éxito rotundo?",
        "Para este trimestre, ¿cuál es la meta de marketing innegociable a la que el Agente PM debe alinear el 100% de sus sugerencias?",
    ],
    8: [
        "¿Existen regulaciones legales, normativas industriales o políticas de privacidad estrictas que los entregables del Agente PM tienen prohibido infringir?",
        "¿Cuál es el ángulo discursivo o asociación de marca que representaría una amenaza letal para la reputación corporativa?",
        "¿Qué metodologías, bases de datos o secretos industriales conforman la ventaja injusta de esta empresa y deben mantenerse confidenciales?",
    ],
    9: [
        "Dado el modelo de negocio de la marca, ¿qué arquetipo de PM se ajusta mejor: Growth_PM, Technical_PM, Data_PM o Brand_Experience_PM?",
        "En una escala del 1 al 10, ¿cuál debe ser el peso del enfoque técnico vs. negocios vs. experiencia de usuario para el Agente PM de esta marca?",
        "¿Cuál debe ser el sesgo metodológico innegociable del PM? (ej. 'Priorizar velocidad de experimentación sobre perfección visual')",
    ],
}

# ══════════════════════════════════════════════════════════════════
# HERRAMIENTAS DEL AGENTE CEO
# Fuente: ARCHITECTURE.md § "Herramientas (Tool Calling Schemas)"
# ══════════════════════════════════════════════════════════════════


@tool
def escanear_directorio_onboarding(
    ruta_directorio: str,
    tipos_archivo_permitidos: Optional[List[str]] = None,
) -> str:
    """
    Escanea el directorio local de una nueva marca para extraer la documentación
    fundacional y mapearla a los 9 vectores de negocio.

    Lee recursivamente los archivos de texto en la ruta especificada. Para cada
    archivo válido extrae su contenido e intenta identificar a qué Vector de
    Negocio pertenece según palabras clave. Devuelve un reporte estructurado
    del contenido encontrado, listo para que el CEO lo analice.

    Args:
        ruta_directorio: Ruta local absoluta en el entorno Cowork.
                         Ej.: "/NJM_OS/Marcas/Disrupt/00_ONBOARDING_INPUT"
        tipos_archivo_permitidos: Filtro de extensiones a leer sin el punto.
                                  Ej.: ["pdf", "md", "txt", "csv"].
                                  Por defecto: ["txt", "md", "json", "csv"].
    """
    directorio = Path(ruta_directorio)

    if not directorio.exists():
        return (
            f"ERROR: El directorio '{ruta_directorio}' no existe en el sistema de archivos. "
            "Verifica la ruta e inténtalo de nuevo."
        )
    if not directorio.is_dir():
        return f"ERROR: '{ruta_directorio}' existe pero no es un directorio."

    # Normalizar extensiones
    if tipos_archivo_permitidos:
        extensiones = {f".{ext.lstrip('.')}" for ext in tipos_archivo_permitidos}
    else:
        extensiones = _EXTENSIONES_TEXTO

    archivos_encontrados: List[Dict[str, Any]] = []
    archivos_omitidos: List[str] = []

    for archivo in sorted(directorio.rglob("*")):
        if not archivo.is_file():
            continue

        if archivo.suffix.lower() not in extensiones:
            if archivo.suffix.lower() == ".pdf":
                archivos_omitidos.append(
                    f"{archivo.name} (PDF — requiere instalar 'pypdf' para lectura automática)"
                )
            continue

        try:
            contenido = archivo.read_text(encoding="utf-8", errors="replace")
            archivos_encontrados.append(
                {
                    "archivo": str(archivo),
                    "extension": archivo.suffix,
                    "caracteres": len(contenido),
                    "extracto": contenido[:500].strip(),
                }
            )
        except Exception as exc:  # noqa: BLE001
            archivos_omitidos.append(f"{archivo.name} (Error de lectura: {exc})")

    if not archivos_encontrados:
        return (
            f"ADVERTENCIA: No se encontró ningún archivo legible en '{ruta_directorio}'. "
            f"Extensiones buscadas: {sorted(extensiones)}. "
            f"Archivos omitidos: {archivos_omitidos or 'ninguno'}."
        )

    reporte_lineas = [
        f"ESCANEO COMPLETADO — {len(archivos_encontrados)} archivo(s) leído(s) "
        f"en '{ruta_directorio}'.",
        "",
    ]

    for item in archivos_encontrados:
        reporte_lineas.append(f"### {Path(item['archivo']).name} ({item['caracteres']} chars)")
        reporte_lineas.append(item["extracto"])
        reporte_lineas.append("")

    if archivos_omitidos:
        reporte_lineas.append(f"Archivos omitidos: {', '.join(archivos_omitidos)}")

    return "\n".join(reporte_lineas)


@tool
def generar_reporte_brechas(
    vectores_incompletos: List[int],
    resumen_ejecutivo: str,
) -> str:
    """
    Exporta un documento Markdown al escritorio del Encargado Real detallando
    qué información falta en los Vectores de Negocio tras el escaneo inicial.

    Genera un archivo '00_GAP_ANALYSIS_<timestamp>.md' en el directorio Cowork.
    Activa este protocolo antes de llamar a `escribir_libro_vivo`.

    Args:
        vectores_incompletos: IDs (1–9) de los vectores que no alcanzaron
                              cobertura al 100%. Ej.: [3, 5, 8].
        resumen_ejecutivo: Explicación en lenguaje natural de por qué la
                           información actual es insuficiente para operar.
    """
    if not vectores_incompletos:
        return "INFO: Todos los vectores están completos. No es necesario generar reporte de brechas."

    invalidos = [v for v in vectores_incompletos if v not in range(1, 10)]
    if invalidos:
        return f"ERROR: IDs de vector inválidos: {invalidos}. Solo se aceptan valores del 1 al 9."

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"00_GAP_ANALYSIS_{timestamp}.md"
    directorio_salida = _COWORK_ROOT / "Reportes"
    directorio_salida.mkdir(parents=True, exist_ok=True)
    ruta_reporte = directorio_salida / nombre_archivo

    nombres_vectores = {
        1: "Núcleo Estratégico (Brand Core)",
        2: "Modelo de Negocio y Economía de la Oferta",
        3: "Mapeo de Audiencia y Mercado",
        4: "Ecosistema Competitivo",
        5: "Infraestructura de Canales y Touchpoints",
        6: "Histórico y Aprendizajes",
        7: "Objetivos y KPIs (North Star)",
        8: "Board Governance y Mitigación de Riesgo",
        9: "Perfil Operativo del Agente PM",
    }

    lineas = [
        "# REPORTE DE BRECHAS ESTRATÉGICAS — NJM OS",
        f"**Generado:** {datetime.now(timezone.utc).isoformat()}",
        f"**Estado Auditoría:** INCOMPLETO — {len(vectores_incompletos)}/9 vectores vacíos",
        "",
        "---",
        "",
        "## Resumen Ejecutivo (C-Level)",
        "",
        resumen_ejecutivo,
        "",
        "---",
        "",
        "## Vectores con Brechas Detectadas",
        "",
    ]

    for v_id in sorted(vectores_incompletos):
        nombre = nombres_vectores.get(v_id, f"Vector {v_id}")
        lineas.append(f"### Vector {v_id}: {nombre}")
        lineas.append("")
        lineas.append("**Estado:** ❌ INCOMPLETO — Datos insuficientes para operar.")
        lineas.append("")
        lineas.append("**Preguntas de extracción requeridas:**")
        lineas.append("")
        for pregunta in _PREGUNTAS_POR_VECTOR.get(v_id, ["Sin preguntas definidas."]):
            lineas.append(f"- {pregunta}")
        lineas.append("")

    lineas += [
        "---",
        "",
        "## Instrucción al Encargado Real",
        "",
        "El Agente CEO ha bloqueado la operación del Agente PM.",
        "**Ningún entregable será generado hasta que los vectores marcados estén al 100%.**",
        "",
        "Para desbloquear el sistema, responde las preguntas de cada vector.",
        "El Agente CEO procesará tus respuestas y completará el Libro Vivo.",
    ]

    ruta_reporte.write_text("\n".join(lineas), encoding="utf-8")

    return (
        f"REPORTE DE BRECHAS GENERADO:\n"
        f"  Ruta: {ruta_reporte}\n"
        f"  Vectores incompletos: {sorted(vectores_incompletos)}\n"
        f"  Acción requerida: El Encargado Real debe responder las preguntas de entrevista."
    )


@tool
def iniciar_entrevista_profundidad(
    vectores_objetivo: List[int],
    modo_stress_test: bool,
) -> str:
    """
    Lanza un cuestionario interactivo al Encargado Real para rellenar los
    vacíos estratégicos detectados en el escaneo inicial.

    Despliega las "Killer Questions" únicamente para los vectores marcados
    como vacíos. Activa `modo_stress_test` para incluir preguntas C-Suite
    sobre flujo de caja, riesgos PR y compliance (Vectores 2, 5 y 8).

    Args:
        vectores_objetivo: IDs (1–9) de los vectores que requieren
                           intervención humana para completarse.
        modo_stress_test: Si True, activa preguntas de nivel C-Suite para
                          los vectores 2, 5 y 8 (finanzas, operaciones, compliance).
    """
    invalidos = [v for v in vectores_objetivo if v not in range(1, 10)]
    if invalidos:
        return f"ERROR: IDs de vector inválidos: {invalidos}. Solo se aceptan valores del 1 al 9."

    vectores_stress = {2, 5, 8}
    preguntas_adicionales = {
        2: [
            "STRESS TEST FINANCIERO: Si el CAC se inflara un 30%, ¿la estructura de precios actual absorbe el impacto sin entrar en pérdidas operativas?",
            "DISTRIBUCIÓN DE CAPITAL: ¿Qué % del presupuesto exige ROI a 30 días vs. qué % puede quemarse en experimentación a largo plazo?",
        ],
        5: [
            "STRESS TEST OPERATIVO: ¿Existe algún proceso manual insostenible (ej. pasar leads de Excel a mano) que DEBE automatizarse antes de escalar?",
        ],
        8: [
            "STRESS TEST COMPLIANCE: ¿Qué regulaciones legales o industriales pueden multar o demandar a la marca si el PM las ignora?",
        ],
    }

    bloques: List[str] = [
        "═══════════════════════════════════════════════════════",
        "  ENTREVISTA DE PROFUNDIDAD — AGENTE CEO / NJM OS",
        "  Rol: C-Level Advisor | Modo: Extracción de ADN",
        "═══════════════════════════════════════════════════════",
        "",
        "Responde cada pregunta con precisión. El Agente CEO no puede",
        "inventar, suponer ni inferir los datos que no proveas.",
        "",
    ]

    for v_id in sorted(vectores_objetivo):
        preguntas = list(_PREGUNTAS_POR_VECTOR.get(v_id, []))

        if modo_stress_test and v_id in vectores_stress:
            preguntas = preguntas + preguntas_adicionales.get(v_id, [])

        nombres_vectores = {
            1: "Núcleo Estratégico", 2: "Modelo de Negocio", 3: "Audiencia y Mercado",
            4: "Ecosistema Competitivo", 5: "Infraestructura de Canales",
            6: "Histórico y Aprendizajes", 7: "Objetivos y KPIs",
            8: "Gobernanza y Riesgo", 9: "Perfil del Agente PM",
        }
        bloques.append(f"──── VECTOR {v_id}: {nombres_vectores.get(v_id, '')} ────")
        bloques.append("")

        for i, pregunta in enumerate(preguntas, 1):
            bloques.append(f"  {v_id}.{i}. {pregunta}")
            bloques.append("")

    bloques += [
        "═══════════════════════════════════════════════════════",
        "  Proporciona tus respuestas en formato:",
        "  'Vector X.Y: [tu respuesta]'",
        "  El CEO procesará cada respuesta y actualizará el Libro Vivo.",
        "═══════════════════════════════════════════════════════",
    ]

    return "\n".join(bloques)


@tool
def escribir_libro_vivo(
    ruta_destino: str,
    datos_consolidados_vectores: str,
) -> str:
    """
    Genera el archivo maestro del ADN de la marca (Libro Vivo).
    Solo ejecutable cuando el Checklist Maestro está al 100%.

    Valida el JSON contra el schema LibroVivo (Pydantic) antes de escribir.
    Bloquea la escritura si algún vector está vacío o inválido.
    Guarda el archivo en la ruta especificada dentro del entorno Cowork.

    Args:
        ruta_destino: Ruta donde se guardará el archivo.
                      Ej.: "/NJM_OS/Marcas/Disrupt/01_ESTRATEGIA_CENTRAL/LIBRO_VIVO_Disrupt.json"
        datos_consolidados_vectores: JSON string con la información validada
                                     de los 9 vectores (debe cumplir LibroVivo schema).
    """
    # 1. Parsear JSON
    try:
        datos = json.loads(datos_consolidados_vectores)
    except json.JSONDecodeError as exc:
        return (
            f"ERROR DE PARSING: datos_consolidados_vectores no es un JSON válido.\n"
            f"Detalle: {exc}\n"
            "Corrige el formato antes de volver a llamar esta herramienta."
        )

    # 2. Validar contra schema LibroVivo (Pydantic strict)
    try:
        libro = LibroVivo.model_validate(datos)
    except ValidationError as exc:
        errores = exc.errors()
        resumen = "\n".join(
            f"  - [{'/'.join(str(loc) for loc in e['loc'])}] {e['msg']}"
            for e in errores
        )
        return (
            f"ERROR DE VALIDACIÓN: El Libro Vivo tiene {len(errores)} brecha(s) pendiente(s).\n"
            f"El Agente CEO no puede escribir el Libro Vivo hasta que se corrijan:\n"
            f"{resumen}\n\n"
            "Protocolo: Usa `generar_reporte_brechas` e `iniciar_entrevista_profundidad` "
            "para obtener los datos faltantes del Encargado Real."
        )

    # 3. Escribir en el sistema de archivos
    ruta = Path(ruta_destino)
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            libro.model_dump_json(indent=2),
            encoding="utf-8",
        )
    except PermissionError:
        return f"ERROR DE PERMISOS: No se puede escribir en '{ruta_destino}'. Verifica los permisos del directorio."
    except OSError as exc:
        return f"ERROR DE SISTEMA DE ARCHIVOS: {exc}"

    nombre_marca = libro.metadata.nombre_marca
    timestamp = libro.metadata.fecha_ultima_firma.isoformat()

    return (
        f"LIBRO VIVO GENERADO EXITOSAMENTE:\n"
        f"  Marca: {nombre_marca}\n"
        f"  Ruta: {ruta_destino}\n"
        f"  Firmado: {timestamp}\n"
        f"  Estado: COMPLETO_100% — El Agente PM puede operar."
    )


@tool
def levantar_tarjeta_roja(
    motivo_bloqueo: str,
    nivel_riesgo: str,
    vector_vulnerado: int,
) -> str:
    """
    Bloquea una táctica del Agente PM que contradiga el Libro Vivo o represente
    un riesgo financiero, operativo, reputacional o de compliance.

    Esta herramienta interrumpe el flujo del PM, registra la alerta en el estado
    global y notifica al Encargado Real con una justificación de riesgo estructurada.

    Args:
        motivo_bloqueo: Explicación estratégica de por qué la táctica es inviable.
                        Ej.: "El margen de CAC no soporta esta campaña."
        nivel_riesgo: Categoría del riesgo. Valores válidos:
                      "financiero" | "operativo" | "reputacional" |
                      "compliance" | "incoherencia_adn"
        vector_vulnerado: ID del Vector del Libro Vivo (1–9) que la táctica está rompiendo.
    """
    niveles_validos = {nr.value for nr in NivelRiesgo}
    if nivel_riesgo not in niveles_validos:
        return (
            f"ERROR: nivel_riesgo '{nivel_riesgo}' no es válido. "
            f"Valores aceptados: {sorted(niveles_validos)}"
        )

    if vector_vulnerado not in range(1, 10):
        return f"ERROR: vector_vulnerado debe ser un entero del 1 al 9. Recibido: {vector_vulnerado}"

    nombres_vectores = {
        1: "Núcleo Estratégico (Brand Core)",
        2: "Modelo de Negocio y Economía de la Oferta",
        3: "Mapeo de Audiencia y Mercado",
        4: "Ecosistema Competitivo",
        5: "Infraestructura de Canales y Touchpoints",
        6: "Histórico y Aprendizajes",
        7: "Objetivos y KPIs (North Star)",
        8: "Board Governance y Mitigación de Riesgo",
        9: "Perfil Operativo del Agente PM",
    }

    timestamp = datetime.now(timezone.utc).isoformat()

    alerta = (
        f"🚨 TARJETA ROJA — Agente CEO\n"
        f"  Timestamp: {timestamp}\n"
        f"  Nivel de Riesgo: {nivel_riesgo.upper()}\n"
        f"  Vector Vulnerado: {vector_vulnerado} — {nombres_vectores.get(vector_vulnerado)}\n"
        f"  Motivo de Bloqueo: {motivo_bloqueo}\n"
        f"\n"
        f"  ACCIÓN REQUERIDA: El Encargado Real debe revisar esta alerta y decidir:\n"
        f"    A) Ajustar la táctica para cumplir con el Libro Vivo.\n"
        f"    B) Forzar la aprobación asumiendo el riesgo documentado."
    )

    return alerta


# ══════════════════════════════════════════════════════════════════
# MODELO — singleton de módulo (TD-07)
# ══════════════════════════════════════════════════════════════════

# Instanciado una sola vez al cargar el módulo. load_dotenv() en main.py
# debe ejecutarse ANTES de que este módulo sea importado.
_LLM = ChatOpenAI(model=MODEL_NAME, temperature=0)

# ══════════════════════════════════════════════════════════════════
# REGISTRO DE HERRAMIENTAS
# ══════════════════════════════════════════════════════════════════

CEO_TOOLS = [
    escanear_directorio_onboarding,
    generar_reporte_brechas,
    iniciar_entrevista_profundidad,
    escribir_libro_vivo,
    levantar_tarjeta_roja,
    buscar_contexto_marca,
]

_TOOL_MAP: Dict[str, Any] = {t.name: t for t in CEO_TOOLS}

# ══════════════════════════════════════════════════════════════════
# NODO LANGGRAPH — nodo_ceo
# ══════════════════════════════════════════════════════════════════


def nodo_ceo(state: NJM_OS_State) -> Dict[str, Any]:
    """
    Nodo LangGraph del Agente CEO.

    Flujo interno:
      1. Vincula herramientas al singleton _LLM.
      2. Inyecta el System Prompt Maestro del CEO al inicio del historial.
      3. Ejecuta el loop agéntico: LLM → Tool calls → ToolMessages → LLM.
      4. Por cada tool call, detecta side-effects en el estado global:
         - levantar_tarjeta_roja         → audit_status=RISK_BLOCKED, risk_flag=True
         - escribir_libro_vivo           → audit_status=COMPLETE, libro_vivo actualizado
         - generar_reporte_brechas       → audit_status=GAP_DETECTED, gap_report_path
         - iniciar_entrevista_profundidad → interview_questions poblado
      5. Devuelve el parche de estado con solo los campos modificados.

    Args:
        state: Estado actual del grafo (NJM_OS_State).

    Returns:
        Diccionario con las claves del estado que cambiaron en esta ejecución.
    """
    # ── 1. Vincular herramientas al singleton ──────────────────────
    model_with_tools = _LLM.bind_tools(CEO_TOOLS)

    # ── 2. Construir historial con System Prompt ───────────────────
    system_message = SystemMessage(content=SYSTEM_PROMPT_CEO.strip())
    historial = [system_message] + list(state["messages"])

    # ── 3. Acumuladores del parche de estado ──────────────────────
    nuevos_mensajes: List[Any] = []
    nuevas_alertas: List[str] = []
    nuevos_documentos: List[str] = []
    nuevo_estado_validacion: Optional[str] = None
    nuevo_libro_vivo: Optional[Dict[str, Any]] = None
    nuevo_audit_status: Optional[str] = None
    nuevo_gap_report_path: Optional[str] = None
    nuevas_interview_questions: Optional[List[str]] = None
    nuevo_risk_flag: Optional[bool] = None
    nuevo_risk_details: Optional[str] = None

    # ── 4. Loop agéntico ──────────────────────────────────────────
    # El CEO puede encadenar múltiples herramientas antes de responder
    # al humano (ej.: escanear → detectar brechas → generar reporte → entrevistar).
    max_iteraciones = 10  # Techo de seguridad para evitar loops infinitos.

    for _ in range(max_iteraciones):
        respuesta: AIMessage = model_with_tools.invoke(historial + nuevos_mensajes)
        nuevos_mensajes.append(respuesta)

        # Sin tool calls → el CEO terminó su razonamiento
        if not respuesta.tool_calls:
            break

        # ── 5. Ejecutar cada tool call y recolectar side-effects ──
        for tc in respuesta.tool_calls:
            nombre_tool = tc["name"]
            args_tool = tc["args"]
            tool_call_id = tc["id"]

            # Ejecutar la herramienta
            herramienta = _TOOL_MAP.get(nombre_tool)
            if herramienta is None:
                resultado_str = f"ERROR: Herramienta '{nombre_tool}' no registrada en CEO_TOOLS."
            else:
                try:
                    resultado_str = herramienta.invoke(args_tool)
                except Exception as exc:  # noqa: BLE001
                    resultado_str = f"ERROR al ejecutar '{nombre_tool}': {exc}"

            # Añadir ToolMessage para que el LLM vea el resultado
            tool_message = ToolMessage(
                content=resultado_str,
                tool_call_id=tool_call_id,
            )
            nuevos_mensajes.append(tool_message)

            # ── Side-effects en el estado global ──────────────────
            if nombre_tool == "levantar_tarjeta_roja":
                nuevo_estado_validacion = EstadoValidacion.BLOQUEO_CEO.value
                nuevo_audit_status = "RISK_BLOCKED"
                nuevo_risk_flag = True
                nuevo_risk_details = args_tool.get("motivo_bloqueo", resultado_str[:200])
                nuevas_alertas.append(resultado_str)

            elif nombre_tool == "escribir_libro_vivo":
                if resultado_str.startswith("LIBRO VIVO GENERADO EXITOSAMENTE"):
                    ruta = args_tool.get("ruta_destino", "")
                    nuevos_documentos.append(ruta)
                    nuevo_audit_status = "COMPLETE"
                    try:
                        nuevo_libro_vivo = json.loads(args_tool.get("datos_consolidados_vectores", "{}"))
                    except json.JSONDecodeError:
                        pass

            elif nombre_tool == "generar_reporte_brechas":
                nuevo_audit_status = "GAP_DETECTED"
                for linea in resultado_str.splitlines():
                    if "Ruta:" in linea:
                        ruta_reporte = linea.split("Ruta:", 1)[-1].strip()
                        nuevos_documentos.append(ruta_reporte)
                        nuevo_gap_report_path = ruta_reporte
                        break

            elif nombre_tool == "iniciar_entrevista_profundidad":
                vectores = args_tool.get("vectores_objetivo", [])
                nuevas_interview_questions = [
                    pregunta
                    for v_id in vectores
                    for pregunta in _PREGUNTAS_POR_VECTOR.get(v_id, [])
                ]

    # ── 6. Construir parche de estado ─────────────────────────────
    parche: Dict[str, Any] = {"messages": nuevos_mensajes}

    if nuevas_alertas:
        parche["alertas_internas"] = nuevas_alertas
    if nuevos_documentos:
        parche["documentos_generados"] = nuevos_documentos
    if nuevo_estado_validacion is not None:
        parche["estado_validacion"] = nuevo_estado_validacion
    if nuevo_libro_vivo is not None:
        parche["libro_vivo"] = nuevo_libro_vivo
    if nuevo_audit_status is not None:
        parche["audit_status"] = nuevo_audit_status
    if nuevo_gap_report_path is not None:
        parche["gap_report_path"] = nuevo_gap_report_path
    if nuevas_interview_questions is not None:
        parche["interview_questions"] = nuevas_interview_questions
    if nuevo_risk_flag is not None:
        parche["risk_flag"] = nuevo_risk_flag
    if nuevo_risk_details is not None:
        parche["risk_details"] = nuevo_risk_details

    return parche
