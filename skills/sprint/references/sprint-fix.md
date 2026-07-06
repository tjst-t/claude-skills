# sprint fix

Lightweight fix path for small changes that don't warrant a full sprint cycle. Fix, test, commit — nothing more.

> Renamed from `sprint hotfix`. The old name still works as a deprecated alias — `sprint hotfix` runs this flow and prints a one-line deprecation note ("`sprint hotfix` is now `sprint fix`").

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

If unsure, start with `sprint fix`. If the change turns out to be larger than expected, stop and suggest `sprint idea` instead.

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
- If tests fail for unrelated reasons, log but don't block the fix

### 4. Commit

- Stage only the modified files (not `git add -A`)
- Commit with message: `fix: {brief description}`
- Do NOT push automatically — let the user decide when to push

### 5. Optional: Log to ROADMAP

If the user wants tracking, append an entry to the `backlog` array in `docs/ROADMAP.json` with an in-place `jq` mutation (see `references/roadmap-jq.md` → Reading patterns — do not Read the whole ROADMAP for this):

```bash
jq --argjson new '{"title":"Fix login button size","description":"Increased padding and font-size per user feedback","added_in":"fix","reason":"User request","status":"done"}' \
  '.backlog += [$new]' docs/ROADMAP.json > /tmp/roadmap.json && mv /tmp/roadmap.json docs/ROADMAP.json
```

Only do this if the user asks for it. Most fixes don't need tracking.

## Time-domain UI fix

If the bug involves animation, smooth scroll, transition, debounce/throttle, or async-render coordination, the regular Flow above is insufficient. Follow the "Fix workflow for time-domain bugs" in [time-domain-tests.md](time-domain-tests.md) instead: tag the AC `[time-domain]`, write the progression-sampling test FIRST and confirm it fails, then implement the fix and confirm it passes. Continue with this file's Step 4 (Commit) and Step 5 (Optional: Log to ROADMAP).

## Important Behaviors

- **Fast**: The entire fix should take under a minute for simple changes. No planning, no review, no demo ceremony.
- **Minimal scope**: Fix only what was asked. Don't refactor, don't add tests for unrelated code, don't improve surrounding code.
- **Test but don't gate**: Run tests to catch breakage, but don't block the commit on unrelated test failures.
- **No sprint state changes**: `sprint fix` does not modify sprint status, story status, or progress in ROADMAP.json (unless the user explicitly asks).
- **Works during any phase**: Can be used mid-sprint, between sprints, or after all sprints are done. Does not interfere with sprint state.
