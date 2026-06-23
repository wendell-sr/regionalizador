"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { MapPin, Loader2, CheckCircle2, XCircle, Download } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { StatusBadge } from "@/components/status-badge";
import {
  createGeocodingJob,
  geocodedFileUrl,
  getGeocodedResult,
  getGeocodingJob,
  type GeocodedItem,
  type GeocodingJobStatus,
} from "@/lib/api";

export function GeocodingForm() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [job, setJob] = useState<GeocodingJobStatus | null>(null);
  const [items, setItems] = useState<GeocodedItem[]>([]);

  useEffect(() => {
    if (!job) return;
    if (job.status === "done" || job.status === "failed") {
      getGeocodedResult(job.id).then((r) => setItems(r.items)).catch(() => {});
      return;
    }
    const t = setTimeout(async () => {
      try {
        const next = await getGeocodingJob(job.id);
        setJob(next);
      } catch {
        /* ignore transient errors */
      }
    }, 2000);
    return () => clearTimeout(t);
  }, [job]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) {
      toast.error("Anexe um arquivo XLSX/CSV");
      return;
    }
    setSubmitting(true);
    try {
      const j = await createGeocodingJob(file);
      setJob(j);
      setItems([]);
      toast.success("Job de geocoding criado", { description: j.id });
    } catch (err) {
      toast.error("Erro", { description: String(err) });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MapPin className="h-5 w-5" /> Geocoding de Escolas/Participantes
        </CardTitle>
        <CardDescription>
          Resolve CEP/endereço → lat/lon via Nominatim + AwesomeAPI. Sem chave de API.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        <form onSubmit={handleSubmit} className="grid gap-3">
          <input
            type="file"
            accept=".xlsx,.csv"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1 file:text-primary-foreground hover:file:bg-primary/90"
            data-testid="geocoding-file"
          />
          <Button type="submit" disabled={submitting || !file} data-testid="geocoding-submit">
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Enviando...
              </>
            ) : (
              "Iniciar geocoding"
            )}
          </Button>
        </form>

        {job && (
          <div className="grid gap-3 rounded-md border p-3" data-testid="geocoding-status">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <StatusBadge status={job.status} />
                <span className="text-sm font-mono">{job.id.slice(0, 8)}</span>
              </div>
              <span className="text-xs text-muted-foreground">
                {job.succeeded}/{job.total} resolvidos
              </span>
            </div>
            <Progress value={Math.round(job.progress * 100)} />
            {job.message && <p className="text-xs text-muted-foreground">{job.message}</p>}

            {job.status === "done" && items.length > 0 && (
              <div className="grid gap-2 pt-2">
                <div className="flex gap-2">
                  <a
                    href={geocodedFileUrl(job.id, "geocoded.xlsx")}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:bg-primary/90"
                  >
                    <Download className="h-3 w-3" /> geocoded.xlsx
                  </a>
                  {job.failed > 0 && (
                    <a
                      href={geocodedFileUrl(job.id, "failed_only.xlsx")}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm hover:bg-accent"
                    >
                      <Download className="h-3 w-3" /> failed_only.xlsx
                    </a>
                  )}
                </div>
                <div className="max-h-48 overflow-auto rounded-md border text-sm">
                  <table className="w-full">
                    <thead className="bg-muted/50 sticky top-0">
                      <tr>
                        <th className="p-1 text-left">Input</th>
                        <th className="p-1 text-right">Lat</th>
                        <th className="p-1 text-right">Lon</th>
                        <th className="p-1 text-left">Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.slice(0, 50).map((it) => (
                        <tr key={it.index} className="border-t">
                          <td className="p-1 max-w-xs truncate text-xs">
                            {it.success ? (
                              <CheckCircle2 className="mr-1 inline h-3 w-3 text-emerald-600" />
                            ) : (
                              <XCircle className="mr-1 inline h-3 w-3 text-red-600" />
                            )}
                            {it.input}
                          </td>
                          <td className="p-1 text-right font-mono text-xs">
                            {it.lat != null ? it.lat.toFixed(4) : "—"}
                          </td>
                          <td className="p-1 text-right font-mono text-xs">
                            {it.lon != null ? it.lon.toFixed(4) : "—"}
                          </td>
                          <td className="p-1 text-xs">{it.source ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {items.length > 50 && (
                  <p className="text-xs text-muted-foreground">
                    Mostrando 50 de {items.length} linhas
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {job && job.status === "done" && (
          <Button variant="outline" onClick={() => router.refresh()}>
            Geocodificar outro arquivo
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
