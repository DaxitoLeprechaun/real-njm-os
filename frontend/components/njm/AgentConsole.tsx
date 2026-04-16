"use client";

import { useEffect, useRef, useState } from "react";
import { X, Terminal } from "lucide-react";

export interface AgentConsoleProps {
  open: boolean;
  onClose: () => void;
  agentLabel: string;
  logs: string[];
  /** When true the simulation is still running (shows blinking cursor) */
  running: boolean;
}

export default function AgentConsole({
  open,
  onClose,
  agentLabel,
  logs,
  running,
}: AgentConsoleProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on every new log
  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, open]);

  if (!open) return null;

  return (
    <div
      className="fixed bottom-0 right-0 z-50 flex flex-col"
      style={{
        width: "min(520px, 100vw)",
        height: "320px",
        background: "rgb(2 6 23)", // slate-950
        border: "1px solid rgb(30 41 59)", // slate-800
        borderBottom: "none",
        borderRadius: "12px 12px 0 0",
        boxShadow: "0 -8px 40px rgba(0,0,0,0.6)",
      }}
    >
      {/* Title bar */}
      <div
        className="flex items-center justify-between px-4 py-2.5 shrink-0"
        style={{
          borderBottom: "1px solid rgb(30 41 59)",
          background: "rgb(2 6 23)",
          borderRadius: "12px 12px 0 0",
        }}
      >
        <div className="flex items-center gap-2">
          {/* Traffic-light dots */}
          <span className="w-3 h-3 rounded-full bg-rose-500 opacity-80" />
          <span className="w-3 h-3 rounded-full bg-amber-400 opacity-80" />
          <span className="w-3 h-3 rounded-full bg-emerald-500 opacity-80" />
          <Terminal
            className="ml-2 w-3.5 h-3.5 text-slate-500"
            strokeWidth={1.5}
          />
          <span
            className="text-xs font-mono font-medium text-slate-400 ml-1"
            style={{ fontFamily: "'Fira Code', monospace" }}
          >
            njm-os — {agentLabel}
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-slate-600 hover:text-slate-300 transition-colors duration-100"
          aria-label="Cerrar consola"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Log output */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1">
        {logs.map((line, i) => (
          <LogLine key={i} text={line} />
        ))}

        {/* Blinking cursor on last active line */}
        {running && (
          <div
            className="flex items-center gap-1 text-xs font-mono text-slate-400"
            style={{ fontFamily: "'Fira Code', monospace" }}
          >
            <span className="text-emerald-400">$</span>
            <BlinkingCursor />
          </div>
        )}

        {!running && logs.length > 0 && (
          <div
            className="text-xs font-mono text-slate-600 mt-2 pt-2"
            style={{
              fontFamily: "'Fira Code', monospace",
              borderTop: "1px solid rgb(30 41 59)",
            }}
          >
            Process exited with code 0
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}

function LogLine({ text }: { text: string }) {
  const color = text.startsWith("[✓]")
    ? "text-emerald-400"
    : text.startsWith("[⏳]")
    ? "text-amber-400"
    : text.startsWith("[✗]") || text.startsWith("[!]")
    ? "text-rose-400"
    : "text-slate-300";

  return (
    <p
      className={`text-xs font-mono leading-relaxed ${color}`}
      style={{ fontFamily: "'Fira Code', monospace" }}
    >
      {text}
    </p>
  );
}

function BlinkingCursor() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const id = setInterval(() => setVisible((v) => !v), 530);
    return () => clearInterval(id);
  }, []);

  return (
    <span
      className="inline-block w-2 h-3.5 bg-slate-400"
      style={{ opacity: visible ? 1 : 0 }}
    />
  );
}
