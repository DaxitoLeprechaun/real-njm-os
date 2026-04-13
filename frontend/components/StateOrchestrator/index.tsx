'use client';

import type { GraphExecutionState, StateOrchestratorProps } from './types';
import { StepRow } from './StepRow';

// ── Blink cursor keyframe — injected once, scoped to this component ───────────
// Movement: 1 (static) — only this cursor is animated per explicit spec.
const BLINK_STYLE = `
@keyframes njm-blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}
.njm-blink-cursor {
  animation: njm-blink 1s step-end infinite;
}
`;

// ── Formatters ────────────────────────────────────────────────────────────────

function fmtTimestamp(ts: number): string {
  return new Date(ts).toLocaleString('es-MX', {
    dateStyle:              'short',
    timeStyle:              'medium',
    hour12:                 false,
  });
}

function fmtElapsed(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(2)}s`;
  const m = Math.floor(ms / 60_000);
  const s = ((ms % 60_000) / 1000).toFixed(1);
  return `${m}m ${s}s`;
}

// ── Header status config ──────────────────────────────────────────────────────

const GRAPH_STATUS_COLOR: Record<GraphExecutionState['status'], string> = {
  running:     'var(--success)',
  done:        'var(--text-secondary)',
  error:       'var(--danger)',
  interrupted: '#D97706',
};

const GRAPH_STATUS_LABEL: Record<GraphExecutionState['status'], string> = {
  running:     'RUNNING',
  done:        'DONE',
  error:       'ERROR',
  interrupted: 'INTERRUPTED',
};

// ── Step counts for summary bar ───────────────────────────────────────────────

function computeSummary(state: GraphExecutionState) {
  let thinking = 0;
  let success  = 0;
  let warning  = 0;
  let error    = 0;

  for (const step of state.steps) {
    if (step.status === 'thinking') thinking++;
    else if (step.status === 'success') success++;
    else if (step.status === 'warning') warning++;
    else if (step.status === 'error') error++;
  }

  const elapsed =
    state.steps.length > 0 && state.steps[state.steps.length - 1].ended_at
      ? (state.steps[state.steps.length - 1].ended_at as number) - state.created_at
      : Date.now() - state.created_at;

  return { thinking, success, warning, error, elapsed };
}

// ── Column header labels ──────────────────────────────────────────────────────

const COL_LABELS = ['SEQ', 'NODE', 'TYPE', 'STATE', 'DUR'] as const;
const COL_WIDTHS = '28px 1fr 44px 120px 80px';

// ── StateOrchestrator ─────────────────────────────────────────────────────────

export function StateOrchestrator({
  state,
  showSnapshots = true,
  className,
  style,
}: StateOrchestratorProps) {
  const statusColor = GRAPH_STATUS_COLOR[state.status];
  const statusLabel = GRAPH_STATUS_LABEL[state.status];
  const summary     = computeSummary(state);

  return (
    <>
      {/* Inject blink keyframe once — scoped, no globals pollution */}
      <style>{BLINK_STYLE}</style>

      <div
        className={className}
        style={{
          display:        'flex',
          flexDirection:  'column',
          background:     'var(--bg-base)',
          border:         '1px solid var(--border)',
          boxShadow:      '2px 2px 0 oklch(0% 0 0)',
          overflow:       'hidden',
          ...style,
        }}
      >
        {/* ── Title bar ───────────────────────────────────────────── */}
        <div
          style={{
            display:          'flex',
            alignItems:       'center',
            gap:              '10px',
            padding:          '0 10px',
            height:           '26px',
            background:       'var(--bg-raised)',
            borderBottom:     '1px solid var(--border)',
            flexShrink:       0,
          }}
        >
          <span
            style={{
              fontFamily:     'var(--font-geist-mono)',
              fontSize:       '10px',
              fontWeight:     700,
              letterSpacing:  '0.1em',
              textTransform:  'uppercase' as const,
              padding:        '0 6px',
              lineHeight:     '16px',
              background:     'var(--text-primary)',
              color:          'var(--bg-base)',
              flexShrink:     0,
            }}
          >
            STATE ORCHESTRATOR
          </span>

          <span
            style={{
              display:        'inline-flex',
              alignItems:     'center',
              gap:            '5px',
              fontFamily:     'var(--font-geist-mono)',
              fontSize:       '10px',
              letterSpacing:  '0.1em',
              color:          statusColor,
            }}
          >
            <span
              aria-hidden="true"
              style={{
                display:        'inline-block',
                width:          '5px',
                height:         '5px',
                borderRadius:   '50%',
                background:     statusColor,
                flexShrink:     0,
              }}
            />
            {statusLabel}
          </span>

          <span style={{ flex: 1 }} />

          <span
            style={{
              fontFamily:     'var(--font-geist-mono)',
              fontSize:       '10px',
              color:          'var(--text-tertiary)',
              letterSpacing:  '0.03em',
              fontVariantNumeric: 'tabular-nums',
              flexShrink:     0,
            }}
          >
            {state.steps.length} STEPS
          </span>
        </div>

        {/* ── Graph identity bar ──────────────────────────────────── */}
        <div
          style={{
            display:        'flex',
            alignItems:     'center',
            flexWrap:       'wrap',
            gap:            '0 14px',
            padding:        '2px 10px',
            borderBottom:   '1px solid var(--border-subtle)',
            background:     'var(--bg-surface)',
            flexShrink:     0,
          }}
        >
          {[
            ['graph',   state.graph_id],
            ['thread',  state.thread_id],
            ['run',     state.run_id.slice(0, 12) + '…'],
            ['created', fmtTimestamp(state.created_at)],
            ['updated', fmtTimestamp(state.updated_at)],
          ].map(([k, v]) => (
            <span
              key={k}
              style={{
                fontFamily:         'var(--font-geist-mono)',
                fontSize:           '10px',
                fontVariantNumeric: 'tabular-nums',
                whiteSpace:         'nowrap',
                lineHeight:         '18px',
              }}
            >
              <span style={{ color: 'var(--text-tertiary)' }}>{k}: </span>
              <span style={{ color: 'var(--text-secondary)' }}>{v}</span>
            </span>
          ))}

          {/* Graph-level metadata extras */}
          {state.metadata &&
            Object.entries(state.metadata).map(([k, v]) => (
              <span
                key={k}
                style={{
                  fontFamily:         'var(--font-geist-mono)',
                  fontSize:           '10px',
                  fontVariantNumeric: 'tabular-nums',
                  whiteSpace:         'nowrap',
                  lineHeight:         '18px',
                }}
              >
                <span style={{ color: 'var(--text-tertiary)' }}>{k}: </span>
                <span style={{ color: 'var(--text-secondary)' }}>
                  {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                </span>
              </span>
            ))}
        </div>

        {/* ── Column headers ──────────────────────────────────────── */}
        <div
          style={{
            display:              'grid',
            gridTemplateColumns:  COL_WIDTHS,
            alignItems:           'center',
            padding:              '0 8px 0 8px',
            height:               '18px',
            borderBottom:         '1px solid var(--border)',
            background:           'var(--bg-surface)',
            flexShrink:           0,
          }}
        >
          {COL_LABELS.map((col, i) => (
            <span
              key={col}
              style={{
                fontFamily:     'var(--font-geist-mono)',
                fontSize:       '9px',
                letterSpacing:  '0.12em',
                color:          'var(--text-tertiary)',
                paddingLeft:    i > 0 ? '6px' : '0',
                borderLeft:     i > 0 ? '1px solid var(--border-subtle)' : 'none',
                overflow:       'hidden',
                textOverflow:   'ellipsis',
                whiteSpace:     'nowrap',
              }}
            >
              {col}
            </span>
          ))}
        </div>

        {/* ── Steps list ──────────────────────────────────────────── */}
        <div
          style={{
            flex:           1,
            overflowY:      'auto',
            overflowX:      'hidden',
            minHeight:      0,
            scrollbarWidth: 'thin',
            scrollbarColor: 'var(--border) transparent',
          }}
        >
          {state.steps.length === 0 ? (
            <div
              style={{
                display:        'flex',
                alignItems:     'center',
                justifyContent: 'center',
                height:         '80px',
                fontFamily:     'var(--font-geist-mono)',
                fontSize:       '10px',
                letterSpacing:  '0.15em',
                color:          'var(--text-tertiary)',
                textTransform:  'uppercase' as const,
              }}
            >
              SIN PASOS REGISTRADOS
            </div>
          ) : (
            state.steps.map((step) => (
              <StepRow
                key={step.run_id + step.seq}
                step={step}
                showSnapshots={showSnapshots}
              />
            ))
          )}
        </div>

        {/* ── Summary / stats bar ─────────────────────────────────── */}
        <div
          style={{
            display:        'flex',
            alignItems:     'center',
            gap:            '16px',
            padding:        '0 10px',
            height:         '24px',
            borderTop:      '2px solid var(--border)',
            background:     'var(--bg-surface)',
            flexShrink:     0,
            overflow:       'hidden',
          }}
        >
          {[
            { label: 'ELAPSED',  value: fmtElapsed(summary.elapsed),              color: 'var(--text-primary)'   },
            { label: 'THINKING', value: summary.thinking,                          color: 'var(--text-secondary)' },
            { label: 'SUCCESS',  value: summary.success,                           color: '#00FF00'                },
            { label: 'WARNING',  value: summary.warning,                           color: '#D97706'                },
          ].map(({ label, value, color }) => (
            <span
              key={label}
              style={{
                display:            'inline-flex',
                alignItems:         'center',
                gap:                '5px',
                fontFamily:         'var(--font-geist-mono)',
                fontSize:           '10px',
                letterSpacing:      '0.05em',
                flexShrink:         0,
              }}
            >
              <span style={{ color: 'var(--text-tertiary)' }}>{label}</span>
              <span style={{ color, fontVariantNumeric: 'tabular-nums' }}>{value}</span>
            </span>
          ))}

          {summary.error > 0 && (
            <span
              style={{
                fontFamily:     'var(--font-geist-mono)',
                fontSize:       '10px',
                letterSpacing:  '0.05em',
                color:          'var(--danger)',
                flexShrink:     0,
              }}
            >
              {summary.error} ERR
            </span>
          )}

          <span style={{ flex: 1 }} />

          <span
            style={{
              fontFamily:     'var(--font-geist-mono)',
              fontSize:       '9px',
              letterSpacing:  '0.05em',
              color:          'var(--text-tertiary)',
              flexShrink:     0,
            }}
          >
            NJM OS / LANGGRAPH
          </span>
        </div>
      </div>
    </>
  );
}

// ── Demo state — realistic NJM OS PM agent run ────────────────────────────────

const T = Date.now() - 9_100;

export const DEMO_STATE: GraphExecutionState = {
  graph_id:   'pm_agent_v3',
  thread_id:  'thr-2a4f8c1e-9b3d',
  run_id:     'run-7f2e5d1a-4c8b-11ef-9f3a-0242ac130003',
  status:     'running',
  created_at: T,
  updated_at: T + 9_100,
  metadata: {
    skill_version: 'business_case_v3',
    trigger:       'user_request',
  },
  steps: [
    {
      seq:       0,
      node_name: '__start__',
      node_type: 'router',
      status:    'success',
      run_id:    'chn-a1b2c3d4-0000',
      started_at: T,
      ended_at:   T + 148,
      duration_ms: 148,
      input_snapshot: {
        peticion: 'Genera un Business Case para LinkedIn Ads Q2',
        usuario:  'juan@disrupt.mx',
      },
      output_snapshot: {
        next_node: 'parse_intent',
        confidence: 0.97,
      },
      metadata: {
        tags:          ['langgraph', 'graph'],
        checkpoint_id: 'ckpt-00000000-init',
        adn_check:     true,
      },
    },
    {
      seq:       1,
      node_name: 'parse_intent',
      node_type: 'agent',
      status:    'success',
      run_id:    'llm-b2c3d4e5-0001',
      parent_run_id: 'chn-a1b2c3d4-0000',
      started_at:  T + 148,
      ended_at:    T + 1_203,
      duration_ms: 1_055,
      input_snapshot: {
        messages: [
          { role: 'user', content: 'Genera un Business Case para LinkedIn Ads Q2' },
        ],
      },
      output_snapshot: {
        intent:         'business_case',
        deliverable:    'linkedin_ads_q2',
        framework:      'business_case_v3',
        confidence:     0.94,
      },
      metadata: {
        model:          'claude-3-5-sonnet-20241022',
        token_count:    312,
        tags:           ['anthropic', 'intent-classification'],
        checkpoint_id:  'ckpt-00000001-parse',
        adn_check:      true,
        attempt:        1,
        max_attempts:   3,
      },
    },
    {
      seq:       2,
      node_name: 'search_libro_vivo',
      node_type: 'tool',
      status:    'success',
      run_id:    'tool-c3d4e5f6-0002',
      parent_run_id: 'chn-a1b2c3d4-0000',
      started_at:  T + 1_203,
      ended_at:    T + 3_102,
      duration_ms: 1_899,
      input_snapshot: {
        query:   'LinkedIn Ads B2B demand generation canal ICP Director+',
        top_k:   8,
        filters: { tipo: 'estrategia_canal', estado: 'activo' },
      },
      output_snapshot: {
        total_retrieved: 8,
        top_score:       0.923,
        sources: [
          'libro_vivo/canal_estrategia.md',
          'libro_vivo/presupuestos_2026.md',
          'libro_vivo/mensajes_conversion.md',
        ],
      },
      metadata: {
        tags:          ['rag', 'retriever', 'libro-vivo'],
        checkpoint_id: 'ckpt-00000002-rag',
        token_count:   0,
        attempt:       1,
        max_attempts:  3,
      },
    },
    {
      seq:       3,
      node_name: 'fetch_market_benchmarks',
      node_type: 'tool',
      status:    'warning',
      run_id:    'tool-d4e5f6a7-0003',
      parent_run_id: 'chn-a1b2c3d4-0000',
      started_at:  T + 3_102,
      ended_at:    T + 5_447,
      duration_ms: 2_345,
      input_snapshot: {
        sector:  'B2B SaaS MX',
        metrics: ['cpc_linkedin', 'ctr_industria', 'conversion_rate'],
        periodo: 'Q1_2026',
      },
      output_snapshot: {
        cpc_promedio_mxn:              28.47,
        ctr_industria_pct:             0.54,
        conversion_rate_benchmark_pct: 2.3,
        fuente:                        'LinkedIn Campaign Manager Benchmark Report 2025',
      },
      metadata: {
        tags:          ['analytics', 'benchmark', 'external-api'],
        checkpoint_id: 'ckpt-00000003-bench',
        attempt:       2,
        max_attempts:  3,
        error_message: 'Rate limit hit on attempt 1 — retried with exponential backoff (1.5s)',
      },
    },
    {
      seq:       4,
      node_name: 'agent_reasoning',
      node_type: 'agent',
      status:    'thinking',
      run_id:    'llm-e5f6a7b8-0004',
      parent_run_id: 'chn-a1b2c3d4-0000',
      started_at:  T + 5_447,
      metadata: {
        model:         'claude-3-5-sonnet-20241022',
        tags:          ['anthropic', 'synthesis', 'reasoning'],
        checkpoint_id: 'ckpt-00000004-reason',
        attempt:       1,
        max_attempts:  3,
      },
    },
  ],
};
