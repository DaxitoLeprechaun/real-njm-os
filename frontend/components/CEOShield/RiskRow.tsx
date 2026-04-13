'use client';

import { memo } from 'react';
import type { DetectedRisk, RiskLevel } from './types';

// ── Risk level config ─────────────────────────────────────────────────────────

const LEVEL_COLOR: Record<RiskLevel, string> = {
  CRITICAL: '#FF0000',
  HIGH:     '#D97706',
  MEDIUM:   'var(--text-secondary)',
};

const LEVEL_BG: Record<RiskLevel, string> = {
  CRITICAL: 'rgba(255,0,0,0.05)',
  HIGH:     'rgba(217,119,6,0.05)',
  MEDIUM:   'transparent',
};

const LEVEL_BORDER: Record<RiskLevel, string> = {
  CRITICAL: '2px solid #FF0000',
  HIGH:     '2px solid #D97706',
  MEDIUM:   '2px solid var(--border)',
};

function fmtEvidence(val: unknown): string {
  if (val === undefined || val === null) return '';
  try {
    return JSON.stringify(val, null, 2);
  } catch {
    return String(val);
  }
}

interface RiskRowProps {
  risk: DetectedRisk;
  index: number;
}

export const RiskRow = memo(function RiskRow({ risk, index }: RiskRowProps) {
  const color  = LEVEL_COLOR[risk.level];
  const bg     = LEVEL_BG[risk.level];
  const border = LEVEL_BORDER[risk.level];

  return (
    <div
      style={{
        display:        'grid',
        gridTemplateColumns: '80px 100px 1fr',
        gap:            '0',
        background:     bg,
        borderLeft:     border,
        borderBottom:   '1px solid var(--border-subtle)',
        alignItems:     'stretch',
      }}
    >
      {/* Index */}
      <div
        style={{
          display:        'flex',
          alignItems:     'center',
          justifyContent: 'center',
          borderRight:    '1px solid var(--border-subtle)',
          padding:        '8px 0',
        }}
      >
        <span
          style={{
            fontFamily:         'var(--font-geist-mono)',
            fontSize:           '18px',
            fontWeight:         900,
            color,
            fontVariantNumeric: 'tabular-nums',
            letterSpacing:      '-0.04em',
            lineHeight:         1,
          }}
        >
          {String(index + 1).padStart(2, '0')}
        </span>
      </div>

      {/* Level + category */}
      <div
        style={{
          display:        'flex',
          flexDirection:  'column',
          justifyContent: 'center',
          gap:            '3px',
          padding:        '8px 10px',
          borderRight:    '1px solid var(--border-subtle)',
        }}
      >
        <span
          style={{
            fontFamily:     'var(--font-geist-mono)',
            fontSize:       '10px',
            fontWeight:     700,
            letterSpacing:  '0.1em',
            textTransform:  'uppercase' as const,
            color,
          }}
        >
          {risk.level}
        </span>
        <span
          style={{
            fontFamily:     'var(--font-geist-mono)',
            fontSize:       '9px',
            letterSpacing:  '0.08em',
            textTransform:  'uppercase' as const,
            color:          'var(--text-tertiary)',
          }}
        >
          {risk.category}
        </span>
      </div>

      {/* Description + evidence */}
      <div
        style={{
          display:        'flex',
          flexDirection:  'column',
          justifyContent: 'center',
          gap:            '4px',
          padding:        '8px 12px',
        }}
      >
        <span
          style={{
            fontFamily:     'var(--font-geist-mono)',
            fontSize:       '12px',
            color:          'var(--text-primary)',
            lineHeight:     1.45,
            letterSpacing:  '0.01em',
          }}
        >
          {risk.description}
        </span>

        {risk.evidence !== undefined && (
          <details>
            <summary
              style={{
                cursor:         'pointer',
                listStyle:      'none',
                userSelect:     'none' as const,
                fontFamily:     'var(--font-geist-mono)',
                fontSize:       '9px',
                letterSpacing:  '0.1em',
                textTransform:  'uppercase' as const,
                color:          'var(--text-tertiary)',
              }}
            >
              [ VER EVIDENCIA TÉCNICA ]
            </summary>
            <pre
              style={{
                fontFamily:     'var(--font-geist-mono)',
                fontSize:       '11px',
                lineHeight:     1.5,
                margin:         '4px 0 0 0',
                padding:        '6px 8px',
                borderLeft:     `1px solid ${color}`,
                color:          'var(--text-secondary)',
                whiteSpace:     'pre-wrap',
                wordBreak:      'break-all',
                maxHeight:      '120px',
                overflowY:      'auto',
                scrollbarWidth: 'thin',
                background:     'var(--bg-surface)',
              }}
            >
              {fmtEvidence(risk.evidence)}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
});
