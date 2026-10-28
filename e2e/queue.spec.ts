import { expect, test } from "@playwright/test";

test("the queue shows every claim waiting", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Claims queue" }),
  ).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(25);
  await expect(
    page.getByRole("list", { name: "Claims by status" }).getByRole("listitem"),
  ).toHaveText([
    "Waiting 25",
    "In progress 0",
    "Waiting for sign-off 0",
    "Decided 0",
  ]);
});

test("a claim opens in full", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "CLM-1001" }).click();
  await expect(page).toHaveURL(/#\/claims\/CLM-1001$/);
  await expect(page.getByRole("heading", { name: "CLM-1001" })).toBeVisible();
  await expect(page.getByText(/^My flight home from Rome/)).toBeVisible();

  const items = page.locator("section", { hasText: "Items claimed" });
  await expect(items.locator("tbody tr")).toHaveCount(3);
  await expect(items.locator("tfoot")).toHaveText(/Total\s*\$420\.00/);

  const documents = page
    .getByRole("heading", { name: "Documents" })
    .locator("+ ul > li");
  await expect(documents).toHaveCount(4);

  await expect(page.getByText("Premium", { exact: true })).toBeVisible();
  await expect(page.getByText("CLM-0412")).toBeVisible();
});
