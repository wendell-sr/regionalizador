import { describe, expect, it, vi } from "vitest";
import { suggestRegions } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  suggestRegions: vi.fn(),
}));

const mockSuggest = vi.mocked(suggestRegions);

describe("suggestRegions API client (smoke)", () => {
  it("returns parsed result on success", async () => {
    mockSuggest.mockResolvedValueOnce({
      recommended: 3,
      n_participants: 50,
      scores: [{ k: 3, silhouette: 0.6, inertia: 200 }],
    });
    const r = await suggestRegions({
      participants: [{ lat: -22.9, lon: -43.2, qty: 1 }],
    });
    expect(r.recommended).toBe(3);
    expect(r.n_participants).toBe(50);
  });

  it("propagates API errors", async () => {
    mockSuggest.mockRejectedValueOnce(new Error("500"));
    await expect(
      suggestRegions({ participants: [{ lat: 0, lon: 0, qty: 1 }] })
    ).rejects.toThrow("500");
  });
});
