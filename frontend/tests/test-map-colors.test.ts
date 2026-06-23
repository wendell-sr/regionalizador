import { describe, expect, it } from "vitest";
import { getStatusColor, getStatusLabel, STATUS_COLORS } from "@/lib/map-colors";

describe("map-colors", () => {
  it("exposes all 5 status colors", () => {
    expect(Object.keys(STATUS_COLORS)).toEqual(
      expect.arrayContaining(["ok", "over_capacity", "under_capacity", "empty", "too_large"])
    );
  });

  it("returns green for ok", () => {
    expect(getStatusColor("ok")).toBe("#10b981");
  });

  it("returns red for over_capacity", () => {
    expect(getStatusColor("over_capacity")).toBe("#ef4444");
  });

  it("returns yellow for under_capacity", () => {
    expect(getStatusColor("under_capacity")).toBe("#f59e0b");
  });

  it("falls back to ok color for unknown status", () => {
    expect(getStatusColor("weird_status")).toBe(STATUS_COLORS.ok);
  });

  it("returns ok color for undefined", () => {
    expect(getStatusColor(undefined)).toBe(STATUS_COLORS.ok);
  });

  it("returns human-readable label", () => {
    expect(getStatusLabel("over_capacity")).toBe("Acima da capacidade");
    expect(getStatusLabel("empty")).toBe("Vazia");
  });
});
