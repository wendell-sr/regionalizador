import type { FeatureCollection } from "./geojson";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export type JobStatus = {
  id: string;
  status: string;
  progress: number;
  message: string;
  metrics: Record<string, unknown>;
};

export type KScore = {
  k: number;
  silhouette: number | null;
  inertia: number | null;
};

export type SuggestRegionsPayload = {
  participants: { lat: number | null; lon: number | null; qty: number }[];
  city_name?: string;
  target_crs?: string;
};

export type SuggestRegionsResult = {
  recommended: number;
  n_participants: number;
  scores: KScore[];
};

export type GeocodingJobStatus = {
  id: string;
  status: string;
  total: number;
  processed: number;
  succeeded: number;
  failed: number;
  progress: number;
  message: string;
};

export type GeocodedItem = {
  index: number;
  input: string;
  lat: number | null;
  lon: number | null;
  source: string | null;
  success: boolean;
};

export type GeocodedResult = {
  items: GeocodedItem[];
};

export async function createJob(form: FormData): Promise<JobStatus> {
  const res = await fetch(`${API_URL}/jobs`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getJob(id: string): Promise<JobStatus> {
  const res = await fetch(`${API_URL}/jobs/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getJobGeojson(id: string): Promise<FeatureCollection> {
  const res = await fetch(`${API_URL}/jobs/${id}/geojson`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function suggestRegions(payload: SuggestRegionsPayload): Promise<SuggestRegionsResult> {
  const res = await fetch(`${API_URL}/jobs/suggest-regions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createGeocodingJob(file: File): Promise<GeocodingJobStatus> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/jobs/geocode`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getGeocodingJob(id: string): Promise<GeocodingJobStatus> {
  const res = await fetch(`${API_URL}/jobs/geocoding/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getGeocodedResult(id: string): Promise<GeocodedResult> {
  const res = await fetch(`${API_URL}/jobs/geocoding/${id}/geocoded`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function geocodedFileUrl(id: string, name: "geocoded.xlsx" | "failed_only.xlsx") {
  return `${API_URL}/jobs/geocoding/${id}/files/${name}`;
}

export type CompareStatus = {
  id: string;
  status: string;
  progress: number;
  message: string;
};

export type AlgorithmMetrics = {
  algorithm: "kmeans" | "kmedoids" | "dbscan";
  n_clusters: number;
  n_noise: number;
  silhouette: number | null;
  inertia: number | null;
  runtime_ms: number;
};

export type CompareResult = {
  winner: "kmeans" | "kmedoids" | "dbscan";
  n_participants: number;
  algorithms: AlgorithmMetrics[];
};

export async function createCompareJob(form: FormData): Promise<CompareStatus> {
  const res = await fetch(`${API_URL}/jobs/compare`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCompareStatus(id: string): Promise<CompareStatus> {
  const res = await fetch(`${API_URL}/jobs/compare/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCompareResult(id: string): Promise<CompareResult> {
  const res = await fetch(`${API_URL}/jobs/compare/${id}/compare`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function fileUrl(id: string, name: string) {
  return `${API_URL}/jobs/${id}/files/${name}`;
}
