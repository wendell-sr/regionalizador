import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useFilters } from "@/lib/hooks/use-filters";

const replace = vi.fn();
let params: URLSearchParams;

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/jobs/abc",
  useSearchParams: () => params,
}));

beforeEach(() => {
  replace.mockReset();
  params = new URLSearchParams();
});

describe("useFilters", () => {
  it("returns defaults when no params", () => {
    const { result } = renderHook(() => useFilters());
    expect(result.current.filters.layers).toContain("region");
    expect(result.current.filters.statuses).toContain("ok");
    expect(result.current.filters.minCapacityRatio).toBe(0);
    expect(result.current.filters.maxRadiusKm).toBeNull();
  });

  it("parses layers from URL", () => {
    params = new URLSearchParams("layers=region,school");
    const { result } = renderHook(() => useFilters());
    expect(result.current.filters.layers).toEqual(["region", "school"]);
  });

  it("parses statuses from URL", () => {
    params = new URLSearchParams("statuses=over_capacity,empty");
    const { result } = renderHook(() => useFilters());
    expect(result.current.filters.statuses).toEqual(["over_capacity", "empty"]);
  });

  it("parses minCap as float in [0,1]", () => {
    params = new URLSearchParams("minCap=0.5");
    const { result } = renderHook(() => useFilters());
    expect(result.current.filters.minCapacityRatio).toBe(0.5);
  });

  it("clamps minCap to [0,1]", () => {
    params = new URLSearchParams("minCap=2.5");
    const { result } = renderHook(() => useFilters());
    expect(result.current.filters.minCapacityRatio).toBe(1);
  });

  it("parses maxRadius", () => {
    params = new URLSearchParams("maxRadius=3.5");
    const { result } = renderHook(() => useFilters());
    expect(result.current.filters.maxRadiusKm).toBe(3.5);
  });

  it("setLayer toggles and writes to URL", () => {
    const { result } = renderHook(() => useFilters());
    act(() => result.current.setLayer("region", false));
    expect(replace).toHaveBeenCalled();
    const url = replace.mock.calls[0][0] as string;
    expect(url).toContain("layers=");
  });

  it("clear removes all filter params", () => {
    params = new URLSearchParams("layers=region&statuses=ok&minCap=0.5&maxRadius=2");
    const { result } = renderHook(() => useFilters());
    act(() => result.current.clear());
    const url = replace.mock.calls[0][0] as string;
    expect(url).not.toContain("layers=");
    expect(url).not.toContain("statuses=");
    expect(url).not.toContain("minCap=");
    expect(url).not.toContain("maxRadius=");
  });

  it("default values don't pollute URL", () => {
    const { result } = renderHook(() => useFilters());
    act(() => result.current.setMinCapacity(0));
    act(() => result.current.setMaxRadius(null));
    expect(replace).not.toHaveBeenCalled();
  });
});
