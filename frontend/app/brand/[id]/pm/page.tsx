"use client";

import { useState } from "react";
import { toast } from "sonner";
import SlideOver from "@/components/njm/SlideOver";
import AgentConsole from "@/components/njm/AgentConsole";
import CEOShield from "@/components/njm/CEOShield";
import { useAgentConsole } from "@/hooks/useAgentConsole";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Artefacto {
  id: string;
  titulo: string;
  framework: string;
  tipo: string;
  fecha: string;
  contenidoMd: string;
}

const MOCK_ARTEFACTOS: Artefacto[] = [
  {
    id: "ansoff",
    titulo: "Matriz de Ansoff",
    framework: "Ansoff Matrix",
    tipo: "Análisis Estratégico",
    fecha: "2026-04-10",
    contenidoMd: `# Matriz de Ansoff — Disrupt

## Penetración de Mercado
- Aumentar share en segmento SaaS B2B mid-market
- KPI: +15% MRR en 90 días
- Táctica: pricing anual con descuento 20%

## Desarrollo de Producto
- Módulo Analytics en roadmap Q2
- Integración nativa: Slack / Zapier / HubSpot
- ETA: Semana 8 del sprint actual

## Desarrollo de Mercado
- Expansión LATAM: México + Colombia (H2 2026)
- Partnerships: HubSpot, Salesforce ecosystem
- TAM objetivo: $18M en 24 meses

## Diversificación
- Línea de consultoría premium (TAM estimado: $2.3M)
- Productización del playbook interno como SaaS vertical`,
  },
  {
    id: "prd",
    titulo: "PRD de Campaña",
    framework: "Product Requirements Doc",
    tipo: "Documento de Producto",
    fecha: "2026-04-08",
    contenidoMd: `# PRD — Campaña Growth Q2 2026

## Objetivo
Capturar 200 leads calificados en 60 días via inbound.

## Stakeholders
- CEO:       Juan M.
- PM:        Agente NJM OS
- Marketing: TBD (contratación en curso)

## Requerimientos Funcionales
1. Landing page con A/B test
   - Variante A: propuesta de valor directa
   - Variante B: social proof + testimonials
2. Lead magnet: whitepaper "SaaS Scaling Playbook LATAM"
3. Secuencia nurturing: 5 emails, cadencia 3 días

## Métricas de Éxito
| Métrica          | Target  |
|------------------|---------|
| CVR Landing      | >= 4.5% |
| Email open rate  | >= 28%  |
| SQLs generados   | 40      |
| CAC máximo       | $120    |

## Criterios de Aceptación
- Deploy en staging: Semana 2
- QA + legal review: Semana 3
- Go-live: Semana 4`,
  },
  {
    id: "roadmap",
    titulo: "Roadmap Q3",
    framework: "OKR Roadmap",
    tipo: "Planificación",
    fecha: "2026-04-12",
    contenidoMd: `# Roadmap Q3 2026

## OKR Principal
O:   Consolidar posición como referente SaaS en LATAM
KR1: 500 nuevos MRR (net new)
KR2: NPS >= 55
KR3: 3 casos de estudio publicados

## Sprint Breakdown
--------------------------------------------
Semana 01-02:  Investigación de mercado MX
Semana 03-04:  MVP landing LATAM
Semana 05-06:  Beta con usuarios piloto (n=20)
Semana 07-08:  Iteración basada en datos reales
Semana 09-10:  Lanzamiento público + PR push
Semana 11-12:  Retro + planning Q4
--------------------------------------------

## Dependencias Críticas
- Partner legal MX: contrato pendiente firma
- Integración Stripe MX: ETA semana 3
- Traducción UX strings: asignado a diseño

## Riesgos
[HIGH]  Regulación fintech MX puede retrasar GTM
[MED]   Dependencia partner local para soporte
[LOW]   Rotación de early adopters sin onboarding optimizado`,
  },
  {
    id: "blue-ocean",
    titulo: "Blue Ocean Canvas",
    framework: "Blue Ocean Strategy",
    tipo: "Análisis Competitivo",
    fecha: "2026-04-05",
    contenidoMd: `# Blue Ocean Canvas — Disrupt

## ELIMINAR
- Implementaciones largas (+6 meses)
- Soporte exclusivo en inglés
- Modelos de precios opacos por asiento

## REDUCIR
- Curva de aprendizaje (objetivo: < 2h onboarding)
- Precio de entrada (freemium tier)
- Fricción en setup inicial

## AUMENTAR
- Time-to-value (objetivo: < 2 semanas)
- Localización LATAM profunda (ES/PT)
- Transparencia de pricing

## CREAR
- Módulo NJM OS embebido como diferencial
- Community-led growth (Discord + Slack)
- Certificaciones de partner para agencias`,
  },
  {
    id: "pestel",
    titulo: "Análisis PESTEL",
    framework: "PESTEL Framework",
    tipo: "Análisis de Entorno",
    fecha: "2026-04-03",
    contenidoMd: `# Análisis PESTEL — Disrupt (LATAM)

## Político
- Estabilidad regulatoria: MEDIA en MX, BAJA en AR
- Incentivos startups tech: Colombia Productiva activo

## Económico
- Inflación MX: 4.1% (estable)
- Tipo de cambio: riesgo volatilidad AR/CLP
- Venture capital LATAM: +22% YoY en 2025

## Social
- Adopción SaaS B2B LATAM: crecimiento 31% YoY
- Brecha digital: oportunidad en segmento mid-market
- Talento tech local: alta disponibilidad, menor costo

## Tecnológico
- IA generativa: ventana de oportunidad open
- Infraestructura cloud: AWS/GCP expansion activa
- Ciberseguridad: regulación emergente en BR/MX

## Ecológico
- ESG reporting: tendencia creciente en corporativos
- Oportunidad: módulo carbon footprint tracking

## Legal
- LGPD Brasil: compliance obligatorio desde 2021
- Ley Fintech MX: aplica si procesamos pagos
- GDPR awareness: requerido para clientes EU`,
  },
];

const PM_EXECUTION_SEQUENCE = [
  "[✓] Iniciando Agente PM...",
  "[✓] Cargando Libro Vivo — Vectores 1-9...",
  "[⏳] Evaluando Framework Ansoff para táctica actual...",
  "[✓] Alineación con Vector 2 (Modelo de Negocio): OK",
  "[⏳] Analizando restricciones presupuestarias Vector 5...",
  "[⏳] Calculando ROI estimado para campaña Q2...",
  "[✓] ROI proyectado: 3.2x en 90 días (baseline conservador)",
  "[⏳] Redactando Business Case — estructura 4-secciones...",
  "[✓] Sección 1: Executive Summary — DONE",
  "[✓] Sección 2: Análisis de Mercado — DONE",
  "[⏳] Sección 3: Plan de Ejecución — generando milestones...",
  "[✓] Sección 3: Plan de Ejecución — DONE",
  "[✓] Sección 4: Métricas & KPIs — DONE",
  "[✓] Business Case listo para revisión del CEO.",
];

export default function PMWorkspacePage({
  params,
}: {
  params: { id: string };
}) {
  const [activeArtefacto, setActiveArtefacto] = useState<Artefacto | null>(null);
  const [shieldOpen, setShieldOpen] = useState(false);
  const [shieldMessage, setShieldMessage] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);

  const agentConsole = useAgentConsole();

  async function handleConsultarPM() {
    setExecuting(true);
    agentConsole.invoke("pm-execution");
    try {
      const res = await fetch(`${API_URL}/api/ejecutar-tarea`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          peticion: "Ejecuta la táctica de marketing más adecuada para la marca.",
          modo: "ejecucion",
          nombre_marca: "Disrupt",
          thread_id: threadId ?? undefined,
        }),
      });
      const data = await res.json();
      if (data.thread_id) setThreadId(data.thread_id);
      if (data.estado_ejecucion === "BLOQUEO_CEO") {
        const msg =
          data.contenido_tarjeta?.check_coherencia_adn?.justificacion ||
          data.contenido_tarjeta?.log_errores_escalamiento?.[0] ||
          "El CEO bloqueó la ejecución por riesgo estratégico.";
        setShieldMessage(msg);
        setShieldOpen(true);
      } else if (!res.ok) {
        toast.error("Error al consultar el PM");
      }
    } catch {
      toast.error("No se pudo conectar con el backend");
    } finally {
      setExecuting(false);
    }
  }

  return (
    <div className="p-8 pb-28 relative">
      {/* Header */}
      <div className="mb-8">
        <p
          className="text-xs uppercase tracking-widest mb-1 font-semibold"
          style={{ color: "hsl(var(--pm-accent))" }}
        >
          PM Workspace
        </p>
        <h1 className="text-2xl font-bold text-foreground capitalize">{params.id}</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          {MOCK_ARTEFACTOS.length} artefactos generados
        </p>
      </div>

      {/* Artifacts Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {MOCK_ARTEFACTOS.map((artefacto) => (
          <button
            key={artefacto.id}
            onClick={() => setActiveArtefacto(artefacto)}
            className="glass rounded-xl p-5 text-left group hover:scale-[1.015] active:scale-[0.99] transition-all duration-150 cursor-pointer relative overflow-hidden"
          >
            {/* Accent top bar */}
            <div
              className="absolute top-0 left-0 right-0 h-[2px]"
              style={{ background: "hsl(var(--pm-accent))" }}
            />

            {/* Type badge */}
            <span
              className="inline-block text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded-full mb-3"
              style={{
                color: "hsl(var(--pm-accent))",
                background: "hsl(var(--pm-accent) / 0.12)",
              }}
            >
              {artefacto.tipo}
            </span>

            {/* Title */}
            <h3 className="font-semibold text-foreground text-sm leading-snug">
              {artefacto.titulo}
            </h3>

            {/* Hover metadata reveal */}
            <div className="grid grid-rows-[0fr] group-hover:grid-rows-[1fr] transition-all duration-300 ease-out">
              <div className="overflow-hidden">
                <div className="mt-3 pt-3 border-t border-white/[0.06]">
                  <p className="text-xs text-muted-foreground">
                    <span className="text-muted-foreground/60">Framework:</span>{" "}
                    {artefacto.framework}
                  </p>
                  <p className="text[11px] text-muted-foreground/40 mt-0.5">
                    {artefacto.fecha}
                  </p>
                </div>
              </div>
            </div>

            {/* Static footer (fades on hover) */}
            <p className="text-[10px] text-muted-foreground/30 mt-3 uppercase tracking-wider group-hover:opacity-0 transition-opacity duration-200">
              {artefacto.framework}
            </p>
          </button>
        ))}
      </div>

      {/* Simulate CEO Block button — dev/test helper */}
      <div className="mt-8 flex justify-center">
        <button
          onClick={() => setShieldOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-semibold uppercase tracking-widest transition-all duration-150 hover:brightness-110 active:scale-[0.97]"
          style={{
            background: "rgb(225 29 72 / 0.1)",
            border: "1px solid rgb(225 29 72 / 0.35)",
            color: "rgb(251 113 133)",
          }}
        >
          <span aria-hidden>🛡</span>
          Simular Bloqueo CEO
        </button>
      </div>

      {/* SlideOver: Document Viewer */}
      <SlideOver
        open={activeArtefacto !== null}
        onOpenChange={(open) => {
          if (!open) setActiveArtefacto(null);
        }}
        title={activeArtefacto?.titulo}
        description={
          activeArtefacto
            ? `${activeArtefacto.framework} · ${activeArtefacto.fecha}`
            : undefined
        }
      >
        {activeArtefacto && (
          <pre
            className="text-xs text-foreground/80 leading-relaxed whitespace-pre-wrap break-words"
            style={{ fontFamily: "'Fira Code', 'Courier New', monospace" }}
          >
            {activeArtefacto.contenidoMd}
          </pre>
        )}
      </SlideOver>

      {/* Agent Console */}
      <AgentConsole
        open={agentConsole.open}
        onClose={agentConsole.close}
        agentLabel="PM Agent"
        logs={agentConsole.logs}
        running={agentConsole.running}
      />

      {/* CEO Shield Modal */}
      <CEOShield
        open={shieldOpen}
        onOpenChange={setShieldOpen}
        riskMessage={shieldMessage || "El CEO bloqueó la ejecución por riesgo estratégico."}
        onApprove={() => {
          agentConsole.invoke("ceo-approve");
        }}
        onReject={() => {
          agentConsole.invoke("ceo-reject");
        }}
      />

      {/* Floating CTA */}
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40 pointer-events-none">
        <button
          onClick={handleConsultarPM}
          disabled={executing}
          className="pointer-events-auto flex items-center gap-2.5 px-7 py-3.5 rounded-full font-semibold text-sm text-white transition-all duration-200 hover:brightness-110 active:scale-[0.97] disabled:opacity-60 disabled:cursor-not-allowed"
          style={{
            background: "hsl(var(--pm-accent))",
            boxShadow:
              "0 0 40px hsl(var(--pm-accent) / 0.35), 0 8px 24px rgba(0,0,0,0.5)",
          }}
        >
          <span aria-hidden>🤖</span>
          Consultar PM / Ejecutar Táctica
        </button>
      </div>
    </div>
  );
}
