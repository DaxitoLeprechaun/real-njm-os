"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

export interface CEOShieldProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  riskMessage?: string;
  onApprove?: () => void;
  onReject?: () => void;
}

export default function CEOShield({
  open,
  onOpenChange,
  riskMessage = "El presupuesto propuesto excede el límite del Vector 5.",
  onApprove,
  onReject,
}: CEOShieldProps) {
  function handleApprove() {
    onApprove?.();
    onOpenChange(false);
  }

  function handleReject() {
    onReject?.();
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        showCloseButton={false}
        className="sm:max-w-md p-0 overflow-hidden"
        style={{
          background: "rgb(2 6 23)", // slate-950
          border: "2px solid rgb(225 29 72)", // rose-600
          borderRadius: "12px",
          boxShadow:
            "0 0 0 1px rgb(225 29 72 / 0.3), 0 0 60px rgb(225 29 72 / 0.15), 0 24px 64px rgba(0,0,0,0.7)",
        }}
      >
        {/* Red alert header stripe */}
        <div
          className="px-6 pt-6 pb-4"
          style={{ borderBottom: "1px solid rgb(225 29 72 / 0.3)" }}
        >
          <DialogHeader>
            <DialogTitle
              className="text-rose-500 font-black tracking-widest uppercase text-lg leading-tight"
              style={{ letterSpacing: "0.12em" }}
            >
              ⚠️ APROBACIÓN ESTRATÉGICA REQUERIDA
            </DialogTitle>
            <DialogDescription className="text-slate-400 text-xs mt-1 font-mono uppercase tracking-wider">
              CEO Shield — Human-in-the-Loop activado
            </DialogDescription>
          </DialogHeader>
        </div>

        {/* Risk block */}
        <div className="px-6 py-5">
          <div
            className="rounded-lg p-4"
            style={{
              background: "rgb(225 29 72 / 0.08)",
              border: "1px solid rgb(225 29 72 / 0.25)",
            }}
          >
            <p className="text-[10px] font-mono font-semibold uppercase tracking-widest text-rose-500 mb-1.5">
              Riesgo Detectado
            </p>
            <p className="text-sm text-slate-200 leading-relaxed">
              {riskMessage}
            </p>
          </div>

          <p className="text-xs text-slate-500 mt-4 leading-relaxed">
            Esta acción requiere aprobación manual antes de continuar. Revisa
            los vectores afectados antes de decidir.
          </p>
        </div>

        {/* Action buttons */}
        <div
          className="flex flex-col sm:flex-row gap-2 px-6 pb-6"
          style={{ borderTop: "1px solid rgb(30 41 59)" }}
        >
          <div className="flex flex-col sm:flex-row gap-2 w-full pt-4">
            {/* Primary: Approve — brutalist rose outline */}
            <button
              onClick={handleApprove}
              className="flex-1 px-4 py-2.5 rounded-lg text-sm font-bold uppercase tracking-widest transition-all duration-150 active:scale-[0.97]"
              style={{
                background: "transparent",
                border: "1.5px solid rgb(225 29 72)",
                color: "rgb(251 113 133)", // rose-400
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background =
                  "rgb(225 29 72 / 0.15)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background =
                  "transparent";
              }}
            >
              APROBAR ASUMIENDO RIESGO
            </button>

            {/* Secondary: Reject — solid light */}
            <button
              onClick={handleReject}
              className="flex-1 px-4 py-2.5 rounded-lg text-sm font-bold uppercase tracking-widest bg-slate-100 text-slate-900 hover:bg-white transition-all duration-150 active:scale-[0.97]"
            >
              RECHAZAR Y RE-PLANIFICAR
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
