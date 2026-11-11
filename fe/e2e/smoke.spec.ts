import { expect, test } from "@playwright/test";

test("the public page returns security headers", async ({ request }) => {
  const response = await request.get("/");

  expect(response.headers()["content-security-policy"]).toContain(
    "frame-ancestors 'none'",
  );
  expect(response.headers()["x-frame-options"]).toBe("DENY");
  expect(response.headers()["content-security-policy"]).toContain("script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com");
  expect(response.headers()["content-security-policy"]).toContain("frame-src https://challenges.cloudflare.com");
});

test("Cazung is public only and supports keyboard controls", async ({ page }) => {
  await page.goto("/");
  const canvas = page.getByRole("button", { name: "Open chat with Cazung" });
  await expect(canvas).toBeVisible();
  await canvas.press("Enter");
  await expect(page.getByRole("heading", { name: "Cazung" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("heading", { name: "Cazung" })).toBeHidden();
  await page.goto("/admin");
  await expect(page.getByRole("button", { name: "Open chat with Cazung" })).toHaveCount(0);
});

test("Cazung click opens chat but dragging does not", async ({ page }) => {
  await page.goto("/");
  const canvas = page.getByRole("button", { name: "Open chat with Cazung" });
  const box = await canvas.boundingBox();
  if (!box) throw new Error("Cazung canvas is not visible.");
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 20, box.y + box.height / 2, { steps: 3 });
  await page.mouse.up();
  await expect(page.getByRole("heading", { name: "Cazung" })).toBeHidden();
  await canvas.click();
  await expect(page.getByRole("heading", { name: "Cazung" })).toBeVisible();
});

test("the public page has no horizontal overflow on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto("/");
  await page.locator("main").waitFor();

  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const innerWidth = await page.evaluate(() => window.innerWidth);

  expect(scrollWidth).toBeLessThanOrEqual(innerWidth);
});

test("an unauthenticated admin visit redirects to login", async ({ page }) => {
  await page.goto("/admin");

  await expect(page).toHaveURL(/\/admin\/login$/);
  await expect(page.getByRole("heading", { name: "Admin sign in" })).toBeVisible();
});

test("an unauthenticated admin API request is not cached", async ({ request }) => {
  const response = await request.get("/api/admin/blocks");

  expect(response.status()).toBe(401);
  expect(response.headers()["cache-control"]).toContain("no-store");
});
