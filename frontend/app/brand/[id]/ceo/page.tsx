"use client";

import { useState } from "react";
import { UploadCloud } from "lucide-react";
import VectorCard from "@/components/njm/VectorCard";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

interface VectorEstrategico {
  id: string;
  titulo: string;
  estado: "completo" | "incompleto";
}

const MOCK_VECTORES: VectorEstrategico[] = [
  { id: "v1", titulo: "Brand Core & Identidad",       estado: "completo"   },
  { id: "v2", titulo: "Modelo de Negocio",             estado: "completo"   },
  { id: "v3", titulo: "Mapeo de Audiencia",            estado: "incompleto" },
  { id: "v4", titulo: "Posicionamiento Competitivo",   estado: "incompleto" },
  { id: "v5", titulo: "Estrategia de Canales",         estado: "completo"   },
  { id: "v6", titulo: "Propuesta de Valor",            estado: "incompleto" },
  { id: "v7", titulo: "KPIs & Métricas Clave",         estado: "incompleto" },
  { id: "v8", titulo: "Plan de Crecimiento",           estado: "completo"   },
];

export default function CEOWorkspacePage({
  params,
}: {
  params: { id: string };
}) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [activeVectorId, setActiveVectorId] = useState<string | null>(null);
  const [manualInput, setManualInput] = useState("");

  function handleCargarDoc(vectorId: string) {
    setActiveVectorId(vectorId);
    setManualInput("");
    setDialogOpen(true);
  }

  const activeVector = MOCK_VECTORES.find((v) => v.id === activeVectorId);
  const completados = MOCK_VECTORES.filter((v) => v.estado === "completo").length;

  return (
    <div className="p-8 pb-28 relative">
      {/* Header */}
      <div className="mb-8">
        <p
          className="text-xs uppercase tracking-widest mb-1 font-semibold"
          style={{ color: "hsl(var(--ceo-accent))" }}
        >
          CEO Workspace
        </p>
        <h1 className="text-2xl font-bold text-foreground capitalize">{params.id}</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          {completados} / {MOCK_VECTORES.length} vectores estratégicos completados
        </p>
      </div>

      {/* Vectores Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {MOCK_VECTORES.map((vector) => (
          <VectorCard
            key={vector.id}
            titulo={vector.titulo}
            estado={vector.estado}
            onAction={() => handleCargarDoc(vector.id)}
          />
        ))}
      </div>

      {/* Ingest Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Cargar Documento</DialogTitle>
            {activeVector && (
              <DialogDescription>
                {activeVector.titulo} — sube un archivo o ingresa contexto manualmente.
              </DialogDescription>
            )}
          </DialogHeader>

          {/* Drag & Drop Zone */}
          <div className="mt-2 border-2 border-dashed border-white/20 rounded-xl flex flex-col items-center justify-center gap-3 py-10 px-6 cursor-pointer hover:border-white/30 hover:bg-white/[0.02] transition-all duration-150">
            <UploadCloud className="w-10 h-10 text-muted-foreground/40" />
            <div className="text-center">
              <p className="text-sm font-medium text-muted-foreground">
                Arrastra documentos aquí
              </p>
              <p className="text-xs text-muted-foreground/50 mt-0.5">
                PDF, DOCX, TXT — máx. 10 MB
              </p>
            </div>
          </div>

          {/* Manual Input */}
          <div className="mt-1">
            <p className="text-[10px] text-muted-foreground/50 mb-2 uppercase tracking-wider font-semibold">
              o responde manualmente
            </p>
            <Textarea
              placeholder="Describe el contexto del vector estratégico..."
              value={manualInput}
              onChange={(e) => setManualInput(e.target.value)}
              className="min-h-[96px] resize-none text-sm"
            />
          </div>
        </DialogContent>
      </Dialog>

      {/* Floating CTA */}
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40 pointer-events-none">
        <button
          className="pointer-events-auto flex items-center gap-2.5 px-7 py-3.5 rounded-full font-semibold text-sm text-white transition-all duration-200 hover:brightness-110 active:scale-[0.97]"
          style={{
            background: "hsl(var(--ceo-accent))",
            boxShadow:
              "0 0 40px hsl(var(--ceo-accent) / 0.35), 0 8px 24px rgba(0,0,0,0.5)",
          }}
        >
          <span aria-hidden>⚡</span>
          Invocar CEO para Auditoría
        </button>
      </div>
    </div>
  );
}
