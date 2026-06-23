"use client";

import L from "leaflet";

let patched = false;

export function patchLeafletIcons(): void {
  if (patched || typeof window === "undefined") return;
  patched = true;

  const iconRetinaUrl = new URL("leaflet/dist/images/marker-icon-2x.png", import.meta.url).toString();
  const iconUrl = new URL("leaflet/dist/images/marker-icon.png", import.meta.url).toString();
  const shadowUrl = new URL("leaflet/dist/images/marker-shadow.png", import.meta.url).toString();

  delete (L.Icon.Default.prototype as { _getIconUrl?: unknown })._getIconUrl;
  L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl });
}
