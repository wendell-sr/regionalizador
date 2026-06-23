import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { GeocodingForm } from "@/components/geocoding-form";

vi.mock("@/lib/api", () => ({
  createGeocodingJob: vi.fn(),
  getGeocodingJob: vi.fn(),
  getGeocodedResult: vi.fn(),
  geocodedFileUrl: (id: string, name: string) => `/api/${id}/${name}`,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn(), push: vi.fn() }),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("GeocodingForm (render-only)", () => {
  it("renders the form with file input and submit button", () => {
    render(<GeocodingForm />);
    expect(screen.getByTestId("geocoding-file")).toBeInTheDocument();
    expect(screen.getByTestId("geocoding-submit")).toBeInTheDocument();
  });

  it("submit button is disabled when no file is selected", () => {
    render(<GeocodingForm />);
    expect(screen.getByTestId("geocoding-submit")).toBeDisabled();
  });

  it("displays card title", () => {
    render(<GeocodingForm />);
    expect(screen.getByText(/Geocoding de Escolas/)).toBeInTheDocument();
  });
});
