import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { claimRoutes, instructions, stubApi, summaries } from "./testApi";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.location.hash = "";
});

it("shows the queue by default", async () => {
  stubApi({ "/api/claims": summaries });
  render(<App />);
  expect(
    await screen.findByRole("heading", { name: "Claims queue" }),
  ).toBeDefined();
  expect(
    screen
      .getByRole("link", { name: "Claims queue" })
      .getAttribute("aria-current"),
  ).toBe("page");
});

it("follows the address to the instructions and to a claim", async () => {
  stubApi({ "/api/instructions": instructions, ...claimRoutes });
  window.location.hash = "#/instructions";
  render(<App />);
  expect(
    await screen.findByRole("heading", { name: "Agent instructions" }),
  ).toBeDefined();
  window.location.hash = "#/claims/CLM-1001";
  expect(
    await screen.findByRole("heading", { name: "CLM-1001" }),
  ).toBeDefined();
});
