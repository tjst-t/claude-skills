# sprint verify

Verify the Sprint implementation is complete and correct. Run this after `sprint run`.

## Phase 1: Completeness check

0. **Machine guard scan (run this FIRST — later phases read its output, never re-run its greps):**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT:-.}/hooks/run-guards.py --sprint {SprintID} --base {Sprint base SHA}
   ```
   This writes `docs/sprint-logs/{SprintID}/guards-run.json` — every grep-shaped check machine-run once: the forbidden-degradation scan (test-discipline Rule 6), done-judgment Guards 2/3/6/7 (+ configured 5/8), the E2E network-mock and `waitForTimeout` scans, and the prototype testid drift check. The machine authors the **facts** (which pattern hit, where); you apply the **policy** on each hit per the check's `note` and the skill docs. Running these greps by hand instead of reading the JSON is a defect. If this phase (or a later fix) changes code, re-run the scan so the artifact reflects the final tree.
1. Read only the current Sprint slice (see `references/roadmap-jq.md` → Reading patterns):
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
   - **Time-domain AC check**: For each AC tagged `[time-domain]`, the linked test must satisfy the progression-sampler shape defined in `references/time-domain-tests.md`. The `e2e_wait_for_timeout` hits in `guards-run.json` are the triage list: a hit in a `[time-domain]` AC's test means the forbidden `waitForTimeout` + final-state-only pattern — replace with a progression sampler before continuing.
   - **Prototype drift check** (GUI Sprints only): read `prototype_testid_drift` from `guards-run.json`. Each hit is a `data-testid` present in an approved `prototype/*.html` but missing from the implementation source — the implementation diverged from the approved prototype layout. Surface the list to the user and either update the implementation to match or update the prototype to reflect an intentional change. Do not silently accept drift.
3. If gaps are found, execute the missing work immediately

## Phase 1.5: E2E tests and acceptance criteria verification

All test-shape rules live in `references/test-discipline.md`. This phase applies them.

### Step 1: Start the real server

1. Run `make serve` (or the project's startup command) to bring up the real server
2. **Login gate**: Verify that the authentication endpoint the frontend uses exists and returns 200 for the dev token. If it does not exist, create it immediately.

### Step 2: Run tests and validate test shape

**Step 2.0 — Machine verifier (authoritative status).** Do NOT decide pass/fail by reading test output yourself — that is the exact hole that produced the fabrication incident (`references/verify-execution.md`). Run the project's declared verification through the wrapper, which writes a machine-authored verdict from real exit codes (+ JUnit):

```bash
python3 ${CLAUDE_PLUGIN_ROOT:-.}/hooks/run-verify.py --sprint {SprintID}
```

Then read `docs/sprint-logs/{SprintID}/verify-run.json`. Every `status` you later write in `verification-results.json` MUST be copied from this machine result; you author only `evidence` (verbatim log excerpts). If `run-verify.py` exits 2 (no verify command configured), that is a **gap**, not a pass — declare a `.claude/verify.json` (see `references/verify-execution.md`) or escalate; do not proceed as if tests passed. The framework-specific test-shape validations below (real browser, no network mocks, entry-point) still apply on top of the machine verdict.

3. **For GUI Stories**: Run `npx playwright test *.e2e.spec.ts`. For each `*.e2e.spec.ts`, validate against `test-discipline.md` Rules 2 and 4: real browser, no network mocks (read `e2e_network_mock` in `guards-run.json` — the machine already ran the greps; any hit is a rejection), user-affordance interactions, UI-state assertions, real-login auth. Mock tests are **never** a substitute. Any failure or shape violation: fix it, loop, escalate per `test-discipline.md` "Escalation" only if Claude Code genuinely cannot resolve.
4. **For non-GUI Stories**: Run the project's acceptance test runner. For each test file, validate against `test-discipline.md` Rule 2 by the Story's `story_type` (subprocess for `cli`, real HTTP client for `api`, public API only for `library`). Confirm every scenario step in `scenario-{StoryID}.json` has a corresponding action+assertion. Re-check classification — if the deliverable is browser-observable, it's a GUI Story (Rule 4 applies). Missing tests are a gap; fix now.
5. Document results in `docs/sprint-logs/{SprintID}/verification-results.json` (schema: `verification_results` in SPRINT_LOGS_SCHEMA.json). Each test entry includes its `story` and `acceptance_criteria` fields so traceability is derivable from this single file. **Each `status` is copied from the machine verdict in `verify-run.json` (Step 2.0), never decided by reading output**; `evidence` is your verbatim excerpt of the log. **Gate** (Rule 3): if `summary.skip > 0` or `summary.fail > 0`, OR `verify-run.json` `overall_machine_status != "pass"`, the Sprint cannot proceed past Phase 1.5. A failure here is escalated as `sprint verify failed` (mark the AC `fail`, Sprint `partial`/`needs_human`, stop) — it is NEVER reinterpreted as "pre-existing" or "out of scope".

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

## Phase 1.7: 8-Guard Done Judgment (mandatory per Story)

Before any Story can transition to `done`, apply the 8 guards to each Story in the Sprint. The guard definitions, patterns, and policies live in **`references/sprint-done-judgment.md` (canonical)** — this phase only says who runs what.

The mechanical half already ran in Phase 1 step 0: `guards-run.json` holds the machine-authored facts for Guards 2, 3, 6, 7 (and the configured Guard 5 / Guard 8 greps). Do NOT re-run those greps by hand — read the JSON and triage its hits. The judgment half (guard applicability, hit disposition) is yours:

1. **Guard 1 — user_review_required** (model): read `.user_review_required` from the Story slice. `true` ⇒ the Story cannot transition to `done` autonomously — only `needs_user_review`.
2. **Guard 2 — nil-injection mock** (machine facts + triage): attribute `guard2_nil_injection` hits to Stories by file. 3+ hits within one Story ⇒ warn and require user approval at the next sprint demo.
3. **Guard 3 — mock-mode smoke** (machine facts + triage): any `guard3_mock_mode_smoke` hit ⇒ that test does not satisfy priority_rule 9; a separate real-mode smoke is required.
4. **Guard 4 — priority_rule 9 exception validity** (model): if any Story `review_reason` or `decisions.json` rationale invokes the priority_rule 9 exception clause, confirm it names an explicit障害シナリオ identifier (`kill-9` / `停電` / `Shamir-unseal` / `ネットワーク遮断` / `disk-full` / `OOM` / `プロセスクラッシュ`). Unmatched claims are invalid; fall back to the normal real-mode smoke requirement.
5. **Guard 5 — call-path existence** (model, machine-assisted): for any AC describing cross-service coupling (API + Workflow trigger, backend → external SDK, etc.), check the coupling's grep — from `guards-run.json` `call_paths` when `.claude/guards.json` declares them, else run the greps from `sprint-done-judgment.md` Guard 5. Zero hits ⇒ the coupling does not exist in code ⇒ Story cannot be `done`.
6. **Guard 6 — deferred-comment residue** (machine facts + triage): every `guard6_deferred_comments` hit must have a corresponding backlog entry referencing the comment's file and line numbers. Any hit without one blocks `done` for the owning Story.
7. **Guard 7 — ADR conformance** (machine facts + triage): `guard7_adr_machine_checks` hits block `done` unless recorded as legitimate exceptions in `decisions.json` `guard7_exceptions`. Record hits under `guard7_adr_conformance` with the ADR id. (The machine scan covers `.claude/guards.json` `adr_checks` plus `machine_check:` blocks in ADR docs; confirm the ADRs in `decisions.json` `touched_adrs` are covered by one of the two.)
8. **Guard 8 — destructive multi-version test** (machine facts + triage): if the Story touched a configured data path, `guard8_destructive_tests` must be clean AND the destructive test must **pass** in the machine verdict (`verify-run.json`) — existence without a passing run does not count. A documented `guard8_rationale: n/a` meta Story is exempt.

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
    "guard7_adr_conformance": "pass | fail | warn",
    "guard8_destructive_multi_version_test": "pass | fail | n/a",
    "overall": "ok | needs_user_review"
  }
}
```

`overall: needs_user_review` ⇒ the Story cannot be marked `done` by `sprint done`. `sprint done` reads this block as its final gate; see `sprint-done.md`.

## Phase 1.8: Independent verifier (only with `--with-verifier`)

This phase runs **only** when `sprint verify` is invoked with `--with-verifier` (which `autopilot --auto` always passes). Phases 1.7 and earlier are run by the same session that implemented the code, which grades itself too leniently; this phase brings in a separate checker to backstop them. This is the Sprint's **single deep verification pass** — it runs once, at the end of verify, and no other layer re-derives its work (the implementing session reads machine facts in 1.7; the done gate and autopilot read recorded results).

1. Spawn a **fresh Agent** (a separate read-only Claude session) whose prompt is the spec in `references/verifier-agent.md` — including its verbatim skeptical stance. Give it the Sprint ID, the base SHA, the paths to `docs/ROADMAP.json` and `docs/sprint-logs/{SprintID}/guards-run.json`, and the **implementer-reported concerns** collected during `sprint run` (Step 1's `[{note, theme}]` list), which the verifier corroborates/dedupes and consolidates into the report's `concerns[]` sensor (category 5). It has NO write access to source / tests / ROADMAP.
2. The verifier re-derives, without trusting this session's `done_judgment`:
   - **AC ↔ code**: every AC reachable through the user's entry point, asserted on the real backend round-trip (not a green test name)
   - **Forbidden-category scan** (`test-discipline.md` Rule 6 forbidden-degradation categories): reconcile the machine facts in `guards-run.json` (freshness, spot-checks) rather than re-grepping the whole diff — per `verifier-agent.md` category 2
   - **ADR conformance** against `decisions.json` `touched_adrs`
   - **Compromise completeness** vs. the self-reported `compromises.json` / `done_judgment`
3. The verifier writes `docs/sprint-logs/{SprintID}/verification-report.json` per `references/VERIFICATION_REPORT_SCHEMA.json`.
4. **Reconcile**: where the verifier disagrees with this session's self-report, the verifier wins. A verifier `fail` in the AC or ADR category that maps to an immediate-stop condition halts autopilot; a `fail` / `warn` the implementer missed is merged into `compromises.json` with `overlooked_by_autopilot: true`, and the owning Story's `done_judgment.overall` is downgraded to `needs_user_review`.

Without `--with-verifier`, skip this phase entirely; the single-session 8-guard pass (Phase 1.7) is the only gate. In that standalone case there is no `verification-report.json` to hold the `concerns[]` sensor and no milestone retrospective to roll it up, so simply **surface any implementer-reported concerns to the user** at the end of verify (one line each) rather than dropping them — the user decides whether any is worth a backlog item. The structured concerns→retrospective→self-audit path exists only under autopilot (which always runs the verifier).

## Phase 2: Sprint-level cross-Story review via /review

Story-level reviews during `sprint run` already covered each Story's diff in isolation (with their own capped fix loop). This phase reviews only what those reviews structurally could not see: **cross-Story issues** — inconsistencies between Stories, integration problems, duplicated code across Stories. Re-reviewing the whole Sprint diff would repeat work the Story-level reviews already did.

4. After all gaps are filled, compute the cross-Story surface:
   - files touched by 2 or more Stories in this Sprint (compare the per-Story branch diffs)
   - interfaces between Stories (code in one Story that calls / imports / renders what another Story introduced)
   Then invoke the `/review` skill directly via the Skill tool, scoped to that surface (name the files and the cross-Story focus in the invocation). Do NOT just mention /review or tell the user to run it — you must actually call it yourself. Exception: if the Sprint has a single Story or the Stories share no files/interfaces, run one `/review` over the full Sprint diff instead (there was no Story-level review overlap to rely on).
5. Read ALL findings produced by `/review`. For each finding:
   - If the fix direction is clear (code style, missing error handling, naming issues, refactoring with obvious approach, etc.), fix it immediately and autonomously
   - Only escalate to the user for decisions with significant architectural impact (changing data models, introducing major dependencies, altering public APIs, or deviating from the sprint plan)
6. **Re-run `/review` at most once**, only if fixes were applied in step 5, and scoped to the files those fixes touched. Findings still open after the re-run are NOT looped again — an unbounded polish loop costs more than it catches. Dispose of each residual explicitly, with two hard rules:
   - **A correctness bug is not deferrable by the cap.** The cap bounds review rounds, not bug fixing: fix it and prove it with tests (machine verdict), or escalate as `needs_human`. Only quality/polish residuals may be deferred.
   - **Every deferred residual must reach a human channel**: route it to the Phase 2.5 backlog proposals (user-facing — presented interactively, or listed under "Backlog items added" at the autopilot milestone). A fix applied without a re-review round is logged to `docs/sprint-logs/{SprintID}/decisions.json`. Silently absorbing a residual is forbidden — the cap trades review rounds for tokens, never visibility.
7. If any findings require user input due to architectural impact, present them all together in a single summary with your recommended approach for each. The user can then confirm or override specific items. Log all autonomous decisions in `docs/sprint-logs/{SprintID}/`.

## Phase 2.5: Backlog proposals

Collect any out-of-scope issues discovered during the completeness check, smoke test, or code review that are NOT bugs in the current Sprint but warrant future attention (e.g., tech debt, missing tests in unrelated modules, performance concerns, refactoring opportunities). Present them to the user:
- For each item, provide a short title and one-line description
- Ask the user which items to add to the Backlog section of `docs/ROADMAP.json`
- For each approved item, use the "Append to backlog" filter from `references/roadmap-jq.md`:
  ```bash
  jq --argjson item "$ITEM" '.backlog += [$item]' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
  ```
- If no out-of-scope issues were found, skip this step

## Phase 3: Finalize

8. Update `docs/ROADMAP.json` to reflect the verified state via in-place `jq` mutations (see `references/roadmap-jq.md` → Named write filters). Concrete filters:
   - **Mark each AC pass/fail**: "Mark AC status" filter, one invocation per AC
   - **Mark Stories that completed verification as `done`**: "Mark Story status" filter
   - Backlog items approved in Phase 2.5 already appended above
9. **Record verify metrics** — update `docs/sprint-logs/{SprintID}/run-metrics.json` (created by `sprint run`; schema in `references/SPRINT_LOGS_SCHEMA.json`) via `jq`: `verifier_ran` (Phase 1.8 on/off), `sprint_review_runs` (1 or 2), `guards_machine_run` (guards-run.json present). This is the token-budget sensor: together with `sprint run`'s agent/cycle counts it lets the milestone retrospective answer "where did the tokens go" with data instead of impressions.
