# Test generation rules

Per GUI Story, generate **two separate test files**. Each serves a different purpose and runs at a different phase.

## E2E tests — `tests/e2e/{story-slug}.e2e.spec.ts`

Real end-to-end tests that run a real browser against the real running backend. The full shape (real browser, no network mocks, UI-affordance interactions, UI-state assertions, real-login auth) is defined by `sprint/references/test-discipline.md` Rules 2 and 4 — that document is the authority; this file adds only what is specific to writing the file:

- Use `data-testid` attributes for all selectors (never CSS classes or text content)
- Cover the happy path and every acceptance criterion from ROADMAP.json
- **Name tests** with the AC reference: `[AC-{StoryID}-{N}] {description}` (e.g., `[AC-Sb1e4d8-1-1] should show VM list after login`)
- Each test sets up its own test data via API calls in `test.beforeEach()` and cleans up in `test.afterEach()` — these setup/cleanup hooks are the only place a test may bypass the UI
- Tests assume the server is already running (`make serve`); do not start the server inside the test
- Use a dedicated test user/token documented in CLAUDE.md
- For mutations, verify persistence by reading back **through the UI** (navigate, confirm the item appears), not via direct API or DB query

For examples, see `test-examples.md`.

**When E2E tests run**: during `sprint verify` (after all Stories are merged and the server is running).

## Mock tests — `tests/e2e/{story-slug}.mock.spec.ts`

Frontend-only tests using `page.route()` mocks. These verify UI behavior for states that are hard to reproduce with a real server.

Rules:

- Cover: empty state, loading state, error state (500, timeout), edge cases (long strings, special characters)
- Use `page.route()` to mock API responses
- **Mock all dependent endpoints**: explicitly mock every endpoint the component calls
- **Mock data must match real API contract**: read the backend handler to confirm response structure
- **Verify all mocked endpoints are actually called**: assert mock handlers were called
- **Assert mutation request bodies**: for POST/PUT/PATCH, inspect `route.request().postDataJSON()` and assert required fields
- Name tests in the format: `[MOCK] {scenario} should {expected behavior}`

For examples, see `test-examples.md`.

**When mock tests run**: during `sprint run` (per-Story, fast feedback loop).

## Time-domain AC tests

If an AC describes motion that unfolds over time (animation, smooth scroll, transition, debounce/throttle, lazy render, async layout coordination), tag its `description` with `[time-domain]` and write the test using the progression-sampler pattern. The full schema, Playwright template, forbidden patterns, and fix workflow live in `time-domain-tests.md`. Time-domain tests run during `sprint verify` against the real server.

## Endpoint contract table

For each GUI Story, produce an endpoint contract and include it in the spec JSON file (`docs/sprint-logs/{SprintID}/gui-spec-{StoryID}.json`). The structure follows `endpoint_contracts` in SPRINT_LOGS_SCHEMA.json:

```json
{
  "endpoint_contracts": [
    {
      "path": "/api/v1/vms",
      "method": "GET",
      "registered": true,
      "request_fields": null,
      "response_fields": {"items": "VM[]", "next_cursor": "string"}
    }
  ]
}
```

How to fill:

- Read the project's router file (e.g., `internal/api/router.go` for Go, `config/routes.rb` for Rails, `src/routes/` for Express) to confirm each endpoint is registered.
- Read the corresponding handler function to extract the exact field names from serialization annotations.
- The frontend API types **must** match `response_fields` exactly.

For POST/PUT/PATCH, `request_fields` defines what mock tests **must** assert via `route.request().postDataJSON()`. If left null, tests cannot verify the request body.

If any endpoint has `"registered": false`, flag it to `sprint plan` as a missing backend task.
