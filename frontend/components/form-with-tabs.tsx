"use client";

import { useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RegionalizationForm } from "@/components/regionalization-form";
import { CompareResults } from "@/components/compare-results";
import { toast } from "sonner";

interface UploadedFiles {
  schools: File | null;
  participants: File | null;
  shapefile: File | null;
}

export function FormWithTabs() {
  const [files, setFiles] = useState<UploadedFiles>({
    schools: null,
    participants: null,
    shapefile: null,
  });
  const [cityName, setCityName] = useState("Rio de Janeiro");
  const [nClustersHint, setNClustersHint] = useState(7);
  const formRef = useRef<HTMLFormElement>(null);

  function buildCompareFormData(): FormData | null {
    if (!files.schools || !files.participants || !files.shapefile) {
      toast.error("Anexe os 3 arquivos antes de comparar");
      return null;
    }
    const fd = new FormData();
    fd.append("schools", files.schools);
    fd.append("participants", files.participants);
    fd.append("shapefile", files.shapefile);
    fd.append("city_name", cityName);
    fd.append("n_clusters_hint", String(nClustersHint));
    return fd;
  }

  return (
    <Tabs defaultValue="regionalize" className="w-full">
      <TabsList>
        <TabsTrigger value="regionalize">Regionalizar</TabsTrigger>
        <TabsTrigger value="compare">Comparar algoritmos</TabsTrigger>
      </TabsList>

      <TabsContent value="regionalize">
        <FilePickers
          files={files}
          onFilesChange={setFiles}
          onCityChange={setCityName}
          cityName={cityName}
        >
          <RegionalizationForm />
        </FilePickers>
      </TabsContent>

      <TabsContent value="compare">
        <div className="grid gap-4">
          <FilePickers
            files={files}
            onFilesChange={setFiles}
            onCityChange={setCityName}
            cityName={cityName}
            showNClusters
            nClusters={nClustersHint}
            onNClustersChange={setNClustersHint}
          />
          <CompareResults
            formData={buildCompareFormData() as FormData}
            onUseAlgorithm={(algo) => {
              toast.success("Algoritmo selecionado", {
                description: `${algo} será usado no próximo job`,
              });
            }}
          />
        </div>
      </TabsContent>
    </Tabs>
  );
}

function FilePickers({
  files,
  onFilesChange,
  onCityChange,
  cityName,
  showNClusters,
  nClusters,
  onNClustersChange,
  children,
}: {
  files: UploadedFiles;
  onFilesChange: (f: UploadedFiles) => void;
  onCityChange: (c: string) => void;
  cityName: string;
  showNClusters?: boolean;
  nClusters?: number;
  onNClustersChange?: (n: number) => void;
  children?: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Arquivos + município</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        <div className="grid gap-1">
          <label className="text-sm font-medium" htmlFor="shared-shapefile">
            Shapefile (.zip)
          </label>
          <input
            id="shared-shapefile"
            type="file"
            accept=".zip"
            onChange={(e) =>
              onFilesChange({ ...files, shapefile: e.target.files?.[0] ?? null })
            }
            className="text-sm file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1 file:text-primary-foreground"
          />
        </div>
        <div className="grid gap-1">
          <label className="text-sm font-medium" htmlFor="shared-schools">
            Escolas (XLSX/CSV)
          </label>
          <input
            id="shared-schools"
            type="file"
            accept=".xlsx,.csv"
            onChange={(e) =>
              onFilesChange({ ...files, schools: e.target.files?.[0] ?? null })
            }
            className="text-sm file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1 file:text-primary-foreground"
          />
        </div>
        <div className="grid gap-1">
          <label className="text-sm font-medium" htmlFor="shared-participants">
            Participantes (XLSX/CSV)
          </label>
          <input
            id="shared-participants"
            type="file"
            accept=".xlsx,.csv"
            onChange={(e) =>
              onFilesChange({ ...files, participants: e.target.files?.[0] ?? null })
            }
            className="text-sm file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1 file:text-primary-foreground"
          />
        </div>
        <div className="grid gap-1">
          <label className="text-sm font-medium" htmlFor="shared-city">
            Município
          </label>
          <input
            id="shared-city"
            type="text"
            value={cityName}
            onChange={(e) => onCityChange(e.target.value)}
            className="rounded-md border bg-background px-3 py-1 text-sm"
            data-testid="shared-city"
          />
        </div>
        {showNClusters && onNClustersChange && (
          <div className="grid gap-1">
            <label className="text-sm font-medium" htmlFor="shared-k">
              K (sugestão inicial)
            </label>
            <input
              id="shared-k"
              type="number"
              min={2}
              max={15}
              value={nClusters}
              onChange={(e) => onNClustersChange(Number(e.target.value))}
              className="rounded-md border bg-background px-3 py-1 text-sm"
            />
          </div>
        )}
        {children}
      </CardContent>
    </Card>
  );
}
