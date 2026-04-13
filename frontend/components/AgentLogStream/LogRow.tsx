'use client';

import { memo } from 'react';
import type { LogEntry } from './types';
import { ToolPayload } from './ToolPayload';

interface LogRowProps {
  entry: LogEntry;
  /** ts_start of the first entry in the stream — used to compute elapsed */
  streamT0: number;
  toolsCollapsed: boolean;
}

// ── Visual mappings ──────────────────────────────────────────────────────────

const KIND_COLOR: Record<LogEntry['kind'], string> = {
  node:      'var(--text-secondary)',
  tool:      'var(--text-primary)',
  llm:       'var(--success)',
  retriever: 'var(--text-secondary)',
  custom:    'var(--text-tertiary)',
};

const KIND_LABEL: Record<LogEntry['kind'], string> = {
  node:      'NODE',
  tool:      'TOOL',
  llm:       'LLM ',
  retriever: 'RET ',
  custom:    'CUST',
};

// ── Formatters ───────────────────────────────────────────────────────────────

function fmtElapsed(ms: number): string {
  if (ms < 0) ms = 0;
  const s = ms / 1000;
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(3);
  if (m > 0) return `${m}:${sec.padStart(6, '0')}`;
  return `+${sec.padStart(7, '0')}`;
}

function fmtDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms).toString().padStart(4, '0')}ms`;
  return `${(ms / 1000).toFixed(2)}s `;
}

// ── Status indicator ─────────────────────────────────────────────────────────

function StatusCell({
  status,
  delta_ms,
}: {
  status: LogEntry['status'];
  delta_ms?: number;
}) {
  if (status === 'running') {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          fontFamily: 'var(--font-geist-mono)',
          fontSize: '10px',
          letterSpacing: '0.06em',
          color: 'var(--text-tertiary)',
        }}
      >
        <span
          className="animate-pulse"
          aria-hidden="true"
          style={{
            display: 'inline-block',
            width: '5px',
            height: '5px',
            borderRadius: '50%',
            background: 'var(--text-secondary)',
            flexShrink: 0,
          }}
        />
        RUN
      </span>
    );
  }

  if (status === 'stream') {
    return (
      <span
        style={{
          fontFamily: 'var(--font-geist-mono)',
          fontSize: '10px',
          letterSpacing: '0.06em',
          color: 'var(--success)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '3px',
        }}
      >
        LIVE
        <span
          className="animate-pulse"
          aria-hidden="true"
          style={{
            display: 'inline-block',
            width: '4px',
            height: '4px',
            borderRadius: '50%',
            background: 'var(--success)',
            flexShrink: 0,
          }}
        />
      </span>
    );
  }

  if (status === 'error') {
    return (
      <span
        style={{
          fontFamily: 'var(--font-geist-mono)',
          fontSize: '10px',
          letterSpacing: '0.06em',
          color: 'var(--danger)',
        }}
      >
        ERR
      </span>
    );
  }

  // ok
  return (
    <span
      style={{
        fontFamily: 'var(--font-geist-mono)',
        fontSize: '10px',
        letterSpacing: '0.04em',
        color: 'var(--text-tertiary)',
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      {delta_ms !== undefined ? fmtDuration(delta_ms) : 'OK  '}
    </span>
  );
}

// ── Row component ─────────────────────────────────────────────────────────────

export const LogRow = memo(function LogRow({
  entry,
  streamT0,
  toolsCollapsed,
}: LogRowProps) {
  const kindColor = KIND_COLOR[entry.kind];
  const kindLabel = KIND_LABEL[entry.kind];
  const elapsed = entry.ts_start - streamT0;
  const isTool = entry.kind === 'tool';
  const isError = entry.status === 'error';

  const rowBg = isError
    ? 'var(--danger-bg)'
    : isTool && entry.status === 'running'
    ? 'oklch(14% 0.005 60)'
    : 'transparent';

  const leftAccent = isError
    ? '2px solid var(--danger)'
    : isTool
    ? `2px solid ${kindColor}`
    : entry.kind === 'llm'
    ? `2px solid var(--success)`
    : '2px solid transparent';

  return (
    <div
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        background: rowBg,
        borderLeft: leftAccent,
      }}
    >
      {/* ── Primary row — 5 columns ──────────────────────────────────── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '80px 40px 1fr 172px 64px',
          alignItems: 'center',
          minHeight: '22px',
          padding: '1px 8px 1px 6px',
          fontFamily: 'var(--font-geist-mono)',
          fontSize: '11px',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {/* elapsed */}
        <span
          style={{
            color: 'var(--text-tertiary)',
            paddingRight: '8px',
            borderRight: '1px solid var(--border-subtle)',
            letterSpacing: '0.02em',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
          title={`+${elapsed}ms desde inicio`}
        >
          {fmtElapsed(elapsed)}
        </span>

        {/* kind badge */}
        <span
          style={{
            color: kindColor,
            paddingLeft: '8px',
            paddingRight: '6px',
            borderRight: '1px solid var(--border-subtle)',
            letterSpacing: '0.06em',
            fontWeight: entry.kind === 'tool' ? 700 : 400,
            fontSize: '10px',
          }}
        >
          {kindLabel}
        </span>

        {/* name */}
        <span
          style={{
            color: isError ? 'var(--danger)' : 'var(--text-primary)',
            paddingLeft: '8px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            letterSpacing: '0.02em',
          }}
          title={entry.name}
        >
          {entry.name}
        </span>

        {/* event kind */}
        <span
          style={{
            color: 'var(--text-tertiary)',
            paddingLeft: '8px',
            borderLeft: '1px solid var(--border-subtle)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            fontSize: '10px',
            letterSpacing: '0.03em',
          }}
          title={entry.event}
        >
          {entry.event}
        </span>

        {/* status */}
        <span
          style={{
            paddingLeft: '8px',
            borderLeft: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <StatusCell status={entry.status} delta_ms={entry.delta_ms} />
        </span>
      </div>

      {/* ── Tags strip ───────────────────────────────────────────────── */}
      {entry.tags.length > 0 && (
        <div
          style={{
            paddingLeft: '134px',
            paddingBottom: '3px',
            paddingRight: '8px',
            display: 'flex',
            gap: '3px',
            flexWrap: 'wrap',
          }}
        >
          {entry.tags.map((tag) => (
            <span
              key={tag}
              style={{
                fontFamily: 'var(--font-geist-mono)',
                fontSize: '9px',
                letterSpacing: '0.08em',
                color: 'var(--text-tertiary)',
                border: '1px solid var(--border-subtle)',
                padding: '0 3px',
                background: 'var(--bg-raised)',
                lineHeight: '14px',
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* ── Token count strip (LLM only) ─────────────────────────────── */}
      {entry.kind === 'llm' && entry.token_count !== undefined && (
        <div
          style={{
            paddingLeft: '134px',
            paddingBottom: '3px',
            fontFamily: 'var(--font-geist-mono)',
            fontSize: '10px',
            color: 'var(--success)',
            letterSpacing: '0.04em',
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {entry.token_count.toLocaleString()} tokens
        </div>
      )}

      {/* ── run_id strip (always shown, tiny) ────────────────────────── */}
      <div
        style={{
          paddingLeft: '134px',
          paddingBottom: '2px',
          fontFamily: 'var(--font-geist-mono)',
          fontSize: '9px',
          letterSpacing: '0.04em',
          color: 'var(--text-tertiary)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          paddingRight: '8px',
        }}
        title={entry.run_id}
      >
        run_id: {entry.run_id}
      </div>

      {/* ── Tool payload (collapsible) ────────────────────────────────── */}
      {isTool && (
        <ToolPayload
          input={entry.input}
          output={entry.output}
          status={entry.status}
          defaultExpanded={!toolsCollapsed}
        />
      )}
    </div>
  );
});
