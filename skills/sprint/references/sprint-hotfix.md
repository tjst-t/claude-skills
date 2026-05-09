# sprint hotfix

Lightweight fix path for small changes that don't warrant a full sprint cycle. Fix, test, commit — nothing more.

## When to Use

- CSS/styling tweaks ("make the button bigger", "change the color")
- Text/copy changes ("fix the typo", "change the label")
- Small bug fixes (off-by-one, missing null check, wrong URL)
- Minor UI adjustments (spacing, alignment, icon swap)
- Configuration changes (environment variables, feature flags)

## When NOT to Use — Use a Full Sprint Instead

- New feature or screen (even a small one)
- Changes that affect multiple Stories or cross component boundaries
- Changes that require new acceptance criteria
- Anything that needs design discussion or architectural decisions

If unsure, start with hotfix. If the change turns out to be larger than expected, stop and suggest `sprint propose` instead.

## Flow

### 1. Understand the request

The user describes what to fix. No story format needed, no acceptance criteria — just the problem and the desired outcome.

### 2. Implement the fix

- Make the change directly — no worktree, no sub-agent
- Keep changes minimal and focused — fix exactly what was asked
- For UI changes: use `/frontend-design` if the change involves visual design quality
- If an approved prototype exists in `prototype/`, check if the fix conflicts with the prototype and update it if needed

### 3. Run affected tests

- Identify test files that cover the modified code
- Run them: mock tests, E2E tests, acceptance tests — whatever is relevant
- If tests fail due to the change (e.g., element text changed), update the tests to match the new behavior
- If tests fail for unrelated reasons, log but don't block the hotfix

### 4. Commit

- Stage only the modified files (not `git add -A`)
- Commit with message: `hotfix: {brief description}`
- Do NOT push automatically — let the user decide when to push

### 5. Optional: Log to ROADMAP

If the user wants tracking, add an entry to the `backlog` array in `docs/ROADMAP.json` with `"status": "done"`:

```json
{
  "title": "Fix login button size",
  "description": "Increased padding and font-size per user feedback",
  "added_in": "hotfix",
  "reason": "User request",
  "status": "done"
}
```

Only do this if the user asks for it. Most hotfixes don't need tracking.

## Time-domain UI hotfix

If the bug involves animation, smooth scroll, transition, debounce/throttle, or async-render coordination (Shiki / mermaid / images / debounced input), the regular Flow above is insufficient — final-state-only tests routinely pass while the user-visible motion is broken. Override the Flow as follows:

1. **Mark the AC as `[time-domain]`** — see gui-spec SKILL Phase 4C for the schema (trigger / progression / final). If the AC doesn't exist yet, write it first; if it exists without the tag, add the tag and break it into the three parts.
2. **Write the progression-sampling Playwright test BEFORE touching the implementation.** The test must assert both:
   - **intermediate progression** — state captured at multiple ms offsets inside `page.evaluate` (monotonic constraint, threshold by t=N ms, etc.), AND
   - **final convergence** — the steady-state condition.

   See [gui-spec test-examples.md "Time-domain Test Example"](../../gui-spec/references/test-examples.md) for the template.
3. **Verify the new test FAILS against the broken implementation.** If it passes against the broken state, the test is wrong (likely a final-state-only assertion that lets the bug slip through). Iterate on the test until it reproduces the user-visible regression.
4. **Implement the fix.** Iterate until the test passes.
5. Continue with the regular Flow steps 4 (Commit) and 5 (Optional: Log to ROADMAP).

This workflow exists because UI time-domain regressions (animation stops short, scroll lands in the wrong place, transition stutters) routinely pass final-state-only tests — past incidents needed 10+ iterations to root-cause when the test gap was filled only at the end. A 100ms-cadence sampler reveals stuck states at first sight.

## Important Behaviors

- **Fast**: The entire hotfix should take under a minute for simple changes. No planning, no review, no demo ceremony.
- **Minimal scope**: Fix only what was asked. Don't refactor, don't add tests for unrelated code, don't improve surrounding code.
- **Test but don't gate**: Run tests to catch breakage, but don't block the commit on unrelated test failures.
- **No sprint state changes**: Hotfix does not modify sprint status, story status, or progress in ROADMAP.json (unless the user explicitly asks).
- **Works during any phase**: Can be used mid-sprint, between sprints, or after all sprints are done. Does not interfere with sprint state.
