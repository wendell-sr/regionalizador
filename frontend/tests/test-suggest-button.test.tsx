import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { SuggestRegionsButton } from "@/components/suggest-regions-button";
import { suggestRegions } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  suggestRegions: vi.fn(),
}));

const mockSuggest = vi.mocked(suggestRegions);

function makeFile(content = "fake"): File {
  return new File([content], "p.xlsx", {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
}

beforeEach(() => {
  mockSuggest.mockReset();
});

describe("SuggestRegionsButton (render-only)", () => {
  it("is disabled when no file is provided", () => {
    render(<SuggestRegionsButton participantsFile={null} onAccept={() => {}} />);
    expect(screen.getByTestId("suggest-button")).toBeDisabled();
  });

  it("is enabled when file is provided", () => {
    render(<SuggestRegionsButton participantsFile={makeFile()} onAccept={() => {}} />);
    expect(screen.getByTestId("suggest-button")).not.toBeDisabled();
  });

  it("displays the suggested label", () => {
    render(<SuggestRegionsButton participantsFile={makeFile()} onAccept={() => {}} />);
    expect(screen.getByText("Sugerir regiões")).toBeInTheDocument();
  });
});
