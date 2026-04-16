"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface UseAgentConsoleReturn {
  open: boolean;
  logs: string[];
  running: boolean;
  invoke: (sequenceId: string) => void;
  close: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function useAgentConsole(): UseAgentConsoleReturn {
  const [open, setOpen] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  function closeStream() {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  }

  const invoke = useCallback((sequenceId: string) => {
    closeStream();
    setLogs([]);
    setRunning(true);
    setOpen(true);

    const url = `${API_URL}/api/v1/agent/stream?sequenceId=${encodeURIComponent(sequenceId)}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (event) => {
      const data = event.data as string;
      if (data === "[DONE]") {
        closeStream();
        setRunning(false);
        return;
      }
      setLogs((prev) => [...prev, data]);
    };

    es.onerror = () => {
      closeStream();
      setRunning(false);
      setLogs((prev) => [...prev, "[!] Error de conexión con el agente."]);
    };
  }, []);

  const close = useCallback(() => {
    closeStream();
    setOpen(false);
    setRunning(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => () => closeStream(), []);

  return { open, logs, running, invoke, close };
}
