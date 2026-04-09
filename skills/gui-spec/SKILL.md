---
name: gui-spec
description: GUI specification elicitation for React/web UI components. Use this skill when a Sprint contains Stories that involve building or modifying UI components, screens, forms, modals, dashboards, or any interactive frontend elements. This skill runs before implementation to clarify user scenarios, state transitions, and acceptance criteria — turning ambiguous UI requirements into concrete Playwright test specifications that Claude Code can execute autonomously.
---

# GUI Spec

Elicits GUI specifications through structured dialogue, then generates Playwright acceptance tests that allow autonomous implementation and self-verification.

## When to Use

Called from `sprint plan` when one or more Stories involve GUI work. Do **not** call this during `sprint run` or `sprint verify` — specs must be finalized before implementation begins.

## Process

### Phase 1: Detect GUI Stories

Analyze the Sprint's Stories and Tasks. A Story involves GUI if it mentions:
- Component, screen, page, view, form, modal, dialog, drawer, panel
- UI, UX, frontend, React, htmx
- "display", "show", "render", "interact", "click", "input"

If no GUI Stories are found, skip this skill entirely and return to `sprint plan`.

### Phase 2: Derive Scenarios (one Story at a time)

For each GUI Story, reason through the following aspects and **auto-select the recommended approach** when a clear best practice or conventional answer exists. Only ask the user when a genuinely ambiguous design decision arises (e.g., multiple viable UX patterns with real trade-offs, domain-specific behavior that cannot be inferred from context).

**Aspects to reason through (adapt to context):**

1. **Entry point**: How does the user reach this UI? (direct URL, button click, navigation menu, etc.)
2. **Happy path**: The primary action flow — what the user does step by step and what happens after each step
3. **Data states**: What the UI shows when there is no data, when loading, and when an error occurs
4. **Edge cases**: Inputs or actions the UI should prevent or handle specially (empty fields, long strings, duplicate entries, etc.)
5. **Success feedback**: What the user sees after a successful action (toast, redirect, inline update, etc.)
6. **Failure feedback**: What the user sees when the action fails (server error, validation error, etc.)

**Auto-decision principle**: For each aspect, first determine if there is a clear recommendation based on existing project conventions, common UX patterns, or the Story context. If so, state your choice and rationale briefly and move on. If the decision is genuinely ambiguous (multiple viable approaches with meaningful trade-offs), ask the user — but batch related questions into a single message rather than asking one at a time.

Present the complete scenario summary (auto-decided items + any questions) to the user for a single confirmation pass, rather than iterating through each item individually.

### Phase 3: Generate State Transition Diagram

Based on the elicited scenarios, generate a Mermaid state diagram covering:
- All UI states (empty, loading, populated, error, submitting, success)
- All user actions that trigger transitions
- Which interactive elements (buttons, inputs) are enabled/disabled in each state

Present the diagram to the user as part of the scenario summary. If the user identifies missing states or transitions, update accordingly.

**Example output:**
```mermaid
stateDiagram-v2
    [*] --> Empty: page load (no data)
    Empty --> Loading: user clicks Add
    Loading --> Populated: API success
    Loading --> Error: API failure
    Populated --> Loading: user clicks Add again
    Error --> Loading: user clicks Retry
```

### Phase 4: Generate Playwright Acceptance Tests

Convert the confirmed scenarios and state diagram into Playwright test cases. Write these as concrete, runnable test code.

**Rules for generated tests:**
- Use `data-testid` attributes for all selectors (never CSS classes or text content)
- Cover: happy path, empty state, loading state, error state, each edge case identified
- Use `page.route()` to mock API responses — do not depend on a real backend
- Each test must be independent (no shared state between tests)
- Name tests in the format: `「シナリオ名」should [expected behavior]`
- **Mock all dependent endpoints**: テスト対象コンポーネントが呼ぶ全エンドポイントを明示的にモックする。1つでも未モックのエンドポイントがあると、サイレントフォールバックが発動して誤って通過する可能性がある。
- **Mock data must match real API contract**: モックが返すデータは実際の API レスポンス形式と一致させる。ページネーション API（`{ items: [...] }`）をそのまま返すこと。実装前に `internal/api/` の handler を読んでレスポンス形式を確認すること。
- **Avoid overly broad URL wildcards**: `*/tenants` のようなワイルドカードは本来存在しないパスにもマッチする。可能な限り具体的なパスを使うか、ワイルドカードを使う場合はその意図をコメントで明記する。
- **Verify all mocked endpoints are actually called**: 各テストの末尾で `expect(mockHandler).toHaveBeenCalled()` 等でモックが実際に呼ばれたことを確認する（呼ばれなかったモックは設計ミスの可能性がある）。
- **Verify endpoint registration before writing tests**: For every endpoint the test will mock, confirm it is registered in the backend router (e.g., `internal/api/router.go`). If the endpoint does not exist yet, add a TODO comment in the test file: `// TODO: backend must implement POST /api/v1/auth/verify`. This prevents tests from silently passing against a frontend that calls non-existent endpoints.

**Example:**
```typescript
import { test, expect } from '@playwright/test';

test('VM list: should show empty state when no VMs exist', async ({ page }) => {
  await page.route('/api/vms', route => route.fulfill({ json: [] }));
  await page.goto('/vms');
  await expect(page.getByTestId('empty-state-message')).toBeVisible();
  await expect(page.getByTestId('create-vm-button')).toBeEnabled();
});

test('VM list: should show VM as running after start succeeds', async ({ page }) => {
  await page.route('/api/vms', route => route.fulfill({
    json: [{ id: 'vm-1', name: 'test-vm', status: 'stopped' }]
  }));
  await page.route('/api/vms/vm-1/start', route => route.fulfill({ json: { status: 'running' } }));
  await page.goto('/vms');
  await page.getByTestId('vm-start-button-vm-1').click();
  await expect(page.getByTestId('vm-status-vm-1')).toHaveText('running');
});
```

### Phase 4.5: Endpoint contract table

For each GUI Story, produce a contract table and include it in the spec document (`docs/sprint-logs/{SprintID}/gui-spec-{StoryID}.md`):

| Endpoint | Method | Router registration confirmed | Request fields (from handler) | Response fields (from handler) |
|---|---|---|---|---|
| `/api/v1/auth/verify` | POST | ✓ / ✗ | — | `status: string` |
| `/api/v1/organizations` | GET | ✓ / ✗ | — | `items: Organization[], next_cursor: string` |

**How to fill this table**:
- Read `internal/api/router.go` (or equivalent) to confirm each endpoint is registered. Mark ✗ if missing.
- Read the corresponding handler function to extract the exact JSON field names from struct tags.
- The TypeScript types in `web/src/api/` **must** match the "Response fields" column exactly.

If any row has ✗ in "Router registration confirmed", flag it to `sprint plan` as a missing backend task before implementation begins.

### Phase 5: Update Roadmap

For each GUI Story, append the following to its entry in `docs/ROADMAP.md`:

```markdown
**Acceptance Criteria (GUI):**
- [ ] State diagram confirmed with user (see sprint-logs/{SprintID}/gui-spec-{StoryID}.md)
- [ ] Playwright tests pass: `npx playwright test {test-file}`
- [ ] All interactive elements have `data-testid` attributes
- [ ] API calls are mocked in tests (no real backend dependency)
```

Write the full spec output (state diagram + test code) to `docs/sprint-logs/{SprintID}/gui-spec-{StoryID}.md`.

Create the sprint-logs directory if it doesn't exist.

## Output Contract

This skill produces:
1. Confirmed Mermaid state diagram per GUI Story
2. Playwright test file at `tests/e2e/{story-slug}.spec.ts` (or equivalent path per project conventions)
3. Spec document at `docs/sprint-logs/{SprintID}/gui-spec-{StoryID}.md`
4. Updated acceptance criteria in `docs/ROADMAP.md`

`sprint run` implementation sub-agents must:
- Add `data-testid` to every interactive element
- Run `npx playwright test` and fix failures before marking the Story complete
- Never mark a GUI Story as `[x]` if Playwright tests are failing

## Important Behaviors

- **Auto-decide, then confirm once**: Reason through all aspects autonomously, auto-select when recommendations are clear, and present a single summary for user confirmation. Only ask individual questions when a design decision is genuinely ambiguous with meaningful trade-offs.
- **Diagram before tests**: Present the state diagram as part of the scenario summary. Tests derived from an unconfirmed diagram will likely be wrong.
- **Mock everything**: All tests use `page.route()` mocks. A test that requires a running backend is not acceptable — it cannot run autonomously in CI.
- **data-testid is mandatory**: If the implementation doesn't have `data-testid` attributes, Playwright tests become fragile. This is a non-negotiable convention.
- **Short-circuit if no GUI**: If no Stories in the Sprint involve GUI, skip immediately and tell `sprint plan` to continue without GUI spec.
- **Read the handler, not the type name**: When generating mock data for Playwright tests, always read the actual backend handler (`internal/api/*_handler.go`) to get response field names from JSON struct tags. Never infer field names from Go type names or TypeScript conventions — Go uses `json:"ram_mb"` tags that often differ from the field name itself (e.g., `RAMMB int \`json:"ram_mb"\``).
