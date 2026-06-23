"use client";

import { Marker, Popup } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import type { Feature } from "@/lib/geojson";

const participantIcon = L.divIcon({
  className: "participant-marker",
  html: '<div style="background:#7c3aed;width:8px;height:8px;border-radius:50%;border:1px solid white;box-shadow:0 1px 2px rgba(0,0,0,0.3)"></div>',
  iconSize: [8, 8],
  iconAnchor: [4, 4],
});

export function ParticipantCluster({ features }: { features: Feature[] }) {
  const points: [number, number][] = features
    .filter((f) => f.geometry?.type === "Point")
    .map((f) => {
      const [lon, lat] = (f.geometry as { coordinates: [number, number] }).coordinates;
      return [lat, lon] as [number, number];
    });

  return (
    <MarkerClusterGroup chunkedLoading>
      {points.map((pos, i) => {
        const f = features[i];
        return (
          <Marker key={i} position={pos} icon={participantIcon}>
            <Popup>
              <div className="text-sm">
                Participante
                {f.properties.qty && f.properties.qty > 1
                  ? ` (x${f.properties.qty})`
                  : ""}
                {f.properties.region_id != null && (
                  <div>Região: {f.properties.region_id}</div>
                )}
              </div>
            </Popup>
          </Marker>
        );
      })}
    </MarkerClusterGroup>
  );
}
