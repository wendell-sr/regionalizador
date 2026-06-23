"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StatusBadge } from "@/components/status-badge";
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
        {job.status === "done" && (
          <div className="flex gap-2 pt-4">
            <a
              href={`/api/backend/jobs/${job.id}/files/regionalizacao_regioes.xlsx`}
              className="underline text-sm"
              target="_blank"
            >
              Baixar XLSX
            </a>
            <a
              href={`/api/backend/jobs/${job.id}/files/regioes.kml`}
              className="underline text-sm"
              target="_blank"
            >
              Baixar KML
            </a>
          </div>
        )}
      </CardContent>
      <CardContent>
        <h2 className="mb-2 text-sm font-medium">Mapa</h2>
        <JobMap jobId={job.id} status={job.status} />
      </CardContent>
    </Card>
  );
}
