import { expect, test } from "@playwright/test";

test("the agent's instructions are shown read only", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Agent instructions" }).click();
  await expect(
    page.getByRole("heading", { name: "Agent instructions" }),
  ).toBeVisible();
  await expect(page.getByText(/^# The UnderCover Agent/)).toBeVisible();
  await expect(page.locator("main").locator("input, textarea")).toHaveCount(0);
});
