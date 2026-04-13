"""
NJM OS — Agente PM (Motor Operativo y Metodológico)

Fuente de verdad: ARCHITECTURE.md §§ PM-Sistema, PM-Skills, PM-Autocorrección, PM-Memoria

Responsabilidades:
  1. Leer el Libro Vivo del estado para construir su System Prompt dinámicamente.
  2. Seleccionar la Skill correcta de las 14 disponibles y ejecutarla.
  3. Pasar por el protocolo de autocorrección (máx. 2 intentos) antes de escalar.
  4. Emitir el payload TARJETA_SUGERENCIA_UI al frontend al finalizar.
  5. Acumular rutas de artefactos en state['documentos_generados'].

El System Prompt de este nodo es un Template Engine:
  Los campos de Vector 9 (arquetipo, sesgo, matriz cognitiva) y las
  restricciones financieras de Vectores 1, 2, 5, 7 y 8 se inyectan en
  tiempo real desde state['libro_vivo'] en cada disparo del nodo.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from core.estado import NJM_PM_State
from core.schemas import EstadoValidacion
from tools.pm_skills import PM_SKILLS, _SKILL_MAP

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DEL MODELO
# ══════════════════════════════════════════════════════════════════

# Claude 3.5 Sonnet — mismo modelo que el CEO para coherencia de ecosistema.
# temperature=0: el PM es un operador determinista, no un ente creativo libre.
MODEL_NAME = "claude-3-5-sonnet-20241022"

# Máximo de iteraciones internas del loop agéntico (techo de seguridad).
_MAX_ITERACIONES = 12

# Máximo de alertas acumuladas antes de escalar al CEO sin intentar más.
_MAX_ALERTAS_AUTOCORRECCION = 2

# Patrón para extraer la ruta del archivo de la respuesta de cada skill.
# Ejemplo de línea: "  Archivo generado: /absolute/path/to/file.md"
_RE_RUTA_ARCHIVO = re.compile(r"Archivo generado:\s*(.+)")

# ══════════════════════════════════════════════════════════════════
# TEMPLATE DEL SYSTEM PROMPT MAESTRO — Agente PM (v3 LangGraph)
# Fuente: ARCHITECTURE.md § "Prompt de Sistema Maestro: Agente PM (v3 - LangGraph Integrado)"
#
# Los campos entre {llaves} son variables dinámicas que se inyectan en
# _construir_prompt_pm() leyendo state['libro_vivo'] y state['alertas_internas'].
# Las llaves literales del Markdown se escapan con {{doble}}.
# ══════════════════════════════════════════════════════════════════

_PROMPT_TEMPLATE_PM = """\
[SISTEMA CORE Y ROL PARAMETRIZADO]
Eres el Agente PM (Product/Project Manager) de NJM OS, operando en el entorno \
local de Claude Cowork. Eres un operador determinista, no un ente creativo libre. \
Tu trabajo es traducir la estrategia macro del "Libro Vivo" en tácticas ejecutables, \
entregables nativos y decisiones fundamentadas en teoría de producto.

Para esta iteración, el Agente CEO te ha configurado bajo el siguiente perfil operativo estricto:
- **Arquetipo Dominante:** {arquetipo_principal}
- **Sesgo Metodológico Innegociable:** {sesgo_metodologico}
- **Matriz Cognitiva:** Enfoque Técnico: {enfoque_tecnico}/10 \
| Enfoque Negocios: {enfoque_negocio}/10 \
| Enfoque UX: {enfoque_usuario_ux}/10

DEBES ajustar todas tus recomendaciones tácticas y el uso de tus herramientas para \
maximizar los puntajes de tu Matriz Cognitiva y obedecer tu Sesgo Metodológico.

[REGLA DE ORO / RESTRICCIÓN DE ESTADO]
Tu ÚNICA fuente de verdad es el objeto JSON `libro_vivo` presente en tu estado de \
memoria. TIENES ESTRICTAMENTE PROHIBIDO asumir métricas, presupuestos, tonos de voz \
o canales que no estén explícitamente validados en ese JSON. \
Si el humano te pide algo que contradice el Libro Vivo, el Libro Vivo siempre gana.

Restricciones operativas activas que debes verificar antes de cada acción:
- Líneas rojas de marca (Vector 1): {lineas_rojas_marca}
- CAC máximo tolerable (Vector 2): ${cac_maximo_tolerable_usd} USD
- Cash Conversion Cycle (Vector 2): {cash_conversion_cycle_dias} días
- Presupuesto de pauta mensual (Vector 5): ${presupuesto_pauta_mensual_usd} USD
- Punto de quiebre operativo (Vector 5): {punto_quiebre_operativo}
- Zonas rojas de compliance (Vector 8): {zonas_rojas_compliance}
- North Star Metric (Vector 7): {north_star_metric}
- Objetivo táctico del trimestre (Vector 7): {objetivo_tactico_trimestre}

[ARSENAL TÁCTICO (TOOL CALLING)]
Tienes acceso a 14 Skills (APIs locales) para generar documentos en Claude Cowork. \
Selecciona la herramienta correcta antes de redactar:
1. **Ideación y Justificación:** `generar_vision_producto`, `generar_analisis_ansoff`, \
`generar_analisis_porter`, `generar_auditoria_foda`, `generar_concepto_producto`, \
`generar_business_case`.
2. **Planeación y Ejecución:** `generar_prd`, `generar_roadmap`, `generar_backlog_historias`.
3. **Validación, Lanzamiento y Retiro:** `generar_plan_beta`, \
`generar_requisitos_usabilidad`, `generar_plan_demanda`, \
`evaluar_preparacion_lanzamiento`, `generar_plan_eol`.

Regla de Ejecución: Todo documento que generes debe guardarse en la ruta: \
`{ruta_espacio_trabajo}`.

[PROTOCOLO DE AUTOCORRECCIÓN (SELF-REFLECTION)]
{bloque_alertas}\
Antes de entregar tu respuesta al humano, evalúa tu propio trabajo:
- Si propusiste un presupuesto que supera `presupuesto_pauta_mensual_usd`, \
  ajusta los montos y regenera el documento.
- Si usaste un tono prohibido por `lineas_rojas_marca`, reescribe el copy.
- Tienes un máximo de {intentos_restantes} intento(s) de autocorrección disponibles. \
  Si agotás los intentos sin resolver el conflicto, detén la ejecución e \
  informa el bloqueo con claridad.

[BANDERAS ROJAS Y ESCALAMIENTO AL CEO]
Debes interrumpir tu tarea e informar un BLOQUEO_CEO si la petición del humano:
- Supera el `cac_maximo_tolerable_usd` de ${cac_maximo_tolerable_usd} USD o amenaza \
  el `cash_conversion_cycle_dias` de {cash_conversion_cycle_dias} días (Vector 2).
- Supera el `punto_quiebre_operativo`: {punto_quiebre_operativo} (Vector 5).
- Exige usar palabras o tácticas restringidas en `lineas_rojas_marca` o \
  `zonas_rojas_compliance` (Vectores 1 y 8).

[FORMATO DE SALIDA ESTRICTO (OUTPUT SCHEMA)]
NUNCA respondas con texto libre al finalizar. Cuando termines de ejecutar herramientas, \
resume tu trabajo en este formato estructurado exacto:

RESUMEN_PM:
  skill_utilizada: <nombre de la skill principal ejecutada>
  propuesta_principal: <1 oración de qué hiciste y por qué>
  framework_metodologico: <marco teórico que fundamenta la decisión>
  check_adn_aprobado: <true o false>
  justificacion_adn: <por qué la propuesta es coherente con el Libro Vivo>

Si entraste en bloqueo, en vez del resumen, escribe:
BLOQUEO_CEO:
  motivo: <qué restricción del Libro Vivo no se puede satisfacer>
  intentos_realizados: <número>
"""


# ══════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════════


def _extraer_rutas_generadas(resultado_tool: str) -> List[str]:
    """
    Parsea la salida de una PM Skill y extrae las rutas absolutas de
    los archivos generados.

    El patrón es: "  Archivo generado: /ruta/absoluta/al/archivo.md"
    """
    return [
        match.group(1).strip()
        for match in _RE_RUTA_ARCHIVO.finditer(resultado_tool)
    ]


def _construir_prompt_pm(state: NJM_PM_State) -> str:
    """
    Construye el System Prompt dinámico del Agente PM inyectando los valores
    de Vector 9 y las restricciones de negocio desde state['libro_vivo'].

    Esta función es el "Template Engine" descrito en ARCHITECTURE.md.
    Nunca lanza excepciones: usa .get() con defaults seguros para campos faltantes,
    lo que fuerza al CEO a haber completado el Libro Vivo antes de que el PM opere.
    """
    lv: Dict[str, Any] = state.get("libro_vivo", {})

    # ── Vector 9: Perfil del PM (campos dinámicos de personalidad) ──
    perfil_pm = lv.get("vector_9_perfil_pm", {})
    matriz = perfil_pm.get("matriz_habilidades", {})

    arquetipo_principal = perfil_pm.get("arquetipo_principal", "⚠️ SIN ARQUETIPO — Libro Vivo incompleto")
    sesgo_metodologico = perfil_pm.get("sesgo_metodologico", "⚠️ SIN SESGO — Libro Vivo incompleto")
    enfoque_tecnico = matriz.get("enfoque_tecnico", "N/D")
    enfoque_negocio = matriz.get("enfoque_negocio", "N/D")
    enfoque_usuario_ux = matriz.get("enfoque_usuario_ux", "N/D")

    # ── Vectores 1, 2, 5, 7, 8: Restricciones operativas ────────────
    v1 = lv.get("vector_1_nucleo", {})
    v2 = lv.get("vector_2_negocio", {})
    v5 = lv.get("vector_5_infraestructura", {})
    v7 = lv.get("vector_7_objetivos", {})
    v8 = lv.get("vector_8_gobernanza", {})

    lineas_rojas = v1.get("lineas_rojas_marca", [])
    lineas_rojas_str = (
        " | ".join(lineas_rojas) if lineas_rojas
        else "⚠️ No definidas — consultar Vector 1"
    )

    unit_econ = v2.get("unit_economics", {})
    cac_maximo = unit_econ.get("cac_maximo_tolerable_usd", "⚠️ N/D")
    ccc_dias = v2.get("cash_conversion_cycle_dias", "⚠️ N/D")
    presupuesto_pauta = v5.get("presupuesto_pauta_mensual_usd", "⚠️ N/D")
    punto_quiebre = v5.get("punto_quiebre_operativo", "⚠️ N/D — consultar Vector 5")

    zonas_compliance = v8.get("zonas_rojas_compliance", [])
    zonas_compliance_str = (
        " | ".join(zonas_compliance) if zonas_compliance
        else "⚠️ No definidas — consultar Vector 8"
    )

    north_star = v7.get("north_star_metric", "⚠️ N/D — consultar Vector 7")
    objetivo_q = v7.get("objetivo_tactico_trimestre", "⚠️ N/D — consultar Vector 7")

    # ── Autocorrección: bloque de alertas activas ────────────────────
    alertas: List[str] = state.get("alertas_internas", [])
    intentos_usados = len(alertas)
    intentos_restantes = max(0, _MAX_ALERTAS_AUTOCORRECCION - intentos_usados)

    if alertas:
        alertas_formateadas = "\n".join(f"  ⚠️ Alerta {i+1}: {a}" for i, a in enumerate(alertas))
        bloque_alertas = (
            f"⚠️ PROTOCOLO DE AUTOCORRECCIÓN ACTIVO — Intento {intentos_usados + 1} de {_MAX_ALERTAS_AUTOCORRECCION}:\n"
            f"Tu intento anterior generó las siguientes alertas de negocio:\n"
            f"{alertas_formateadas}\n"
            f"DEBES leer cada alerta, corregir los parámetros y re-ejecutar la herramienta correspondiente.\n\n"
        )
    else:
        bloque_alertas = ""

    # ── Ruta de trabajo ──────────────────────────────────────────────
    ruta_espacio_trabajo = state.get("ruta_espacio_trabajo", "⚠️ SIN RUTA — definir en estado inicial")

    return _PROMPT_TEMPLATE_PM.format(
        arquetipo_principal=arquetipo_principal,
        sesgo_metodologico=sesgo_metodologico,
        enfoque_tecnico=enfoque_tecnico,
        enfoque_negocio=enfoque_negocio,
        enfoque_usuario_ux=enfoque_usuario_ux,
        lineas_rojas_marca=lineas_rojas_str,
        cac_maximo_tolerable_usd=cac_maximo,
        cash_conversion_cycle_dias=ccc_dias,
        presupuesto_pauta_mensual_usd=presupuesto_pauta,
        punto_quiebre_operativo=punto_quiebre,
        zonas_rojas_compliance=zonas_compliance_str,
        north_star_metric=north_star,
        objetivo_tactico_trimestre=objetivo_q,
        ruta_espacio_trabajo=ruta_espacio_trabajo,
        bloque_alertas=bloque_alertas,
        intentos_restantes=intentos_restantes,
    )


def _guardia_precondiciones(state: NJM_PM_State) -> Optional[str]:
    """
    Verifica que el estado es válido para que el PM opere.
    Devuelve un mensaje de error si algo falla, None si todo está OK.

    Fallos posibles:
      - libro_vivo vacío o faltante → el CEO no ha terminado el onboarding.
      - estado_validacion ya es BLOQUEO_CEO → no hay nada que hacer.
      - alertas_internas >= MAX → debe escalar, no reintentar.
    """
    libro_vivo = state.get("libro_vivo")
    if not libro_vivo:
        return (
            "GUARDIA: libro_vivo está vacío. El Agente CEO debe completar el "
            "onboarding y generar el Libro Vivo antes de que el PM pueda operar."
        )

    estado_actual = state.get("estado_validacion", EstadoValidacion.EN_PROGRESO.value)
    if estado_actual == EstadoValidacion.BLOQUEO_CEO.value:
        return (
            "GUARDIA: El estado ya es BLOQUEO_CEO. El PM no puede operar hasta "
            "que el Encargado Real resuelva el bloqueo activo."
        )

    alertas = state.get("alertas_internas", [])
    if len(alertas) >= _MAX_ALERTAS_AUTOCORRECCION:
        return (
            f"GUARDIA: Se alcanzó el máximo de {_MAX_ALERTAS_AUTOCORRECCION} intentos de "
            f"autocorrección. El sistema escala automáticamente al CEO."
        )

    return None


def _detectar_bloqueo_en_respuesta(texto: str) -> Optional[str]:
    """
    Detecta si el LLM declaró un bloqueo en su respuesta final.
    Devuelve el motivo si hay bloqueo, None si la ejecución fue exitosa.
    """
    if "BLOQUEO_CEO:" in texto:
        lineas = texto.split("\n")
        for i, linea in enumerate(lineas):
            if "motivo:" in linea.lower():
                return linea.split(":", 1)[-1].strip()
        return "El PM detectó una paradoja estratégica no resoluble."
    return None


def _parsear_resumen_pm(texto: str) -> Dict[str, str]:
    """
    Extrae los campos del bloque RESUMEN_PM de la respuesta final del LLM.
    Devuelve un dict con los campos encontrados.
    """
    campos: Dict[str, str] = {}
    patron = re.compile(r"^\s{2}(\w+):\s*(.+)$", re.MULTILINE)
    for match in patron.finditer(texto):
        campos[match.group(1).strip()] = match.group(2).strip()
    return campos


# ══════════════════════════════════════════════════════════════════
# NODO LANGGRAPH — nodo_pm
# ══════════════════════════════════════════════════════════════════


def nodo_pm(state: NJM_PM_State) -> Dict[str, Any]:
    """
    Nodo LangGraph del Agente PM.

    Flujo interno:
      1. Guardia de precondiciones: libro_vivo no vacío, no en bloqueo previo,
         alertas < MAX.
      2. Construcción del System Prompt dinámico desde Vector 9 del Libro Vivo.
      3. Instancia ChatAnthropic + bind de las 14 PM Skills.
      4. Loop agéntico: LLM → Tool calls → ToolMessages → LLM (máx. 12 iteraciones).
      5. Por cada ToolMessage de skill exitosa, extrae la ruta del archivo
         y la acumula en nuevos_documentos.
      6. Al salir del loop, analiza la respuesta final:
         - Si el LLM declara BLOQUEO_CEO → aplica el estado de bloqueo.
         - Si generó documentos → pasa a LISTO_PARA_FIRMA y construye el payload.
         - Si no generó documentos y no hay bloqueo → mantiene EN_PROGRESO.
      7. Devuelve el parche de estado mínimo con solo las claves modificadas.

    Args:
        state: Estado actual del grafo (NJM_PM_State).

    Returns:
        Parche de estado que LangGraph fusiona usando los reductores declarados:
        - messages: acumulados vía add_messages
        - documentos_generados: acumulados vía operator.add
        - alertas_internas: acumuladas vía operator.add
        - estado_validacion, skill_activa, payload_tarjeta_sugerencia: sobrescritos
    """
    parche: Dict[str, Any] = {}

    # ── 1. Guardia de precondiciones ──────────────────────────────
    error_guardia = _guardia_precondiciones(state)
    if error_guardia:
        # Escalar sin llamar al LLM: registrar alerta y bloquear.
        parche["alertas_internas"] = [error_guardia]
        parche["estado_validacion"] = EstadoValidacion.BLOQUEO_CEO.value
        return parche

    # ── 2. Construir System Prompt dinámico ───────────────────────
    system_prompt = _construir_prompt_pm(state)
    system_message = SystemMessage(content=system_prompt)

    # ── 3. Inicializar modelo con las 14 Skills ───────────────────
    llm = ChatAnthropic(model=MODEL_NAME, temperature=0)
    model_with_skills = llm.bind_tools(PM_SKILLS)

    # ── 4. Construir historial inicial ────────────────────────────
    historial = [system_message] + list(state["messages"])

    # ── 5. Acumuladores del parche ────────────────────────────────
    nuevos_mensajes: List[Any] = []
    nuevos_documentos: List[str] = []
    nuevas_alertas: List[str] = []
    skill_utilizada: Optional[str] = None

    # ── 6. Loop agéntico ──────────────────────────────────────────
    for iteracion in range(_MAX_ITERACIONES):

        respuesta: AIMessage = model_with_skills.invoke(historial + nuevos_mensajes)
        nuevos_mensajes.append(respuesta)

        # Sin tool calls → el PM terminó su razonamiento.
        if not respuesta.tool_calls:
            break

        # ── Ejecutar cada tool call ──────────────────────────────
        for tc in respuesta.tool_calls:
            nombre_skill = tc["name"]
            args_skill = tc["args"]
            tool_call_id = tc["id"]

            # Registrar la skill activa (última en ser llamada gana).
            skill_utilizada = nombre_skill
            parche["skill_activa"] = nombre_skill

            # Ejecutar la skill.
            skill_fn = _SKILL_MAP.get(nombre_skill)
            if skill_fn is None:
                resultado_str = (
                    f"ERROR: Skill '{nombre_skill}' no está registrada en PM_SKILLS. "
                    "Usa solo las 14 skills autorizadas por el Agente CEO."
                )
            else:
                try:
                    resultado_str = skill_fn.invoke(args_skill)
                except Exception as exc:  # noqa: BLE001
                    resultado_str = f"ERROR al ejecutar '{nombre_skill}': {exc}"

            # Añadir ToolMessage al historial.
            tool_msg = ToolMessage(
                content=resultado_str,
                tool_call_id=tool_call_id,
            )
            nuevos_mensajes.append(tool_msg)

            # ── Extraer rutas de archivos generados ─────────────
            if resultado_str.startswith("SKILL EJECUTADA"):
                rutas = _extraer_rutas_generadas(resultado_str)
                nuevos_documentos.extend(rutas)
            else:
                # La skill reportó un error — registrar como alerta interna.
                nueva_alerta = f"Error en skill '{nombre_skill}': {resultado_str[:200]}"
                nuevas_alertas.append(nueva_alerta)

    # ── 7. Analizar respuesta final del LLM ───────────────────────
    respuesta_final_texto = ""
    if nuevos_mensajes:
        ultimo = nuevos_mensajes[-1]
        if isinstance(ultimo, AIMessage):
            respuesta_final_texto = (
                ultimo.content if isinstance(ultimo.content, str)
                else str(ultimo.content)
            )

    motivo_bloqueo = _detectar_bloqueo_en_respuesta(respuesta_final_texto)

    if motivo_bloqueo:
        # El PM declaró explícitamente que no puede resolver la petición.
        nuevas_alertas.append(f"BLOQUEO declarado por el PM: {motivo_bloqueo}")
        parche["estado_validacion"] = EstadoValidacion.BLOQUEO_CEO.value
        parche["payload_tarjeta_sugerencia"] = _construir_payload_bloqueo(
            motivo=motivo_bloqueo,
            skill=skill_utilizada or "ninguna",
            alertas=list(state.get("alertas_internas", [])) + nuevas_alertas,
        )

    elif nuevos_documentos:
        # Ejecución exitosa: documentos generados y sin bloqueo.
        parche["estado_validacion"] = EstadoValidacion.LISTO_PARA_FIRMA.value
        resumen = _parsear_resumen_pm(respuesta_final_texto)
        parche["payload_tarjeta_sugerencia"] = _construir_payload_exito(
            skill=skill_utilizada or "desconocida",
            documentos=nuevos_documentos,
            resumen=resumen,
        )

    # Si no hay documentos ni bloqueo explícito, el estado permanece EN_PROGRESO
    # (el nodo fue conversacional o el LLM está razonando).

    # ── 8. Construir parche final ─────────────────────────────────
    parche["messages"] = nuevos_mensajes

    if nuevos_documentos:
        parche["documentos_generados"] = nuevos_documentos

    if nuevas_alertas:
        parche["alertas_internas"] = nuevas_alertas

    return parche


# ══════════════════════════════════════════════════════════════════
# CONSTRUCTORES DE PAYLOAD TARJETA_SUGERENCIA_UI
# Fuente: ARCHITECTURE.md § "PM - Contrato de Interfaz"
# ══════════════════════════════════════════════════════════════════


def _construir_payload_exito(
    skill: str,
    documentos: List[str],
    resumen: Dict[str, str],
) -> Dict[str, Any]:
    """
    Construye el payload TARJETA_SUGERENCIA_UI para el escenario exitoso
    (estado_ejecucion: LISTO_PARA_FIRMA).
    """
    archivos_cowork = [
        {
            "nombre_archivo": doc.split("/")[-1],
            "ruta_absoluta": f"file://{doc}",
        }
        for doc in documentos
    ]

    check_adn = resumen.get("check_adn_aprobado", "true").lower() in {"true", "si", "sí", "1"}

    return {
        "id_transaccion": str(uuid.uuid4()),
        "estado_ejecucion": EstadoValidacion.LISTO_PARA_FIRMA.value,
        "metadata": {
            "skill_utilizada": skill,
            "timestamp_generacion": datetime.now(timezone.utc).isoformat(),
        },
        "contenido_tarjeta": {
            "propuesta_principal": resumen.get(
                "propuesta_principal",
                f"Skill '{skill}' ejecutada. {len(documentos)} documento(s) generado(s).",
            ),
            "framework_metodologico": resumen.get(
                "framework_metodologico",
                "Ver documento generado para el marco metodológico completo.",
            ),
            "check_coherencia_adn": {
                "aprobado": check_adn,
                "justificacion": resumen.get(
                    "justificacion_adn",
                    "Validación pendiente de revisión por el Encargado Real.",
                ),
            },
            "archivos_locales_cowork": archivos_cowork,
            "log_errores_escalamiento": [],
        },
        "acciones_ui_disponibles": [
            {
                "label": "Aprobar y Continuar",
                "accion_backend": "/api/v1/tarjeta/aprobar",
                "variante_visual": "primario_success",
            },
            {
                "label": "Proponer Alternativa",
                "accion_backend": "/api/v1/tarjeta/alternativa",
                "variante_visual": "secundario_outline",
            },
        ],
    }


def _construir_payload_bloqueo(
    motivo: str,
    skill: str,
    alertas: List[str],
) -> Dict[str, Any]:
    """
    Construye el payload TARJETA_SUGERENCIA_UI para el escenario de bloqueo
    (estado_ejecucion: BLOQUEO_CEO).
    """
    return {
        "id_transaccion": str(uuid.uuid4()),
        "estado_ejecucion": EstadoValidacion.BLOQUEO_CEO.value,
        "metadata": {
            "skill_utilizada": skill,
            "timestamp_generacion": datetime.now(timezone.utc).isoformat(),
        },
        "contenido_tarjeta": {
            "propuesta_principal": f"BLOQUEO: {motivo}",
            "framework_metodologico": "Protocolo de Escalamiento al CEO activado.",
            "check_coherencia_adn": {
                "aprobado": False,
                "justificacion": motivo,
            },
            "archivos_locales_cowork": [],
            "log_errores_escalamiento": alertas,
        },
        "acciones_ui_disponibles": [
            {
                "label": "Ajustar Petición",
                "accion_backend": "/api/v1/tarjeta/ajustar",
                "variante_visual": "secundario_outline",
            },
            {
                "label": "Forzar Aprobación (asumir riesgo)",
                "accion_backend": "/api/v1/tarjeta/forzar",
                "variante_visual": "peligro_rojo",
            },
        ],
    }
