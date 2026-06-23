"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CompareResults } from "@/components/compare-results";

export default function ComparePage({ params }: { params: Promise<{ id: string }> }) {
  const [compareId, setCompareId] = useState<string | null>(null);
  const [nClustersHint, setNClustersHint] = useState(7);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  // Resolve params (Next 15 async params)
  if (jobId === null) {
    void params.then((p) => setJobId(p.id));
    return null;
  }

  async function startCompare() {
    setLoading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("n_clusters_hint", String(nClustersHint));
      const res = await fetch(`/api/backend/jobs/${jobId}/compare`, {
        method: "POST",
        body: fd,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setCompareId(data.id);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container py-10 space-y-6">
      <div className="flex items-center gap-3">
        <Button asChild variant="ghost" size="sm">
          <Link href={`/jobs/${jobId}`}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar ao job
          </Link>
        </Button>
      </div>

      <header>
        <h1 className="text-2xl font-bold">Comparativo de algoritmos</h1>
        <p className="text-muted-foreground">
          Reutiliza os arquivos do job{" "}
          <code className="rounded bg-muted px-1">{jobId.slice(0, 8)}</code> para rodar
          K-Means, K-Medoids e DBSCAN.
        </p>
      </header>

      {compareId ? (
        <CompareResults compareId={compareId} onUseAlgorithm={() => {}} />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" /> Iniciar comparativo
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="k-hint">
                K (sugestão inicial)
              </label>
              <input
                id="k-hint"
                type="number"
                min={2}
                max={15}
                value={nClustersHint}
                onChange={(e) => setNClustersHint(Number(e.target.value))}
                className="rounded-md border bg-background px-3 py-1 text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Sugestão: o número de regiões que você usou no job original.
              </p>
            </div>
            <Button onClick={startCompare} disabled={loading} data-testid="start-compare">
              {loading ? "Iniciando..." : "Rodar comparativo"}
            </Button>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </CardContent>
        </Card>
      )}
    </main>
  );
}
