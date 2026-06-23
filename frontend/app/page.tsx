import Link from "next/link";
import { Button } from "@/components/ui/button";
import { GeocodingForm } from "@/components/geocoding-form";
import { FormWithTabs } from "@/components/form-with-tabs";

export default function Home() {
  return (
    <main className="container py-10 space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Regionalizador</h1>
          <p className="text-muted-foreground">Distribua participantes em regiões geográficas</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/jobs">Meus jobs</Link>
        </Button>
      </header>
      <div className="grid gap-6 md:grid-cols-2">
        <FormWithTabs />
        <GeocodingForm />
      </div>
    </main>
  );
}
