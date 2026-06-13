import type { APIRequestContext, Page } from "@playwright/test";
import { expect, test } from "@playwright/test";

const mockApiBaseUrl = "http://127.0.0.1:8001";

test.describe.configure({ mode: "serial" });

async function resetMockApi(request: APIRequestContext) {
  await request.post(`${mockApiBaseUrl}/__reset`);
}

async function bootstrapSession(page: Page) {
  const response = await page.request.post("/api/session", {
    data: {
      sessionToken: "test-session-token",
    },
  });

  expect(response.ok()).toBeTruthy();
}

test.beforeEach(async ({ request }) => {
  await resetMockApi(request);
});

test("bootstraps a local app session and renders the authenticated dashboard shell", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: /Today Start with the one relationship/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Start with the relationship that matters most today." })).toBeVisible();
  await expect(page.getByText("Reply to Amber Flores").first()).toBeVisible();

  await bootstrapSession(page);
  await page.goto("/crash-monitor");

  await expect(page.getByText("Account session active")).toBeVisible();
  await expect(page.getByText("Ada Lovelace", { exact: true })).toBeVisible();
  await expect(page.getByTestId("dashboard-benchmark-value")).toHaveText("SPY");
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
});

test("refreshes the dashboard with updated filters", async ({ page }) => {
  await bootstrapSession(page);
  await page.goto("/crash-monitor");

  await page.getByTestId("dashboard-benchmark-input").fill("QQQ");
  await page.getByTestId("dashboard-refresh-button").click();

  await expect(page.getByTestId("dashboard-status")).toHaveText("Dashboard refreshed.");
  await expect(page.getByTestId("dashboard-benchmark-value")).toHaveText("QQQ");
  await expect(page.getByText("Growth leadership")).toBeVisible();
});

test("saves settings and applies them back to the dashboard", async ({ page }) => {
  await bootstrapSession(page);
  await page.goto("/crash-monitor");

  await page.getByRole("heading", { name: "User dashboard defaults" }).scrollIntoViewIfNeeded();
  await page.getByTestId("settings-benchmark-input").fill("QQQ");
  await page.getByTestId("settings-save-button").click();

  await expect(page.getByTestId("settings-status")).toContainText("Settings saved.");
  await expect(page.getByTestId("dashboard-status")).toHaveText("Dashboard refreshed.");
  await expect(page.getByTestId("dashboard-benchmark-value")).toHaveText("QQQ");
});

test("lets a first-time user defer the business profile setup", async ({ page }) => {
  await bootstrapSession(page);
  await page.goto("/clientos");

  await expect(page.getByText("Set the basics once so Brivoly can sound like your business.")).toBeVisible();
  await page.getByRole("button", { name: "Add later" }).first().click();

  await expect(page.getByText("Set the basics once so Brivoly can sound like your business.")).toHaveCount(0);
});

test("refreshes the alert feed through the local proxy route", async ({ page }) => {
  await bootstrapSession(page);
  await page.goto("/crash-monitor");

  await expect(page.getByText("Baseline alert")).toBeVisible();

  await page.getByTestId("alerts-refresh-button").click();

  await expect(page.getByTestId("alerts-status")).toHaveText("Alert feed refreshed.");
  await expect(page.getByText("Refreshed alert feed")).toBeVisible();
});

test("previews and imports CRM spreadsheet rows through the local proxy routes", async ({ page }) => {
  await bootstrapSession(page);
  await page.goto("/clientos/import");

  await expect(page.getByText("Bring relationship context in without retyping it.")).toBeVisible();

  await page.setInputFiles('[data-testid="crm-import-file-input"]', {
    name: "crm-import.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "contact,company,owner,status,next follow-up,notes\nTaylor Brooks,Beacon Ridge,Samir Patel,Qualification,2024-05-09,Imported from founder sheet\nAmber Flores,Northstar Studio,Ada Lovelace,Discovery,2024-05-10,Duplicate row\n",
    ),
  });
  await page.getByRole("button", { name: "Check context" }).click();

  await expect(page.getByText("Preview ready for 1 importable row.")).toBeVisible();
  await expect(page.getByText("Taylor Brooks")).toBeVisible();
  await expect(page.getByText("This lead already exists in the current CRM queue and will be skipped.")).toBeVisible();

  await page.getByRole("button", { name: "Bring this in" }).click();

  await expect(page.getByText("Imported 1 row, skipped 1 duplicates, and skipped 0 invalid rows.")).toBeVisible();
  await page.goto("/clientos/follow-ups");
  await expect(page.getByText("Beacon Ridge").first()).toBeVisible();
  await expect(page.getByText("Owner · Samir Patel").first()).toBeVisible();
});
