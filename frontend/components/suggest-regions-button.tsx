"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, Sparkles, X } from "lucide-react";
import { toast } from "sonner";
import { suggestRegions, type KScore, type SuggestRegionsResult } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface Props {
  participantsFile: File | null;
  onAccept: (k: number) => void;
}

export function SuggestRegionsButton({ participantsFile, onAccept }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SuggestRegionsResult | null>(null);
  const [open, setOpen] = useState(false);

  async function handleSuggest() {
    if (!participantsFile) {
      toast.error("Anexe o arquivo de participantes primeiro");
      return;
    }
    setLoading(true);
    try {
      const buf = await participantsFile.arrayBuffer();
      const data = await parseParticipantsFile(buf, participantsFile.name);
      if (data.length < 10) {
        toast.error("Mínimo de 10 participantes com lat/lon");
        return;
      }
      const res = await suggestRegions({ participants: data });
      setResult(res);
      setOpen(true);
    } catch (err) {
      toast.error("Erro ao sugerir", { description: String(err) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Button
        type="button"
        variant="outline"
        onClick={handleSuggest}
        disabled={loading || !participantsFile}
        data-testid="suggest-button"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Calculando...
          </>
        ) : (
          <>
            <Sparkles className="mr-2 h-4 w-4" />
            Sugerir regiões
          </>
        )}
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl" data-testid="suggest-dialog">
          <DialogHeader>
            <DialogTitle>Sugestão de regiões</DialogTitle>
            <DialogDescription>
              {result && (
                <>
                  Análise de <strong>{result.n_participants}</strong> participantes.
                  Recomendado: <strong data-testid="recommended">{result.recommended}</strong> regiões.
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          {result && (
            <div className="max-h-96 overflow-auto rounded-md border">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 sticky top-0">
                  <tr>
                    <th className="p-2 text-left">k</th>
                    <th className="p-2 text-right">Silhouette</th>
                    <th className="p-2 text-right">Inertia</th>
                  </tr>
                </thead>
                <tbody>
                  {result.scores.map((s) => (
                    <ScoreRow key={s.k} score={s} recommended={result.recommended} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <DialogFooter>
            <Button variant="ghost" onClick={() => setOpen(false)}>
              <X className="mr-2 h-4 w-4" />
              Fechar
            </Button>
            {result && (
              <Button
                onClick={() => {
                  onAccept(result.recommended);
                  setOpen(false);
                  toast.success("Aplicado", {
                    description: `n_regions = ${result.recommended}`,
                  });
                }}
                data-testid="accept-suggestion"
              >
                Usar {result.recommended}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function ScoreRow({ score, recommended }: { score: KScore; recommended: number }) {
  const isWinner = score.k === recommended;
  return (
    <tr className={isWinner ? "bg-emerald-50 dark:bg-emerald-950/30" : ""}>
      <td className="p-2 font-mono">
        {score.k}
        {isWinner && <span className="ml-2 text-xs text-emerald-600">★ recomendado</span>}
      </td>
      <td className="p-2 text-right font-mono">
        {score.silhouette != null ? score.silhouette.toFixed(3) : "—"}
      </td>
      <td className="p-2 text-right font-mono">
        {score.inertia != null ? score.inertia.toFixed(0) : "—"}
      </td>
    </tr>
  );
}

async function parseParticipantsFile(
  buf: ArrayBuffer,
  filename: string
): Promise<{ lat: number | null; lon: number | null; qty: number }[]> {
  const XLSX = await import("xlsx").catch(() => null);
  if (!XLSX) {
    throw new Error(
      "Parser XLSX não disponível. Instale 'xlsx' ou use CSV (lat,lon por linha)."
    );
  }
  const wb = XLSX.read(buf, { type: "array" });
  const sheet = wb.Sheets[wb.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, { defval: null });

  function pick(row: Record<string, unknown>, aliases: string[]): unknown {
    for (const k of Object.keys(row)) {
      if (aliases.includes(k.toLowerCase().trim())) return row[k];
    }
    return null;
  }

  return rows.map((r) => {
    const lat = Number(pick(r, ["latitude", "lat", "y"]));
    const lon = Number(pick(r, ["longitude", "lon", "long", "lng", "x"]));
    const qty = Number(pick(r, ["qtdcandidato", "quantidade", "qty", "candidatos"])) || 1;
    return {
      lat: Number.isFinite(lat) ? lat : null,
      lon: Number.isFinite(lon) ? lon : null,
      qty,
    };
  });
}
