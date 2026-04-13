'use client';

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
} from 'react';
import type {
  LangGraphEvent,
  LangGraphEventKind,
  LogEntry,
  LogEntryKind,
  StreamStats,
  StreamStatus,
  AgentLogStreamProps,
} from './types';
import { LogRow } from './LogRow';

// ── Event processing ──────────────────────────────────────────────────────────

function kindFromEvent(event: LangGraphEventKind): LogEntryKind {
  if (event.includes('tool')) return 'tool';
  if (event.includes('llm') || event.includes('chat_model')) return 'llm';
  if (event.includes('retriever')) return 'retriever';
  if (event.includes('chain')) return 'node';
  return 'custom';
}

function processLangGraphEvent(
  ev: LangGraphEvent,
  active: Map<string, LogEntry>,
  seq: { n: number },
): { entry: LogEntry; isNew: boolean } {
  const ts = ev.timestamp ?? Date.now();
  const kind = kindFromEvent(ev.event);
  const isStart = ev.event.endsWith('_start');
  const isEnd = ev.event.endsWith('_end');
  const isStream = ev.event.endsWith('_stream');

  if (isStart) {
    const entry: LogEntry = {
      id: `${ev.run_id}::${ev.event}::${seq.n}`,
      run_id: ev.run_id,
      parent_ids: ev.parent_ids ?? [],
      kind,
      event: ev.event,
      name: ev.name,
      status: 'running',
      ts_start: ts,
      input: ev.data?.input,
      tags: ev.tags ?? [],
      metadata: ev.metadata ?? {},
      seq: seq.n++,
    };
    active.set(ev.run_id, entry);
    return { entry, isNew: true };
  }

  const existing = active.get(ev.run_id);

  if (isEnd && existing) {
    existing.status = 'ok';
    existing.ts_end = ts;
    existing.delta_ms = ts - existing.ts_start;
    existing.output = ev.data?.output;

    if (kind === 'llm' && ev.data?.output) {
      const out = ev.data.output as Record<string, unknown>;
      const usageMeta = out.usage_metadata as Record<string, number> | undefined;
      const tokenUsage = out.token_usage as Record<string, number> | undefined;
      const usage = usageMeta ?? tokenUsage;
      if (usage) {
        existing.token_count =
          usage.total_tokens ??
          (usage.input_tokens ?? 0) + (usage.output_tokens ?? 0);
      }
    }
    return { entry: existing, isNew: false };
  }

  if (isStream && existing) {
    existing.status = 'stream';
    return { entry: existing, isNew: false };
  }

  // Orphan event (end or stream with no matching start)
  const orphan: LogEntry = {
    id: `${ev.run_id}::orphan::${seq.n}`,
    run_id: ev.run_id,
    parent_ids: ev.parent_ids ?? [],
    kind,
    event: ev.event,
    name: ev.name,
    status: isEnd ? 'ok' : 'running',
    ts_start: ts,
    ts_end: isEnd ? ts : undefined,
    delta_ms: isEnd ? 0 : undefined,
    input: ev.data?.input,
    output: isEnd ? ev.data?.output : undefined,
    tags: ev.tags ?? [],
    metadata: ev.metadata ?? {},
    seq: seq.n++,
  };
  active.set(ev.run_id, orphan);
  return { entry: orphan, isNew: true };
}

// ── Raw line parser (handles SSE "data: {...}" and bare NDJSON) ───────────────

function parseRawLine(line: string): LangGraphEvent | null {
  const trimmed = line.trim();
  if (!trimmed || trimmed === '[DONE]') return null;
  const json = trimmed.startsWith('data: ') ? trimmed.slice(6).trim() : trimmed;
  if (!json || json === '[DONE]') return null;
  try {
    return JSON.parse(json) as LangGraphEvent;
  } catch {
    return null;
  }
}

// ── Stats ─────────────────────────────────────────────────────────────────────

function computeStats(entries: LogEntry[], t0: number): StreamStats {
  let elapsed_ms = 0;
  let node_count = 0;
  let tool_count = 0;
  let llm_count = 0;
  let token_count = 0;
  let error_count = 0;

  for (const e of entries) {
    if (e.ts_end !== undefined) {
      elapsed_ms = Math.max(elapsed_ms, e.ts_end - t0);
    }
    if (e.kind === 'node') node_count++;
    if (e.kind === 'tool') tool_count++;
    if (e.kind === 'llm') {
      llm_count++;
      token_count += e.token_count ?? 0;
    }
    if (e.status === 'error') error_count++;
  }

  return { elapsed_ms, node_count, tool_count, llm_count, token_count, error_count };
}

// ── Hook ──────────────────────────────────────────────────────────────────────

function useAgentLogStream(
  url: string | undefined,
  staticEvents: LangGraphEvent[] | undefined,
  onCompleteRef: React.RefObject<((entries: LogEntry[]) => void) | undefined>,
  maxEntries: number,
) {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [streamStatus, setStreamStatus] = useState<StreamStatus>('idle');
  const [streamError, setStreamError] = useState<string | null>(null);
  const activeMap = useRef(new Map<string, LogEntry>());
  const seqRef = useRef({ n: 0 });
  const t0Ref = useRef<number>(0);
  const abortRef = useRef<AbortController | null>(null);

  const addOrUpdate = useCallback(
    (ev: LangGraphEvent) => {
      const { entry, isNew } = processLangGraphEvent(ev, activeMap.current, seqRef.current);
      setEntries((prev) => {
        if (isNew) {
          const next = [...prev, entry];
          return next.length > maxEntries ? next.slice(next.length - maxEntries) : next;
        }
        return prev.map((e) => (e.id === entry.id ? { ...entry } : e));
      });
    },
    [maxEntries],
  );

  // Static events mode
  useEffect(() => {
    if (!staticEvents?.length) return;

    activeMap.current.clear();
    seqRef.current = { n: 0 };
    t0Ref.current = staticEvents[0]?.timestamp ?? Date.now();

    const tempActive = new Map<string, LogEntry>();
    const tempSeq = { n: 0 };
    const processed: LogEntry[] = [];

    for (const ev of staticEvents) {
      const { entry, isNew } = processLangGraphEvent(ev, tempActive, tempSeq);
      if (isNew) {
        processed.push(entry);
      } else {
        const idx = processed.findIndex((e) => e.id === entry.id);
        if (idx !== -1) processed[idx] = { ...entry };
      }
    }

    const trimmed =
      processed.length > maxEntries
        ? processed.slice(processed.length - maxEntries)
        : processed;

    setEntries(trimmed);
    setStreamStatus('done');
    onCompleteRef.current?.(trimmed);
  }, [staticEvents, maxEntries, onCompleteRef]);

  // SSE / NDJSON streaming mode
  useEffect(() => {
    if (!url) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    activeMap.current.clear();
    seqRef.current = { n: 0 };
    setEntries([]);
    setStreamError(null);
    setStreamStatus('connecting');
    t0Ref.current = Date.now();

    (async () => {
      try {
        const res = await fetch(url, {
          signal: controller.signal,
          headers: { Accept: 'text/event-stream, application/x-ndjson' },
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        if (!res.body) {
          throw new Error('Response body is null');
        }

        setStreamStatus('streaming');

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';
          for (const line of lines) {
            const ev = parseRawLine(line);
            if (ev) addOrUpdate(ev);
          }
        }

        if (buffer.trim()) {
          const ev = parseRawLine(buffer);
          if (ev) addOrUpdate(ev);
        }

        setStreamStatus('done');
        setEntries((prev) => {
          onCompleteRef.current?.(prev);
          return prev;
        });
      } catch (err: unknown) {
        if (err instanceof Error && err.name === 'AbortError') return;
        const msg =
          err instanceof Error ? err.message : 'Error de stream desconocido';
        setStreamError(msg);
        setStreamStatus('error');
      }
    })();

    return () => {
      controller.abort();
    };
  }, [url, addOrUpdate, onCompleteRef]);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    activeMap.current.clear();
    seqRef.current = { n: 0 };
    setEntries([]);
    setStreamStatus('idle');
    setStreamError(null);
  }, []);

  return { entries, streamStatus, streamError, clear, t0: t0Ref.current };
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function StreamStatusBadge({ status }: { status: StreamStatus }) {
  const MAP: Record<StreamStatus, { label: string; color: string; pulse: boolean }> = {
    idle:       { label: 'INACTIVO',   color: 'var(--text-tertiary)',  pulse: false },
    connecting: { label: 'CONECTANDO', color: 'var(--text-secondary)', pulse: true  },
    streaming:  { label: 'EN VIVO',    color: 'var(--success)',        pulse: true  },
    done:       { label: 'COMPLETO',   color: 'var(--text-tertiary)',  pulse: false },
    error:      { label: 'ERROR',      color: 'var(--danger)',         pulse: false },
  };
  const { label, color, pulse } = MAP[status];

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        fontFamily: 'var(--font-geist-mono)',
        fontSize: '10px',
        letterSpacing: '0.1em',
        color,
      }}
    >
      <span
        aria-hidden="true"
        className={pulse ? 'animate-pulse' : undefined}
        style={{
          display: 'inline-block',
          width: '5px',
          height: '5px',
          borderRadius: '50%',
          background: color,
          flexShrink: 0,
        }}
      />
      {label}
    </span>
  );
}

function StatCell({ label, value }: { label: string; value: string | number }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        fontFamily: 'var(--font-geist-mono)',
        fontSize: '10px',
        letterSpacing: '0.05em',
        flexShrink: 0,
      }}
    >
      <span style={{ color: 'var(--text-tertiary)' }}>{label}</span>
      <span
        style={{
          color: 'var(--text-primary)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {value}
      </span>
    </span>
  );
}

function EmptyState({ status }: { status: StreamStatus }) {
  const containerStyle: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: '6px',
    padding: '32px 16px',
    textAlign: 'center',
  };

  if (status === 'connecting') {
    return (
      <div style={containerStyle}>
        <span
          className="animate-pulse"
          style={{
            fontFamily: 'var(--font-geist-mono)',
            fontSize: '10px',
            letterSpacing: '0.15em',
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
          }}
        >
          CONECTANDO CON LANGGRAPH…
        </span>
      </div>
    );
  }

  if (status === 'idle') {
    return (
      <div style={containerStyle}>
        <span
          style={{
            fontFamily: 'var(--font-geist-mono)',
            fontSize: '10px',
            letterSpacing: '0.15em',
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
          }}
        >
          AGUARDANDO STREAM
        </span>
        <span
          style={{
            fontFamily: 'var(--font-geist-mono)',
            fontSize: '10px',
            color: 'var(--text-tertiary)',
          }}
        >
          Proporciona{' '}
          <code style={{ color: 'var(--text-secondary)' }}>streamUrl</code>
          {' '}o{' '}
          <code style={{ color: 'var(--text-secondary)' }}>events</code>
        </span>
      </div>
    );
  }

  if (status === 'done') {
    return (
      <div style={containerStyle}>
        <span
          style={{
            fontFamily: 'var(--font-geist-mono)',
            fontSize: '10px',
            letterSpacing: '0.15em',
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
          }}
        >
          STREAM COMPLETADO — SIN EVENTOS
        </span>
      </div>
    );
  }

  return null;
}

// ── Main component ────────────────────────────────────────────────────────────

export function AgentLogStream({
  streamUrl,
  events: staticEvents,
  onComplete,
  maxEntries = 500,
  autoScroll = true,
  toolsCollapsed = false,
  className,
  style,
  label = 'AGENT LOG STREAM',
}: AgentLogStreamProps) {
  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  const { entries, streamStatus, streamError, clear, t0 } = useAgentLogStream(
    streamUrl,
    staticEvents,
    onCompleteRef,
    maxEntries,
  );

  const scrollRef = useRef<HTMLDivElement>(null);
  const userScrolledUp = useRef(false);
  const lastScrollTop = useRef(0);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    function onScroll() {
      if (!el) return;
      const scrollingUp = el.scrollTop < lastScrollTop.current;
      lastScrollTop.current = el.scrollTop;
      if (scrollingUp) userScrolledUp.current = true;
      const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 24;
      if (atBottom) userScrolledUp.current = false;
    }

    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    if (!autoScroll || userScrolledUp.current) return;
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [entries, autoScroll]);

  const stats = computeStats(entries, t0);
  const streamT0 = entries[0]?.ts_start ?? t0;
  const isEmpty = entries.length === 0;

  return (
    <div
      className={className}
      style={{
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--bg-base)',
        border: '1px solid var(--border)',
        boxShadow: '2px 2px 0 oklch(0% 0 0)',
        overflow: 'hidden',
        ...style,
      }}
    >
      {/* ── Header bar ────────────────────────────────────────────────── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '0 10px',
          height: '28px',
          background: 'var(--bg-raised)',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-geist-mono)',
            fontSize: '10px',
            fontWeight: 700,
            letterSpacing: '0.1em',
            textTransform: 'uppercase' as const,
            padding: '1px 6px',
            background: 'var(--text-primary)',
            color: 'var(--bg-base)',
            flexShrink: 0,
            lineHeight: '16px',
          }}
        >
          {label}
        </span>

        <StreamStatusBadge status={streamStatus} />

        <span style={{ flex: 1 }} />

        {entries.length > 0 && (
          <button
            type="button"
            onClick={clear}
            style={{
              fontFamily: 'var(--font-geist-mono)',
              fontSize: '9px',
              letterSpacing: '0.1em',
              color: 'var(--text-tertiary)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              textTransform: 'uppercase' as const,
              padding: '2px 4px',
              transition: 'color 0.1s',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.color =
                'var(--text-primary)';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.color =
                'var(--text-tertiary)';
            }}
          >
            LIMPIAR
          </button>
        )}

        <span
          style={{
            fontFamily: 'var(--font-geist-mono)',
            fontSize: '10px',
            color: 'var(--text-tertiary)',
            fontVariantNumeric: 'tabular-nums',
            flexShrink: 0,
          }}
        >
          {entries.length}/{maxEntries}
        </span>
      </div>

      {/* ── Column header ─────────────────────────────────────────────── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '80px 40px 1fr 172px 64px',
          alignItems: 'center',
          padding: '0 8px 0 8px',
          height: '18px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--bg-surface)',
          flexShrink: 0,
        }}
      >
        {(['ELAPSED', 'KIND', 'NAME', 'EVENT', 'STATUS'] as const).map(
          (col, i) => (
            <span
              key={col}
              style={{
                fontFamily: 'var(--font-geist-mono)',
                fontSize: '9px',
                letterSpacing: '0.12em',
                color: 'var(--text-tertiary)',
                paddingLeft: i > 0 ? '8px' : '0',
                borderLeft:
                  i > 0 ? '1px solid var(--border-subtle)' : 'none',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {col}
            </span>
          ),
        )}
      </div>

      {/* ── Log scroll area ────────────────────────────────────────────── */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          minHeight: 0,
          scrollbarWidth: 'thin',
          scrollbarColor: 'var(--border) transparent',
        }}
      >
        {isEmpty ? (
          <EmptyState status={streamStatus} />
        ) : (
          entries.map((entry) => (
            <LogRow
              key={entry.id}
              entry={entry}
              streamT0={streamT0}
              toolsCollapsed={toolsCollapsed}
            />
          ))
        )}
      </div>

      {/* ── Stream error banner ────────────────────────────────────────── */}
      {streamError && (
        <div
          style={{
            padding: '5px 10px',
            borderTop: '1px solid var(--danger-border)',
            background: 'var(--danger-bg)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            flexShrink: 0,
          }}
        >
          <span
            style={{
              fontFamily: 'var(--font-geist-mono)',
              fontSize: '10px',
              letterSpacing: '0.1em',
              color: 'var(--danger)',
              textTransform: 'uppercase' as const,
              flexShrink: 0,
            }}
          >
            STREAM ERR
          </span>
          <span
            style={{
              fontFamily: 'var(--font-geist-mono)',
              fontSize: '11px',
              color: 'var(--text-secondary)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {streamError}
          </span>
        </div>
      )}

      {/* ── Stats bar ─────────────────────────────────────────────────── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          padding: '0 10px',
          height: '24px',
          borderTop: '2px solid var(--border)',
          background: 'var(--bg-surface)',
          flexShrink: 0,
          overflow: 'hidden',
        }}
      >
        <StatCell
          label="ELAPSED"
          value={
            stats.elapsed_ms > 0
              ? `${(stats.elapsed_ms / 1000).toFixed(3)}s`
              : '—'
          }
        />
        <StatCell label="NODES"  value={stats.node_count}  />
        <StatCell label="TOOLS"  value={stats.tool_count}  />
        <StatCell label="LLM"    value={stats.llm_count}   />
        {stats.token_count > 0 && (
          <StatCell
            label="TOKENS"
            value={stats.token_count.toLocaleString()}
          />
        )}
        {stats.error_count > 0 && (
          <span
            style={{
              fontFamily: 'var(--font-geist-mono)',
              fontSize: '10px',
              letterSpacing: '0.05em',
              color: 'var(--danger)',
              flexShrink: 0,
            }}
          >
            {stats.error_count} ERR
          </span>
        )}
        <span style={{ flex: 1 }} />
        <span
          style={{
            fontFamily: 'var(--font-geist-mono)',
            fontSize: '9px',
            letterSpacing: '0.05em',
            color: 'var(--text-tertiary)',
            flexShrink: 0,
          }}
        >
          LANGGRAPH / NJM OS
        </span>
      </div>
    </div>
  );
}

// ── Demo events (realistic NJM OS agent run) ──────────────────────────────────
// Pass to <AgentLogStream events={DEMO_EVENTS} /> for UI testing without backend.

const T = Date.now();

export const DEMO_EVENTS: LangGraphEvent[] = [
  {
    event: 'on_chain_start',
    name: '__start__',
    run_id: 'chn-a1b2c3d4',
    tags: ['langgraph', 'graph'],
    data: { input: { peticion: 'Genera un Business Case para LinkedIn Ads Q2' } },
    timestamp: T,
  },
  {
    event: 'on_chat_model_start',
    name: 'claude-3-5-sonnet-20241022',
    run_id: 'llm-e5f6a7b8',
    parent_ids: ['chn-a1b2c3d4'],
    tags: ['anthropic', 'reasoning'],
    data: {
      input: {
        messages: [
          { role: 'system', content: 'Eres el Agente PM de Disrupt.' },
          { role: 'user',   content: 'Genera un Business Case para LinkedIn Ads Q2' },
        ],
      },
    },
    timestamp: T + 312,
  },
  {
    event: 'on_chat_model_stream',
    name: 'claude-3-5-sonnet-20241022',
    run_id: 'llm-e5f6a7b8',
    parent_ids: ['chn-a1b2c3d4'],
    tags: ['anthropic', 'reasoning'],
    data: { chunk: { content: 'Analizando petición…' } },
    timestamp: T + 847,
  },
  {
    event: 'on_chat_model_end',
    name: 'claude-3-5-sonnet-20241022',
    run_id: 'llm-e5f6a7b8',
    parent_ids: ['chn-a1b2c3d4'],
    tags: ['anthropic', 'reasoning'],
    data: {
      output: {
        content: 'Necesito consultar el Libro Vivo y benchmarks de LinkedIn B2B MX.',
        usage_metadata: { input_tokens: 423, output_tokens: 89, total_tokens: 512 },
      },
    },
    timestamp: T + 1203,
  },
  {
    event: 'on_tool_start',
    name: 'search_libro_vivo',
    run_id: 'tool-c9d0e1f2',
    parent_ids: ['chn-a1b2c3d4'],
    tags: ['rag', 'retriever', 'libro-vivo'],
    data: {
      input: {
        query: 'LinkedIn Ads B2B demand generation canal estrategia ICP',
        top_k: 8,
        filters: { tipo: 'estrategia_canal', estado: 'activo' },
      },
    },
    timestamp: T + 1891,
  },
  {
    event: 'on_tool_end',
    name: 'search_libro_vivo',
    run_id: 'tool-c9d0e1f2',
    parent_ids: ['chn-a1b2c3d4'],
    tags: ['rag', 'retriever', 'libro-vivo'],
    data: {
      output: {
        total_retrieved: 8,
        results: [
          {
            chunk: 'Disrupt prioriza LinkedIn como canal principal de demanda para ICP Director+ en empresas de 50-500 empleados.',
            score: 0.923,
            source: 'libro_vivo/canal_estrategia.md',
          },
          {
            chunk: 'Budget paid social Q1 2026: $2,400 MXN/mes. ROI target: 3.2x en 90 días. Métrica norte: MQLs calificados.',
            score: 0.871,
            source: 'libro_vivo/presupuestos_2026.md',
          },
          {
            chunk: 'Mensajes que convierten en LinkedIn: insight provocador + dato específico + CTA de discovery call.',
            score: 0.848,
            source: 'libro_vivo/mensajes_conversion.md',
          },
        ],
      },
    },
    timestamp: T + 3102,
  },
  {
    event: 'on_tool_start',
    name: 'analyze_market_benchmark',
    run_id: 'tool-a3b4c5d6',
    parent_ids: ['chn-a1b2c3d4'],
    tags: ['analytics', 'benchmark'],
    data: {
      input: {
        sector: 'B2B SaaS MX',
        metrics: ['cpc_linkedin', 'ctr_industria', 'conversion_rate'],
        periodo: 'Q1_2026',
        region: 'LATAM',
      },
    },
    timestamp: T + 3445,
  },
  {
    event: 'on_tool_end',
    name: 'analyze_market_benchmark',
    run_id: 'tool-a3b4c5d6',
    parent_ids: ['chn-a1b2c3d4'],
    tags: ['analytics', 'benchmark'],
    data: {
      output: {
        cpc_promedio_mxn: 28.47,
        ctr_industria_pct: 0.54,
        conversion_rate_benchmark_pct: 2.3,
        leads_proyectados_mes: 14,
        costo_por_mql_mxn: 171.43,
        fuente: 'LinkedIn Campaign Manager Benchmark Report 2025 — LATAM',
      },
    },
    timestamp: T + 4891,
  },
  {
    event: 'on_chain_start',
    name: 'synthesize_deliverable',
    run_id: 'chn-e7f8a9b0',
    parent_ids: ['chn-a1b2c3d4'],
    tags: ['node', 'synthesis'],
    data: {},
    timestamp: T + 5102,
  },
  {
    event: 'on_chat_model_start',
    name: 'claude-3-5-sonnet-20241022',
    run_id: 'llm-c1d2e3f4',
    parent_ids: ['chn-e7f8a9b0'],
    tags: ['anthropic', 'synthesis'],
    data: {
      input: {
        messages: [
          { role: 'system', content: 'Genera el Business Case con formato ADN Disrupt.' },
          { role: 'user',   content: '[contexto libro vivo + benchmarks recuperados]' },
        ],
      },
    },
    timestamp: T + 5219,
  },
  {
    event: 'on_chat_model_stream',
    name: 'claude-3-5-sonnet-20241022',
    run_id: 'llm-c1d2e3f4',
    parent_ids: ['chn-e7f8a9b0'],
    tags: ['anthropic', 'synthesis'],
    data: { chunk: { content: '# Business Case — LinkedIn Ads Q2 2026…' } },
    timestamp: T + 6847,
  },
  {
    event: 'on_chat_model_end',
    name: 'claude-3-5-sonnet-20241022',
    run_id: 'llm-c1d2e3f4',
    parent_ids: ['chn-e7f8a9b0'],
    tags: ['anthropic', 'synthesis'],
    data: {
      output: {
        content: 'Business Case generado con validación ADN Disrupt positiva.',
        usage_metadata: {
          input_tokens: 1847,
          output_tokens: 923,
          total_tokens: 2770,
        },
      },
    },
    timestamp: T + 8203,
  },
  {
    event: 'on_chain_end',
    name: 'synthesize_deliverable',
    run_id: 'chn-e7f8a9b0',
    parent_ids: ['chn-a1b2c3d4'],
    tags: ['node', 'synthesis'],
    data: { output: { status: 'ok', adn_check: true } },
    timestamp: T + 8312,
  },
  {
    event: 'on_chain_end',
    name: '__start__',
    run_id: 'chn-a1b2c3d4',
    tags: ['langgraph', 'graph'],
    data: {
      output: {
        estado_ejecucion: 'LISTO_PARA_FIRMA',
        skill_utilizada: 'business_case_v3',
      },
    },
    timestamp: T + 8891,
  },
];
