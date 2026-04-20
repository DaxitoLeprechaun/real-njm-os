"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

interface ArtefactViewerProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  taskTitle: string;
  running: boolean;
  content: string;
}

export default function ArtefactViewer({
  open,
  onOpenChange,
  taskTitle,
  running,
  content,
}: ArtefactViewerProps) {
  return (
    <Sheet open={open} onOpenChange={running ? () => {} : onOpenChange}>
      <SheetContent
        side="right"
        showCloseButton={!running}
        className="w-[580px] sm:w-[640px] flex flex-col gap-0 p-0 border-l border-white/[0.08] bg-[rgb(2_6_23)]"
      >
        <SheetHeader className="px-6 py-4 border-b border-white/[0.06] shrink-0">
          <div className="flex items-start justify-between gap-3 pr-6">
            <SheetTitle className="text-sm font-mono text-foreground/90 leading-snug">
              {taskTitle}
            </SheetTitle>
            <span
              className={`shrink-0 text-[10px] px-2 py-0.5 rounded-full border font-mono whitespace-nowrap ${
                running
                  ? "text-amber-400 border-amber-500/30 bg-amber-500/10"
                  : "text-pm border-pm/30 bg-pm/10"
              }`}
            >
              {running ? "Generando..." : "Completado"}
            </span>
          </div>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="font-mono text-xs text-foreground/80 bg-slate-900/50 rounded-lg p-4 whitespace-pre-wrap leading-relaxed min-h-[200px]">
            {content ? (
              content
            ) : (
              <span className="text-muted-foreground/30">
                {running ? "Iniciando generación..." : "Sin contenido."}
              </span>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
