"use client";

import { Polygon, Popup } from "react-leaflet";
import type { Feature } from "@/lib/geojson";
import { getStatusColor, getStatusLabel } from "@/lib/map-colors";

export function RegionPolygon({ feature }: { feature: Feature }) {
  if (!feature.geometry || feature.geometry.type !== "Polygon") return null;
  const positions = feature.geometry.coordinates[0].map(
    ([lon, lat]) => [lat, lon] as [number, number]
  );
  const color = getStatusColor(feature.properties.status);
  const p = feature.properties;

  return (
    <Polygon
      pathOptions={{ color, fillColor: color, fillOpacity: 0.25, weight: 2 }}
      positions={positions}
    >
      <Popup>
        <div className="text-sm">
          <div className="font-semibold">Região {p.region_id}</div>
          <div className="text-muted-foreground">
            Status: {getStatusLabel(p.status)}
          </div>
          <div className="mt-1">
            Candidatos: <strong>{p.candidates}</strong> · Capacidade:{" "}
            <strong>{p.capacity}</strong>
          </div>
          <div>
            Escolas: {p.schools} · Participantes: {p.participants}
          </div>
          {p.max_distance_m !== undefined && (
            <div>Raio máx: {p.max_distance_m} m</div>
          )}
        </div>
      </Popup>
    </Polygon>
  );
}
