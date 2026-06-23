"use client";

import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

import {
  type Feature,
  type FeatureCollection,
  getBounds,
  getFeaturesByLayer,
  isCityFeature,
} from "@/lib/geojson";
import { patchLeafletIcons } from "@/lib/leaflet-icon-fix";
import { getJobGeojson } from "@/lib/api";
import { filterGeojson } from "@/lib/filter-geojson";
import { useFilters } from "@/lib/hooks/use-filters";
import { MapPlaceholder } from "./map-placeholder";
import { RegionPolygon } from "./region-polygon";
import { SchoolMarker } from "./school-marker";
import { ParticipantCluster } from "./participant-cluster";
import { MapFilters } from "./map-filters";

patchLeafletIcons();

function FitBounds({ bounds }: { bounds: L.LatLngBoundsExpression | null }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [20, 20] });
  }, [map, bounds]);
  return null;
}

interface JobMapProps {
  jobId: string;
  status: string;
}

export function JobMap({ jobId, status }: JobMapProps) {
  const [fc, setFc] = useState<FeatureCollection | null>(null);
  const [error, setError] = useState<string | null>(null);

  const done = status === "done";
  const { filters } = useFilters();

  useEffect(() => {
    if (!done) return;
    let cancelled = false;
    setFc(null);
    setError(null);
    getJobGeojson(jobId)
      .then((data) => {
        if (!cancelled) setFc(data);
      })
      .catch((e) => {
        if (!cancelled) setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [jobId, done]);

  const filtered = useMemo(() => (fc ? filterGeojson(fc, filters) : null), [fc, filters]);

  const bounds = useMemo(() => (filtered ? getBounds(filtered) : null), [filtered]);
  const regions = useMemo(
    () => (filtered ? getFeaturesByLayer(filtered, "region") : []),
    [filtered]
  );
  const schools = useMemo(
    () => (filtered ? getFeaturesByLayer(filtered, "school") : []),
    [filtered]
  );
  const participants = useMemo(
    () => (filtered ? getFeaturesByLayer(filtered, "participant") : []),
    [filtered]
  );
  const cities = useMemo(
    () => (filtered ? getFeaturesByLayer(filtered, "city") : []),
    [filtered]
  );

  if (!done) {
    return <MapPlaceholder status={status} />;
  }
  if (error) {
    return <MapPlaceholder status="failed" message={error} />;
  }
  if (!fc || !filtered) {
    return <MapPlaceholder status="loading" loading />;
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <MapFilters fc={fc} />
      </div>
      <div
        data-testid="job-map"
        className="h-96 w-full overflow-hidden rounded-lg border"
      >
        <MapContainer
          center={[-22.9, -43.2]}
          zoom={10}
          style={{ height: "100%", width: "100%" }}
          scrollWheelZoom
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {bounds && <FitBounds bounds={bounds} />}
          {cities.map((f, i) => (
            <CityLayer key={`city-${i}`} feature={f} />
          ))}
          {regions.map((f) => (
            <RegionPolygon key={`region-${f.properties.region_id}`} feature={f} />
          ))}
          {schools.map((f, i) => (
            <SchoolMarker key={`school-${i}`} feature={f} />
          ))}
          <ParticipantCluster features={participants} />
        </MapContainer>
      </div>
    </div>
  );
}

function CityLayer({ feature }: { feature: Feature }) {
  if (!isCityFeature(feature)) return null;
  if (!feature.geometry || feature.geometry.type !== "Polygon") return null;
  return (
    <GeoJSON
      data={feature as unknown as GeoJSON.Feature}
      style={{ color: "#475569", weight: 1, fillOpacity: 0.05, dashArray: "4" }}
    />
  );
}
