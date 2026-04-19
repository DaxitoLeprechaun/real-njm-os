"use client";

import { useEffect, useRef, useState } from "react";
import SlideOver from "@/components/njm/SlideOver";
import AgentConsole from "@/components/njm/AgentConsole";
import CEOShield from "@/components/njm/CEOShield";
import { useAgentConsole } from "@/hooks/useAgentConsole";
import type { Tarea } from "@/hooks/useAgentConsole";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SESSION_ID = "dev-session-1";

const KANBAN_COLUMNS: { estado: Tarea["estado"]; label: string }[] = [
  { estado: "BACKLOG", label: "Backlog" },
  { estado: "EN_PROGRESO", label: "En Progreso" },
  { estado: "DONE", label: "Done" },
];

const PRIORIDAD_BADGE: Record<Tarea["prioridad"], string> = {
  ALTA:  "bg-rose-500/20 text-rose-400 border-rose-500/30",
  MEDIA: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  BAJA:  "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
};

const ESTADO_CYCLE: Record<Tarea["estado"], Tarea["estado"]> = {
  BACKLOG: "EN_PROGRESO",
  EN_PROGRESO: "DONE",
  DONE: "BACKLOG",
};

interface TarjetaResultado {
  id_transaccion: string;
  estado_ejecucion: "LISTO_PARA_FIRMA" | "BLOQUEO_CEO";
  metadata: {
    skill_utilizada: string;
    timestamp_generacion: string;
  };
  contenido_tarjeta: {
    propuesta_principal: string;
    framework_metodologico: string;
    check_coherencia_adn: { aprobado: boolean; justificacion: string };
    archivos_locales_cowork: Array<{ nombre_archivo: string; ruta_absoluta: string }>;
    log_errores_escalamiento: string[];
  };
}

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


export default function PMWorkspacePage({
  params,
}: {
  params: { id: string };
}) {
  const [activeArtefacto, setActiveArtefacto] = useState<Artefacto | null>(null);
  const [tarjeta, setTarjeta] = useState<TarjetaResultado | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [terminalExitMessage, setTerminalExitMessage] = useState<string | null>(null);
  const prevRunningRef = useRef(false);
  const agentConsole = useAgentConsole();
  const { tasks } = agentConsole;
  const [localTasks, setLocalTasks] = useState<Tarea[]>([]);
  const [patchingTaskIds, setPatchingTaskIds] = useState<Set<string>>(new Set());
  // Intentionally not persisted: estado is the ground truth (backend stores overrides).
  // On reload, the amber "edited" indicator is cleared but the correct estado is hydrated.
  const [humanTouchedIds, setHumanTouchedIds] = useState<Set<string>>(new Set());
  const agentParams = { brand_id: params.id, session_id: SESSION_ID };
  const shieldOpen = agentConsole.actionRequired?.trigger === "BLOQUEO_CEO";
  const shieldMessage =
    agentConsole.actionRequired?.risk_message ??
    "El PM detectó un riesgo que requiere revisión del CEO.";

  function handleConsultarPM() {
    setTarjeta(null);
    setTerminalExitMessage(null);
    setLocalTasks([]);
    agentConsole.invoke("ceo-audit", agentParams);
  }

  useEffect(() => {
    if (!prevRunningRef.current || agentConsole.running || agentConsole.actionRequired) {
      prevRunningRef.current = agentConsole.running;
      return;
    }
    prevRunningRef.current = agentConsole.running;
    const controller = new AbortController();
    fetch(
      `${API_URL}/api/v1/session/state?brand_id=${params.id}&session_id=${SESSION_ID}`,
      { signal: controller.signal }
    )
      .then((r) => r.json())
      .then((data) => {
        if (data.last_tarjeta) setTarjeta(data.last_tarjeta as TarjetaResultado);
      })
      .catch((err) => {
        if (process.env.NODE_ENV !== "production") console.warn("[session/state]", err);
      });
    return () => controller.abort();
  }, [agentConsole.running, agentConsole.actionRequired, params.id]);

  useEffect(() => {
    if (agentConsole.logs.length > 0) setSubmitting(false);
  }, [agentConsole.logs.length]);

  useEffect(() => {
    if (tasks.length === 0) return;
    setLocalTasks((prev) => {
      const overrideMap = Object.fromEntries(prev.map((t) => [t.id, t.estado]));
      return tasks.map((t) => ({ ...t, estado: overrideMap[t.id] ?? t.estado }));
    });
  }, [tasks]);

  useEffect(() => {
    const controller = new AbortController();
    fetch(
      `${API_URL}/api/v1/session/state?brand_id=${params.id}&session_id=${SESSION_ID}`,
      { signal: controller.signal }
    )
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data.tasks) && data.tasks.length > 0) {
          setLocalTasks(data.tasks as Tarea[]);
        }
        if (data.last_tarjeta) setTarjeta(data.last_tarjeta as TarjetaResultado);
      })
      .catch(() => {});
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleEstadoChange(tareaId: string, currentEstado: Tarea["estado"]) {
    const nextEstado = ESTADO_CYCLE[currentEstado];
    setLocalTasks((prev) =>
      prev.map((t) => (t.id === tareaId ? { ...t, estado: nextEstado } : t))
    );
    setHumanTouchedIds((prev) => new Set(prev).add(tareaId));
    setPatchingTaskIds((prev) => new Set(prev).add(tareaId));
    fetch(`${API_URL}/api/v1/tasks/${tareaId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        brand_id: params.id,
        session_id: SESSION_ID,
        estado: nextEstado,
      }),
    })
      .catch(() => {
        setLocalTasks((prev) =>
          prev.map((t) => (t.id === tareaId ? { ...t, estado: currentEstado } : t))
        );
        setHumanTouchedIds((prev) => {
          const next = new Set(prev);
          next.delete(tareaId);
          return next;
        });
      })
      .finally(() => setPatchingTaskIds((prev) => { const next = new Set(prev); next.delete(tareaId); return next; }));
  }

  function tarjetaToArtefacto(t: TarjetaResultado): Artefacto {
    const rawDate = new Date(t.metadata.timestamp_generacion);
    const date = isNaN(rawDate.getTime()) ? "—" : rawDate.toLocaleDateString("es-MX");
    const files =
      t.contenido_tarjeta.archivos_locales_cowork
        .map((f) => `- ${f.nombre_archivo}`)
        .join("\n") || "— sin archivos adjuntos —";
    const errors =
      t.contenido_tarjeta.log_errores_escalamiento.length
        ? "\n\n## Errores de escalamiento\n" +
          t.contenido_tarjeta.log_errores_escalamiento.map((e) => `- ${e}`).join("\n")
        : "";
    return {
      id: t.id_transaccion,
      titulo: t.contenido_tarjeta.propuesta_principal,
      framework: t.contenido_tarjeta.framework_metodologico,
      tipo: t.estado_ejecucion === "LISTO_PARA_FIRMA" ? "Resultado PM" : "Bloqueado CEO",
      fecha: date,
      contenidoMd:
        `# ${t.contenido_tarjeta.propuesta_principal}\n\n` +
        `**Framework:** ${t.contenido_tarjeta.framework_metodologico}\n\n` +
        `**Coherencia ADN:** ${t.contenido_tarjeta.check_coherencia_adn.aprobado ? "✓" : "✗"} ${t.contenido_tarjeta.check_coherencia_adn.justificacion}\n\n` +
        `## Archivos entregables\n${files}` +
        errors,
    };
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
            {MOCK_ARTEFACTOS.length + (tarjeta ? 1 : 0)} artefactos generados
        </p>
      </div>

      {/* Live PM Result Card */}
      {tarjeta && (
        <div className="mb-8">
          <p className="text-xs uppercase tracking-widest mb-3 font-semibold text-muted-foreground">
            Resultado PM
          </p>
          <button
            onClick={() => setActiveArtefacto(tarjetaToArtefacto(tarjeta))}
            className="w-full glass rounded-xl p-5 text-left group hover:scale-[1.01] active:scale-[0.99] transition-all duration-150 cursor-pointer relative overflow-hidden"
          >
            <div
              className="absolute top-0 left-0 right-0 h-[2px]"
              style={{
                background:
                  tarjeta.estado_ejecucion === "LISTO_PARA_FIRMA"
                    ? "hsl(var(--pm-accent))"
                    : "rgb(225 29 72)",
              }}
            />
            <span
              className="inline-block text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded-full mb-3"
              style={{
                color:
                  tarjeta.estado_ejecucion === "LISTO_PARA_FIRMA"
                    ? "hsl(var(--pm-accent))"
                    : "rgb(251 113 133)",
                background:
                  tarjeta.estado_ejecucion === "LISTO_PARA_FIRMA"
                    ? "hsl(var(--pm-accent) / 0.12)"
                    : "rgb(225 29 72 / 0.12)",
              }}
            >
              {tarjeta.estado_ejecucion === "LISTO_PARA_FIRMA" ? "Listo para firma" : "Bloqueado CEO"}
            </span>
            <h3 className="font-semibold text-foreground text-sm leading-snug">
              {tarjeta.contenido_tarjeta.propuesta_principal}
            </h3>
            <div className="grid grid-rows-[0fr] group-hover:grid-rows-[1fr] transition-all duration-300 ease-out">
              <div className="overflow-hidden">
                <div className="mt-3 pt-3 border-t border-white/[0.06]">
                  <p className="text-xs text-muted-foreground">
                    <span className="text-muted-foreground/60">Framework:</span>{" "}
                    {tarjeta.contenido_tarjeta.framework_metodologico}
                  </p>
                  <p className="text-[11px] text-muted-foreground/40 mt-0.5">
                    {tarjeta.metadata.skill_utilizada} ·{" "}
                    {new Date(tarjeta.metadata.timestamp_generacion).toLocaleDateString("es-MX")}
                  </p>
                </div>
              </div>
            </div>
            <p className="text-[10px] text-muted-foreground/30 mt-3 uppercase tracking-wider group-hover:opacity-0 transition-opacity duration-200">
              {tarjeta.contenido_tarjeta.framework_metodologico}
            </p>
          </button>
        </div>
      )}

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
                  <p className="text-[11px] text-muted-foreground/40 mt-0.5">
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

      {/* Tablero Táctico — Phase 2.6 */}
      <div className="mt-12">
        <div className="flex items-center gap-3 mb-4">
          <p
            className="text-xs uppercase tracking-widest font-semibold"
            style={{ color: "hsl(var(--pm-accent))" }}
          >
            Tablero Táctico
          </p>
          {localTasks.length > 0 && (
            <span className="text-[10px] px-2 py-0.5 rounded-full font-mono text-pm/60 border border-pm/20">
              {localTasks.length} tarea{localTasks.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {localTasks.length === 0 ? (
          <div className="glass-subtle rounded-xl p-6 border border-white/[0.04] flex items-center gap-3">
            <span className="text-muted-foreground/30 text-lg" aria-hidden>⏳</span>
            <p className="text-sm text-muted-foreground/40 font-mono">
              Esperando desglose táctico del PM...
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {KANBAN_COLUMNS.map(({ estado, label }) => {
              const col = localTasks.filter((t) => t.estado === estado);
              return (
                <div key={estado} className="flex flex-col gap-2">
                  <div className="flex items-center justify-between px-1 mb-1">
                    <span className="text-[10px] uppercase tracking-widest font-semibold text-muted-foreground/50">
                      {label}
                    </span>
                    <span className="text-[10px] font-mono text-muted-foreground/30">
                      {col.length}
                    </span>
                  </div>
                  <div className="flex flex-col gap-2 min-h-[80px]">
                    {col.length === 0 ? (
                      <div className="rounded-lg border border-white/[0.04] border-dashed p-3 flex items-center justify-center">
                        <span className="text-[10px] text-muted-foreground/20 font-mono">vacío</span>
                      </div>
                    ) : (
                      col.map((tarea) => (
                        <button
                          key={tarea.id}
                          onClick={() => handleEstadoChange(tarea.id, tarea.estado)}
                          disabled={patchingTaskIds.has(tarea.id)}
                          className={`glass-subtle rounded-lg p-3 flex flex-col gap-1.5 text-left w-full cursor-pointer hover:border-white/[0.14] active:scale-[0.98] transition-all duration-100 disabled:opacity-50 disabled:cursor-not-allowed border ${
                            humanTouchedIds.has(tarea.id)
                              ? "border-white/[0.06] border-l-2 border-l-amber-500/40"
                              : "border-white/[0.06]"
                          }`}
                        >
                          <p className="text-xs font-medium text-foreground/80 leading-snug">
                            {tarea.titulo}
                          </p>
                          <p className="text-[10px] text-muted-foreground/50 leading-relaxed">
                            {tarea.descripcion}
                          </p>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span
                              className={`text-[9px] px-1.5 py-0.5 rounded border font-mono uppercase tracking-wide ${PRIORIDAD_BADGE[tarea.prioridad as Tarea["prioridad"]] ?? ""}`}
                            >
                              {tarea.prioridad}
                            </span>
                            <span className="text-[9px] text-muted-foreground/30 font-mono">
                              {tarea.responsable}
                            </span>
                            {humanTouchedIds.has(tarea.id) && (
                              <span className="ml-auto text-[8px] text-amber-500/60 font-mono uppercase tracking-wider">
                                edited
                              </span>
                            )}
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
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
        exitMessage={terminalExitMessage ?? undefined}
      />

      {/* CEO Shield Modal */}
      <CEOShield
        open={shieldOpen}
        onOpenChange={() => {}}
        riskMessage={shieldMessage}
        submitting={submitting}
        onApprove={() => {
          setSubmitting(true);
          agentConsole.resume("APPROVED", agentParams).then(() =>
            agentConsole.invoke("ceo-audit", agentParams)
          );
        }}
        onReject={() => {
          setSubmitting(true);
          agentConsole.resume("REJECTED", agentParams).then(() => {
            setTerminalExitMessage("CEO rechazó la ejecución.");
            agentConsole.invoke("ceo-reject", agentParams);
          });
        }}
      />

      {/* Floating CTA */}
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40 pointer-events-none">
        <button
          onClick={handleConsultarPM}
          disabled={agentConsole.running}
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
