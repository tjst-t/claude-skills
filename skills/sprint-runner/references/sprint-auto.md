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

Autonomous execution cannot ask the user for help. Follow these rules when things go wrong:

| Failure | Action | Max retries |
|---------|--------|-------------|
| **Tests fail after implementation** | Fix and re-run. If still failing after 3 attempts, mark the Story as incomplete, log the failure, and continue to the next Story. | 3 |
| **Build does not compile** | Read error output, attempt fix. If unresolvable after 2 attempts, stop the Sprint and mark status as `partial`. | 2 |
| **Smoke test endpoint missing** | Create the missing endpoint if it's part of the current Sprint's scope. If it belongs to a different Sprint, log it as a blocker and skip the Story. | 1 |
| **Merge conflict** | Attempt automatic resolution. If the conflict is non-trivial (both sides changed the same logic), log the conflict details and mark status as `partial`. | 1 |
| **Sprint has unresolvable dependency** | Stop the Sprint, mark as `blocked`, log the dependency. | 0 |

When a Sprint completes as `partial`:
- Completed Stories remain marked `[x]`
- Incomplete Stories remain `[ ]` with failure details in `docs/sprint-logs/{SprintID}/failures.md`
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
