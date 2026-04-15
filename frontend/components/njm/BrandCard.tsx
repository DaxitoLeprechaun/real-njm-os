"use client";

import { useRouter } from "next/navigation";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface BrandCardProps {
  id: string;
  nombre: string;
  sector: string;
  saludAdn: number; // 0–100
}

export default function BrandCard({ id, nombre, sector, saludAdn }: BrandCardProps) {
  const router = useRouter();

  const isHealthy = saludAdn >= 80;
  const isMid = saludAdn >= 50 && saludAdn < 80;

  const accentColor = isHealthy
    ? "hsl(var(--pm-accent))"
    : isMid
    ? "hsl(var(--agency-accent))"
    : "hsl(0 84% 60%)";

  const accentClass = isHealthy
    ? "text-[hsl(var(--pm-accent))]"
    : isMid
    ? "text-[hsl(var(--agency-accent))]"
    : "text-rose-500";

  const indicatorClass = isHealthy
    ? "[&_[data-slot=progress-indicator]]:bg-[hsl(var(--pm-accent))]"
    : isMid
    ? "[&_[data-slot=progress-indicator]]:bg-[hsl(var(--agency-accent))]"
    : "[&_[data-slot=progress-indicator]]:bg-rose-500";

  return (
    <button
      onClick={() => router.push(`/brand/${id}/ceo`)}
      className="glass w-full text-left rounded-2xl p-5 hover:scale-[1.015] active:scale-[0.99] transition-transform duration-150 cursor-pointer group"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="min-w-0">
          <h3 className="font-semibold text-foreground text-base truncate">{nombre}</h3>
          <p className="text-xs text-muted-foreground mt-0.5">{sector}</p>
        </div>
        <span
          className={cn("text-sm font-bold tabular-nums shrink-0 ml-3", accentClass)}
          style={{ color: accentColor }}
        >
          {saludAdn}%
        </span>
      </div>

      {/* ADN Health bar */}
      <Progress
        value={saludAdn}
        className={cn("gap-1.5", indicatorClass)}
      />

      <p className="text-[10px] text-muted-foreground/50 mt-3 uppercase tracking-wider font-medium">
        ADN Salud
      </p>
    </button>
  );
}
