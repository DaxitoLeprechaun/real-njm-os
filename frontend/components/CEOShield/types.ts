// ── CEOShield / Escudo del CEO — HITL interrupt types ────────────────────────
// Models LangGraph's Human-in-the-Loop interrupt payload.
// The graph pauses via interrupt() and resumes via Command(resume=...).

export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM';
export type RiskCategory =
  | 'BUDGET_EXCEED'
  | 'SCOPE_DRIFT'
  | 'ADN_VIOLATION'
  | 'DATA_GAP'
  | 'COMPLIANCE'
  | 'EXTERNAL_DEPENDENCY'
  | 'TIMELINE_RISK'
  | 'UNKNOWN';

export interface DetectedRisk {
  id: string;
  level: RiskLevel;
  category: RiskCategory;
  description: string;
  /** Raw technical evidence — shown verbatim to the CEO consultant */
  evidence?: unknown;
}

export type InterruptType =
  | 'approval_required'
  | 'risk_detected'
  | 'budget_threshold'
  | 'scope_change'
  | 'adn_violation';

/** Full HITL interrupt payload emitted by the LangGraph interrupt() node */
export interface HITLInterruptPayload {
  interrupt_id: string;
  thread_id: string;
  run_id: string;
  /** LangGraph node that called interrupt() */
  node_name: string;
  interrupt_type: InterruptType;
  /** CEO-facing title shown in the large header */
  title: string;
  /** One-sentence summary of the proposed strategy */
  strategy_summary: string;
  /** Exact action the agent wants to execute upon approval */
  proposed_action: string;
  risks: DetectedRisk[];
  budget_impact?: string;
  time_impact?: string;
  /** ADN coherence check result from the validation layer */
  adn_check: boolean;
  /** All raw LangGraph metadata — nothing hidden */
  metadata: Record<string, unknown>;
  created_at: number;
}

/** Action states that drive internal UI transitions */
export type ShieldActionState =
  | 'idle'
  | 'awaiting_reject_reason'
  | 'approving'
  | 'rejecting'
  | 'approved'
  | 'rejected'
  | 'error';

export interface CEOShieldProps {
  payload: HITLInterruptPayload;
  /**
   * Async callback — calls the FastAPI/LangGraph resume endpoint.
   * Must resolve when LangGraph acknowledges the command.
   * Rejection should throw with a human-readable message.
   */
  onApprove: (interruptId: string, notes?: string) => Promise<void>;
  /**
   * Async callback — sends Command(resume={"decision": "reject", "reason": ...})
   * Must resolve when LangGraph acknowledges.
   */
  onReject: (interruptId: string, reason: string) => Promise<void>;
  /** Called after approved/rejected state resolves — parent clears the overlay */
  onDismiss?: () => void;
}
