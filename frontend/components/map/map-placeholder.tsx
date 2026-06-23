"use client";

import { Loader2, MapPin } from "lucide-react";

export function MapPlaceholder({
  status,
  message,
  loading = false,
}: {
  status: string;
  message?: string;
  loading?: boolean;
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="map-placeholder"
      className="flex h-96 w-full flex-col items-center justify-center rounded-lg border border-dashed bg-muted/30 text-muted-foreground"
    >
      {loading ? (
        <>
          <Loader2 className="h-8 w-8 animate-spin" aria-hidden />
          <p className="mt-2 text-sm">Carregando mapa…</p>
        </>
      ) : (
        <>
          <MapPin className="h-8 w-8" aria-hidden />
          <p className="mt-2 text-sm font-medium">Mapa indisponível</p>
          <p className="text-xs">Status: {status}</p>
          {message && <p className="mt-1 max-w-md text-xs">{message}</p>}
        </>
      )}
    </div>
  );
}
