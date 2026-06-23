"use client";

import * as React from "react";
import { Filter, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  ALL_LAYERS,
  ALL_STATUSES,
  countVisibleRegions,
  maxCapacity,
} from "@/lib/filter-geojson";
import { useFilters } from "@/lib/hooks/use-filters";
import { getStatusLabel, STATUS_COLORS } from "@/lib/map-colors";
import type { FeatureCollection, Layer, RegionStatus } from "@/lib/geojson";

const LAYER_LABELS: Record<Layer, string> = {
  region: "Regiões",
  school: "Escolas",
  participant: "Participantes",
  city: "Município",
};

interface MapFiltersProps {
  fc: FeatureCollection;
}

export function MapFilters({ fc }: MapFiltersProps) {
  const { filters, setLayer, setStatus, setMinCapacity, setMaxRadius, clear } = useFilters();
  const capMax = maxCapacity(fc);
  const total = fc.features.filter((f) => f.properties.layer === "region").length;
  const visible = countVisibleRegions(fc, filters);

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" data-testid="open-filters">
          <Filter className="mr-2 h-4 w-4" />
          Filtros
        </Button>
      </SheetTrigger>
      <SheetContent side="right" data-testid="filters-sheet">
        <SheetHeader>
          <SheetTitle>Filtros do mapa</SheetTitle>
          <SheetDescription>
            Mostrando <strong data-testid="visible-count">{visible}</strong> de{" "}
            <strong>{total}</strong> regiões
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 grid gap-6">
          <section className="grid gap-3">
            <h3 className="text-sm font-medium">Camadas</h3>
            {ALL_LAYERS.map((layer) => (
              <div key={layer} className="flex items-center space-x-2">
                <Checkbox
                  id={`layer-${layer}`}
                  checked={filters.layers.includes(layer)}
                  onCheckedChange={(c) => setLayer(layer, !!c)}
                  data-testid={`toggle-layer-${layer}`}
                />
                <Label htmlFor={`layer-${layer}`}>{LAYER_LABELS[layer]}</Label>
              </div>
            ))}
          </section>

          <section className="grid gap-3">
            <h3 className="text-sm font-medium">Status de região</h3>
            {ALL_STATUSES.map((status) => (
              <div key={status} className="flex items-center space-x-2">
                <Checkbox
                  id={`status-${status}`}
                  checked={filters.statuses.includes(status)}
                  onCheckedChange={(c) => setStatus(status, !!c)}
                  data-testid={`toggle-status-${status}`}
                />
                <span
                  className="h-3 w-3 rounded-sm"
                  style={{ background: STATUS_COLORS[status] }}
                  aria-hidden
                />
                <Label htmlFor={`status-${status}`}>{getStatusLabel(status)}</Label>
              </div>
            ))}
          </section>

          <section className="grid gap-3">
            <h3 className="text-sm font-medium">
              Capacidade mínima ({Math.round(filters.minCapacityRatio * 100)}% do máximo)
            </h3>
            <Slider
              min={0}
              max={100}
              step={5}
              value={[Math.round(filters.minCapacityRatio * 100)]}
              onValueChange={(v) => setMinCapacity((v[0] ?? 0) / 100)}
              aria-label="Capacidade mínima"
              data-testid="slider-capacity"
            />
          </section>

          <section className="grid gap-3">
            <h3 className="text-sm font-medium">Raio máximo (km)</h3>
            <Input
              type="number"
              min={0}
              step="0.5"
              placeholder="Sem limite"
              value={filters.maxRadiusKm ?? ""}
              onChange={(e) => {
                const v = e.target.value;
                setMaxRadius(v === "" ? null : Number(v));
              }}
              data-testid="input-max-radius"
            />
            <p className="text-xs text-muted-foreground">Vazio = sem limite</p>
          </section>

          <Button
            variant="ghost"
            onClick={clear}
            data-testid="clear-filters"
            className="mt-2"
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Limpar filtros
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
