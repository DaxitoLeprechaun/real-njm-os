'use client';

import { useCallback, useRef, useState } from 'react';
import type {
  CEOShieldProps,
  ShieldActionState,
  RiskLevel,
  HITLInterruptPayload,
} from './types';
import { RiskRow } from './RiskRow';

// ── Constants ─────────────────────────────────────────────────────────────────

const BLOOD_RED    = '#FF0000';
const INK_BLACK    = '#111111';
const PHOSPHOR_WHT = '#EAEAEA';

// Scanline backdrop — simulates CRT electron beam sweep
const SCANLINE_BG = `
  repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.18) 2px,
    rgba(0,0,0,0.18) 4px
  )
`;

// ── Formatters ────────────────────────────────────────────────────────────────

function fmtTimestamp(ts: number): string {
  return new Date(ts).toLocaleString('es-MX', {
    dateStyle: 'short',
    timeStyle: 'medium',
    hour12:    false,
  });
}

function fmtRunId(id: string): string {
  return id.length > 20 ? `${id.slice(0, 10)}…${id.slice(-6)}` : id;
}

// ── Risk severity summary ─────────────────────────────────────────────────────

function riskSeverityLabel(risks: HITLInterruptPayload['risks']): string {
  const hasCritical = risks.some((r) => r.level === 'CRITICAL');
  const hasHigh     = risks.some((r) => r.level === 'HIGH');
  if (hasCritical) return 'NIVEL CRÍTICO';
  if (hasHigh)     return 'NIVEL ALTO';
  return 'NIVEL MEDIO';
}

function riskSeverityColor(risks: HITLInterruptPayload['risks']): string {
  const hasCritical = risks.some((r) => r.level === 'CRITICAL');
  const hasHigh     = risks.some((r) => r.level === 'HIGH');
  if (hasCritical) return BLOOD_RED;
  if (hasHigh)     return '#D97706';
  return 'var(--text-secondary)';
}

// ── Section divider ───────────────────────────────────────────────────────────

function SectionDivider({ label }: { label: string }) {
  return (
    <div
      style={{
        display:      'flex',
        alignItems:   'center',
        gap:          '10px',
        padding:      '0 20px',
        height:       '28px',
        background:   'var(--bg-raised)',
        borderTop:    '1px solid var(--border)',
        borderBottom: '1px solid var(--border)',
        flexShrink:   0,
      }}
    >
      <span
        style={{
          fontFamily:    'var(--font-geist-mono)',
          fontSize:      '9px',
          fontWeight:    700,
          letterSpacing: '0.18em',
          textTransform: 'uppercase' as const,
          color:         'var(--text-tertiary)',
        }}
      >
        {label}
      </span>
      <div style={{ flex: 1, height: '1px', background: 'var(--border-subtle)' }} />
    </div>
  );
}

// ── ADN badge ─────────────────────────────────────────────────────────────────

function ADNBadge({ pass }: { pass: boolean }) {
  const color = pass ? 'var(--success)' : BLOOD_RED;
  return (
    <span
      style={{
        display:       'inline-flex',
        alignItems:    'center',
        gap:           '5px',
        fontFamily:    'var(--font-geist-mono)',
        fontSize:      '10px',
        fontWeight:    700,
        letterSpacing: '0.1em',
        textTransform: 'uppercase' as const,
        color,
        border:        `1px solid ${color}`,
        padding:       '1px 7px',
        background:    `${color}14`,
        flexShrink:    0,
      }}
    >
      ADN {pass ? 'PASS' : 'FAIL'}
    </span>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export function CEOShield({
  payload,
  onApprove,
  onReject,
  onDismiss,
}: CEOShieldProps) {
  const [actionState, setActionState] = useState<ShieldActionState>('idle');
  const [rejectReason, setRejectReason] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isBusy     = actionState === 'approving' || actionState === 'rejecting';
  const isResolved = actionState === 'approved'  || actionState === 'rejected';

  // ── Approve ────────────────────────────────────────────────────────────────
  const handleApprove = useCallback(async () => {
    if (isBusy || isResolved) return;
    setActionState('approving');
    setErrorMessage(null);
    try {
      await onApprove(payload.interrupt_id);
      setActionState('approved');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al aprobar estrategia';
      setErrorMessage(msg);
      setActionState('error');
    }
  }, [isBusy, isResolved, onApprove, payload.interrupt_id]);

  // ── Reject — two-phase ─────────────────────────────────────────────────────
  const handleRejectClick = useCallback(() => {
    if (isBusy || isResolved) return;
    setActionState('awaiting_reject_reason');
    // Focus the textarea on next tick
    setTimeout(() => textareaRef.current?.focus(), 60);
  }, [isBusy, isResolved]);

  const handleRejectConfirm = useCallback(async () => {
    if (isBusy || isResolved) return;
    setActionState('rejecting');
    setErrorMessage(null);
    try {
      await onReject(payload.interrupt_id, rejectReason.trim());
      setActionState('rejected');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al rechazar estrategia';
      setErrorMessage(msg);
      setActionState('awaiting_reject_reason');
    }
  }, [isBusy, isResolved, onReject, payload.interrupt_id, rejectReason]);

  const handleRejectCancel = useCallback(() => {
    if (isBusy) return;
    setActionState('idle');
    setRejectReason('');
  }, [isBusy]);

  const sevColor = riskSeverityColor(payload.risks);

  // ── Overlay ────────────────────────────────────────────────────────────────
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="ceo-shield-title"
      style={{
        position:        'fixed',
        inset:           0,
        zIndex:          9999,
        display:         'flex',
        alignItems:      'center',
        justifyContent:  'center',
        padding:         '16px',
        // Backdrop: dark + scanlines — CRT system halt
        background:      `rgba(0,0,0,0.88)`,
        backgroundImage: SCANLINE_BG,
      }}
    >
      {/* ── Shield panel ───────────────────────────────────────────────── */}
      <div
        style={{
          display:        'flex',
          flexDirection:  'column',
          width:          '100%',
          maxWidth:       '820px',
          maxHeight:      '92vh',
          background:     '#0A0A0A',
          border:         `2px solid ${BLOOD_RED}`,
          // Hard shadow — industrial tactile depth
          boxShadow:      `4px 4px 0 rgba(255,0,0,0.35), 8px 8px 0 rgba(255,0,0,0.12)`,
          overflow:       'hidden',
        }}
      >
        {/* ── Title bar ──────────────────────────────────────────────── */}
        <div
          style={{
            display:          'flex',
            alignItems:       'center',
            gap:              '12px',
            padding:          '0 16px',
            height:           '32px',
            background:       BLOOD_RED,
            borderBottom:     `2px solid ${BLOOD_RED}`,
            flexShrink:       0,
          }}
        >
          <span
            style={{
              fontFamily:    'var(--font-geist-mono)',
              fontSize:      '10px',
              fontWeight:    900,
              letterSpacing: '0.18em',
              textTransform: 'uppercase' as const,
              color:         INK_BLACK,
            }}
          >
            NJM OS / ESCUDO CEO
          </span>

          <span
            style={{
              fontFamily:    'var(--font-geist-mono)',
              fontSize:      '10px',
              letterSpacing: '0.1em',
              color:         `${INK_BLACK}99`,
            }}
          >
            REV 1.0 / {payload.interrupt_type.toUpperCase()}
          </span>

          <span style={{ flex: 1 }} />

          <span
            style={{
              fontFamily:    'var(--font-geist-mono)',
              fontSize:      '10px',
              fontWeight:    700,
              letterSpacing: '0.14em',
              textTransform: 'uppercase' as const,
              color:         INK_BLACK,
            }}
          >
            SYS-HALT
          </span>

          {/* Blinking halt block */}
          <span
            aria-hidden="true"
            className="njm-blink-cursor"
            style={{
              display:    'inline-block',
              width:      '10px',
              height:     '14px',
              background: INK_BLACK,
              flexShrink: 0,
            }}
          />
        </div>

        {/* ── Scrollable body ──────────────────────────────────────────── */}
        <div
          style={{
            flex:           1,
            overflowY:      'auto',
            overflowX:      'hidden',
            scrollbarWidth: 'thin',
            scrollbarColor: `${BLOOD_RED} transparent`,
          }}
        >
          {/* ── Hero: Strategy title ─────────────────────────────────── */}
          <div
            style={{
              padding:      '24px 20px 20px',
              borderBottom: `1px solid var(--border)`,
            }}
          >
            <p
              style={{
                fontFamily:    'var(--font-geist-mono)',
                fontSize:      '9px',
                fontWeight:    700,
                letterSpacing: '0.2em',
                textTransform: 'uppercase' as const,
                color:         BLOOD_RED,
                marginBottom:  '10px',
              }}
            >
              [ APROBACIÓN REQUERIDA / INTERRUPCIÓN DE FLUJO ]
            </p>

            <h1
              id="ceo-shield-title"
              style={{
                fontFamily:    'var(--font-geist-sans)',
                fontSize:      'clamp(1.8rem, 4vw, 3.6rem)',
                fontWeight:    900,
                letterSpacing: '-0.04em',
                lineHeight:    0.9,
                textTransform: 'uppercase' as const,
                color:         PHOSPHOR_WHT,
                margin:        '0 0 14px 0',
              }}
            >
              {payload.title}
            </h1>

            <p
              style={{
                fontFamily:  'var(--font-geist-mono)',
                fontSize:    '13px',
                color:       'var(--text-secondary)',
                lineHeight:  1.6,
                maxWidth:    '64ch',
                margin:      0,
              }}
            >
              {payload.strategy_summary}
            </p>
          </div>

          {/* ── Proposed action ──────────────────────────────────────── */}
          <SectionDivider label="ACCIÓN PROPUESTA POR EL AGENTE" />
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
            <div
              style={{
                display:       'flex',
                alignItems:    'flex-start',
                gap:           '12px',
              }}
            >
              <span
                aria-hidden="true"
                style={{
                  fontFamily:    'var(--font-geist-mono)',
                  fontSize:      '18px',
                  color:         BLOOD_RED,
                  lineHeight:    1,
                  flexShrink:    0,
                  marginTop:     '2px',
                }}
              >
                ///
              </span>
              <p
                style={{
                  fontFamily:  'var(--font-geist-mono)',
                  fontSize:    '13px',
                  color:       PHOSPHOR_WHT,
                  lineHeight:  1.6,
                  margin:      0,
                }}
              >
                {payload.proposed_action}
              </p>
            </div>

            {(payload.budget_impact || payload.time_impact) && (
              <div
                style={{
                  display:       'flex',
                  gap:           '24px',
                  marginTop:     '12px',
                  paddingTop:    '12px',
                  borderTop:     '1px solid var(--border-subtle)',
                  flexWrap:      'wrap',
                }}
              >
                {payload.budget_impact && (
                  <span
                    style={{
                      fontFamily:    'var(--font-geist-mono)',
                      fontSize:      '11px',
                      color:         'var(--text-secondary)',
                    }}
                  >
                    <span style={{ color: 'var(--text-tertiary)', letterSpacing: '0.1em' }}>
                      IMPACTO PRESUPUESTAL:{' '}
                    </span>
                    {payload.budget_impact}
                  </span>
                )}
                {payload.time_impact && (
                  <span
                    style={{
                      fontFamily:    'var(--font-geist-mono)',
                      fontSize:      '11px',
                      color:         'var(--text-secondary)',
                    }}
                  >
                    <span style={{ color: 'var(--text-tertiary)', letterSpacing: '0.1em' }}>
                      IMPACTO TEMPORAL:{' '}
                    </span>
                    {payload.time_impact}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* ── Risk list ─────────────────────────────────────────────── */}
          <SectionDivider
            label={`RIESGOS DETECTADOS [${payload.risks.length}] — ${riskSeverityLabel(payload.risks)}`}
          />

          {payload.risks.length === 0 ? (
            <div
              style={{
                padding:       '16px 20px',
                fontFamily:    'var(--font-geist-mono)',
                fontSize:      '11px',
                color:         'var(--text-tertiary)',
                letterSpacing: '0.1em',
                textTransform: 'uppercase' as const,
                borderBottom:  '1px solid var(--border)',
              }}
            >
              SIN RIESGOS DETECTADOS
            </div>
          ) : (
            <div style={{ borderBottom: '1px solid var(--border)' }}>
              {payload.risks.map((risk, i) => (
                <RiskRow key={risk.id} risk={risk} index={i} />
              ))}
            </div>
          )}

          {/* ── Technical metadata ────────────────────────────────────── */}
          <SectionDivider label="METADATOS TÉCNICOS" />
          <div
            style={{
              display:        'flex',
              flexWrap:       'wrap',
              gap:            '0 16px',
              padding:        '8px 20px',
              borderBottom:   '1px solid var(--border)',
            }}
          >
            {[
              ['interrupt_id', fmtRunId(payload.interrupt_id)],
              ['thread_id',    fmtRunId(payload.thread_id)],
              ['run_id',       fmtRunId(payload.run_id)],
              ['node',         payload.node_name],
              ['type',         payload.interrupt_type],
              ['created',      fmtTimestamp(payload.created_at)],
            ].map(([k, v]) => (
              <span
                key={k}
                style={{
                  fontFamily:         'var(--font-geist-mono)',
                  fontSize:           '10px',
                  fontVariantNumeric: 'tabular-nums',
                  whiteSpace:         'nowrap',
                  lineHeight:         '20px',
                }}
              >
                <span style={{ color: 'var(--text-tertiary)' }}>{k}: </span>
                <span style={{ color: 'var(--text-secondary)' }}>{v}</span>
              </span>
            ))}

            {Object.entries(payload.metadata).map(([k, v]) => (
              <span
                key={k}
                style={{
                  fontFamily:         'var(--font-geist-mono)',
                  fontSize:           '10px',
                  fontVariantNumeric: 'tabular-nums',
                  whiteSpace:         'nowrap',
                  lineHeight:         '20px',
                }}
              >
                <span style={{ color: 'var(--text-tertiary)' }}>{k}: </span>
                <span style={{ color: 'var(--text-secondary)' }}>
                  {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                </span>
              </span>
            ))}

            <span style={{ display: 'flex', alignItems: 'center', lineHeight: '20px' }}>
              <ADNBadge pass={payload.adn_check} />
            </span>
          </div>

          {/* ── Resolved confirmation banner ──────────────────────────── */}
          {isResolved && (
            <div
              style={{
                margin:        '16px 20px',
                padding:       '14px 16px',
                border:        `2px solid ${actionState === 'approved' ? 'var(--success)' : BLOOD_RED}`,
                background:    actionState === 'approved'
                  ? 'var(--success-bg)'
                  : 'rgba(255,0,0,0.06)',
                display:       'flex',
                alignItems:    'center',
                justifyContent:'space-between',
                gap:           '12px',
                flexWrap:      'wrap',
              }}
            >
              <span
                style={{
                  fontFamily:    'var(--font-geist-mono)',
                  fontSize:      '12px',
                  fontWeight:    700,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase' as const,
                  color:         actionState === 'approved'
                    ? 'var(--success)'
                    : BLOOD_RED,
                }}
              >
                {actionState === 'approved'
                  ? '[ ESTRATEGIA APROBADA — REANUDANDO AGENTE ]'
                  : '[ ESTRATEGIA RECHAZADA — RE-PLANIFICANDO ]'}
              </span>

              {onDismiss && (
                <button
                  type="button"
                  onClick={onDismiss}
                  style={{
                    fontFamily:    'var(--font-geist-mono)',
                    fontSize:      '10px',
                    fontWeight:    700,
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase' as const,
                    padding:       '6px 14px',
                    background:    'transparent',
                    border:        '1px solid var(--border)',
                    color:         'var(--text-secondary)',
                    cursor:        'pointer',
                  }}
                >
                  CERRAR
                </button>
              )}
            </div>
          )}
        </div>

        {/* ── Action footer — always visible, never scrolls away ─────── */}
        <div
          style={{
            background:   'var(--bg-raised)',
            borderTop:    `2px solid ${BLOOD_RED}`,
            padding:      '16px 20px',
            flexShrink:   0,
          }}
        >
          {/* Error banner */}
          {actionState === 'error' && errorMessage && (
            <div
              style={{
                padding:       '8px 12px',
                marginBottom:  '12px',
                border:        `1px solid var(--danger-border)`,
                background:    'var(--danger-bg)',
                display:       'flex',
                alignItems:    'center',
                gap:           '8px',
              }}
            >
              <span
                style={{
                  fontFamily:    'var(--font-geist-mono)',
                  fontSize:      '9px',
                  letterSpacing: '0.12em',
                  textTransform: 'uppercase' as const,
                  color:         'var(--danger)',
                  flexShrink:    0,
                }}
              >
                ERR
              </span>
              <span
                style={{
                  fontFamily:  'var(--font-geist-mono)',
                  fontSize:    '11px',
                  color:       'var(--text-secondary)',
                }}
              >
                {errorMessage}
              </span>
            </div>
          )}

          {/* Reject reason textarea — appears in phase 2 */}
          {actionState === 'awaiting_reject_reason' && (
            <div style={{ marginBottom: '12px' }}>
              <label
                htmlFor="ceo-reject-reason"
                style={{
                  display:       'block',
                  fontFamily:    'var(--font-geist-mono)',
                  fontSize:      '9px',
                  letterSpacing: '0.18em',
                  textTransform: 'uppercase' as const,
                  color:         'var(--text-tertiary)',
                  marginBottom:  '6px',
                }}
              >
                RAZÓN DEL RECHAZO — SE ENVIARÁ AL AGENTE
              </label>
              <textarea
                id="ceo-reject-reason"
                ref={textareaRef}
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Describe por qué se rechaza y qué debe re-planificar el agente..."
                rows={3}
                style={{
                  width:          '100%',
                  fontFamily:     'var(--font-geist-mono)',
                  fontSize:       '12px',
                  color:          PHOSPHOR_WHT,
                  background:     'var(--bg-base)',
                  border:         `1px solid ${BLOOD_RED}`,
                  padding:        '8px 10px',
                  resize:         'vertical',
                  outline:        'none',
                  caretColor:     BLOOD_RED,
                  lineHeight:     1.55,
                }}
              />
            </div>
          )}

          {/* Buttons */}
          {!isResolved && (
            <div
              style={{
                display:   'grid',
                gridTemplateColumns: '1fr 1fr',
                gap:       '12px',
              }}
            >
              {actionState === 'awaiting_reject_reason' ? (
                // Phase 2: confirm / cancel reject
                <>
                  <button
                    type="button"
                    onClick={handleRejectCancel}
                    disabled={isBusy}
                    style={{
                      fontFamily:    'var(--font-geist-mono)',
                      fontSize:      '12px',
                      fontWeight:    700,
                      letterSpacing: '0.12em',
                      textTransform: 'uppercase' as const,
                      padding:       '14px 20px',
                      background:    'transparent',
                      border:        '2px solid var(--border)',
                      color:         'var(--text-secondary)',
                      cursor:        isBusy ? 'not-allowed' : 'pointer',
                      opacity:       isBusy ? 0.5 : 1,
                      transition:    'border-color 0.12s, color 0.12s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isBusy) {
                        (e.currentTarget as HTMLButtonElement).style.borderColor = PHOSPHOR_WHT;
                        (e.currentTarget as HTMLButtonElement).style.color = PHOSPHOR_WHT;
                      }
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border)';
                      (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-secondary)';
                    }}
                  >
                    CANCELAR
                  </button>

                  <button
                    type="button"
                    onClick={handleRejectConfirm}
                    disabled={isBusy}
                    style={{
                      fontFamily:    'var(--font-geist-mono)',
                      fontSize:      '12px',
                      fontWeight:    700,
                      letterSpacing: '0.12em',
                      textTransform: 'uppercase' as const,
                      padding:       '14px 20px',
                      background:    'transparent',
                      border:        `2px solid ${BLOOD_RED}`,
                      color:         BLOOD_RED,
                      cursor:        isBusy ? 'not-allowed' : 'pointer',
                      opacity:       isBusy ? 0.6 : 1,
                      transition:    'background 0.12s, color 0.12s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isBusy) {
                        (e.currentTarget as HTMLButtonElement).style.background = BLOOD_RED;
                        (e.currentTarget as HTMLButtonElement).style.color = INK_BLACK;
                      }
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
                      (e.currentTarget as HTMLButtonElement).style.color = BLOOD_RED;
                    }}
                  >
                    {isBusy ? 'ENVIANDO…' : 'CONFIRMAR RECHAZO →'}
                  </button>
                </>
              ) : (
                // Phase 1: primary approve / reject
                <>
                  <button
                    type="button"
                    onClick={handleApprove}
                    disabled={isBusy}
                    aria-label="Aprobar estrategia y reanudar el agente"
                    style={{
                      fontFamily:    'var(--font-geist-mono)',
                      fontSize:      '12px',
                      fontWeight:    900,
                      letterSpacing: '0.12em',
                      textTransform: 'uppercase' as const,
                      padding:       '14px 20px',
                      background:    isBusy ? '#333' : INK_BLACK,
                      border:        `2px solid ${INK_BLACK}`,
                      color:         PHOSPHOR_WHT,
                      cursor:        isBusy ? 'not-allowed' : 'pointer',
                      opacity:       isBusy ? 0.7 : 1,
                      transition:    'background 0.12s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isBusy) {
                        (e.currentTarget as HTMLButtonElement).style.background = '#333';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isBusy) {
                        (e.currentTarget as HTMLButtonElement).style.background = INK_BLACK;
                      }
                    }}
                  >
                    {actionState === 'approving' ? 'ENVIANDO…' : '[ APROBAR ESTRATEGIA ]'}
                  </button>

                  <button
                    type="button"
                    onClick={handleRejectClick}
                    disabled={isBusy}
                    aria-label="Rechazar estrategia y re-planificar"
                    style={{
                      fontFamily:    'var(--font-geist-mono)',
                      fontSize:      '12px',
                      fontWeight:    700,
                      letterSpacing: '0.12em',
                      textTransform: 'uppercase' as const,
                      padding:       '14px 20px',
                      background:    'transparent',
                      border:        `2px solid ${BLOOD_RED}`,
                      color:         BLOOD_RED,
                      cursor:        isBusy ? 'not-allowed' : 'pointer',
                      opacity:       isBusy ? 0.6 : 1,
                      transition:    'background 0.12s, color 0.12s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isBusy) {
                        (e.currentTarget as HTMLButtonElement).style.background = `${BLOOD_RED}18`;
                      }
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
                    }}
                  >
                    [ RECHAZAR / RE-PLANIFICAR ]
                  </button>
                </>
              )}
            </div>
          )}

          {/* Footer metadata strip */}
          <div
            style={{
              display:        'flex',
              alignItems:     'center',
              justifyContent: 'space-between',
              marginTop:      '10px',
              paddingTop:     '8px',
              borderTop:      '1px solid var(--border-subtle)',
            }}
          >
            <span
              style={{
                fontFamily:    'var(--font-geist-mono)',
                fontSize:      '9px',
                letterSpacing: '0.12em',
                textTransform: 'uppercase' as const,
                color:         'var(--text-tertiary)',
              }}
            >
              INTERRUPT / {fmtRunId(payload.interrupt_id)}
            </span>
            <span
              style={{
                fontFamily:    'var(--font-geist-mono)',
                fontSize:      '9px',
                letterSpacing: '0.1em',
                color:         'var(--text-tertiary)',
              }}
            >
              NJM OS / LANGGRAPH HITL
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Demo payload ──────────────────────────────────────────────────────────────

export const DEMO_HITL_PAYLOAD: HITLInterruptPayload = {
  interrupt_id:     'int-9f3a2b1c-4d5e-11ef-8a2b-0242ac130003',
  thread_id:        'thr-2a4f8c1e-9b3d-4e2f',
  run_id:           'run-7f2e5d1a-4c8b-11ef-9f3a-0242ac130003',
  node_name:        'approval_gate',
  interrupt_type:   'approval_required',
  title:            'Campaña LinkedIn Ads Q2',
  strategy_summary:
    'El agente PM propone lanzar una campaña de LinkedIn Ads dirigida a Directores+ en empresas de 50-500 empleados en MX. Inversión inicial de $2,400 MXN/mes con ROI proyectado de 3.2x en 90 días.',
  proposed_action:
    'Generar el Business Case completo, crear el plan de ejecución de 30-60-90 días, y solicitar aprobación presupuestal para Q2 2026 mediante el flujo de Demand Generation.',
  risks: [
    {
      id:          'risk-001',
      level:       'CRITICAL',
      category:    'BUDGET_EXCEED',
      description: 'El presupuesto propuesto de $2,400 MXN/mes excede el límite pre-aprobado de Q2 en un 18.7%.',
      evidence: {
        budget_disponible_q2_mxn: 2_021,
        budget_propuesto_mxn:     2_400,
        delta_pct:                18.7,
        fuente:                   'libro_vivo/presupuestos_2026.md',
      },
    },
    {
      id:          'risk-002',
      level:       'HIGH',
      category:    'SCOPE_DRIFT',
      description: 'LinkedIn Ads no aparece en el plan de canal aprobado para Q2. Requiere re-alineación con el roadmap de Marketing.',
      evidence: {
        canales_aprobados_q2: ['SEO', 'Content Marketing', 'Email Nurturing'],
        canal_propuesto:      'LinkedIn Ads (Paid Social)',
        plan_version:         'roadmap_mkt_q2_v2.1',
      },
    },
    {
      id:          'risk-003',
      level:       'MEDIUM',
      category:    'DATA_GAP',
      description: 'El benchmark de CPC proviene de datos LATAM agregados. No existe data histórica específica de MX para este segmento ICP.',
      evidence: {
        fuente_benchmark:  'LinkedIn Campaign Manager Report 2025 — LATAM',
        cobertura_geo:     'LATAM (18 países)',
        data_mx_especifica: null,
        confianza_estadistica: '72%',
      },
    },
  ],
  budget_impact:  '+$379 MXN/mes sobre límite Q2 aprobado',
  time_impact:    'Lanzamiento estimado: 2026-05-05 (semana 3 de Q2)',
  adn_check:      false,
  created_at:     Date.now() - 4_200,
  metadata: {
    skill_version:    'business_case_v3',
    graph_version:    'pm_agent_v3',
    attempt:          1,
    langgraph_rev:    '0.2.31',
  },
};
