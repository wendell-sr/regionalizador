import type { RegionStatus } from "./geojson";

export const STATUS_COLORS: Record<RegionStatus, string> = {
  ok: "#10b981",
  over_capacity: "#ef4444",
  under_capacity: "#f59e0b",
  empty: "#94a3b8",
  too_large: "#f97316",
};

export const STATUS_LABELS: Record<RegionStatus, string> = {
  ok: "OK",
  over_capacity: "Acima da capacidade",
  under_capacity: "Abaixo da capacidade",
  empty: "Vazia",
  too_large: "Raio excedido",
};

export function getStatusColor(status: string | undefined): string {
  if (!status) return STATUS_COLORS.ok;
  return (STATUS_COLORS as Record<string, string>)[status] ?? STATUS_COLORS.ok;
}

export function getStatusLabel(status: string | undefined): string {
  if (!status) return STATUS_LABELS.ok;
  return (STATUS_LABELS as Record<string, string>)[status] ?? status;
}
