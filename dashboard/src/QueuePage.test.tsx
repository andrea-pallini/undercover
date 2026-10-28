import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { QueuePage } from "./QueuePage";
import { stubApi, summaries } from "./testApi";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("lists the claims with their status and decision", async () => {
  stubApi({ "/api/claims": summaries });
  render(<QueuePage />);
  const link = await screen.findByRole("link", { name: "CLM-1001" });
  expect(link.getAttribute("href")).toBe("#/claims/CLM-1001");
  const row = within(link.closest("tr") ?? document.body);
  expect(row.getByText("Maya Patel")).toBeDefined();
  expect(row.getByText("Trip delay")).toBeDefined();
  expect(row.getAllByText("$420.00")).toHaveLength(2);
  expect(row.getByText("Jun 24, 2026")).toBeDefined();
  expect(row.getByText("Decided")).toBeDefined();
  expect(row.getByText("Approve")).toBeDefined();
});

it("counts the claims in each status", async () => {
  stubApi({ "/api/claims": summaries });
  render(<QueuePage />);
  const tiles = await screen.findByRole("list", { name: "Claims by status" });
  const counts = within(tiles)
    .getAllByRole("listitem")
    .map((tile) => tile.textContent);
  expect(counts).toEqual([
    "Waiting 1",
    "In progress 0",
    "Waiting for sign-off 0",
    "Decided 1",
  ]);
});

it("says when the backend is down", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  render(<QueuePage />);
  expect(
    await screen.findByText("The backend is not responding."),
  ).toBeDefined();
});
