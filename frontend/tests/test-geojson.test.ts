import { describe, expect, it } from "vitest";
import {
  type Feature,
  type FeatureCollection,
  getBounds,
  getFeaturesByLayer,
  isCityFeature,
  isParticipantFeature,
  isRegionFeature,
  isSchoolFeature,
} from "@/lib/geojson";

function point(lon: number, lat: number, layer: "region" | "school" | "participant" | "city", extra: Record<string, unknown> = {}): Feature {
  return {
    type: "Feature",
    geometry: { type: "Point", coordinates: [lon, lat] },
    properties: { layer, ...extra },
  };
}

function polygon(rings: [number, number][][], layer: "region" | "city" = "region", extra: Record<string, unknown> = {}): Feature {
  return {
    type: "Feature",
    geometry: { type: "Polygon", coordinates: rings },
    properties: { layer, ...extra },
  };
}

describe("geojson utils", () => {
  const fc: FeatureCollection = {
    type: "FeatureCollection",
    features: [
      point(-43.2, -22.9, "school", { name: "E1", capacity: 50 }),
      point(-43.21, -22.91, "school", { name: "E2", capacity: 30 }),
      point(-43.22, -22.92, "participant"),
      polygon([[[-43.2, -22.9], [-43.1, -22.9], [-43.1, -23.0], [-43.2, -23.0], [-43.2, -22.9]]], "region", { region_id: 0 }),
      polygon([[[-43.3, -22.8], [-43.0, -22.8], [-43.0, -23.1], [-43.3, -23.1], [-43.3, -22.8]]], "city", { name: "Rio" }),
    ],
  };

  it("filters by layer", () => {
    expect(getFeaturesByLayer(fc, "school")).toHaveLength(2);
    expect(getFeaturesByLayer(fc, "region")).toHaveLength(1);
    expect(getFeaturesByLayer(fc, "participant")).toHaveLength(1);
    expect(getFeaturesByLayer(fc, "city")).toHaveLength(1);
  });

  it("isXFeature discriminators work", () => {
    expect(isSchoolFeature(fc.features[0])).toBe(true);
    expect(isRegionFeature(fc.features[3])).toBe(true);
    expect(isParticipantFeature(fc.features[2])).toBe(true);
    expect(isCityFeature(fc.features[4])).toBe(true);
  });

  it("computes bounds across points and polygons", () => {
    const bounds = getBounds(fc);
    expect(bounds).not.toBeNull();
    const [[minLat, minLon], [maxLat, maxLon]] = bounds!;
    expect(minLat).toBeCloseTo(-23.1, 5);
    expect(minLon).toBeCloseTo(-43.3, 5);
    expect(maxLat).toBeCloseTo(-22.8, 5);
    expect(maxLon).toBeCloseTo(-43.0, 5);
  });

  it("returns null bounds for empty collection", () => {
    expect(getBounds({ type: "FeatureCollection", features: [] })).toBeNull();
  });
});
