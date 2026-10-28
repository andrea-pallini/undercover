import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { DecisionPanel } from "./DecisionPanel";
import { decision, handlers, refusal, stubApi } from "./testApi";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const route = "/api/claims/CLM-1001/decision";
const overLimit = { ...decision, payout: 1100, needs_sign_off: true };

it("says when there's no decision yet", async () => {
  stubApi({});
  render(<DecisionPanel claimId="CLM-1001" onSignedOff={vi.fn()} />);
  expect(await screen.findByText("No decision yet.")).toBeDefined();
});

it("shows an approval with its reasons and payment", async () => {
  stubApi({
    [route]: {
      ...decision,
      payment: { amount: 420, paid_at: "2026-10-28T09:00:25+00:00" },
    },
  });
  render(<DecisionPanel claimId="CLM-1001" onSignedOff={vi.fn()} />);
  expect(await screen.findByText("Approve")).toBeDefined();
  expect(screen.getByText("$420.00")).toBeDefined();
  expect(
    screen.getByText("The flight was canceled for a crew problem."),
  ).toBeDefined();
  expect(screen.getByText("3. Trip Delay")).toBeDefined();
  expect(screen.getByText("85%")).toBeDefined();
  expect(screen.getByText(/^Paid \$420\.00 on/)).toBeDefined();
});

it("shows an approval not paid yet", async () => {
  stubApi({ [route]: decision });
  render(<DecisionPanel claimId="CLM-1001" onSignedOff={vi.fn()} />);
  expect(await screen.findByText("Not paid yet")).toBeDefined();
});

it("shows a decline without a payment", async () => {
  stubApi({ [route]: { ...decision, decision: "decline", payout: 0 } });
  render(<DecisionPanel claimId="CLM-1001" onSignedOff={vi.fn()} />);
  expect(await screen.findByText("Decline")).toBeDefined();
  expect(screen.queryByText(/paid/i)).toBeNull();
  expect(screen.queryByRole("button")).toBeNull();
});

it("signs off a large payout", async () => {
  const fetchMock = stubApi({
    [route]: overLimit,
    "/api/handlers": handlers,
    "POST /api/claims/CLM-1001/sign-off": overLimit,
  });
  const onSignedOff = vi.fn();
  render(<DecisionPanel claimId="CLM-1001" onSignedOff={onSignedOff} />);
  expect(
    await screen.findByText("Waiting for a handler's sign-off"),
  ).toBeDefined();
  const button = screen.getByRole("button", {
    name: "Sign off and pay $1,100.00",
  });
  expect(button.hasAttribute("disabled")).toBe(true);
  await screen.findByRole("option", { name: "Dana Whitfield" });
  fireEvent.change(screen.getByLabelText("Handler"), {
    target: { value: "HND-01" },
  });
  fireEvent.click(button);
  await vi.waitFor(() => {
    expect(onSignedOff).toHaveBeenCalled();
  });
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/claims/CLM-1001/sign-off",
    expect.objectContaining({ body: JSON.stringify({ handler_id: "HND-01" }) }),
  );
});

it("shows why a sign-off was refused", async () => {
  stubApi({
    [route]: overLimit,
    "/api/handlers": handlers,
    "POST /api/claims/CLM-1001/sign-off": refusal(
      "CLM-1001 isn't waiting for sign-off.",
    ),
  });
  render(<DecisionPanel claimId="CLM-1001" onSignedOff={vi.fn()} />);
  await screen.findByRole("option", { name: "Dana Whitfield" });
  fireEvent.change(screen.getByLabelText("Handler"), {
    target: { value: "HND-01" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Sign off and pay $1,100.00" }),
  );
  expect(
    await screen.findByText("CLM-1001 isn't waiting for sign-off."),
  ).toBeDefined();
});

it("shows who signed off", async () => {
  stubApi({
    [route]: {
      ...overLimit,
      sign_off: {
        handler_id: "HND-01",
        handler_name: "Dana Whitfield",
        at: "2026-10-28T09:10:00+00:00",
      },
      payment: { amount: 1100, paid_at: "2026-10-28T09:10:00+00:00" },
    },
  });
  render(<DecisionPanel claimId="CLM-1001" onSignedOff={vi.fn()} />);
  expect(
    await screen.findByText(/^Signed off by Dana Whitfield/),
  ).toBeDefined();
  expect(screen.getByText(/^Paid \$1,100\.00/)).toBeDefined();
});
