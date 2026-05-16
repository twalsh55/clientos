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
  await expect(page.getByRole("link", { name: "Sign in" })).toBeVisible();
  await expect(page.getByText("You are browsing as a guest right now.")).toBeVisible();

  await bootstrapSession(page);
  await page.goto("/");

  await expect(page.locator("main").getByText("Signed in as Ada Lovelace").first()).toBeVisible();
  await expect(page.getByText("You are signed in and ready to enter either workspace.")).toBeVisible();
  await page.getByRole("link", { name: "Open Crash Monitor" }).click();

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
  await page.goto("/crm");

  await expect(page.getByText("Bring your lead sheet in without retyping it.")).toBeVisible();

  await page.setInputFiles('input[type="file"]', {
    name: "crm-import.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "contact,company,owner,status,next follow-up,notes\nTaylor Brooks,Beacon Ridge,Samir Patel,Qualification,2024-05-09,Imported from founder sheet\nAmber Flores,Northstar Studio,Ada Lovelace,Discovery,2024-05-10,Duplicate row\n",
    ),
  });
  await page.getByRole("button", { name: "Preview import" }).click();

  await expect(page.getByText("Preview ready for 1 importable row.")).toBeVisible();
  await expect(page.getByText("Taylor Brooks")).toBeVisible();
  await expect(page.getByText("This lead already exists in the current CRM queue and will be skipped.")).toBeVisible();

  await page.getByRole("button", { name: "Import rows" }).click();

  await expect(page.getByText("Imported 1 row, skipped 1 duplicates, and skipped 0 invalid rows.")).toBeVisible();
  await expect(page.getByText("Beacon Ridge")).toBeVisible();
  await expect(page.getByText("Owner · Samir Patel").first()).toBeVisible();
});
