"use client";

import { CheckCircle2, Circle, Upload } from "lucide-react";
import { cn } from "@/lib/utils";

interface VectorCardProps {
  titulo: string;
  estado: "completo" | "incompleto";
  onAction: () => void;
}

export default function VectorCard({ titulo, estado, onAction }: VectorCardProps) {
  const isComplete = estado === "completo";

  return (
    <div
      className={cn(
        "glass rounded-xl p-4 flex items-center gap-4 transition-all duration-150",
        isComplete
          ? "border-[hsl(var(--pm-accent))/30] [&]:border-emerald-500/30"
          : "border-rose-500/30"
      )}
      style={{
        borderColor: isComplete
          ? "hsl(var(--pm-accent) / 0.3)"
          : "rgb(244 63 94 / 0.3)",
      }}
    >
      {/* Status icon */}
      {isComplete ? (
        <CheckCircle2
          className="w-5 h-5 shrink-0"
          style={{ color: "hsl(var(--pm-accent))" }}
        />
      ) : (
        <Circle className="w-5 h-5 shrink-0 text-rose-500" />
      )}

      {/* Title */}
      <p className="text-sm font-medium text-foreground flex-1 leading-snug">{titulo}</p>

      {/* Action */}
      {!isComplete && (
        <button
          onClick={onAction}
          className="flex items-center gap-1.5 text-xs font-semibold text-rose-400 hover:text-rose-300 border border-rose-500/40 hover:border-rose-400/60 rounded-lg px-3 py-1.5 transition-all duration-150 shrink-0 bg-rose-500/[0.06] hover:bg-rose-500/10"
        >
          <Upload className="w-3 h-3" />
          Cargar Doc
        </button>
      )}

      {isComplete && (
        <span
          className="text-xs font-medium px-2.5 py-1 rounded-full shrink-0"
          style={{
            color: "hsl(var(--pm-accent))",
            background: "hsl(var(--pm-accent) / 0.1)",
          }}
        >
          Completo
        </span>
      )}
    </div>
  );
}
