import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { InstructionsPage } from "./InstructionsPage";
import { instructions, stubApi } from "./testApi";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows the instructions, read only", async () => {
  stubApi({ "/api/instructions": instructions });
  const { container } = render(<InstructionsPage />);
  expect(await screen.findByText(/You decide claims\./)).toBeDefined();
  expect(container.querySelectorAll("input, textarea, button")).toHaveLength(0);
});

it("says when the backend is down", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  render(<InstructionsPage />);
  expect(
    await screen.findByText("The backend is not responding."),
  ).toBeDefined();
});
