"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Loader2, Sparkles, Download } from "lucide-react";
import {
  type AlgorithmMetrics,
  type CompareResult,
  createCompareJob,
  getCompareResult,
  getCompareStatus,
  type CompareStatus,
} from "@/lib/api";

const ALGO_LABELS: Record<string, string> = {
  kmeans: "K-Means",
  kmedoids: "K-Medoids",
  dbscan: "DBSCAN",
};

interface Props {
  formData: FormData;
  onUseAlgorithm: (algo: "kmeans" | "kmedoids" | "dbscan") => void;
}

export function CompareResults({ formData, onUseAlgorithm }: Props) {
  const [status, setStatus] = useState<CompareStatus | null>(null);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!status) return;
    if (status.status === "done" || status.status === "failed") {
      if (status.status === "done") {
        getCompareResult(status.id).then(setResult).catch(() => {});
      }
      return;
    }
    const t = setTimeout(async () => {
      try {
        const next = await getCompareStatus(status.id);
        setStatus(next);
      } catch {
        /* ignore */
      }
    }, 2000);
    return () => clearTimeout(t);
  }, [status]);

  async function handleCompare() {
    setSubmitting(true);
    setError(null);
    try {
      const j = await createCompareJob(formData);
      setStatus(j);
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  }

  if (!status) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" /> Comparar algoritmos
          </CardTitle>
          <CardDescription>
            Roda K-Means, K-Medoids e DBSCAN e recomenda o melhor por silhouette.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={handleCompare} disabled={submitting} data-testid="compare-button">
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Iniciando...
              </>
            ) : (
              "Iniciar comparativo"
            )}
          </Button>
          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Comparativo #{status.id.slice(0, 8)}</CardTitle>
          <StatusBadge status={status.status} />
        </div>
        <CardDescription>{status.message || "—"}</CardDescription>
      </CardHeader>
      <CardContent>
        {!result ? (
          <p className="text-sm text-muted-foreground">
            {status.status === "failed" ? status.message : "Aguardando resultado..."}
          </p>
        ) : (
          <div className="grid gap-4">
            <p className="text-sm">
              Recomendado:{" "}
              <strong className="text-emerald-600" data-testid="winner">
                {ALGO_LABELS[result.winner]}
              </strong>{" "}
              ({result.n_participants} participantes)
            </p>
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="p-2 text-left">Algoritmo</th>
                    <th className="p-2 text-right">Clusters</th>
                    <th className="p-2 text-right">Ruído</th>
                    <th className="p-2 text-right">Silhouette</th>
                    <th className="p-2 text-right">Inertia</th>
                    <th className="p-2 text-right">Runtime (ms)</th>
                    <th className="p-2 text-right">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {result.algorithms.map((a) => (
                    <Row
                      key={a.algorithm}
                      algo={a}
                      isWinner={a.algorithm === result.winner}
                      onUse={onUseAlgorithm}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Row({
  algo,
  isWinner,
  onUse,
}: {
  algo: AlgorithmMetrics;
  isWinner: boolean;
  onUse: (a: "kmeans" | "kmedoids" | "dbscan") => void;
}) {
  return (
    <tr className={isWinner ? "border-t bg-emerald-50 dark:bg-emerald-950/30" : "border-t"}>
      <td className="p-2 font-medium">
        {ALGO_LABELS[algo.algorithm] || algo.algorithm}
        {isWinner && <span className="ml-2 text-xs text-emerald-600">★ recomendado</span>}
      </td>
      <td className="p-2 text-right font-mono">{algo.n_clusters}</td>
      <td className="p-2 text-right font-mono">{algo.n_noise}</td>
      <td className="p-2 text-right font-mono">
        {algo.silhouette != null ? algo.silhouette.toFixed(3) : "—"}
      </td>
      <td className="p-2 text-right font-mono">
        {algo.inertia != null ? algo.inertia.toFixed(0) : "—"}
      </td>
      <td className="p-2 text-right font-mono">{algo.runtime_ms}</td>
      <td className="p-2 text-right">
        <Button
          size="sm"
          variant={isWinner ? "default" : "outline"}
          onClick={() => onUse(algo.algorithm)}
          data-testid={`use-${algo.algorithm}`}
        >
          Usar
        </Button>
      </td>
    </tr>
  );
}
