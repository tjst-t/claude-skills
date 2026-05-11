# Test Discipline

The single source of truth for what counts as a valid test in this skill. `sprint plan`, `sprint run`, `sprint verify`, `sprint done`, `sprint auto`, and `gui-spec` all defer to this document. When something here changes, no other file needs to change.

## The Five Rules

### 1. Every Story has a user scenario

Before `sprint run` begins, every Story must have one of:
- `docs/sprint-logs/{SprintID}/scenario-{StoryID}.json` — for `cli` / `api` / `library` / `mixed` Stories. Format: see `story-scenarios.md`.
- `docs/sprint-logs/{SprintID}/gui-spec-{StoryID}.json` — for `gui` Stories. Produced by `gui-spec`.

A scenario is the literal step-by-step sequence of actions the user performs through their real entry point, and the observations the user makes after each step. Every acceptance criterion must be exercised by at least one scenario step.

### 2. Tests drive the user's entry point — never a layer below

| Story type | The test must drive | Forbidden |
|---|---|---|
| `cli` | A subprocess of the real built binary, asserting on stdout / stderr / exit code / files | importing internal packages, invoking `main()` in-process |
| `api` | A real HTTP client against the running server, with the same auth a real consumer uses | calling handler functions directly, single-handler `httptest.ResponseRecorder`, bypassing routing or middleware |
| `gui` | A real Playwright browser (Chromium/Firefox/WebKit) against the real frontend, with traffic flowing to the real backend | `page.route()`, MSW, `setupServer`, `fetch.mockImplementation`, `vi.mock`, `jest.mock` on any network surface; `page.evaluate` to bypass UI interactions for non-time-domain steps; injecting auth tokens into storage as the *only* auth path |
| `library` | A separate consumer-style program that imports only the package's public API | reaching into unexported symbols |
| `mixed` | Each declared entry point has its own scenario block, all of which execute | omitting any block |

Layer-internal tests (unit tests against an internal handler, a fake transport, etc.) are fine as supplementary coverage but never replace the scenario-driven E2E.

### 3. No silent skips

Every acceptance criterion's test must complete with status `pass` in the most recent `verification-results.json`. The following all count as **NOT executed** and block the Sprint:

- `test.skip(...)` / `it.skip(...)` / conditional skip annotations
- File excluded from the run config
- Test marked `pending`
- "Verified manually" / "tested with curl" / "inspected the diff" — none of these are tests
- Any AC without a corresponding test entry in `verification-results.json`

If a test genuinely cannot run (missing credentials, undocumented business rule, environment Claude Code cannot provision), this is a `needs_human` escalation logged to `failures.json`. It is **never** an autonomous decision to skip.

### 4. GUI E2E observes UI state, not intermediate state

The `*.e2e.spec.ts` for every GUI Story must:
- Launch a real Playwright browser context
- Issue user actions through user-observable affordances (`page.click`, `page.fill`, `page.keyboard.press`, navigation via the rendered UI)
- Include at least one assertion on **user-visible UI state that depends on the backend round-trip** (rendered list item, success toast, updated badge, URL change). Asserting only on a loading spinner or pre-network state does not qualify.
- Exercise the real login UI at least once per session (a `loginViaUI` helper is fine); pure storage-injection auth is rejected unless a separate test covers login end-to-end.

Verification via grep, run by `sprint verify`:
```
page.route(   MSW   setupServer   fetch.mockImplementation   vi.mock   jest.mock
```
Any hit on the network surface in an `*.e2e.spec.ts` is rejected.

### 5. Status reflects reality

- A Story's `status: "done"` requires all its scenario steps to have been executed in a passing test in the most recent run.
- An AC's `status: "pass"` in ROADMAP.json requires at least one passing test entry in `verification-results.json` that lists the AC in its `acceptance_criteria` field.
- A Sprint's `status: "done"` requires all of the above for every Story it contains, plus `summary.skip == 0` and `summary.fail == 0` in `verification-results.json`.

Writing `pass` / `done` for tests that did not actually run in this Sprint is forbidden. `verification-results.json` is a record of executed verifications, not an aspirational checklist.

## What disqualifies a test

A test does not count toward Sprint completion if it:

- Calls internal functions / handlers / packages instead of the user's entry point (Rule 2)
- Skips, comments out, or `TODO`-s any step in the scenario (Rule 1)
- Asserts only on a synthetic intermediate (mocked DB row, in-memory struct, loading state) instead of what the user observes (Rule 4)
- Stops short of the `expected` of any scenario step (Rule 1)
- Uses `page.route()` / MSW / fake fetch on the network path of a GUI E2E (Rule 2, Rule 4)
- Bypasses auth, routing, middleware, or serialization that real consumers must go through (Rule 2)
- For CLI: invokes via `go run` or chained build steps that bypass the produced artifact in a way the user wouldn't (Rule 2)

If the only feasible way to make a test pass is to violate one of these, escalate as `needs_human` — do not weaken the test.

## Escalation

When a rule cannot be satisfied:
1. Log the diagnosis to `docs/sprint-logs/{SprintID}/failures.json` (what was tried, what failed, why Claude Code cannot resolve it).
2. Mark the affected Story `blocked` with a `needs_human` reason via `jq` mutation (see SKILL.md "Writes").
3. The Sprint stays `partial` / `in_progress`, NOT `done`. The user (or autopilot milestone review) handles it.
