import { Suspense } from "react";
import { JobStatusView } from "@/components/job-status";

export default async function JobPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <main className="container py-10 space-y-6">
      <h1 className="text-2xl font-bold">Acompanhamento</h1>
      <Suspense fallback={<p>Carregando…</p>}>
        <JobStatusView id={id} />
      </Suspense>
    </main>
  );
}
