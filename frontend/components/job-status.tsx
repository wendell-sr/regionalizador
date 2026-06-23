"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";
import { BarChart3, Download, FileSpreadsheet, Map as MapIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { getJob, type JobStatus } from "@/lib/api";

const JobMap = dynamic(
  () => import("@/components/map/job-map").then((m) => m.JobMap),
  { ssr: false, loading: () => null }
);

export function JobStatusView({ id }: { id: string }) {
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const j = await getJob(id);
        if (!cancelled) setJob(j);
        if (j.status !== "done" && j.status !== "failed") {
          setTimeout(poll, 2000);
        }
      } catch (e) {
        if (!cancelled) setError(String(e));
      }
    }
    poll();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) return <p className="text-destructive">Erro: {error}</p>;
  if (!job) return <p>Carregando...</p>;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Job {job.id.slice(0, 8)}</CardTitle>
            <StatusBadge status={job.status} />
          </div>
          <CardDescription>{job.message || "—"}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <Progress value={Math.round(job.progress * 100)} />
          {Object.keys(job.metrics).length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
              {Object.entries(job.metrics).map(([k, v]) => (
                <div key={k} className="rounded-md border p-3">
                  <p className="text-xs text-muted-foreground">{k}</p>
                  <p className="text-lg font-semibold">{String(v)}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {job.status === "done" && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Download className="h-4 w-4" /> Downloads
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <a
                href={`/api/backend/jobs/${job.id}/files/regionalizacao_regioes.xlsx`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm hover:bg-accent"
              >
                <FileSpreadsheet className="h-4 w-4" /> regionalizacao_regioes.xlsx
              </a>
              <a
                href={`/api/backend/jobs/${job.id}/files/regionalizacao_escolas.xlsx`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm hover:bg-accent"
              >
                <FileSpreadsheet className="h-4 w-4" /> regionalizacao_escolas.xlsx
              </a>
              <a
                href={`/api/backend/jobs/${job.id}/files/regionalizacao_participantes.xlsx`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm hover:bg-accent"
              >
                <FileSpreadsheet className="h-4 w-4" /> regionalizacao_participantes.xlsx
              </a>
              <a
                href={`/api/backend/jobs/${job.id}/files/regioes.kml`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm hover:bg-accent"
              >
                <MapIcon className="h-4 w-4" /> regioes.kml
              </a>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <BarChart3 className="h-4 w-4" /> Análise avançada
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Compare K-Means, K-Medoids e DBSCAN nos mesmos dados.
              </p>
              <Button asChild className="w-full">
                <Link href={`/jobs/${job.id}/compare`}>
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Comparar algoritmos
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <MapIcon className="h-4 w-4" /> Mapa
          </CardTitle>
        </CardHeader>
        <CardContent>
          <JobMap jobId={job.id} status={job.status} />
        </CardContent>
      </Card>
    </div>
  );
}
