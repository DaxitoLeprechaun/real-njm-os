'use client';

import { useState } from 'react';
import type { LogEntryStatus } from './types';

interface ToolPayloadProps {
  input: unknown;
  output: unknown;
  status: LogEntryStatus;
  defaultExpanded: boolean;
}

function formatJSON(val: unknown): string {
  if (val === undefined || val === null) return 'null';
  try {
    return JSON.stringify(val, null, 2);
  } catch {
    return String(val);
  }
}

const INDENT = '52px';

export function ToolPayload({ input, output, status, defaultExpanded }: ToolPayloadProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const accentColor =
    status === 'error'
      ? 'var(--danger)'
      : status === 'ok'
      ? 'var(--success)'
      : 'var(--border)';

  return (
    <div style={{ borderTop: '1px solid var(--border-subtle)' }}>
      {/* Toggle row */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          width: '100%',
          padding: `2px 8px 2px ${INDENT}`,
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontFamily: 'var(--font-geist-mono)',
          fontSize: '9px',
          letterSpacing: '0.15em',
          color: 'var(--text-tertiary)',
          textTransform: 'uppercase',
          textAlign: 'left',
          lineHeight: '18px',
        }}
      >
        <span
          aria-hidden="true"
          style={{
            display: 'inline-block',
            transform: expanded ? 'rotate(90deg)' : 'none',
            transition: 'transform 0.1s ease',
            lineHeight: 1,
            fontSize: '11px',
          }}
        >
          ›
        </span>
        {expanded ? 'COLAPSAR' : 'EXPANDIR'} PAYLOAD
        {status === 'running' && (
          <span
            className="animate-pulse"
            style={{ color: 'var(--text-tertiary)', marginLeft: '6px' }}
          >
            — ESPERANDO RESPUESTA
          </span>
        )}
      </button>

      {/* Payload body */}
      {expanded && (
        <div
          style={{
            paddingLeft: INDENT,
            paddingRight: '8px',
            paddingBottom: '6px',
            background: 'var(--bg-surface)',
          }}
        >
          {/* INPUT block */}
          {input !== undefined && (
            <div style={{ marginBottom: '5px' }}>
              <div
                style={{
                  fontFamily: 'var(--font-geist-mono)',
                  fontSize: '9px',
                  letterSpacing: '0.15em',
                  textTransform: 'uppercase',
                  color: 'var(--text-tertiary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  marginBottom: '3px',
                  paddingTop: '4px',
                }}
              >
                <span
                  aria-hidden="true"
                  style={{
                    display: 'inline-block',
                    width: '8px',
                    height: '1px',
                    background: 'var(--text-tertiary)',
                    flexShrink: 0,
                  }}
                />
                INPUT
              </div>
              <pre
                style={{
                  fontFamily: 'var(--font-geist-mono)',
                  fontSize: '12px',
                  lineHeight: '1.55',
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                  color: 'var(--text-secondary)',
                  borderLeft: '2px solid var(--border)',
                  paddingLeft: '8px',
                  maxHeight: '220px',
                  overflowY: 'auto',
                  scrollbarWidth: 'thin',
                  scrollbarColor: 'var(--border) transparent',
                }}
              >
                {formatJSON(input)}
              </pre>
            </div>
          )}

          {/* OUTPUT block */}
          {output !== undefined ? (
            <div>
              <div
                style={{
                  fontFamily: 'var(--font-geist-mono)',
                  fontSize: '9px',
                  letterSpacing: '0.15em',
                  textTransform: 'uppercase',
                  color: 'var(--text-tertiary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  marginBottom: '3px',
                  paddingTop: '2px',
                }}
              >
                <span
                  aria-hidden="true"
                  style={{
                    display: 'inline-block',
                    width: '8px',
                    height: '1px',
                    background: accentColor,
                    flexShrink: 0,
                  }}
                />
                OUTPUT
              </div>
              <pre
                style={{
                  fontFamily: 'var(--font-geist-mono)',
                  fontSize: '12px',
                  lineHeight: '1.55',
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                  color: 'var(--text-secondary)',
                  borderLeft: `2px solid ${accentColor}`,
                  paddingLeft: '8px',
                  maxHeight: '220px',
                  overflowY: 'auto',
                  scrollbarWidth: 'thin',
                  scrollbarColor: 'var(--border) transparent',
                }}
              >
                {formatJSON(output)}
              </pre>
            </div>
          ) : status === 'running' ? (
            <div
              style={{
                fontFamily: 'var(--font-geist-mono)',
                fontSize: '12px',
                color: 'var(--text-tertiary)',
                borderLeft: '2px solid var(--border)',
                paddingLeft: '8px',
                fontStyle: 'italic',
                paddingTop: '2px',
                paddingBottom: '2px',
              }}
            >
              aguardando respuesta de herramienta…
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
