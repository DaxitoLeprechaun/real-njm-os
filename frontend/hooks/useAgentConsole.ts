"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────

export interface AgentParams {
  brand_id: string;
  session_id: string;
}

export interface ActionRequiredEvent {
  trigger: "BLOQUEO_CEO" | "GAP_DETECTED";
  risk_message?: string;
  questions?: string[];
  gap_report_path?: string | null;
  session_id: string;
  brand_id: string;
}

export interface UseAgentConsoleReturn {
  open: boolean;
  logs: string[];
  running: boolean;
  actionRequired: ActionRequiredEvent | null;
  invoke: (sequenceId: string, params?: Partial<AgentParams>) => void;
  resume: (answers: string, params: AgentParams) => Promise<void>;
  close: () => void;
}

// ── Hook ───────────────────────────────────────────────────────────────────

export function useAgentConsole(): UseAgentConsoleReturn {
  const [open, setOpen] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [actionRequired, setActionRequired] = useState<ActionRequiredEvent | null>(null);
  const esRef = useRef<EventSource | null>(null);

  function closeStream() {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  }

  const invoke = useCallback(
    (sequenceId: string, params: Partial<AgentParams> = {}) => {
      closeStream();
      setLogs([]);
      setRunning(true);
      setOpen(true);
      setActionRequired(null);

      const brand_id = params.brand_id ?? "disrupt";
      const session_id = params.session_id ?? "dev-session-1";

      const url = new URL(`${API_URL}/api/v1/agent/stream`);
      url.searchParams.set("sequenceId", sequenceId);
      url.searchParams.set("brand_id", brand_id);
      url.searchParams.set("session_id", session_id);

      const es = new EventSource(url.toString());
      esRef.current = es;

      es.onmessage = (event) => {
        const raw = event.data as string;

        // Legacy sentinel — kept for backward compat with mock sequences.
        if (raw === "[DONE]") {
          closeStream();
          setRunning(false);
          return;
        }

        let parsed: Record<string, unknown>;
        try {
          parsed = JSON.parse(raw);
        } catch {
          // Non-JSON line — treat as plain log text (mock sequences).
          setLogs((prev) => [...prev, raw]);
          return;
        }

        if (parsed.type === "log") {
          setLogs((prev) => [...prev, parsed.text as string]);
        } else if (parsed.type === "action_required") {
          setActionRequired(parsed as unknown as ActionRequiredEvent);
          closeStream();
          setRunning(false);
        } else if (parsed.type === "done") {
          closeStream();
          setRunning(false);
        }
      };

      es.onerror = () => {
        closeStream();
        setRunning(false);
        setLogs((prev) => [...prev, "[!] Error de conexión con el agente."]);
      };
    },
    []
  );

  const resume = useCallback(async (answers: string, params: AgentParams) => {
    const res = await fetch(`${API_URL}/api/v1/agent/resume`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        brand_id: params.brand_id,
        session_id: params.session_id,
        answers,
      }),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Resume failed: ${err}`);
    }
  }, []);

  const close = useCallback(() => {
    closeStream();
    setOpen(false);
    setRunning(false);
    setActionRequired(null);
  }, []);

  useEffect(() => () => closeStream(), []);

  return { open, logs, running, actionRequired, invoke, close, resume };
}
