# sprint auto

Execute a single Sprint autonomously — plan, run, verify, and done — without user interaction. All decisions are made by Claude and logged for post-hoc review.

This command is designed to be called by the `autopilot` skill for multi-sprint execution, but can also be invoked directly by the user for a single autonomous sprint.

## Prerequisites

- `docs/ROADMAP.md` must exist with at least one unfinished Sprint
- `docs/VISION.md` and `docs/DESIGN_PRINCIPLES.md` should exist (read them if present — they guide autonomous decisions). If missing, **fall back to interactive mode**: run the normal `sprint plan` → `sprint run` → `sprint verify` → `sprint done` sequence instead, which asks the user for decisions. Log a warning explaining why auto mode was downgraded.

## Execution Flow

### 0. Branch setup

Create a dedicated branch for this Sprint's autonomous work:
- `git checkout -b autopilot/{SprintID}` from the current branch
- All commits during this Sprint happen on this branch
- The branch is merged back (or into main) during `sprint done` or at the autopilot milestone review
- This prevents autonomous pushes from landing directly on main

### 1. Autonomous Plan

Same as `sprint plan` but fully autonomous:
- Read `docs/ROADMAP.md`, `docs/VISION.md`, `docs/DESIGN_PRINCIPLES.md`
- Identify the next unfinished Sprint
- Validate and rewrite user stories autonomously
- Evaluate story granularity — if a Story is overloaded, split it autonomously based on VISION and DESIGN_PRINCIPLES guidance
- Run `gui-spec` in **autonomous mode** (see gui-spec SKILL.md "Autonomous Mode" section — all scenarios are derived and confirmed without user interaction)
- Log all planning decisions to `docs/sprint-logs/{SprintID}/decisions.md`
- Update `docs/ROADMAP.md` with any changes

**No user confirmation.** All decisions are logged.

### 2. Autonomous Run

Same as `sprint run` but:
- All technical and architectural decisions are made autonomously
- Decisions that would normally be escalated to the user are instead decided by consulting `docs/VISION.md` and `docs/DESIGN_PRINCIPLES.md`, then logged to `docs/sprint-logs/{SprintID}/decisions.md` with rationale
- Out-of-scope issues are automatically added to the Backlog section (no user approval needed)

### 3. Autonomous Verify

Same as `sprint verify` but:
- All findings are fixed autonomously
- Architectural decisions are made by consulting VISION and DESIGN_PRINCIPLES, then logged
- Backlog proposals are automatically added
- Smoke test failures are fixed immediately

### 4. Autonomous Done

Same as `sprint done` but:
- Worktree cleanup proceeds without confirmation (unmerged worktrees are logged as warnings, not deleted)
- Commit and push the `autopilot/{SprintID}` branch without user confirmation (safe — this is not main)
- Skip the summary presentation (the calling skill or user can read the logs)

## Failure Recovery

Autonomous execution cannot ask the user for help. The default behavior is **keep trying until fixed**. Only give up when further attempts cannot possibly succeed.

### Test failures (mock tests, E2E tests, acceptance tests)

**Loop until fixed:**
1. Read the failure output carefully
2. Analyze the root cause (frontend bug, backend bug, integration mismatch, test data issue, timing issue)
3. Fix the issue
4. Re-run the failing tests
5. If still failing, go back to step 1 with a different approach

**Give up only when:**
- The fix requires information that is not available in the codebase (e.g., external API credentials, third-party service configuration)
- The fix requires a design decision that contradicts both VISION.md and DESIGN_PRINCIPLES.md (genuine conflict with no clear resolution)
- The same root cause has been correctly identified but the fix is architecturally impossible within the current Sprint's scope (e.g., requires a database migration from a prior Sprint that was not completed)

When giving up:
- Log the full diagnosis to `docs/sprint-logs/{SprintID}/failures.md`: what was tried, why each attempt failed, and why further attempts are futile
- Mark the Story as incomplete with a clear summary of the blocker
- **Flag it prominently** so the user sees it at milestone review: add `⚠️ BLOCKED: {reason}` to the Story entry in ROADMAP.md

### Other failures

| Failure | Action |
|---------|--------|
| **Build does not compile** | Read error output, fix, and rebuild. Loop until it compiles. Give up only if the error is caused by a missing dependency or tool that cannot be installed autonomously. |
| **E2E endpoint missing** | Create the missing endpoint if it's part of the current Sprint's scope. If it belongs to a different Sprint, log it as a blocker and mark the Story incomplete. |
| **Merge conflict** | Attempt automatic resolution. If the conflict is in logic (not just formatting), read both sides, understand intent, and resolve. Give up only if the conflict represents a genuine design disagreement between two Stories that requires user input. |
| **Sprint has unresolvable dependency** | Stop the Sprint, mark as `blocked`, log the dependency. |

### Sprint completion status

- `success` — all Stories complete, all tests pass
- `partial` — some Stories incomplete (blocked items flagged with ⚠️)
- `blocked` — Sprint cannot proceed due to external dependency

When a Sprint completes as `partial`:
- Completed Stories remain marked `[x]`
- Incomplete Stories remain `[ ]` with `⚠️ BLOCKED: {reason}` and failure details in `docs/sprint-logs/{SprintID}/failures.md`
- The Sprint status stays `[IN PROGRESS]`, not `[DONE]`
- The calling skill (autopilot) decides whether to continue to the next Sprint or stop

## Decision Logging

All autonomous decisions MUST be logged to `docs/sprint-logs/{SprintID}/decisions.md` in this format:

```markdown
# Sprint {SprintID} — Autonomous Decisions

## Planning Decisions
- **Story S001-3 split**: Split into S001-3 and S001-4 because the original had CRUD + search in one story. Guided by DESIGN_PRINCIPLES: "one story = one user-facing behavior".
- **GUI spec: login form entry point**: Auto-selected direct URL `/login` — standard pattern, no ambiguity.

## Implementation Decisions
- **Auth middleware approach**: Chose JWT over session cookies. Rationale: VISION.md specifies stateless API, DESIGN_PRINCIPLES prefers "existing library > custom".
- **Backlog added**: "Refactor legacy error handler" — found during Story S001-2 implementation.

## Review Decisions
- **Naming convention fix**: Renamed `getData` to `fetchOrganizations` — specificity rule from DESIGN_PRINCIPLES.
```

## Return Value

When called by the `autopilot` skill, return:
- Sprint ID and title
- Completion status (success / partial / failed)
- Number of stories completed
- List of decisions made (summary, not full log)
- Any warnings or unresolved issues
- Path to full decision log
