"use client";

import { useCallback, useMemo } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { ALL_LAYERS, ALL_STATUSES, DEFAULT_FILTERS, type Filters } from "@/lib/filter-geojson";
import type { Layer, RegionStatus } from "@/lib/geojson";

function parseLayer(v: string | null): Layer[] {
  if (!v) return DEFAULT_FILTERS.layers;
  return ALL_LAYERS.filter((l) => v.split(",").includes(l));
}

function parseStatus(v: string | null): RegionStatus[] {
  if (!v) return DEFAULT_FILTERS.statuses;
  return ALL_STATUSES.filter((s) => v.split(",").includes(s));
}

function parseMinCap(v: string | null): number {
  if (v == null) return DEFAULT_FILTERS.minCapacityRatio;
  const n = Number(v);
  return Number.isFinite(n) ? Math.max(0, Math.min(1, n)) : DEFAULT_FILTERS.minCapacityRatio;
}

function parseMaxRadius(v: string | null): number | null {
  if (v == null || v === "") return DEFAULT_FILTERS.maxRadiusKm;
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : DEFAULT_FILTERS.maxRadiusKm;
}

export function useFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const filters: Filters = useMemo(
    () => ({
      layers: parseLayer(searchParams.get("layers")),
      statuses: parseStatus(searchParams.get("statuses")),
      minCapacityRatio: parseMinCap(searchParams.get("minCap")),
      maxRadiusKm: parseMaxRadius(searchParams.get("maxRadius")),
    }),
    [searchParams]
  );

  const update = useCallback(
    (next: Filters) => {
      const params = new URLSearchParams(searchParams.toString());
      if (
        next.layers.length === ALL_LAYERS.length ||
        next.layers.join(",") === ALL_LAYERS.join(",")
      ) {
        params.delete("layers");
      } else {
        params.set("layers", next.layers.join(","));
      }
      if (next.statuses.length === ALL_STATUSES.length) {
        params.delete("statuses");
      } else {
        params.set("statuses", next.statuses.join(","));
      }
      if (next.minCapacityRatio === 0) params.delete("minCap");
      else params.set("minCap", String(next.minCapacityRatio));
      if (next.maxRadiusKm == null) params.delete("maxRadius");
      else params.set("maxRadius", String(next.maxRadiusKm));

      const qs = params.toString();
      const target = `${pathname}${qs ? "?" + qs : ""}`;
      const current = `${pathname}${searchParams.toString() ? "?" + searchParams.toString() : ""}`;
      if (target === current) return;
      router.replace(target, { scroll: false });
    },
    [router, pathname, searchParams]
  );

  const setLayer = useCallback(
    (layer: Layer, visible: boolean) => {
      const set = new Set(filters.layers);
      if (visible) set.add(layer);
      else set.delete(layer);
      update({ ...filters, layers: Array.from(set) });
    },
    [filters, update]
  );

  const setStatus = useCallback(
    (status: RegionStatus, visible: boolean) => {
      const set = new Set(filters.statuses);
      if (visible) set.add(status);
      else set.delete(status);
      update({ ...filters, statuses: Array.from(set) });
    },
    [filters, update]
  );

  const setMinCapacity = useCallback(
    (n: number) => update({ ...filters, minCapacityRatio: n }),
    [filters, update]
  );

  const setMaxRadius = useCallback(
    (km: number | null) => update({ ...filters, maxRadiusKm: km }),
    [filters, update]
  );

  const clear = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    ["layers", "statuses", "minCap", "maxRadius"].forEach((k) => params.delete(k));
    const qs = params.toString();
    router.replace(`${pathname}${qs ? "?" + qs : ""}`, { scroll: false });
  }, [router, pathname, searchParams]);

  return { filters, setLayer, setStatus, setMinCapacity, setMaxRadius, clear };
}
