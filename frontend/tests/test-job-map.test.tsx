import * as React from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MapPlaceholder } from "@/components/map/map-placeholder";
import { getStatusColor } from "@/lib/map-colors";

vi.mock("@/lib/api", () => ({
  getJobGeojson: vi.fn(),
}));

vi.mock("@/lib/leaflet-icon-fix", () => ({
  patchLeafletIcons: vi.fn(),
}));

vi.mock("@/lib/hooks/use-filters", () => ({
  useFilters: () => ({
    filters: {
      layers: ["region", "school", "participant", "city"],
      statuses: ["ok", "over_capacity", "under_capacity", "empty", "too_large"],
      minCapacityRatio: 0,
      maxRadiusKm: null,
    },
    setLayer: vi.fn(),
    setStatus: vi.fn(),
    setMinCapacity: vi.fn(),
    setMaxRadius: vi.fn(),
    clear: vi.fn(),
  }),
}));

vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  GeoJSON: () => <div data-testid="geojson-layer" />,
  Marker: ({ children }: { children: React.ReactNode }) => <div data-testid="marker">{children}</div>,
  Popup: ({ children }: { children: React.ReactNode }) => <div data-testid="popup">{children}</div>,
  Polygon: ({ children }: { children: React.ReactNode }) => <div data-testid="polygon">{children}</div>,
  useMap: () => ({ fitBounds: vi.fn() }),
}));

vi.mock("react-leaflet-cluster", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="cluster">{children}</div>,
}));

import { JobMap } from "@/components/map/job-map";
import { getJobGeojson } from "@/lib/api";

const mockGetJobGeojson = vi.mocked(getJobGeojson);

describe("MapPlaceholder", () => {
  it("shows status and message for non-done jobs", () => {
    render(<MapPlaceholder status="loading" message="Aguarde" />);
    expect(screen.getByTestId("map-placeholder")).toBeInTheDocument();
    expect(screen.getByText("Status: loading")).toBeInTheDocument();
    expect(screen.getByText("Aguarde")).toBeInTheDocument();
  });

  it("shows loading spinner when loading prop is true", () => {
    render(<MapPlaceholder status="loading" loading />);
    expect(screen.getByText("Carregando mapa…")).toBeInTheDocument();
  });
});

describe("JobMap", () => {
  beforeEach(() => {
    mockGetJobGeojson.mockReset();
  });

  it("renders placeholder when job is not done", () => {
    render(<JobMap jobId="abc" status="loading" />);
    expect(screen.getByTestId("map-placeholder")).toBeInTheDocument();
    expect(screen.getByText("Status: loading")).toBeInTheDocument();
  });

  it("fetches GeoJSON when status is done and renders map", async () => {
    mockGetJobGeojson.mockResolvedValueOnce({
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: [-43.2, -22.9] },
          properties: { layer: "school", name: "E1", capacity: 50, region_id: 0 },
        },
      ],
    });
    render(<JobMap jobId="abc" status="done" />);
    await waitFor(() => {
      expect(screen.getByTestId("map-container")).toBeInTheDocument();
    });
    expect(mockGetJobGeojson).toHaveBeenCalledWith("abc");
  });

  it("shows error placeholder when fetch fails", async () => {
    mockGetJobGeojson.mockRejectedValueOnce(new Error("boom"));
    render(<JobMap jobId="abc" status="done" />);
    await waitFor(() => {
      expect(screen.getByText("Status: failed")).toBeInTheDocument();
    });
    expect(screen.getByText("Error: boom")).toBeInTheDocument();
  });
});

describe("status colors (smoke check)", () => {
  it("ok is green", () => {
    expect(getStatusColor("ok")).toMatch(/^#[0-9a-f]{6}$/i);
  });
});
