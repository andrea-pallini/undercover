import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ClaimPage } from "./ClaimPage";
import { claimRoutes, history, stubApi } from "./testApi";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows the claim in full", async () => {
  stubApi(claimRoutes);
  render(<ClaimPage claimId="CLM-1001" />);
  expect(
    await screen.findByText("My flight home from Rome was canceled."),
  ).toBeDefined();
  expect(screen.getByText("Waiting")).toBeDefined();
  expect(screen.getByText("Jun 18, 2026, Rome, Italy")).toBeDefined();
  expect(screen.getByText("Airport hotel")).toBeDefined();
  expect(screen.getByText("$420.00")).toBeDefined();
  expect(screen.getByText("Hotel receipt")).toBeDefined();
  expect(screen.getByText("One night: $245.00.")).toBeDefined();
});

it("shows the policy and the customer's earlier claims", async () => {
  stubApi(claimRoutes);
  render(<ClaimPage claimId="CLM-1001" />);
  expect(await screen.findByText("Premium")).toBeDefined();
  expect(screen.getByText("Electronics plus")).toBeDefined();
  expect(
    screen.getByText("Rome, Italy, Jun 10, 2026 to Jun 18, 2026"),
  ).toBeDefined();
  expect(await screen.findByText("CLM-0412")).toBeDefined();
  expect(screen.getByText("Maya Patel", { selector: "strong" })).toBeDefined();
});

it("says when a customer has no earlier claims", async () => {
  stubApi({
    ...claimRoutes,
    "/api/customers/CUS-3001/history": { ...history, previous_claims: [] },
  });
  render(<ClaimPage claimId="CLM-1001" />);
  expect(await screen.findByText("No earlier claims.")).toBeDefined();
});

it("says when there is no such claim", async () => {
  stubApi({});
  render(<ClaimPage claimId="CLM-9999" />);
  expect(await screen.findByText("There is no claim CLM-9999.")).toBeDefined();
});

it("says when the backend is down", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  render(<ClaimPage claimId="CLM-1001" />);
  expect(
    await screen.findByText("The backend is not responding."),
  ).toBeDefined();
});
