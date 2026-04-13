"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { AgentLogStream, DEMO_EVENTS } from "@/components/AgentLogStream";
import { StateOrchestrator, DEMO_STATE } from "@/components/StateOrchestrator";
import { CEOShield, DEMO_HITL_PAYLOAD } from "@/components/CEOShield";

interface ArchivoCowork {
  nombre_archivo: string;
  ruta_absoluta: string;
}

interface CheckADN {
  aprobado: boolean;
  justificacion: string;
}

interface ContenidoTarjeta {
  propuesta_principal: string;
  framework_metodologico: string;
  check_coherencia_adn: CheckADN;
  archivos_locales_cowork: ArchivoCowork[];
  log_errores_escalamiento: string[];
}

interface AccionUI {
  label: string;
  accion_backend: string;
  variante_visual: "primario_success" | "secundario_outline" | "peligro_rojo";
}

interface TarjetaData {
  id_transaccion: string;
  estado_ejecucion: "LISTO_PARA_FIRMA" | "BLOQUEO_CEO";
  metadata: { skill_utilizada: string; timestamp_generacion: string };
  contenido_tarjeta: ContenidoTarjeta;
  acciones_ui_disponibles: AccionUI[];
}

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString("es-MX", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

function shortId(id: string): string {
  return id.split("-")[0].toUpperCase();
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-mono uppercase mb-2" style={{ fontSize: "10px", letterSpacing: "0.15em", color: "var(--text-tertiary)" }}>
      {children}
    </p>
  );
}

function Divider() {
  return <div style={{ borderTop: "1px solid var(--border)" }} />;
}

const BTN_CLASS: Record<AccionUI["variante_visual"], string> = {
  primario_success:  "btn-action btn-ok",
  secundario_outline: "btn-action btn-dim",
  peligro_rojo:      "btn-action btn-err",
};

const VARIANT = {
  LISTO_PARA_FIRMA: { color: "var(--success)", label: "LISTO PARA FIRMA" },
  BLOQUEO_CEO:      { color: "var(--danger)",  label: "BLOQUEO CEO — ESCUDO ACTIVO" },
} as const;

function TarjetaCard({ data }: { data: TarjetaData }) {
  const { color, label } = VARIANT[data.estado_ejecucion];
  const c = data.contenido_tarjeta;
  const isSuccess = data.estado_ejecucion === "LISTO_PARA_FIRMA";

  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderTop: `3px solid ${color}`, boxShadow: "2px 2px 0 oklch(0% 0 0)" }}>
      <div className="flex items-center gap-3 px-5 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <span aria-hidden="true" className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
        <span className="font-mono font-semibold" style={{ fontSize: "11px", letterSpacing: "0.1em", color }}>
          {label}
        </span>
        <span className="font-mono ml-auto" style={{ fontSize: "11px", color: "var(--text-tertiary)" }}>
          #{shortId(data.id_transaccion)}
        </span>
        <span className="font-mono" style={{ fontSize: "11px", color: "var(--text-tertiary)" }}>
          {formatTimestamp(data.metadata.timestamp_generacion)}
        </span>
      </div>

      <div className="px-5 py-2" style={{ borderBottom: "1px solid var(--border)" }}>
        <span className="font-mono" style={{ fontSize: "10px", color: "var(--text-tertiary)" }}>
          skill: <span style={{ color: "var(--text-secondary)" }}>{data.metadata.skill_utilizada}</span>
        </span>
      </div>

      <div className="p-5 space-y-5">
        <div>
          <FieldLabel>{isSuccess ? "Propuesta" : "Motivo del Bloqueo"}</FieldLabel>
          <p className="font-serif" style={{ fontSize: "18px", color: "var(--text-primary)", lineHeight: 1.75, fontWeight: 500 }}>
            {c.propuesta_principal}
          </p>
        </div>

        <Divider />

        {isSuccess ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <FieldLabel>Framework Metodológico</FieldLabel>
              <p className="font-serif" style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: 1.65 }}>
                {c.framework_metodologico}
              </p>
            </div>
            <div>
              <FieldLabel>Check de Coherencia ADN</FieldLabel>
              <div className="flex items-start gap-2">
                <span className="font-mono font-bold flex-shrink-0" style={{ fontSize: "18px", lineHeight: 1, color: c.check_coherencia_adn.aprobado ? "var(--success)" : "var(--danger)" }}>
                  {c.check_coherencia_adn.aprobado ? "✓" : "✗"}
                </span>
                <p className="font-serif" style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: 1.65 }}>
                  {c.check_coherencia_adn.justificacion}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div>
              <FieldLabel>Check de Coherencia ADN</FieldLabel>
              <div className="flex items-start gap-2">
                <span className="font-mono font-bold flex-shrink-0" style={{ fontSize: "18px", lineHeight: 1, color: "var(--danger)" }}>✗</span>
                <p className="font-serif" style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: 1.65 }}>
                  {c.check_coherencia_adn.justificacion}
                </p>
              </div>
            </div>

            {c.log_errores_escalamiento.length > 0 && (
              <>
                <Divider />
                <div>
                  <FieldLabel>Registro de Errores</FieldLabel>
                  <div className="p-4 space-y-2" style={{ border: "1px solid var(--danger-border)", background: "var(--danger-bg)" }}>
                    {c.log_errores_escalamiento.map((error, i) => (
                      <div key={i} className="flex items-start gap-3">
                        <span className="font-mono flex-shrink-0" style={{ fontSize: "10px", color: "var(--danger)", marginTop: "2px" }}>
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <p className="font-mono" style={{ fontSize: "11px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                          {error}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            <Divider />

            <div>
              <FieldLabel>Protocolo Activo</FieldLabel>
              <p className="font-serif" style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: 1.65 }}>
                {c.framework_metodologico}
              </p>
            </div>
          </>
        )}

        {isSuccess && c.archivos_locales_cowork.length > 0 && (
          <>
            <Divider />
            <div>
              <FieldLabel>Entregables — Claude Cowork</FieldLabel>
              <ul className="space-y-2">
                {c.archivos_locales_cowork.map((archivo) => (
                  <li key={archivo.ruta_absoluta}>
                    <a
                      href={archivo.ruta_absoluta}
                      className="font-mono hover-text-primary flex items-center gap-2"
                      style={{ fontSize: "12px", textDecoration: "none" }}
                    >
                      <span style={{ color: "var(--text-tertiary)" }}>→</span>
                      <span style={{ textDecoration: "underline", textUnderlineOffset: "3px" }}>{archivo.nombre_archivo}</span>
                    </a>
                    <p className="font-mono ml-4 mt-0.5 truncate" style={{ fontSize: "10px", color: "var(--text-tertiary)" }}>
                      {archivo.ruta_absoluta}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}

      </div>

      <div style={{ background: "var(--bg-raised)", borderTop: "2px solid var(--border)", padding: "16px 20px" }}>
        <p className="font-mono uppercase mb-3" style={{ fontSize: "9px", letterSpacing: "0.2em", color: "var(--text-tertiary)" }}>
          Decisión Requerida
        </p>
        <div className="flex flex-wrap items-center gap-3">
          {data.acciones_ui_disponibles.map((accion) => (
            <button
              key={accion.accion_backend}
              className={BTN_CLASS[accion.variante_visual]}
              onClick={() => alert(`Acción: ${accion.label}\nEndpoint: ${accion.accion_backend}`)}
            >
              {accion.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

const SUGERENCIAS = [
  "Genera un Business Case para lanzar una campaña de LinkedIn Ads en Q2",
  "Crea un Análisis de Ansoff para decidir si diversificamos o penetramos el mercado actual",
  "Necesito un PRD para el módulo de reportes automáticos",
  "Arma un Plan de Demand Generation para generar 60 MQLs en Q2",
  "Evalúa si estamos listos para lanzar el nuevo servicio de consultoría",
];

export default function Home() {
  const [peticion, setPeticion] = useState("");
  const [loading, setLoading] = useState(false);
  const [tarjeta, setTarjeta] = useState<TarjetaData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [shieldOpen, setShieldOpen] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  // Simulated async HITL callbacks — replace with real fetch to backend
  const handleApprove = useCallback(async (interruptId: string) => {
    await new Promise<void>((resolve) => setTimeout(resolve, 1200));
    console.log("HITL APPROVED", interruptId);
  }, []);

  const handleReject = useCallback(async (interruptId: string, reason: string) => {
    await new Promise<void>((resolve) => setTimeout(resolve, 1200));
    console.log("HITL REJECTED", interruptId, reason);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!peticion.trim()) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setTarjeta(null);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/api/ejecutar-tarea", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ peticion: peticion.trim() }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error desconocido." }));
        const detalle = typeof err.detail === "object"
          ? err.detail.detalle ?? JSON.stringify(err.detail)
          : String(err.detail);
        throw new Error(detalle);
      }

      setTarjeta(await res.json());
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      setError(err instanceof Error ? err.message : "Error de red. ¿Está corriendo el backend?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-base)" }}>
      <header style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-surface)" }}>
        <div className="max-w-5xl mx-auto px-6 flex items-center gap-4" style={{ height: "44px" }}>
          <div className="flex items-center gap-3">
            <span className="font-mono font-bold" style={{ fontSize: "11px", letterSpacing: "0.06em", padding: "2px 8px", background: "var(--text-primary)", color: "var(--bg-base)" }}>
              NJM OS
            </span>
            <span className="font-mono" style={{ fontSize: "10px", letterSpacing: "0.12em", color: "var(--text-tertiary)" }}>AGENTE PM</span>
            <span aria-hidden="true" style={{ color: "var(--border)", fontSize: "12px" }}>/</span>
            <span className="font-mono" style={{ fontSize: "10px", letterSpacing: "0.12em", color: "var(--text-secondary)" }}>DISRUPT</span>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--success)" }} />
            <span className="font-mono" style={{ fontSize: "10px", letterSpacing: "0.08em", color: "var(--text-tertiary)" }}>CLAUDE 3.5 SONNET</span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 space-y-10">
        <section>
          <div className="mb-5">
            <p className="font-mono uppercase mb-1" style={{ fontSize: "10px", letterSpacing: "0.15em", color: "var(--text-tertiary)" }}>
              Nueva Petición — Agente PM
            </p>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
              El Agente PM consultará el Libro Vivo de{" "}
              <span style={{ color: "var(--text-primary)" }}>Disrupt</span>{" "}
              y producirá el entregable metodológico correspondiente.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            <div style={{ border: "1px solid var(--border)", background: "var(--bg-surface)" }}>
              <div className="flex items-center gap-2 px-4 py-2" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <span className="font-mono" style={{ fontSize: "11px", color: "var(--success)" }}>›</span>
                <span className="font-mono uppercase" style={{ fontSize: "9px", letterSpacing: "0.15em", color: "var(--text-tertiary)" }}>stdin</span>
              </div>
              <textarea
                value={peticion}
                onChange={(e) => setPeticion(e.target.value)}
                placeholder="Describe el entregable o análisis estratégico que necesitas..."
                rows={4}
                aria-label="Petición al Agente PM"
                className="input-mono font-mono w-full px-4 py-3 bg-transparent resize-none outline-none"
                style={{ fontSize: "13px", color: "var(--text-primary)", caretColor: "var(--success)" }}
              />
            </div>

            <div>
              <p className="font-mono uppercase mb-2" style={{ fontSize: "9px", letterSpacing: "0.15em", color: "var(--text-tertiary)" }}>
                Accesos rápidos
              </p>
              <div className="space-y-0.5">
                {SUGERENCIAS.map((s, i) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setPeticion(s)}
                    className="w-full text-left flex items-start gap-3"
                    style={{ background: "none", border: "none", cursor: "pointer", padding: "4px 0" }}
                  >
                    <span className="font-mono flex-shrink-0" style={{ fontSize: "10px", color: "var(--text-tertiary)", width: "20px", fontVariantNumeric: "tabular-nums", marginTop: "1px" }}>
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="font-mono hover-text-primary" style={{ fontSize: "12px", lineHeight: 1.5 }}>
                      {s}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-4 pt-1">
              <button
                type="submit"
                disabled={loading || !peticion.trim()}
                className="font-mono uppercase"
                style={{
                  fontSize: "11px",
                  letterSpacing: "0.1em",
                  padding: "8px 20px",
                  border: `1px solid ${!loading && peticion.trim() ? "var(--text-primary)" : "var(--border)"}`,
                  background: !loading && peticion.trim() ? "var(--text-primary)" : "transparent",
                  color: !loading && peticion.trim() ? "var(--bg-base)" : "var(--text-tertiary)",
                  cursor: !loading && peticion.trim() ? "pointer" : "not-allowed",
                  transition: "all 0.15s",
                }}
              >
                {loading ? "EJECUTANDO..." : "EJECUTAR TAREA →"}
              </button>
              {loading && (
                <span className="font-mono animate-pulse" style={{ fontSize: "10px", color: "var(--text-tertiary)" }}>
                  Consultando Libro Vivo · Generando entregable
                </span>
              )}
            </div>
          </form>
        </section>

        {error && (
          <div className="px-5 py-4" style={{ border: "1px solid var(--danger-border)", borderTop: "2px solid var(--danger)", background: "var(--danger-bg)" }}>
            <p className="font-mono uppercase mb-1" style={{ fontSize: "10px", letterSpacing: "0.12em", color: "var(--danger)" }}>
              Error de Conexión
            </p>
            <p className="font-mono" style={{ fontSize: "12px", color: "var(--text-secondary)" }}>{error}</p>
          </div>
        )}

        {tarjeta && (
          <section className="space-y-4">
            <div className="flex items-center gap-4">
              <p className="font-mono uppercase flex-shrink-0" style={{ fontSize: "10px", letterSpacing: "0.15em", color: "var(--text-tertiary)" }}>
                Tarjeta de Sugerencia
              </p>
              <div aria-hidden="true" style={{ flex: 1, borderTop: "1px solid var(--border)" }} />
            </div>
            <TarjetaCard data={tarjeta} />
          </section>
        )}

        <section className="space-y-2">
          <div className="flex items-center gap-4">
            <p className="font-mono uppercase flex-shrink-0" style={{ fontSize: "10px", letterSpacing: "0.15em", color: "var(--text-tertiary)" }}>
              Agent Log Stream — Demo
            </p>
            <div aria-hidden="true" style={{ flex: 1, borderTop: "1px solid var(--border)" }} />
          </div>
          <AgentLogStream
            events={DEMO_EVENTS}
            label="NJM OS / AGENTE PM"
            toolsCollapsed={false}
            autoScroll={true}
            style={{ height: "480px" }}
          />
        </section>

        <section className="space-y-2">
          <div className="flex items-center gap-4">
            <p className="font-mono uppercase flex-shrink-0" style={{ fontSize: "10px", letterSpacing: "0.15em", color: "var(--text-tertiary)" }}>
              State Orchestrator — Demo
            </p>
            <div aria-hidden="true" style={{ flex: 1, borderTop: "1px solid var(--border)" }} />
          </div>
          <StateOrchestrator
            state={DEMO_STATE}
            showSnapshots={true}
            style={{ height: "520px" }}
          />
        </section>

        <section className="space-y-2">
          <div className="flex items-center gap-4">
            <p className="font-mono uppercase flex-shrink-0" style={{ fontSize: "10px", letterSpacing: "0.15em", color: "var(--text-tertiary)" }}>
              Escudo CEO — HITL Interrupt
            </p>
            <div aria-hidden="true" style={{ flex: 1, borderTop: "1px solid var(--border)" }} />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              type="button"
              onClick={() => setShieldOpen(true)}
              className="btn-action btn-err"
            >
              SIMULAR INTERRUPCIÓN HITL
            </button>
            <span className="font-mono" style={{ fontSize: "10px", color: "var(--text-tertiary)" }}>
              Activa el Escudo del CEO con el payload demo
            </span>
          </div>
        </section>
      </main>

      {shieldOpen && (
        <CEOShield
          payload={DEMO_HITL_PAYLOAD}
          onApprove={handleApprove}
          onReject={handleReject}
          onDismiss={() => setShieldOpen(false)}
        />
      )}
    </div>
  );
}
