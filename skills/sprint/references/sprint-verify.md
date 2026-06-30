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
   - **Time-domain AC check**: For each AC tagged `[time-domain]`, the linked test must satisfy the progression-sampler shape defined in `gui-spec/references/time-domain-tests.md`. The forbidden `page.waitForTimeout` + final-state-only pattern is rejected. Replace with a progression sampler before continuing.
   - **Prototype drift check** (GUI Sprints only): If `prototype/` contains HTML files for this Sprint's Stories, extract every `data-testid` value from those files. For each testid, confirm it appears in the implementation source (frontend components / templates). Missing testids mean the implementation diverged from the approved prototype layout — surface the list to the user and either update the implementation to match or update the prototype to reflect an intentional change. Do not silently accept drift.
3. If gaps are found, execute the missing work immediately

## Phase 1.5: E2E tests and acceptance criteria verification

All test-shape rules live in `references/test-discipline.md`. This phase applies them.

### Step 1: Start the real server

1. Run `make serve` (or the project's startup command) to bring up the real server
2. **Login gate**: Verify that the authentication endpoint the frontend uses exists and returns 200 for the dev token. If it does not exist, create it immediately.

### Step 2: Run tests and validate test shape

3. **For GUI Stories**: Run `npx playwright test *.e2e.spec.ts`. For each `*.e2e.spec.ts`, validate against `test-discipline.md` Rules 2 and 4: real browser, no network mocks (grep `page.route(`, `MSW`, `setupServer`, `fetch.mockImplementation`, `vi.mock`, `jest.mock`), user-affordance interactions, UI-state assertions, real-login auth. Mock tests are **never** a substitute. Any failure or shape violation: fix it, loop, escalate per `test-discipline.md` "Escalation" only if Claude Code genuinely cannot resolve.
4. **For non-GUI Stories**: Run the project's acceptance test runner. For each test file, validate against `test-discipline.md` Rule 2 by the Story's `story_type` (subprocess for `cli`, real HTTP client for `api`, public API only for `library`). Confirm every scenario step in `scenario-{StoryID}.json` has a corresponding action+assertion. Re-check classification — if the deliverable is browser-observable, it's a GUI Story (Rule 4 applies). Missing tests are a gap; fix now.
5. Document results in `docs/sprint-logs/{SprintID}/verification-results.json` (schema: `verification_results` in SPRINT_LOGS_SCHEMA.json). Each test entry includes its `story` and `acceptance_criteria` fields so traceability is derivable from this single file. **Gate** (Rule 3): if `summary.skip > 0` or `summary.fail > 0`, the Sprint cannot proceed past Phase 1.5.

### Step 3: Acceptance criteria traceability check

6. Read acceptance criteria for each Story from `docs/ROADMAP.json`.
7. For every AC, verify at least one test in `verification-results.json` lists it in `acceptance_criteria` AND has `status: "pass"`. Naming convention for the test: GUI uses `[AC-{StoryID}-{N}]` in `*.e2e.spec.ts`; non-GUI uses test functions named with the AC reference.
8. Missing test → create, run, and ensure it appears in `verification-results.json`. Failing test → fix and re-run. Skipped / pending / not-actually-executed → treat as failure (Rule 3); never claim `pass` for a test that did not run (Rule 5).

### Step 3.5: Diff coverage scan (Rule 6)

Verify that everything **implemented** in this Sprint — not just what was **declared** — is exercised by a passing test.

10. Compute the Sprint's diff against its base branch: `git diff --name-status {base}..HEAD` plus per-file content diffs as needed.
11. Collect the "user-observable additions" reports from each implementation sub-agent (returned during `sprint run` — Rule 6). Treat them as a starting list, not the final list.
12. Independently enumerate user-observable surfaces added in the diff (per `test-discipline.md` Rule 6 categories):
    - **API**: grep for new route registrations (`router.{get,post,put,patch,delete}(`, `app.{get,post,...}(`, `@app.route`, `routes.{get,...}`, etc.) and new request/response fields; compare against base branch.
    - **CLI**: scan command/flag definitions (e.g., `cobra.Command`, `argparse.add_argument`, `commander.option`, `clap`) for new entries.
    - **GUI**: scan route definitions (`<Route path=...>`, file-based routing additions under `pages/` or `app/`) and new interactive components (`data-testid` additions on actionable elements).
    - **Library**: scan new exported names in the package's public surface (e.g., `export function`, capital-letter names in Go, new `__all__` entries in Python).
13. For each enumerated surface, confirm at least one test in `verification-results.json` exercises it. The match rule is shape-specific:
    - API route → a test whose name or `file` indicates it issues a request to that exact `{method} {path}`
    - CLI flag/subcommand → a test that spawns the binary with that flag/subcommand in its `action` step
    - GUI screen/component → a real-browser test that navigates to the route / interacts with the component's `data-testid`
    - Library export → a consumer-style test that imports and calls the symbol
14. **For every untested addition**, choose one resolution and apply it now:
    - **Add coverage**: write an AC + scenario step + test, run it, update `verification-results.json`. Preferred when the addition is intentional and in scope.
    - **Revert**: remove the addition from the diff. Use when it's scope creep that wasn't approved.
    - **Escalate**: if neither (a) nor (b) is feasible, log to `failures.json` with the surface name and why it can't be tested, mark the Story `partial` / `needs_human`, and stop. The user decides.
15. Log the diff coverage scan results (enumerated additions and their resolution status) to `verification-results.json` under a top-level `diff_coverage` field, so `sprint done` can confirm it ran.
9. For human readability, render a markdown traceability table at the end of the verify summary (derived from `verification-results.json`, not stored as a separate file):

```markdown
| Story | Acceptance Criterion | Test | Status |
|-------|---------------------|------|--------|
| Sb1e4d8-1 | AC-1: VM list displays after login | [AC-Sb1e4d8-1-1] in vm-list.e2e.spec.ts | ✅ Pass |
| Sb1e4d8-2 | AC-1: User can create organization | test_create_org in acceptance_test.go | ✅ Pass |
```

> **Why this step exists**: Mock tests (run during sprint-run) verify frontend behavior in isolation. E2E tests verify the full stack works together. The traceability check ensures every requirement has a passing test in this Sprint's run.

## Phase 1.7: 6-Guard Done Judgment (mandatory per Story)

Before any Story can transition to `done`, apply all 6 guards from `references/sprint-done-judgment.md` to each Story in the Sprint. This catches the "偽 done" patterns identified in the 2026-05-17 audit (user_review_required bypass, nil-injection mocks, mock-mode smoke, priority_rule 9 exception misuse, missing call paths, deferred-comment residue).

For each Story:

1. **Guard 1 — user_review_required**: read `.user_review_required` from the Story in `docs/ROADMAP.json`. If `true`, the Story cannot transition to `done` autonomously — only `needs_user_review`.
2. **Guard 2 — nil-injection mock**: grep the Story's main implementation files for `if [a-zA-Z_]+\.[A-Z][a-zA-Z]* != nil \{` (the multi-dep nil-guard anti-pattern). 3+ hits in the same Story ⇒ warn and require user approval at the next sprint demo.
3. **Guard 3 — mock-mode smoke**: scan `tests/acceptance/devvm/` (or the project's equivalent real-mode smoke path) for `MOCK=true|--fake-|DRY_RUN=1|fake_core: true|InMemoryStore`. Any hit ⇒ priority_rule 9 not satisfied; a separate real-mode smoke is required.
4. **Guard 4 — priority_rule 9 exception validity**: if any Story `review_reason` or `decisions.json` rationale invokes the priority_rule 9 exception clause, confirm it names an explicit障害シナリオ identifier (`kill-9` / `停電` / `Shamir-unseal` / `ネットワーク遮断` / `disk-full` / `OOM` / `プロセスクラッシュ`). Unmatched claims are invalid; fall back to the normal real-mode smoke requirement.
5. **Guard 5 — call-path existence**: for any AC describing cross-service coupling (API + Workflow trigger, backend → external SDK, etc.), run the call-path greps from `sprint-done-judgment.md` Guard 5. Zero hits ⇒ the coupling does not exist in code ⇒ Story cannot be `done`.
6. **Guard 6 — deferred-comment residue**: run `git diff {Sprint base SHA}..HEAD -- 'cmd/' 'internal/' 'ansible/'` and grep for newly-added `// TODO.*Phase [0-9]` / `// Sprint [0-9].*で.*実装` / `// Sprint [0-9].*で.*追加` / `# TODO.*Phase [0-9]` etc. Any match without a corresponding backlog entry referencing the comment line numbers blocks `done` for the owning Story.

Record each guard's outcome under `done_judgment` in `verification-results.json`:

```json
{
  "story_id": "S5225ae-5",
  "done_judgment": {
    "guard1_user_review_required_not_done": "pass | fail",
    "guard2_nil_injection_mock": "pass | fail | warn",
    "guard3_mock_mode_not_real_smoke": "pass | fail",
    "guard4_priority_rule_9_exception_valid": "pass | fail | n/a",
    "guard5_call_path_grep": "pass | fail",
    "guard6_deferred_comment_clean": "pass | fail",
    "overall": "ok | needs_user_review"
  }
}
```

`overall: needs_user_review` ⇒ the Story cannot be marked `done` by `sprint done`. `sprint done` reads this block as its final gate; see `sprint-done.md`.

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
