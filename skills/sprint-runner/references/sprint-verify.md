# sprint verify

Verify the Sprint implementation is complete and correct. Run this after `sprint run`.

## Phase 1: Completeness check

1. Read `docs/ROADMAP.md` and identify the current Sprint
2. Use a subagent to perform a comprehensive review:
   - Compare every Task in the Sprint against the actual code changes and test logs in `docs/sprint-logs/{SprintID}/`
   - Check for any Tasks marked incomplete or missing implementation
   - Check for any Tasks that were implemented but not marked complete
   - **For GUI Stories**: Verify that `npx playwright test` passes for each Story's test file. If any tests are failing, treat this as an incomplete Task and execute the missing work immediately.
   - **API mock contract check**: For GUI Stories, compare the data shapes returned by Playwright test mocks against the actual backend handler implementations. Pay special attention to pagination response wrappers (`items` wrapper presence/absence). If mocks diverge from the real API, fix the tests immediately.
3. If gaps are found, execute the missing work immediately

## Phase 1.5: E2E tests and acceptance criteria verification

Perform the following before invoking `/review`:

### Step 1: Start the real server

1. Run `make serve` (or the project's startup command) to bring up the real server
2. **Login gate**: Verify that the authentication endpoint the frontend uses exists and returns 200 for the dev token. If it does not exist, create it immediately.

### Step 2: Run E2E tests

3. **For GUI Stories**: Run all E2E test files: `npx playwright test *.e2e.spec.ts`
   - These tests hit the real server (no mocks) and verify the full stack works together
   - If any E2E tests fail, fix the issue (could be frontend, backend, or integration problem) and re-run
4. **For non-GUI Stories**: Run backend acceptance tests (e.g., `go test ./tests/acceptance/...` or equivalent)
   - If no acceptance tests exist for a Story, this is a gap — create them now
5. Document test results in `docs/sprint-logs/{SprintID}/e2e-results.md`

### Step 3: Acceptance criteria traceability check

6. For each Story in the Sprint, read its acceptance criteria from `docs/ROADMAP.md`
7. For each acceptance criterion, verify a corresponding test exists:
   - GUI Stories: look for `[AC-{StoryID}-{N}]` tagged tests in `*.e2e.spec.ts`
   - Non-GUI Stories: look for test functions named with the acceptance criterion reference
8. **If any acceptance criterion has no corresponding test**: create the missing test and run it
9. **If any acceptance criterion's test is failing**: fix the implementation and re-run
10. Log the traceability matrix to `docs/sprint-logs/{SprintID}/acceptance-matrix.md`:

```markdown
| Story | Acceptance Criterion | Test | Status |
|-------|---------------------|------|--------|
| S002-1 | AC-1: VM list displays after login | [AC-S002-1-1] in vm-list.e2e.spec.ts | ✅ Pass |
| S002-1 | AC-2: VM can be started | [AC-S002-1-2] in vm-list.e2e.spec.ts | ✅ Pass |
| S002-2 | AC-1: User can create organization | test_create_org in acceptance_test.go | ✅ Pass |
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
- Ask the user which items to add to the Backlog section of `docs/ROADMAP.md`
- Only add items the user approves
- If no out-of-scope issues were found, skip this step

## Phase 3: Finalize

8. Update `docs/ROADMAP.md` to reflect the verified state (including any backlog items approved in Phase 2.5)
