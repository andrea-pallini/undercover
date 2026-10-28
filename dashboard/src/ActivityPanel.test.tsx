import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ActivityPanel } from "./ActivityPanel";
import { progress, stubApi } from "./testApi";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("says when the agent hasn't worked on the claim", async () => {
  stubApi({});
  render(<ActivityPanel claimId="CLM-1001" />);
  expect(
    await screen.findByText("The agent hasn't worked on this claim yet."),
  ).toBeDefined();
});

it("shows the steps and the time left while the agent works", async () => {
  stubApi({ "/api/claims/CLM-1001/progress": progress });
  render(<ActivityPanel claimId="CLM-1001" />);
  expect(await screen.findByText("Reading claim CLM-1001")).toBeDefined();
  expect(screen.getByText("About 20 seconds left")).toBeDefined();
});

it("shows when the run finished", async () => {
  stubApi({
    "/api/claims/CLM-1001/progress": {
      ...progress,
      finished_at: "2026-10-28T09:00:30+00:00",
      seconds_remaining: null,
    },
  });
  render(<ActivityPanel claimId="CLM-1001" />);
  expect(await screen.findByText(/^Finished at/)).toBeDefined();
  expect(screen.queryByText(/left$/)).toBeNull();
});
