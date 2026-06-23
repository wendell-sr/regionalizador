import Link from "next/link";
import { Button } from "@/components/ui/button";
import { RegionalizationForm } from "@/components/regionalization-form";
import { GeocodingForm } from "@/components/geocoding-form";

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

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Regionalização</h2>
        <p className="text-sm text-muted-foreground">
          Envie shapefile, escolas e participantes. Acompanhe o resultado com mapa interativo.
        </p>
        <RegionalizationForm />
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Geocoding de Escolas/Participantes</h2>
        <p className="text-sm text-muted-foreground">
          Resolve CEP ou endereço em lat/lon antes de gerar o XLSX. Útil quando o arquivo original
          não tem coordenadas.
        </p>
        <GeocodingForm />
      </section>
    </main>
  );
}
