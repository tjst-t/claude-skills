# Playwright Test Examples

## E2E Test Example (real server, no mocks)

```typescript
import { test, expect } from '@playwright/test';

test.describe('VM management', () => {
  let testVmId: string;

  test.beforeEach(async ({ request }) => {
    // Create test data via API
    const res = await request.post('/api/vms', {
      data: { name: 'test-vm', flavor_id: 'small' },
      headers: { Authorization: 'Bearer test-token' },
    });
    testVmId = (await res.json()).id;
  });

  test.afterEach(async ({ request }) => {
    // Clean up test data
    await request.delete(`/api/vms/${testVmId}`, {
      headers: { Authorization: 'Bearer test-token' },
    });
  });

  test('[AC-Sb1e4d8-1-1] should display VM in list', async ({ page }) => {
    await page.goto('/vms');
    await expect(page.getByTestId(`vm-row-${testVmId}`)).toBeVisible();
  });

  test('[AC-Sb1e4d8-1-2] should start VM and show running status', async ({ page }) => {
    await page.goto('/vms');
    await page.getByTestId(`vm-start-button-${testVmId}`).click();
    await expect(page.getByTestId(`vm-status-${testVmId}`)).toHaveText('running');
  });
});
```

## Mock Test Example (frontend-only, error/edge cases)

```typescript
import { test, expect } from '@playwright/test';

test('[MOCK] VM list: should show error message on server failure', async ({ page }) => {
  await page.route('/api/vms', route => route.fulfill({ status: 500 }));
  await page.goto('/vms');
  await expect(page.getByTestId('error-message')).toBeVisible();
});

test('[MOCK] VM list: should show empty state when no VMs exist', async ({ page }) => {
  await page.route('/api/vms', route => route.fulfill({ json: [] }));
  await page.goto('/vms');
  await expect(page.getByTestId('empty-state-message')).toBeVisible();
});

test('[MOCK] VM create: should send required fields to backend', async ({ page }) => {
  await page.route('/api/vms', async route => {
    if (route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      expect(body.name).toBeTruthy();
      expect(body.flavor_id).toBeTruthy();
      return route.fulfill({ status: 201, json: { id: 'vm-1', name: body.name } });
    }
    return route.fulfill({ json: [] });
  });
  await page.goto('/vms');
  await page.getByTestId('vm-create-button').click();
  await page.getByTestId('vm-name-input').fill('my-vm');
  await page.getByTestId('vm-create-submit').click();
  await expect(page.getByTestId('vm-row-vm-1')).toBeVisible();
});
```

## Time-domain Test Example (animation / smooth scroll / transition)

For AC tagged `[time-domain]` (see gui-spec SKILL Phase 4C). The progression sampler runs **inside `page.evaluate`** so the 100ms cadence is honored by the browser event loop — not warped by Playwright IPC latency.

```typescript
import { test, expect } from '@playwright/test';

type Sample = { t: number; scrollTop: number; scrollHeight: number; clientHeight: number };

test('[AC-Sb1e4d8-1-3] should smooth-scroll to bottom without stalling mid-flight', async ({ page }) => {
  await page.goto('/conversations/long-session');
  await page.waitForSelector('[data-testid="conversation-list"]');

  // Sampler runs in-browser. Click the trigger inside page.evaluate
  // so t=0 is the click, and the loop cadence is not perturbed by IPC.
  const samples: Sample[] = await page.evaluate(async () => {
    const el = document.querySelector<HTMLElement>('[data-testid="conversation-list"]')!;
    const trigger = document.querySelector<HTMLElement>('[data-testid="scroll-to-bottom"]')!;
    const out: Sample[] = [];
    const t0 = performance.now();
    trigger.click();
    for (let i = 0; i < 25; i++) {  // ~2.5s window, 100ms cadence
      await new Promise(r => setTimeout(r, 100));
      out.push({
        t: Math.round(performance.now() - t0),
        scrollTop: el.scrollTop,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
      });
    }
    return out;
  });

  // Progression assertion: scrollTop must be monotonically non-decreasing
  // during the smooth animation window (first ~1.5s).
  const ys = samples.slice(0, 15).map(s => s.scrollTop);
  const monotonic = ys.slice(1).every((y, i) => y >= ys[i]);
  expect(monotonic, `animation not monotonic: ys=${JSON.stringify(ys)}`).toBe(true);

  // Progression assertion: at t≈500ms, must exceed 50% of final scrollTop
  // (= animation actually progresses, not stuck at 0).
  const finalScrollTop = samples[samples.length - 1].scrollTop;
  expect(
    samples[5].scrollTop,
    `no early progress by t=500ms: samples[:6]=${JSON.stringify(samples.slice(0, 6))}`,
  ).toBeGreaterThan(finalScrollTop * 0.5);

  // Final assertion: at t≈2500ms, must be at the bottom.
  const last = samples[samples.length - 1];
  const gap = last.scrollHeight - last.scrollTop - last.clientHeight;
  expect(gap, `final gap=${gap}, samples=${JSON.stringify(samples)}`).toBeLessThan(4);
});
```

**Why progression matters here**: with only the final assertion, a regression where the smooth scroll stalls at e.g. `scrollTop=64944` and a downstream fallback (interval pin, instant snap, retry) lands on the bottom would still pass. The user sees broken motion; final-state-only tests don't. The progression block makes the failure visible at the exact sample where it stalls.
