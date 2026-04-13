"use client";

import { useState } from "react";

// ── Types (espejo del contrato TARJETA_SUGERENCIA_UI del backend) ──────────
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
  metadata: {
    skill_utilizada: string;
    timestamp_generacion: string;
  };
  contenido_tarjeta: ContenidoTarjeta;
  acciones_ui_disponibles: AccionUI[];
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString("es-MX", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

const BOTON_CLASES: Record<AccionUI["variante_visual"], string> = {
  primario_success:
    "bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-5 py-2.5 rounded-lg transition-colors text-sm",
  secundario_outline:
    "border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 font-medium px-5 py-2.5 rounded-lg transition-colors text-sm",
  peligro_rojo:
    "bg-red-600 hover:bg-red-700 text-white font-semibold px-5 py-2.5 rounded-lg transition-colors text-sm",
};

// ── Sub-componentes ────────────────────────────────────────────────────────

function TarjetaExito({ data }: { data: TarjetaData }) {
  const c = data.contenido_tarjeta;

  return (
    <div className="border border-emerald-200 bg-emerald-50 rounded-2xl overflow-hidden shadow-sm">
      {/* Header verde */}
      <div className="bg-emerald-600 px-6 py-4 flex items-center gap-3">
        <span className="text-white text-2xl">✅</span>
        <div>
          <p className="text-white font-bold text-lg leading-tight">
            LISTO PARA FIRMA
          </p>
          <p className="text-emerald-100 text-xs">
            Skill:{" "}
            <span className="font-mono font-semibold">
              {data.metadata.skill_utilizada}
            </span>{" "}
            · {formatTimestamp(data.metadata.timestamp_generacion)}
          </p>
        </div>
        <span className="ml-auto text-emerald-200 text-xs font-mono opacity-70">
          #{data.id_transaccion.split("-")[0]}
        </span>
      </div>

      <div className="p-6 space-y-5">
        {/* Propuesta principal */}
        <div className="bg-white rounded-xl border border-emerald-100 p-4">
          <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-1">
            Propuesta
          </p>
          <p className="text-gray-900 text-base font-medium leading-snug">
            {c.propuesta_principal}
          </p>
        </div>

        {/* Framework + Check ADN en fila */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-white rounded-xl border border-emerald-100 p-4">
            <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-1">
              Framework Metodológico
            </p>
            <p className="text-gray-700 text-sm">{c.framework_metodologico}</p>
          </div>

          <div className="bg-white rounded-xl border border-emerald-100 p-4">
            <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-1">
              Check de Coherencia ADN
            </p>
            <div className="flex items-start gap-2 mt-1">
              <span className="text-lg leading-none">
                {c.check_coherencia_adn.aprobado ? "✅" : "⚠️"}
              </span>
              <p className="text-gray-700 text-sm leading-snug">
                {c.check_coherencia_adn.justificacion}
              </p>
            </div>
          </div>
        </div>

        {/* Archivos generados */}
        {c.archivos_locales_cowork.length > 0 && (
          <div className="bg-white rounded-xl border border-emerald-100 p-4">
            <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider mb-3">
              Entregables Generados en Claude Cowork
            </p>
            <ul className="space-y-2">
              {c.archivos_locales_cowork.map((archivo) => (
                <li key={archivo.ruta_absoluta}>
                  <a
                    href={archivo.ruta_absoluta}
                    className="flex items-center gap-2 group text-sm text-emerald-700 hover:text-emerald-900 transition-colors"
                  >
                    <span className="text-base">📄</span>
                    <span className="font-mono font-medium group-hover:underline underline-offset-2">
                      {archivo.nombre_archivo}
                    </span>
                    <span className="text-emerald-400 text-xs ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
                      Abrir →
                    </span>
                  </a>
                  <p className="text-gray-400 text-xs font-mono ml-6 truncate">
                    {archivo.ruta_absoluta}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Botones de acción */}
        <div className="flex flex-wrap gap-3 pt-1">
          {data.acciones_ui_disponibles.map((accion) => (
            <button
              key={accion.accion_backend}
              className={BOTON_CLASES[accion.variante_visual]}
              onClick={() =>
                alert(`Acción: ${accion.label}\nEndpoint: ${accion.accion_backend}`)
              }
            >
              {accion.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function TarjetaBloqueo({ data }: { data: TarjetaData }) {
  const c = data.contenido_tarjeta;

  return (
    <div className="border border-red-200 bg-red-50 rounded-2xl overflow-hidden shadow-sm">
      {/* Header rojo */}
      <div className="bg-red-600 px-6 py-4 flex items-center gap-3">
        <span className="text-white text-2xl">🚨</span>
        <div>
          <p className="text-white font-bold text-lg leading-tight">
            BLOQUEO CEO
          </p>
          <p className="text-red-100 text-xs">
            Skill:{" "}
            <span className="font-mono font-semibold">
              {data.metadata.skill_utilizada}
            </span>{" "}
            · {formatTimestamp(data.metadata.timestamp_generacion)}
          </p>
        </div>
        <span className="ml-auto text-red-200 text-xs font-mono opacity-70">
          #{data.id_transaccion.split("-")[0]}
        </span>
      </div>

      <div className="p-6 space-y-5">
        {/* Motivo de bloqueo */}
        <div className="bg-white rounded-xl border border-red-100 p-4">
          <p className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-1">
            Motivo del Bloqueo
          </p>
          <p className="text-gray-900 text-base font-medium leading-snug">
            {c.propuesta_principal}
          </p>
        </div>

        {/* Check ADN (fallido) */}
        <div className="bg-white rounded-xl border border-red-100 p-4">
          <p className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-1">
            Check de Coherencia ADN
          </p>
          <div className="flex items-start gap-2 mt-1">
            <span className="text-lg leading-none">❌</span>
            <p className="text-gray-700 text-sm leading-snug">
              {c.check_coherencia_adn.justificacion}
            </p>
          </div>
        </div>

        {/* Log de errores */}
        {c.log_errores_escalamiento.length > 0 && (
          <div className="bg-red-900 rounded-xl p-4">
            <p className="text-xs font-semibold text-red-300 uppercase tracking-wider mb-3">
              Registro de Errores para el CEO
            </p>
            <ul className="space-y-2">
              {c.log_errores_escalamiento.map((error, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-red-100 font-mono"
                >
                  <span className="text-red-400 shrink-0 mt-0.5">›</span>
                  <span className="leading-snug">{error}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Framework / Protocolo activo */}
        <div className="bg-white rounded-xl border border-red-100 p-4">
          <p className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-1">
            Protocolo Activo
          </p>
          <p className="text-gray-700 text-sm">{c.framework_metodologico}</p>
        </div>

        {/* Botones de acción */}
        <div className="flex flex-wrap gap-3 pt-1">
          {data.acciones_ui_disponibles.map((accion) => (
            <button
              key={accion.accion_backend}
              className={BOTON_CLASES[accion.variante_visual]}
              onClick={() =>
                alert(`Acción: ${accion.label}\nEndpoint: ${accion.accion_backend}`)
              }
            >
              {accion.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Componente principal ───────────────────────────────────────────────────

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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!peticion.trim()) return;

    setLoading(true);
    setTarjeta(null);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/api/ejecutar-tarea", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ peticion: peticion.trim() }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error desconocido." }));
        const detalle =
          typeof err.detail === "object"
            ? err.detail.detalle ?? JSON.stringify(err.detail)
            : String(err.detail);
        throw new Error(detalle);
      }

      const data: TarjetaData = await res.json();
      setTarjeta(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error de red. ¿Está corriendo el backend?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center text-gray-950 font-black text-sm">
              N
            </div>
            <span className="font-bold text-white text-lg tracking-tight">
              NJM OS
            </span>
          </div>
          <div className="h-5 w-px bg-gray-700" />
          <span className="text-gray-400 text-sm">Agente PM · Disrupt</span>
          <div className="ml-auto flex items-center gap-2">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            <span className="text-xs text-gray-400">Claude 3.5 Sonnet</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        {/* Título */}
        <div>
          <h1 className="text-2xl font-bold text-white">
            ¿Qué entregable necesitas hoy?
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            El Agente PM leerá el Libro Vivo de{" "}
            <span className="text-emerald-400 font-medium">Disrupt</span> y
            generará el documento metodológico correspondiente.
          </p>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={peticion}
            onChange={(e) => setPeticion(e.target.value)}
            placeholder="Ej: Genera un Business Case para lanzar una campaña de LinkedIn Ads en Q2..."
            rows={4}
            className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-gray-100 placeholder-gray-500 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
          />

          {/* Sugerencias rápidas */}
          <div className="flex flex-wrap gap-2">
            {SUGERENCIAS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setPeticion(s)}
                className="text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 px-3 py-1.5 rounded-full transition-colors"
              >
                {s.slice(0, 45)}…
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={loading || !peticion.trim()}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold py-3 rounded-xl transition-colors text-sm flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg
                  className="animate-spin h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                El Agente PM está trabajando…
              </>
            ) : (
              "Ejecutar Tarea →"
            )}
          </button>
        </form>

        {/* Error de red / API */}
        {error && (
          <div className="bg-red-950 border border-red-800 rounded-xl px-5 py-4">
            <p className="text-red-400 font-semibold text-sm">Error de conexión</p>
            <p className="text-red-300 text-sm mt-1 font-mono">{error}</p>
          </div>
        )}

        {/* Tarjeta de Sugerencia */}
        {tarjeta && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="h-px flex-1 bg-gray-800" />
              <span className="text-xs text-gray-500 uppercase tracking-widest">
                Tarjeta de Sugerencia
              </span>
              <div className="h-px flex-1 bg-gray-800" />
            </div>

            {tarjeta.estado_ejecucion === "LISTO_PARA_FIRMA" ? (
              <TarjetaExito data={tarjeta} />
            ) : (
              <TarjetaBloqueo data={tarjeta} />
            )}
          </div>
        )}
      </main>
    </div>
  );
}
