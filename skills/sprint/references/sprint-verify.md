# sprint verify

Verify the Sprint implementation is complete and correct. Run this after `sprint run`.

## Phase 1: Completeness check

1. Read only the current Sprint slice (see SKILL.md "Roadmap Reading Patterns"):
   ```bash
   jq '.sprints[.progress.current_sprint]' docs/ROADMAP.json
   ```
2. Use a subagent to perform a comprehensive review:
   - Compare every Task in the Sprint against the actual code changes and test logs in `docs/sprint-logs/{SprintID}/`
   - Check for any Tasks marked incomplete or missing implementation
   - Check for any Tasks that were implemented but not marked complete
   - **Scenario file presence** (`test-discipline.md` Rule 1): every Story has `scenario-{StoryID}.json` (non-GUI) or `gui-spec-{StoryID}.json` (GUI). Missing → derive it now per `story-scenarios.md` before continuing.
   - **For GUI Stories**: Verify that `npx playwright test` passes for each Story's test file. Failing tests are incomplete Tasks — execute the missing work immediately.
   - **API mock contract check**: For GUI Stories, compare the data shapes returned by Playwright test mocks against the actual backend handler implementations. Pay special attention to pagination response wrappers (`items` wrapper presence/absence). If mocks diverge from the real API, fix the tests immediately.
   - **Time-domain AC check**: For each AC whose `description` contains the `[time-domain]` tag, the linked test must contain (a) a progression sampler that captures state at multiple ms offsets inside `page.evaluate`, AND (b) a final-state assertion. A test that consists only of `await page.waitForTimeout(...)` followed by a single state assertion is rejected as the **forbidden pattern** (see gui-spec SKILL Phase 4C) — replace it with a progression-sampling test before continuing. This is non-negotiable: time-domain regressions routinely pass final-state-only tests while the user-visible motion is broken.
3. If gaps are found, execute the missing work immediately

## Phase 1.5: E2E tests and acceptance criteria verification

All test-shape rules live in `references/test-discipline.md`. This phase applies them.

### Step 1: Start the real server

1. Run `make serve` (or the project's startup command) to bring up the real server
2. **Login gate**: Verify that the authentication endpoint the frontend uses exists and returns 200 for the dev token. If it does not exist, create it immediately.

### Step 2: Run tests and validate test shape

3. **For GUI Stories**: Run `npx playwright test *.e2e.spec.ts`. For each `*.e2e.spec.ts`, validate against `test-discipline.md` Rules 2 and 4: real browser, no network mocks (grep `page.route(`, `MSW`, `setupServer`, `fetch.mockImplementation`, `vi.mock`, `jest.mock`), user-affordance interactions, UI-state assertions, real-login auth. Mock tests are **never** a substitute. Any failure or shape violation: fix it, loop, escalate per `test-discipline.md` "Escalation" only if Claude Code genuinely cannot resolve.
4. **For non-GUI Stories**: Run the project's acceptance test runner. For each test file, validate against `test-discipline.md` Rule 2 by the Story's `story_type` (subprocess for `cli`, real HTTP client for `api`, public API only for `library`). Confirm every scenario step in `scenario-{StoryID}.json` has a corresponding action+assertion. Re-check classification — if the deliverable is browser-observable, it's a GUI Story (Rule 4 applies). Missing tests are a gap; fix now.
5. Document results in `docs/sprint-logs/{SprintID}/e2e-results.json`. **Gate** (Rule 3): if `summary.skip > 0` or `summary.fail > 0`, the Sprint cannot proceed past Phase 1.5.

### Step 3: Acceptance criteria traceability check

6. Read acceptance criteria for each Story from `docs/ROADMAP.json`.
7. Verify each AC has a corresponding test: GUI Stories use `[AC-{StoryID}-{N}]` tagged tests in `*.e2e.spec.ts`; non-GUI Stories use test functions named with the AC reference.
8. Missing test → create and run it. Failing test → fix and re-run. Skipped / pending / not-actually-executed → treat as failure (Rule 3); never write `pass` in the matrix for a test that did not run (Rule 5).
9. Log the traceability matrix to `docs/sprint-logs/{SprintID}/acceptance-matrix.json`:

```markdown
| Story | Acceptance Criterion | Test | Status |
|-------|---------------------|------|--------|
| Sb1e4d8-1 | AC-1: VM list displays after login | [AC-Sb1e4d8-1-1] in vm-list.e2e.spec.ts | ✅ Pass |
| Sb1e4d8-1 | AC-2: VM can be started | [AC-Sb1e4d8-1-2] in vm-list.e2e.spec.ts | ✅ Pass |
| Sb1e4d8-2 | AC-1: User can create organization | test_create_org in acceptance_test.go | ✅ Pass |
```

> **Why this step exists**: Mock tests (run during sprint-run) verify frontend behavior in isolation. E2E tests verify the full stack works together. The acceptance criteria traceability check ensures nothing was forgotten — every requirement has a test, and every test passes.

## Phase 2: Sprint-level code review via /review

This is a final review of the entire Sprint's changes as a whole. Story-level reviews during `sprint run` catch issues within each Story, but this Sprint-level review catches cross-Story issues: inconsistencies between Stories, integration problems, duplicated code across Stories, and overall coherence.

4. After all gaps are filled, invoke the `/review` skill directly by using the Skill tool. Do NOT just mention /review or tell the user to run it — you must actually call it yourself as a slash command so that it executes and produces findings. This is a critical step; skipping it or deferring it to the user defeats the purpose of verify.
5. Read ALL findings produced by `/review`. For each finding:
   - If the fix direction is clear (code style, missing error handling, naming issues, refactoring with obvious approach, etc.), fix it immediately and autonomously
   - Only escalate to the user for decisions with significant architectural impact (changing data models, introducing major dependencies, altering public APIs, or deviating from the sprint plan)
6. After fixing findings, re-run `/review` to confirm the fixes are clean. Repeat until no more fixable findings remain.
7. If any findings require user input due to architectural impact, present them all together in a single summary with your recommended approach for each. The user can then confirm or override specific items. Log all autonomous decisions in `docs/sprint-logs/{SprintID}/`.

## Phase 2.5: Backlog proposals

Collect any out-of-scope issues discovered during the completeness check, smoke test, or code review that are NOT bugs in the current Sprint but warrant future attention (e.g., tech debt, missing tests in unrelated modules, performance concerns, refactoring opportunities). Present them to the user:
- For each item, provide a short title and one-line description
- Ask the user which items to add to the Backlog section of `docs/ROADMAP.json`
- For each approved item, use the "Append to backlog" filter from SKILL.md:
  ```bash
  jq --argjson item "$ITEM" '.backlog += [$item]' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
  ```
- If no out-of-scope issues were found, skip this step

## Phase 3: Finalize

8. Update `docs/ROADMAP.json` to reflect the verified state via in-place `jq` mutations (see SKILL.md "Writes"). Concrete filters:
   - **Mark each AC pass/fail**: "Mark AC status" filter, one invocation per AC
   - **Mark Stories that completed verification as `done`**: "Mark Story status" filter
   - Backlog items approved in Phase 2.5 already appended above
