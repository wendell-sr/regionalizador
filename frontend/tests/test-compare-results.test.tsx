import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { CompareResults } from "@/components/compare-results";

vi.mock("@/lib/api", () => ({
  createCompareJob: vi.fn(),
  getCompareStatus: vi.fn(),
  getCompareResult: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

const blankForm = new FormData();

beforeEach(() => {
  vi.clearAllMocks();
});

describe("CompareResults (render-only)", () => {
  it("renders the compare button when no job exists", () => {
    render(<CompareResults formData={blankForm} onUseAlgorithm={() => {}} />);
    expect(screen.getByTestId("compare-button")).toBeInTheDocument();
  });

  it("displays card title", () => {
    render(<CompareResults formData={blankForm} onUseAlgorithm={() => {}} />);
    expect(screen.getByText(/Comparar algoritmos/)).toBeInTheDocument();
  });
});
