import { type APIRequestContext, expect, test } from "@playwright/test";

// These tests play the agent's part through the API, so no model is called.

async function startRun(request: APIRequestContext, claimId: string) {
  const response = await request.post(`/api/claims/${claimId}/runs`, {
    data: { thread_id: `e2e-${claimId}` },
  });
  expect(response.status()).toBe(201);
}

async function decide(
  request: APIRequestContext,
  claimId: string,
  decision: string,
  payout: number,
) {
  const response = await request.post(`/api/claims/${claimId}/decision`, {
    data: {
      decision,
      payout,
      reasons: `The agent's reasons for ${claimId}.`,
      policy_section: "4. Baggage Delay",
      confidence: 85,
    },
  });
  expect(response.status()).toBe(201);
}

test("the claim page follows the agent's work to a paid approval", async ({
  page,
  request,
}) => {
  await page.goto("/#/claims/CLM-1004");
  await expect(page.getByText("No decision yet.")).toBeVisible();

  await startRun(request, "CLM-1004");
  await request.post("/api/runs/e2e-CLM-1004/steps", {
    data: { description: "Reading claim CLM-1004" },
  });
  await expect(page.locator(".claim-head")).toContainText("In progress");
  await expect(page.getByText("Reading claim CLM-1004")).toBeVisible();
  await expect(
    page.getByText(/^(About \d+ seconds? left|Finishing up)$/),
  ).toBeVisible();

  await decide(request, "CLM-1004", "approve", 186);
  const paid = await request.post("/api/claims/CLM-1004/payments", {
    data: { amount: 186 },
  });
  expect(paid.status()).toBe(201);
  await request.post("/api/runs/e2e-CLM-1004/finish");

  const decision = page.getByRole("region", { name: "Decision" });
  await expect(page.locator(".claim-head")).toContainText("Decided");
  await expect(decision.getByText("Approve")).toBeVisible();
  await expect(decision.getByText("$186.00", { exact: true })).toBeVisible();
  await expect(decision.getByText("85%")).toBeVisible();
  await expect(
    decision.getByText("The agent's reasons for CLM-1004."),
  ).toBeVisible();
  await expect(decision.getByText(/^Paid \$186\.00 on/)).toBeVisible();
  await expect(page.getByText(/^Finished at/)).toBeVisible();
});

test("a payout over $1,000 waits for a handler's sign-off", async ({
  page,
  request,
}) => {
  await startRun(request, "CLM-1002");
  await decide(request, "CLM-1002", "approve", 1100);
  await page.goto("/#/claims/CLM-1002");
  await expect(page.locator(".claim-head")).toContainText(
    "Waiting for sign-off",
  );

  const blocked = await request.post("/api/claims/CLM-1002/payments", {
    data: { amount: 1100 },
  });
  expect(blocked.status()).toBe(409);
  expect(await blocked.json()).toEqual({
    detail: "A payout over $1,000.00 needs a handler's sign-off.",
  });

  await page.getByLabel("Handler").selectOption({ label: "Dana Whitfield" });
  await page
    .getByRole("button", { name: "Sign off and pay $1,100.00" })
    .click();
  await expect(page.locator(".claim-head")).toContainText("Decided");
  await expect(page.getByText(/^Paid \$1,100\.00 on/)).toBeVisible();
  await expect(page.getByText(/^Signed off by Dana Whitfield/)).toBeVisible();
});

test("a decline shows its reasons and no payment", async ({
  page,
  request,
}) => {
  await startRun(request, "CLM-1005");
  await decide(request, "CLM-1005", "decline", 0);
  await page.goto("/#/claims/CLM-1005");

  const decision = page.getByRole("region", { name: "Decision" });
  await expect(decision.getByText("Decline")).toBeVisible();
  await expect(
    decision.getByText("The agent's reasons for CLM-1005."),
  ).toBeVisible();
  await expect(decision.getByText(/paid/i)).toHaveCount(0);
  await expect(decision.getByRole("button")).toHaveCount(0);
});

test("the queue shows new statuses and decisions without a reload", async ({
  page,
  request,
}) => {
  await page.goto("/");
  const row = page.locator("tr", { hasText: "CLM-1006" });
  await expect(row).toContainText("Waiting");

  await startRun(request, "CLM-1006");
  await expect(row).toContainText("In progress", { timeout: 10_000 });

  await decide(request, "CLM-1006", "refer", 0);
  await expect(row).toContainText("Decided", { timeout: 10_000 });
  await expect(row).toContainText("Refer");
});

test("the agent is offered only on waiting claims", async ({
  page,
  request,
}) => {
  await page.goto("/#/claims/CLM-1007");
  const run = page.getByRole("button", { name: "Run the agent" });
  await expect(run).toBeVisible();

  await startRun(request, "CLM-1007");
  await expect(page.locator(".claim-head")).toContainText("In progress");
  await expect(run).toHaveCount(0);
});
