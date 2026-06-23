"use client";

import { Marker, Popup } from "react-leaflet";
import L from "leaflet";
import type { Feature } from "@/lib/geojson";

const schoolIcon = L.divIcon({
  className: "school-marker",
  html: '<div style="background:#2563eb;width:14px;height:14px;border-radius:3px;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.4)"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

export function SchoolMarker({ feature }: { feature: Feature }) {
  if (!feature.geometry || feature.geometry.type !== "Point") return null;
  const [lon, lat] = feature.geometry.coordinates;
  const p = feature.properties;

  return (
    <Marker position={[lat, lon]} icon={schoolIcon}>
      <Popup>
        <div className="text-sm">
          <div className="font-semibold">{p.name || "Escola"}</div>
          <div>Capacidade: {p.capacity ?? 0}</div>
          {p.region_id != null && <div>Região: {p.region_id}</div>}
        </div>
      </Popup>
    </Marker>
  );
}
