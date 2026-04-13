// ── StateOrchestrator types ───────────────────────────────────────────────────
// Maps LangGraph graph execution state to NJM OS visual states.

/** The 3 visual states rendered by StateOrchestrator */
export type OrchestratorVisualState = 'thinking' | 'success' | 'warning' | 'error';

/** Semantic node category derived from LangGraph node role */
export type NodeType =
  | 'agent'     // reasoning / LLM call
  | 'response'  // final output node
  | 'retry'     // retry / backoff node
  | 'tool'      // tool invocation
  | 'router'    // conditional edge / router
  | 'subgraph'; // nested subgraph

/** A single executed step in the LangGraph run */
export interface AgentNodeStep {
  /** Stable insertion index (0-based) */
  seq: number;
  /** LangGraph node name (e.g. "__start__", "agent_reasoning") */
  node_name: string;
  /** Semantic category used to drive visual state defaults */
  node_type: NodeType;
  /**
   * Visual state:
   *  - 'thinking'  → agent nodes currently processing (terminal active)
   *  - 'success'   → completed response nodes (green #00FF00 border + VERIFIED_BY_OS)
   *  - 'warning'   → retry nodes (amber bg, black text)
   *  - 'error'     → failed nodes (danger red)
   */
  status: OrchestratorVisualState;
  /** LangGraph run_id for this node's invocation */
  run_id: string;
  /** Parent run_id when node is nested in a subgraph */
  parent_run_id?: string;
  /** Unix timestamp in ms — node start */
  started_at: number;
  /** Unix timestamp in ms — node end (absent while thinking) */
  ended_at?: number;
  /** Computed duration in ms */
  duration_ms?: number;
  /** Raw state snapshot fed into this node */
  input_snapshot?: unknown;
  /** Raw state snapshot produced by this node */
  output_snapshot?: unknown;
  /** All technical metadata — never hidden from UI */
  metadata: {
    attempt?: number;
    max_attempts?: number;
    model?: string;
    token_count?: number;
    tags?: string[];
    error_message?: string;
    adn_check?: boolean;
    checkpoint_id?: string;
    [key: string]: unknown;
  };
}

/** Full graph execution state — root prop for StateOrchestrator */
export interface GraphExecutionState {
  graph_id: string;
  thread_id: string;
  run_id: string;
  status: 'running' | 'done' | 'error' | 'interrupted';
  steps: AgentNodeStep[];
  /** Unix ms — graph created */
  created_at: number;
  /** Unix ms — last mutation */
  updated_at: number;
  metadata?: Record<string, unknown>;
}

export interface StateOrchestratorProps {
  /** Full LangGraph execution state JSON */
  state: GraphExecutionState;
  /** Show input_snapshot / output_snapshot inline (default: true) */
  showSnapshots?: boolean;
  className?: string;
  style?: React.CSSProperties;
}
