// ── LangGraph streaming event types ──────────────────────────────────────────
// Covers LangGraph v0.2+ .astream_events() API output.

export type LangGraphEventKind =
  | 'on_chain_start'
  | 'on_chain_end'
  | 'on_chain_stream'
  | 'on_tool_start'
  | 'on_tool_end'
  | 'on_llm_start'
  | 'on_llm_end'
  | 'on_llm_stream'
  | 'on_chat_model_start'
  | 'on_chat_model_end'
  | 'on_chat_model_stream'
  | 'on_retriever_start'
  | 'on_retriever_end'
  | 'on_custom_event';

export type LogEntryKind = 'node' | 'tool' | 'llm' | 'retriever' | 'custom';
export type LogEntryStatus = 'running' | 'ok' | 'error' | 'stream';
export type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'done' | 'error';

// Raw event emitted by LangGraph's astream_events()
export interface LangGraphEvent {
  event: LangGraphEventKind;
  name: string;
  run_id: string;
  parent_ids?: string[];
  tags?: string[];
  metadata?: Record<string, unknown>;
  data?: {
    input?: unknown;
    output?: unknown;
    chunk?: unknown;
    [key: string]: unknown;
  };
  // ms since epoch — injected client-side when absent in raw stream
  timestamp?: number;
}

// Processed, merged view of a LangGraph event pair (start + end collapsed)
export interface LogEntry {
  id: string;
  run_id: string;
  parent_ids: string[];
  kind: LogEntryKind;
  event: LangGraphEventKind;
  name: string;
  status: LogEntryStatus;
  ts_start: number;
  ts_end?: number;
  delta_ms?: number;
  input?: unknown;
  output?: unknown;
  token_count?: number;
  tags: string[];
  metadata: Record<string, unknown>;
  seq: number; // stable insertion order
}

export interface StreamStats {
  elapsed_ms: number;
  node_count: number;
  tool_count: number;
  llm_count: number;
  token_count: number;
  error_count: number;
}

export interface AgentLogStreamProps {
  /** SSE or NDJSON endpoint that emits LangGraph events */
  streamUrl?: string;
  /** Alternatively, pass a static array (for testing / replay) */
  events?: LangGraphEvent[];
  /** Fired when the stream closes cleanly */
  onComplete?: (entries: LogEntry[]) => void;
  /** Max entries kept in DOM before oldest are pruned (default: 500) */
  maxEntries?: number;
  /** Stick to the newest entry (default: true) */
  autoScroll?: boolean;
  /** Start tool payloads collapsed (default: false — expanded) */
  toolsCollapsed?: boolean;
  className?: string;
  style?: React.CSSProperties;
  label?: string;
}
