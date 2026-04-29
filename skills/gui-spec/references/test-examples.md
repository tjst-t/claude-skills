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

  test('[AC-S002-1-1] should display VM in list', async ({ page }) => {
    await page.goto('/vms');
    await expect(page.getByTestId(`vm-row-${testVmId}`)).toBeVisible();
  });

  test('[AC-S002-1-2] should start VM and show running status', async ({ page }) => {
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
