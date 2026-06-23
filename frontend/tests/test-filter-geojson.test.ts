import { describe, expect, it } from "vitest";
import {
  countRegions,
  countVisibleRegions,
  DEFAULT_FILTERS,
  filterGeojson,
  maxCapacity,
  type Filters,
} from "@/lib/filter-geojson";
import type { FeatureCollection, RegionStatus } from "@/lib/geojson";

function region(
  region_id: number,
  status: RegionStatus,
  capacity: number,
  max_distance_m: number
) {
  return {
    type: "Feature" as const,
    geometry: { type: "Polygon" as const, coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] },
    properties: { layer: "region" as const, region_id, status, capacity, max_distance_m },
  };
}

function school(i: number) {
  return {
    type: "Feature" as const,
    geometry: { type: "Point" as const, coordinates: [0, 0] },
    properties: { layer: "school" as const, name: `E${i}`, capacity: 10, region_id: 0 },
  };
}

function participant(i: number) {
  return {
    type: "Feature" as const,
    geometry: { type: "Point" as const, coordinates: [0, 0] },
    properties: { layer: "participant" as const, qty: 1, region_id: 0 },
  };
}

const fc: FeatureCollection = {
  type: "FeatureCollection",
  features: [
    region(0, "ok", 50, 500),
    region(1, "over_capacity", 20, 1500),
    region(2, "under_capacity", 80, 3000),
    region(3, "empty", 0, 0),
    school(0),
    school(1),
    participant(0),
  ],
};

describe("filterGeojson", () => {
  it("returns all features with default filters", () => {
    const out = filterGeojson(fc, DEFAULT_FILTERS);
    expect(out.features.length).toBe(fc.features.length);
  });

  it("filters by layer", () => {
    const filters: Filters = { ...DEFAULT_FILTERS, layers: ["region"] };
    const out = filterGeojson(fc, filters);
    expect(out.features.every((f) => f.properties.layer === "region")).toBe(true);
    expect(out.features.length).toBe(4);
  });

  it("filters by status", () => {
    const filters: Filters = { ...DEFAULT_FILTERS, statuses: ["ok"] };
    const out = filterGeojson(fc, filters);
    const regions = out.features.filter((f) => f.properties.layer === "region");
    expect(regions.length).toBe(1);
    expect(regions[0].properties.status).toBe("ok");
  });

  it("filters by min capacity (ratio)", () => {
    const filters: Filters = { ...DEFAULT_FILTERS, minCapacityRatio: 0.5 };
    const out = filterGeojson(fc, filters);
    const regions = out.features.filter((f) => f.properties.layer === "region");
    // capMax=80, min=40. Aceita regions com cap 50 e 80.
    expect(regions.length).toBe(2);
  });

  it("filters by max radius in km", () => {
    const filters: Filters = { ...DEFAULT_FILTERS, maxRadiusKm: 1 };
    const out = filterGeojson(fc, filters);
    const regions = out.features.filter((f) => f.properties.layer === "region");
    // max_distances 500m=0.5, 1500m=1.5 (excluído), 3000m=3 (excluído), 0m=0
    expect(regions.length).toBe(2);
  });

  it("null maxRadiusKm means no limit", () => {
    const filters: Filters = { ...DEFAULT_FILTERS, maxRadiusKm: null };
    const out = filterGeojson(fc, filters);
    expect(out.features.length).toBe(fc.features.length);
  });

  it("countRegions returns number of region features", () => {
    expect(countRegions(fc)).toBe(4);
  });

  it("countVisibleRegions respects filters", () => {
    const filters: Filters = { ...DEFAULT_FILTERS, statuses: ["ok", "empty"] };
    expect(countVisibleRegions(fc, filters)).toBe(2);
  });

  it("maxCapacity returns highest capacity", () => {
    expect(maxCapacity(fc)).toBe(80);
  });

  it("combines multiple filters", () => {
    const filters: Filters = {
      ...DEFAULT_FILTERS,
      layers: ["region"],
      statuses: ["ok", "under_capacity"],
      minCapacityRatio: 0.5,
    };
    const out = filterGeojson(fc, filters);
    expect(out.features.length).toBe(2);
  });

  it("empty fc returns empty", () => {
    const out = filterGeojson({ type: "FeatureCollection", features: [] }, DEFAULT_FILTERS);
    expect(out.features).toEqual([]);
  });
});
