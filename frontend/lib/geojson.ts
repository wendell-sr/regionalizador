export type RegionStatus =
  | "ok"
  | "over_capacity"
  | "under_capacity"
  | "empty"
  | "too_large";

export type Geometry =
  | { type: "Point"; coordinates: [number, number] }
  | { type: "Polygon"; coordinates: [number, number][][] }
  | { type: "MultiPolygon"; coordinates: [number, number][][][] }
  | null;

export type Layer = "region" | "school" | "participant" | "city";

export interface FeatureProperties {
  layer: Layer;
  region_id?: number | null;
  status?: RegionStatus;
  name?: string;
  capacity?: number;
  qty?: number;
  candidates?: number;
  participants?: number;
  schools?: number;
  max_distance_m?: number;
}

export interface Feature {
  type: "Feature";
  geometry: Geometry;
  properties: FeatureProperties;
}

export interface FeatureCollection {
  type: "FeatureCollection";
  features: Feature[];
}

export function getFeaturesByLayer(fc: FeatureCollection, layer: Layer): Feature[] {
  return fc.features.filter((f) => f.properties.layer === layer);
}

export function isRegionFeature(f: Feature): boolean {
  return f.properties.layer === "region";
}

export function isSchoolFeature(f: Feature): boolean {
  return f.properties.layer === "school";
}

export function isParticipantFeature(f: Feature): boolean {
  return f.properties.layer === "participant";
}

export function isCityFeature(f: Feature): boolean {
  return f.properties.layer === "city";
}

export function getBounds(fc: FeatureCollection): [[number, number], [number, number]] | null {
  let minLon = Infinity;
  let minLat = Infinity;
  let maxLon = -Infinity;
  let maxLat = -Infinity;
  let found = false;

  for (const f of fc.features) {
    const g = f.geometry;
    if (!g) continue;
    if (g.type === "Point") {
      const [lon, lat] = g.coordinates;
      minLon = Math.min(minLon, lon);
      minLat = Math.min(minLat, lat);
      maxLon = Math.max(maxLon, lon);
      maxLat = Math.max(maxLat, lat);
      found = true;
    } else if (g.type === "Polygon") {
      for (const ring of g.coordinates) {
        for (const [lon, lat] of ring) {
          minLon = Math.min(minLon, lon);
          minLat = Math.min(minLat, lat);
          maxLon = Math.max(maxLon, lon);
          maxLat = Math.max(maxLat, lat);
          found = true;
        }
      }
    }
  }

  if (!found) return null;
  return [
    [minLat, minLon],
    [maxLat, maxLon],
  ];
}
