"""
NJM OS — Modelos Pydantic de Validación de Datos

Fuente de verdad: ARCHITECTURE.md § "CEO - El Esquema de Datos Final (LIBRO_VIVO_SCHEMA)"
                                   § "PM - Contrato de Interfaz (TARJETA_SUGERENCIA_UI)"

Dos contratos estrictos:
  1. LibroVivo          → validado por el Agente CEO antes de que el PM opere.
  2. TarjetaSugerenciaUI → emitida por el PM al finalizar cada tarea; consumida por Next.js.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ══════════════════════════════════════════════════════════════════
# ENUMS COMPARTIDOS
# ══════════════════════════════════════════════════════════════════


class EstadoValidacion(str, Enum):
    EN_PROGRESO = "EN_PROGRESO"
    BLOQUEO_CEO = "BLOQUEO_CEO"
    LISTO_PARA_FIRMA = "LISTO_PARA_FIRMA"


class EstadoAuditoria(str, Enum):
    COMPLETO_100 = "COMPLETO_100%"


class ArquetipoPM(str, Enum):
    GROWTH = "Growth_PM"
    TECHNICAL = "Technical_PM"
    DATA = "Data_PM"
    BRAND_EXPERIENCE = "Brand_Experience_PM"


class NivelRiesgo(str, Enum):
    FINANCIERO = "financiero"
    OPERATIVO = "operativo"
    REPUTACIONAL = "reputacional"
    COMPLIANCE = "compliance"
    INCOHERENCIA_ADN = "incoherencia_adn"


class VarianteVisualBoton(str, Enum):
    PRIMARIO_SUCCESS = "primario_success"
    SECUNDARIO_OUTLINE = "secundario_outline"
    PELIGRO_ROJO = "peligro_rojo"


# ══════════════════════════════════════════════════════════════════
# LIBRO VIVO — Sub-modelos por Vector
# ══════════════════════════════════════════════════════════════════


class MetadataLibroVivo(BaseModel):
    nombre_marca: str = Field(..., description="Nombre comercial de la marca cliente.")
    fecha_ultima_firma: datetime = Field(..., description="ISO 8601. Última vez que el CEO validó el Libro Vivo.")
    estado_auditoria: EstadoAuditoria = Field(
        ..., description="Solo puede ser COMPLETO_100%. El CEO bloquea la escritura si no."
    )


class Vector1Nucleo(BaseModel):
    """Brand Core: UVP, tono de voz y líneas rojas innegociables."""

    uvp: str = Field(..., description="Proposición de Valor Única. Promesa exacta y cuantificable al mercado.")
    posicionamiento: str = Field(..., description="Territorio competitivo definido por dos ejes cartesianos.")
    arquetipo_comunicacion: str = Field(..., description="Modelo de comportamiento corporativo / arquetipo metodológico.")
    lineas_rojas_marca: List[str] = Field(
        ...,
        min_length=1,
        description="Lo que esta marca NUNCA haría. Usado por el CEO para levantar tarjetas rojas.",
    )


class UnitEconomics(BaseModel):
    ticket_promedio_usd: float = Field(..., gt=0)
    ltv_proyectado_usd: float = Field(..., gt=0)
    cac_maximo_tolerable_usd: float = Field(
        ..., gt=0, description="Techo de CAC para mantener margen operativo sano."
    )


class Vector2Negocio(BaseModel):
    """Modelo de negocio, unit economics y estructura de márgenes."""

    unit_economics: UnitEconomics
    cash_conversion_cycle_dias: int = Field(
        ..., gt=0, description="Días desde inversión en adquisición hasta retorno con utilidad."
    )
    modelo_pricing: str = Field(
        ..., description="Estrategia de precios: 'penetracion', 'premium' o 'suscripcion'."
    )
    producto_estrella_bcg: str = Field(..., description="Producto/servicio que financia el crecimiento.")
    producto_vaca_lechera_bcg: str = Field(..., description="Producto/servicio que sostiene la operación.")
    moats_economicos: List[str] = Field(..., description="Barreras de entrada que protegen los márgenes.")


class Vector3Audiencia(BaseModel):
    """Jobs-to-be-Done, fricción transaccional y trigger de compra."""

    jtbd_funcional: str = Field(..., description="El 'trabajo' funcional para el que el cliente contrata la marca.")
    jtbd_socioemocional: str = Field(..., description="El 'trabajo' socioemocional.")
    friccion_transaccional: str = Field(..., description="Principal objeción que impide el cierre de compra.")
    trigger_event: str = Field(..., description="Evento detonante que activa la búsqueda activa de la solución.")
    criterio_desempate: str = Field(..., description="Variable decisiva al comparar con la competencia final.")


class Competidor(BaseModel):
    nombre: str
    vulnerabilidad_tactica: str


class Vector4Competencia(BaseModel):
    """Ecosistema competitivo: directos, sustitutos y saturación de canal."""

    competidores_directos: List[Competidor] = Field(..., min_length=1, max_length=3)
    amenaza_sustitutos: str = Field(..., description="Solución alternativa de mayor riesgo de sustitución a largo plazo.")
    tactica_a_disrumpir: str = Field(..., description="Canal o táctica saturada que debemos evitar o disrumpir.")


class Vector5Infraestructura(BaseModel):
    """Canales, presupuesto y punto de quiebre operativo."""

    arquitectura_funnel: str = Field(..., description="Camino crítico desde el primer impacto hasta el cierre.")
    cuello_botella_funnel: str = Field(..., description="Punto de mayor fricción o abandono en el funnel actual.")
    presupuesto_pauta_mensual_usd: float = Field(..., gt=0)
    punto_quiebre_operativo: str = Field(
        ...,
        description="Qué se rompe primero si la demanda se triplica (servidores, logística, equipo de ventas).",
    )
    deuda_tecnica_adquisicion: Optional[str] = Field(
        None, description="Procesos manuales insostenibles que deben automatizarse antes de escalar."
    )
    activo_first_party_data: str = Field(..., description="Activo de primera parte más valioso (email list, CRM, etc.).")


class CampañaHistorica(BaseModel):
    descripcion: str
    roi_observado: Optional[str] = None
    diagnostico: str


class Vector6Historico(BaseModel):
    """Auditoría de éxitos, fracasos y deuda estratégica."""

    campañas_exitosas: List[CampañaHistorica] = Field(..., min_length=1)
    campañas_fallidas: List[CampañaHistorica] = Field(default_factory=list)
    practicas_obsoletas: List[str] = Field(
        default_factory=list, description="Lo que sigue vivo solo por inercia corporativa."
    )


class Vector7Objetivos(BaseModel):
    """North Star Metric y metas de negocio a 12 meses y por trimestre."""

    north_star_metric: str = Field(..., description="El único número que, si mejora, garantiza crecimiento saludable.")
    objetivo_negocio_12_meses: str = Field(..., description="Meta comercial macro a 12 meses.")
    objetivo_tactico_trimestre: str = Field(
        ..., description="Meta innegociable del trimestre actual. El PM alinea el 100% de sus sugerencias aquí."
    )


class Vector8Gobernanza(BaseModel):
    """Compliance, riesgos de PR y propiedad intelectual."""

    zonas_rojas_compliance: List[str] = Field(
        ...,
        min_length=1,
        description="Regulaciones legales o normativas industriales que los entregables no pueden infringir.",
    )
    riesgo_pr: str = Field(..., description="Ángulo discursivo o asociación de marca letal para la reputación.")
    propiedad_intelectual_confidencial: str = Field(
        ..., description="Metodologías o secretos industriales que no deben exponerse a modelos externos."
    )


class MatrizHabilidades(BaseModel):
    enfoque_tecnico: int = Field(..., ge=1, le=10, description="Capacidad de análisis de producto y software.")
    enfoque_negocio: int = Field(..., ge=1, le=10, description="Capacidad de análisis de ROI y viabilidad comercial.")
    enfoque_usuario_ux: int = Field(..., ge=1, le=10, description="Capacidad de empatía y diseño de experiencia.")


class Vector9PerfilPM(BaseModel):
    """Configuración del arquetipo del Agente PM dictada por el CEO."""

    arquetipo_principal: ArquetipoPM = Field(..., description="Define el rol dominante según el modelo de negocio.")
    matriz_habilidades: MatrizHabilidades
    sesgo_metodologico: str = Field(
        ...,
        description="Instrucción de comportamiento innegociable. Ej.: 'Priorizar velocidad de experimentación sobre perfección visual'.",
    )
    skills_especificas_activas: List[str] = Field(
        default_factory=list,
        description="Subset de las 14 Skills del PM que tienen prioridad para esta marca.",
    )


# ──────────────────────────────────────────────────────────────────
# LIBRO VIVO — Modelo raíz
# ──────────────────────────────────────────────────────────────────


class LibroVivo(BaseModel):
    """
    ADN estratégico, financiero y operativo de la marca.
    El Agente CEO solo puede escribir este modelo si los 9 vectores están al 100%.
    El Agente PM tiene acceso de solo lectura durante toda su ejecución.
    """

    model_config = {"strict": True}

    metadata: MetadataLibroVivo
    vector_1_nucleo: Vector1Nucleo
    vector_2_negocio: Vector2Negocio
    vector_3_audiencia: Vector3Audiencia
    vector_4_competencia: Vector4Competencia
    vector_5_infraestructura: Vector5Infraestructura
    vector_6_historico: Vector6Historico
    vector_7_objetivos: Vector7Objetivos
    vector_8_gobernanza: Vector8Gobernanza
    vector_9_perfil_pm: Vector9PerfilPM

    @field_validator("metadata")
    @classmethod
    def auditoria_debe_estar_completa(cls, v: MetadataLibroVivo) -> MetadataLibroVivo:
        if v.estado_auditoria != EstadoAuditoria.COMPLETO_100:
            raise ValueError(
                "El Libro Vivo solo puede instanciarse con estado_auditoria='COMPLETO_100%'. "
                "El Agente CEO está en falta: ejecuta generar_reporte_brechas primero."
            )
        return v


# ══════════════════════════════════════════════════════════════════
# TARJETA SUGERENCIA UI — Contrato de Interfaz PM → Next.js
# ══════════════════════════════════════════════════════════════════


class MetadataTarjeta(BaseModel):
    skill_utilizada: str = Field(..., description="Ej.: 'generar_business_case'")
    timestamp_generacion: datetime


class CheckCoherenciaADN(BaseModel):
    aprobado: bool
    justificacion: str = Field(
        ..., description="Ej.: 'Alineado con el valor de Accesibilidad del Vector 1'."
    )


class ArchivoCowork(BaseModel):
    nombre_archivo: str = Field(..., description="Ej.: 'PRD_Q3_Campaña.docx'")
    ruta_absoluta: str = Field(..., description="Ej.: 'file:///NJM_OS/Marcas/Disrupt/PRD_Q3_Campaña.docx'")


class ContenidoTarjeta(BaseModel):
    propuesta_principal: str = Field(
        ..., description="Resumen ejecutivo de 1 oración. Ej.: 'Pivotar a estrategia de Retención de Clientes'."
    )
    framework_metodologico: str = Field(
        ..., description="Ej.: 'Fundamentado en: Matriz de Ansoff y Customer Lifetime Value'."
    )
    check_coherencia_adn: CheckCoherenciaADN
    archivos_locales_cowork: List[ArchivoCowork] = Field(
        default_factory=list,
        description="Links directos a los entregables. Vacío si el estado es BLOQUEO_CEO.",
    )
    log_errores_escalamiento: List[str] = Field(
        default_factory=list,
        description="Solo se popula si estado_ejecucion es BLOQUEO_CEO.",
    )


class AccionUI(BaseModel):
    label: str = Field(..., description="Texto del botón. Ej.: 'Aprobar y Ejecutar'")
    accion_backend: str = Field(..., description="Endpoint o evento que dispara en FastAPI/LangGraph.")
    variante_visual: VarianteVisualBoton


class TarjetaSugerenciaUI(BaseModel):
    """
    Payload que el Agente PM inyecta en payload_tarjeta_sugerencia al finalizar.
    Next.js lo consume para renderizar la tarjeta de decisión sin lógica adicional.

    - estado_ejecucion == LISTO_PARA_FIRMA → tarjeta verde, archivos adjuntos, botón de aprobación.
    - estado_ejecucion == BLOQUEO_CEO      → banner rojo, log de errores, botones de escalamiento.
    """

    model_config = {"strict": True}

    id_transaccion: UUID = Field(..., description="UUID para trazabilidad de la decisión firmada.")
    estado_ejecucion: EstadoValidacion = Field(
        ...,
        description="Solo acepta LISTO_PARA_FIRMA o BLOQUEO_CEO. EN_PROGRESO es inválido aquí.",
    )
    metadata: MetadataTarjeta
    contenido_tarjeta: ContenidoTarjeta
    acciones_ui_disponibles: List[AccionUI] = Field(..., min_length=1)

    @field_validator("estado_ejecucion")
    @classmethod
    def no_puede_estar_en_progreso(cls, v: EstadoValidacion) -> EstadoValidacion:
        if v == EstadoValidacion.EN_PROGRESO:
            raise ValueError(
                "TarjetaSugerenciaUI no puede emitirse con estado EN_PROGRESO. "
                "El grafo de LangGraph solo debe construir este payload en el nodo final."
            )
        return v

    @field_validator("contenido_tarjeta")
    @classmethod
    def validar_coherencia_estado_archivos(cls, v: ContenidoTarjeta, info) -> ContenidoTarjeta:
        estado = info.data.get("estado_ejecucion")
        if estado == EstadoValidacion.BLOQUEO_CEO and v.archivos_locales_cowork:
            raise ValueError(
                "Un BLOQUEO_CEO no puede incluir archivos_locales_cowork. "
                "El PM canceló la generación de artefactos antes de escalar."
            )
        return v


# ══════════════════════════════════════════════════════════════════
# MOTOR DE DESGLOSE — Tarea (Phase 2.6)
# ══════════════════════════════════════════════════════════════════


class PrioridadTarea(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class EstadoTarea(str, Enum):
    BACKLOG = "BACKLOG"
    EN_PROGRESO = "EN_PROGRESO"
    DONE = "DONE"


class Tarea(BaseModel):
    id: str = Field(..., description="Ej.: 'tarea-001'. Único por sesión.")
    titulo: str = Field(..., max_length=60, description="Título accionable corto.")
    descripcion: str = Field(..., description="Descripción ejecutable de 1 oración.")
    responsable: str = Field(..., description="PM | CEO | Encargado Real")
    prioridad: PrioridadTarea
    estado: EstadoTarea = Field(default=EstadoTarea.BACKLOG)
    skill_origen: str = Field(..., description="Skill PM que generó esta tarea.")
