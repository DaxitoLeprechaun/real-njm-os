"""
NJM OS — Fixtures de desarrollo

Contiene datos de prueba para smoke-tests locales.
No importar en producción — solo para dev fallback en api/main.py.
"""

from __future__ import annotations

from typing import Any, Dict

DEV_BRAND_ID = "disrupt"
DEV_SESSION_ID = "dev-session-1"

# Simula el output del CEO tras onboarding completo de la marca Disrupt.
# En producción, este dict se lee del checkpointer por brand_id + session_id.
_LIBRO_VIVO_DISRUPT: Dict[str, Any] = {
    "metadata": {
        "nombre_marca": "Disrupt",
        "fecha_ultima_firma": "2026-04-13T00:00:00Z",
        "estado_auditoria": "COMPLETO_100%",
    },
    "vector_1_nucleo": {
        "uvp": "La única agencia B2B que garantiza ROI medible en 90 días o devuelve el fee.",
        "posicionamiento": "Eje X: Precio vs. Especialización — territorio: Alta especialización / Precio medio-alto.",
        "arquetipo_comunicacion": "Consultor Senior: directo, basado en datos, sin rodeos.",
        "lineas_rojas_marca": [
            "No hacer claims de ROI garantizado sin datos reales",
            "No comparar con competencia por precio",
            "No usar lenguaje informal o emojis en comunicación corporativa",
        ],
    },
    "vector_2_negocio": {
        "unit_economics": {
            "ticket_promedio_usd": 4500.0,
            "ltv_proyectado_usd": 27000.0,
            "cac_maximo_tolerable_usd": 900.0,
        },
        "cash_conversion_cycle_dias": 38,
        "modelo_pricing": "premium",
        "producto_estrella_bcg": "Consultoría de Demand Generation B2B",
        "producto_vaca_lechera_bcg": "Reportes mensuales de performance",
        "moats_economicos": [
            "Metodología propietaria de atribución multi-touch",
            "Base de datos de benchmarks B2B por industria",
        ],
    },
    "vector_3_audiencia": {
        "jtbd_funcional": "Generar leads B2B calificados sin contratar un equipo de marketing interno.",
        "jtbd_socioemocional": "Llegar a la reunión de directorio con métricas que justifiquen el gasto de marketing.",
        "friccion_transaccional": "No tienen claridad sobre qué canales generan ROI real — confunden actividad con resultados.",
        "trigger_event": "La empresa acaba de cerrar una ronda de inversión o tiene presión para escalar revenue en el Q.",
        "criterio_desempate": "Casos de estudio con métricas reales de empresas similares en su industria.",
    },
    "vector_4_competencia": {
        "competidores_directos": [
            {"nombre": "GrowthAgency MX", "vulnerabilidad_tactica": "No tiene especialización técnica — vende volumen, no calidad."},
            {"nombre": "Digital Pros", "vulnerabilidad_tactica": "Reporting manual y sin atribución real."},
            {"nombre": "ScaleB2B", "vulnerabilidad_tactica": "Precios más bajos pero sin metodología probada."},
        ],
        "amenaza_sustitutos": "Contratar un Head of Growth interno ($8k/mes) en vez de externalizar.",
        "tactica_a_disrumpir": "Todos usan casos de éxito anónimos — nosotros publicamos métricas reales con nombre de cliente (con permiso).",
    },
    "vector_5_infraestructura": {
        "arquitectura_funnel": "LinkedIn Ads / Google Search → Landing page → Demo call → Propuesta → Cierre. Ciclo promedio: 21 días.",
        "cuello_botella_funnel": "La tasa de conversión Demo-to-Propuesta es del 40% — hay fricción en la llamada de discovery.",
        "presupuesto_pauta_mensual_usd": 6000.0,
        "punto_quiebre_operativo": "Más de 80 leads/mes colapsa el equipo de ventas de 3 personas — máximo 20 demos/semana.",
        "deuda_tecnica_adquisicion": "Los leads de LinkedIn se pasan manualmente a HubSpot — requiere automatización con Zapier.",
        "activo_first_party_data": "Lista de 2,400 CMOs y VPs de Growth en LATAM con email verificado.",
    },
    "vector_6_historico": {
        "campañas_exitosas": [
            {"descripcion": "Campaña ABM Q4 2025 para sector Fintech", "roi_observado": "4.2x en 60 días", "diagnostico": "Segmentación ultra-específica + contenido de thought leadership funcionó."},
        ],
        "campañas_fallidas": [
            {"descripcion": "Meta Ads B2C Q1 2025", "roi_observado": "0.3x", "diagnostico": "El producto es B2B puro — audiencia de Meta incompatible con el ICP."},
        ],
        "practicas_obsoletas": ["Reportes en PDF estáticos que nadie lee", "Reuniones de status semanales de 2 horas sin agenda"],
    },
    "vector_7_objetivos": {
        "north_star_metric": "MQLs calificados (score > 70 en HubSpot) generados por mes.",
        "objetivo_negocio_12_meses": "Escalar de $180k a $360k ARR cerrando 4 nuevas cuentas enterprise.",
        "objetivo_tactico_trimestre": "Generar 60 MQLs calificados en Q2 con un CPA ≤ $100 USD usando principalmente LinkedIn Ads y contenido SEO.",
    },
    "vector_8_gobernanza": {
        "zonas_rojas_compliance": [
            "No usar datos de contactos sin opt-in explícito (GDPR/LGPD)",
            "No hacer promesas de resultados garantizados en materiales publicitarios",
            "No publicar casos de estudio sin autorización escrita del cliente",
        ],
        "riesgo_pr": "Cualquier campaña que parezca spam masivo destruye la credibilidad de thought leadership que tomó 3 años construir.",
        "propiedad_intelectual_confidencial": "Metodología de atribución multi-touch y base de datos de benchmarks B2B.",
    },
    "vector_9_perfil_pm": {
        "arquetipo_principal": "Technical_PM",
        "matriz_habilidades": {
            "enfoque_tecnico": 9,
            "enfoque_negocio": 8,
            "enfoque_usuario_ux": 5,
        },
        "sesgo_metodologico": (
            "Basar TODAS las decisiones en LTV y reducción de Churn. "
            "Priorizar retención sobre adquisición. "
            "Nunca proponer tácticas sin sustento matemático de CAC vs. LTV."
        ),
        "skills_especificas_activas": [
            "generar_business_case",
            "generar_analisis_ansoff",
            "generar_prd",
            "generar_plan_demanda",
            "evaluar_preparacion_lanzamiento",
        ],
    },
}
