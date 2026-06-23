import type { Feature, FeatureCollection, Layer, RegionStatus } from "./geojson";

export interface Filters {
  layers: Layer[];
  statuses: RegionStatus[];
  minCapacityRatio: number;
  maxRadiusKm: number | null;
}

export const DEFAULT_FILTERS: Filters = {
  layers: ["region", "school", "participant", "city"],
  statuses: ["ok", "over_capacity", "under_capacity", "empty", "too_large"],
  minCapacityRatio: 0,
  maxRadiusKm: null,
};

export const ALL_LAYERS: Layer[] = ["region", "school", "participant", "city"];
export const ALL_STATUSES: RegionStatus[] = [
  "ok",
  "over_capacity",
  "under_capacity",
  "empty",
  "too_large",
];

export function countRegions(fc: FeatureCollection): number {
  return fc.features.filter((f) => f.properties.layer === "region").length;
}

export function countVisibleRegions(fc: FeatureCollection, filters: Filters): number {
  return filterGeojson(fc, filters).features.filter(
    (f) => f.properties.layer === "region"
  ).length;
}

export function maxCapacity(fc: FeatureCollection): number {
  return fc.features
    .filter((f) => f.properties.layer === "region")
    .reduce((acc, f) => Math.max(acc, f.properties.capacity ?? 0), 0);
}

export function filterGeojson(fc: FeatureCollection, filters: Filters): FeatureCollection {
  const capMax = Math.max(1, maxCapacity(fc));
  const minCapAbsolute = filters.minCapacityRatio * capMax;

  const filtered = fc.features.filter((f) => {
    if (!filters.layers.includes(f.properties.layer)) return false;

    if (f.properties.layer === "region") {
      if (!filters.statuses.includes(f.properties.status as RegionStatus)) return false;
      if (minCapAbsolute > 0 && (f.properties.capacity ?? 0) < minCapAbsolute) {
        return false;
      }
      if (filters.maxRadiusKm != null) {
        const r = (f.properties.max_distance_m ?? 0) / 1000;
        if (r > filters.maxRadiusKm) return false;
      }
    }
    return true;
  });

  return { type: "FeatureCollection", features: filtered };
}
