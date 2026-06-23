"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createJob } from "@/lib/api";
import { SuggestRegionsButton } from "@/components/suggest-regions-button";
import { Upload, MapPin, Users, Building2, Settings2 } from "lucide-react";

export function RegionalizationForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [cityName, setCityName] = useState("Rio de Janeiro");
  const [nRegions, setNRegions] = useState(7);
  const [maxRadius, setMaxRadius] = useState(10);
  const [capacityFactor, setCapacityFactor] = useState(1.2);
  const [participantsFile, setParticipantsFile] = useState<File | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    form.set("city_name", cityName);
    form.set("n_regions", String(nRegions));
    form.set("max_radius_km", String(maxRadius));
    form.set("capacity_factor", String(capacityFactor));

    setLoading(true);
    try {
      const job = await createJob(form);
      toast.success("Job criado", { description: job.id });
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      toast.error("Erro ao criar job", { description: String(err) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-6 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" /> Arquivos
          </CardTitle>
          <CardDescription>XLSX ou CSV. Aceita variações de nomes de colunas.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="shapefile">Shapefile do município (.zip)</Label>
            <Input id="shapefile" name="shapefile" type="file" accept=".zip" required />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="schools" className="flex items-center gap-1">
              <Building2 className="h-4 w-4" /> Escolas
            </Label>
            <Input id="schools" name="schools" type="file" accept=".xlsx,.csv" required />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="participants" className="flex items-center gap-1">
              <Users className="h-4 w-4" /> Participantes
            </Label>
            <Input
              id="participants"
              name="participants"
              type="file"
              accept=".xlsx,.csv"
              required
              onChange={(e) => setParticipantsFile(e.target.files?.[0] ?? null)}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings2 className="h-5 w-5" /> Parâmetros
          </CardTitle>
          <CardDescription>Configuração da regionalização</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="city" className="flex items-center gap-1">
              <MapPin className="h-4 w-4" /> Município
            </Label>
            <Input id="city" value={cityName} onChange={(e) => setCityName(e.target.value)} required />
          </div>
          <div className="grid gap-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="n_regions">Número de regiões</Label>
              <SuggestRegionsButton
                participantsFile={participantsFile}
                onAccept={setNRegions}
              />
            </div>
            <Input
              id="n_regions"
              type="number"
              min={1}
              max={50}
              value={nRegions}
              onChange={(e) => setNRegions(Number(e.target.value))}
              required
              data-testid="n-regions-input"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="max_radius">Raio máximo (km)</Label>
            <Input
              id="max_radius"
              type="number"
              step="0.5"
              min={0}
              value={maxRadius}
              onChange={(e) => setMaxRadius(Number(e.target.value))}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="capacity">Fator de capacidade</Label>
            <Input
              id="capacity"
              type="number"
              step="0.1"
              min={1}
              max={2}
              value={capacityFactor}
              onChange={(e) => setCapacityFactor(Number(e.target.value))}
            />
          </div>
        </CardContent>
      </Card>

      <div className="md:col-span-2 flex justify-end">
        <Button type="submit" size="lg" disabled={loading}>
          {loading ? "Enviando..." : "Iniciar regionalização"}
        </Button>
      </div>
    </form>
  );
}
