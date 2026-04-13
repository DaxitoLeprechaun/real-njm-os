'use client';

import { memo } from 'react';
import type { AgentNodeStep, NodeType, OrchestratorVisualState } from './types';

// ── Constants ─────────────────────────────────────────────────────────────────

const NODE_TYPE_LABEL: Record<NodeType, string> = {
  agent:     'AGNT',
  response:  'RESP',
  retry:     'RETR',
  tool:      'TOOL',
  router:    'ROUT',
  subgraph:  'SUBG',
};

// ── Style maps — Density 9, dark NJM OS palette ───────────────────────────────

const ROW_BG: Record<OrchestratorVisualState, string> = {
  thinking: 'transparent',
  success:  'rgba(0, 255, 0, 0.02)',
  warning:  '#FEF3C7',   // amber island — deliberately light in dark context
  error:    'var(--danger-bg)',
};

const ROW_BORDER: Record<OrchestratorVisualState, string> = {
  thinking: '1px solid transparent',
  success:  '1px solid #00FF00',
  warning:  '1px solid #D97706',
  error:    '1px solid var(--danger-border)',
};

const LEFT_ACCENT: Record<OrchestratorVisualState, string> = {
  thinking: '2px solid var(--border-subtle)',
  success:  '2px solid #00FF00',
  warning:  '2px solid #D97706',
  error:    '2px solid var(--danger)',
};

// Text colors per visual state — must handle amber's light bg
const PRIMARY_TEXT: Record<OrchestratorVisualState, string> = {
  thinking: 'var(--text-secondary)',  // technical gray
  success:  'var(--text-primary)',
  warning:  '#111111',                // black on amber bg
  error:    'var(--danger)',
};

const META_TEXT: Record<OrchestratorVisualState, string> = {
  thinking: 'var(--text-tertiary)',
  success:  'var(--text-tertiary)',
  warning:  '#6B4C00',               // dark amber for meta on amber bg
  error:    'var(--danger)',
};

const TYPE_TAG_COLOR: Record<OrchestratorVisualState, string> = {
  thinking: 'var(--text-tertiary)',
  success:  '#00FF00',
  warning:  '#92400E',
  error:    'var(--danger)',
};

// ── Formatters ────────────────────────────────────────────────────────────────

function fmtTime(ts: number): string {
  return new Date(ts).toLocaleTimeString('es-MX', {
    hour:        '2-digit',
    minute:      '2-digit',
    second:      '2-digit',
    fractionalSecondDigits: 3,
    hour12:      false,
  });
}

function fmtDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms).toString().padStart(4, '0')}ms`;
  return `${(ms / 1000).toFixed(3)}s`;
}

function fmtRunId(id: string): string {
  return id.length > 16 ? `${id.slice(0, 8)}…${id.slice(-4)}` : id;
}

function fmtJSON(val: unknown): string {
  try {
    return JSON.stringify(val, null, 2);
  } catch {
    return String(val);
  }
}

// ── VERIFIED_BY_OS Badge ──────────────────────────────────────────────────────

function VerifiedBadge() {
  return (
    <span
      style={{
        display:        'inline-flex',
        alignItems:     'center',
        fontFamily:     'var(--font-geist-mono)',
        fontSize:       '9px',
        letterSpacing:  '0.12em',
        color:          '#00FF00',
        border:         '1px solid #00FF00',
        padding:        '0 5px',
        lineHeight:     '14px',
        flexShrink:     0,
        background:     'rgba(0,255,0,0.04)',
        textTransform:  'uppercase' as const,
      }}
    >
      VERIFIED_BY_OS
    </span>
  );
}

// ── Blinking cursor — Terminal Active ─────────────────────────────────────────

function BlinkCursor() {
  return (
    <span
      aria-hidden="true"
      className="njm-blink-cursor"
      style={{
        display:        'inline-block',
        width:          '1px',
        height:         '0.82em',
        background:     'var(--text-secondary)',
        verticalAlign:  'text-bottom',
        marginLeft:     '2px',
        flexShrink:     0,
      }}
    />
  );
}

// ── Metadata row ──────────────────────────────────────────────────────────────

function MetaRow({
  step,
  metaColor,
  showSnapshots,
}: {
  step: AgentNodeStep;
  metaColor: string;
  showSnapshots: boolean;
}) {
  const m = step.metadata;

  // Build a flat list of key: value pairs — all data, nothing omitted
  const pairs: [string, string][] = [
    ['run_id',   fmtRunId(step.run_id)],
    ['started',  fmtTime(step.started_at)],
  ];

  if (step.ended_at !== undefined) {
    pairs.push(['ended', fmtTime(step.ended_at)]);
  }
  if (step.parent_run_id) {
    pairs.push(['parent', fmtRunId(step.parent_run_id)]);
  }
  if (m.model) {
    pairs.push(['model', m.model]);
  }
  if (m.token_count !== undefined) {
    pairs.push(['tokens', m.token_count.toLocaleString()]);
  }
  if (m.attempt !== undefined && m.max_attempts !== undefined) {
    pairs.push(['attempt', `${m.attempt}/${m.max_attempts}`]);
  }
  if (m.adn_check !== undefined) {
    pairs.push(['adn_check', m.adn_check ? 'PASS' : 'FAIL']);
  }
  if (m.checkpoint_id) {
    pairs.push(['ckpt', fmtRunId(m.checkpoint_id)]);
  }
  if (m.tags && m.tags.length > 0) {
    pairs.push(['tags', m.tags.join(', ')]);
  }
  if (m.error_message) {
    pairs.push(['error', m.error_message]);
  }

  // Any extra unknown metadata keys
  const reservedKeys = new Set([
    'model', 'token_count', 'attempt', 'max_attempts', 'adn_check',
    'checkpoint_id', 'tags', 'error_message',
  ]);
  for (const [k, v] of Object.entries(m)) {
    if (!reservedKeys.has(k) && v !== undefined && v !== null) {
      pairs.push([k, typeof v === 'object' ? JSON.stringify(v) : String(v)]);
    }
  }

  return (
    <div
      style={{
        paddingLeft:    '30px',
        paddingRight:   '8px',
        paddingBottom:  '3px',
        display:        'flex',
        flexWrap:       'wrap',
        gap:            '0 12px',
        fontFamily:     'var(--font-geist-mono)',
        fontSize:       '10px',
        color:          metaColor,
        letterSpacing:  '0.02em',
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      {pairs.map(([k, v]) => (
        <span key={k} style={{ whiteSpace: 'nowrap' }}>
          <span style={{ opacity: 0.6 }}>{k}:</span>
          <span style={{ marginLeft: '3px' }}>{v}</span>
        </span>
      ))}

      {/* Inline snapshots */}
      {showSnapshots && step.input_snapshot !== undefined && (
        <details
          style={{
            width:      '100%',
            marginTop:  '3px',
          }}
        >
          <summary
            style={{
              cursor:     'pointer',
              listStyle:  'none',
              userSelect: 'none' as const,
              color:      metaColor,
              opacity:    0.7,
              fontSize:   '9px',
              letterSpacing: '0.1em',
              textTransform: 'uppercase' as const,
            }}
          >
            INPUT SNAPSHOT
          </summary>
          <pre
            style={{
              fontFamily:     'var(--font-geist-mono)',
              fontSize:       '11px',
              lineHeight:     '1.5',
              margin:         '2px 0 0 0',
              padding:        '4px 8px',
              borderLeft:     `1px solid ${metaColor}`,
              whiteSpace:     'pre-wrap',
              wordBreak:      'break-all',
              color:          metaColor,
              maxHeight:      '160px',
              overflowY:      'auto',
              scrollbarWidth: 'thin',
            }}
          >
            {fmtJSON(step.input_snapshot)}
          </pre>
        </details>
      )}

      {showSnapshots && step.output_snapshot !== undefined && (
        <details
          style={{
            width:      '100%',
            marginTop:  '3px',
          }}
        >
          <summary
            style={{
              cursor:     'pointer',
              listStyle:  'none',
              userSelect: 'none' as const,
              color:      metaColor,
              opacity:    0.7,
              fontSize:   '9px',
              letterSpacing: '0.1em',
              textTransform: 'uppercase' as const,
            }}
          >
            OUTPUT SNAPSHOT
          </summary>
          <pre
            style={{
              fontFamily:     'var(--font-geist-mono)',
              fontSize:       '11px',
              lineHeight:     '1.5',
              margin:         '2px 0 0 0',
              padding:        '4px 8px',
              borderLeft:     `1px solid ${metaColor}`,
              whiteSpace:     'pre-wrap',
              wordBreak:      'break-all',
              color:          metaColor,
              maxHeight:      '160px',
              overflowY:      'auto',
              scrollbarWidth: 'thin',
            }}
          >
            {fmtJSON(step.output_snapshot)}
          </pre>
        </details>
      )}
    </div>
  );
}

// ── StepRow ───────────────────────────────────────────────────────────────────

interface StepRowProps {
  step: AgentNodeStep;
  showSnapshots: boolean;
}

export const StepRow = memo(function StepRow({ step, showSnapshots }: StepRowProps) {
  const vs = step.status;
  const isThinking = vs === 'thinking';
  const isSuccess  = vs === 'success';
  const isWarning  = vs === 'warning';

  const primaryColor = PRIMARY_TEXT[vs];
  const metaColor    = META_TEXT[vs];
  const typeColor    = TYPE_TAG_COLOR[vs];

  return (
    <div
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        borderLeft:   LEFT_ACCENT[vs],
        border:       isSuccess ? ROW_BORDER[vs] : undefined,
        borderLeftWidth: isSuccess ? '2px' : undefined,
        background:   ROW_BG[vs],
      }}
    >
      {/* ── Primary row ────────────────────────────────────────────── */}
      <div
        style={{
          display:              'grid',
          gridTemplateColumns:  '28px 1fr 44px 120px 80px',
          alignItems:           'center',
          minHeight:            '22px',
          padding:              '1px 8px 1px 6px',
          fontFamily:           'var(--font-geist-mono)',
          fontSize:             '11px',
          fontVariantNumeric:   'tabular-nums',
        }}
      >
        {/* seq */}
        <span
          style={{
            color:          'var(--text-tertiary)',
            fontSize:       '10px',
            letterSpacing:  '0.04em',
          }}
        >
          {String(step.seq).padStart(2, '0')}
        </span>

        {/* node_name + optional blink cursor */}
        <span
          style={{
            color:          primaryColor,
            overflow:       'hidden',
            textOverflow:   'ellipsis',
            whiteSpace:     'nowrap',
            letterSpacing:  '0.02em',
            display:        'flex',
            alignItems:     'center',
            gap:            0,
          }}
          title={step.node_name}
        >
          {step.node_name}
          {isThinking && <BlinkCursor />}
        </span>

        {/* node type badge */}
        <span
          style={{
            color:          typeColor,
            fontSize:       '10px',
            letterSpacing:  '0.08em',
            fontWeight:     isSuccess ? 700 : 400,
            paddingLeft:    '6px',
            borderLeft:     '1px solid var(--border-subtle)',
          }}
        >
          {NODE_TYPE_LABEL[step.node_type]}
        </span>

        {/* status area */}
        <span
          style={{
            display:        'flex',
            alignItems:     'center',
            gap:            '6px',
            paddingLeft:    '8px',
            borderLeft:     '1px solid var(--border-subtle)',
          }}
        >
          {isSuccess && <VerifiedBadge />}

          {isThinking && (
            <span
              style={{
                fontFamily:     'var(--font-geist-mono)',
                fontSize:       '10px',
                letterSpacing:  '0.08em',
                color:          'var(--text-tertiary)',
                textTransform:  'uppercase' as const,
              }}
            >
              PROCESSING
            </span>
          )}

          {isWarning && (
            <span
              style={{
                fontFamily:     'var(--font-geist-mono)',
                fontSize:       '10px',
                letterSpacing:  '0.08em',
                color:          '#92400E',
                textTransform:  'uppercase' as const,
              }}
            >
              RETRY
              {step.metadata.attempt !== undefined && (
                <span style={{ marginLeft: '4px', opacity: 0.8 }}>
                  {step.metadata.attempt}/{step.metadata.max_attempts ?? '?'}
                </span>
              )}
            </span>
          )}

          {vs === 'error' && (
            <span
              style={{
                fontFamily:     'var(--font-geist-mono)',
                fontSize:       '10px',
                letterSpacing:  '0.08em',
                color:          'var(--danger)',
                textTransform:  'uppercase' as const,
              }}
            >
              FAILED
            </span>
          )}
        </span>

        {/* duration */}
        <span
          style={{
            fontFamily:         'var(--font-geist-mono)',
            fontSize:           '10px',
            color:              isWarning ? '#6B4C00' : 'var(--text-tertiary)',
            fontVariantNumeric: 'tabular-nums',
            textAlign:          'right',
            letterSpacing:      '0.02em',
            paddingLeft:        '6px',
            borderLeft:         '1px solid var(--border-subtle)',
          }}
        >
          {step.duration_ms !== undefined
            ? fmtDuration(step.duration_ms)
            : isThinking
            ? '—'
            : '—'}
        </span>
      </div>

      {/* ── Metadata row ───────────────────────────────────────────── */}
      <MetaRow
        step={step}
        metaColor={metaColor}
        showSnapshots={showSnapshots}
      />
    </div>
  );
});
