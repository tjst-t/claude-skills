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

**When the fix is outside the current Sprint's scope:**

If the root cause is in code that belongs to a different Sprint (e.g., missing DB migration, incomplete API from a prior Sprint, infrastructure not yet set up):
1. Create a new fix Story in the Backlog of `docs/ROADMAP.md` with a clear description of what needs to be fixed and why
2. Insert a new Sprint (or add the fix Story to the next unfinished Sprint) in the execution order, **before** the current Sprint
3. Mark the current Story as `[ ]` with a dependency note: `Depends on: {fix Story ID}`
4. Mark the current Sprint as `partial` and return — autopilot will execute the fix Sprint next, then retry the current Sprint

This ensures scope-external problems are resolved autonomously rather than escalated to the user.

**Escalate to the user only when Claude Code genuinely cannot resolve the issue:**
- The fix requires information that is not available in the codebase AND cannot be derived (e.g., external API credentials, third-party service secrets, paid service account setup)
- The fix requires human judgment on a real-world constraint that has no representation in code, VISION, or DESIGN_PRINCIPLES (e.g., legal compliance question, business rule that was never documented)

When escalating:
- Log the full diagnosis to `docs/sprint-logs/{SprintID}/failures.md`: what was tried, why each attempt failed, and why Claude Code cannot resolve it
- Mark the Story as incomplete: add `⚠️ NEEDS_HUMAN: {reason}` to the Story entry in ROADMAP.md
- The milestone review will surface this to the user

### Other failures

| Failure | Action |
|---------|--------|
| **Build does not compile** | Read error output, fix, and rebuild. Loop until it compiles. If the error is caused by a missing dependency or tool, attempt to install it. Escalate only if installation requires credentials or permissions Claude Code does not have. |
| **E2E endpoint missing** | Create the missing endpoint if it's part of the current Sprint's scope. If it belongs to a different Sprint, create a fix Sprint in the roadmap (same as scope-external test fix above). |
| **Merge conflict** | Attempt automatic resolution. If the conflict is in logic (not just formatting), read both sides, understand intent, and resolve. Loop until resolved. Escalate only if the conflict represents a genuine ambiguity that cannot be resolved from VISION/PRINCIPLES. |
| **Sprint has unresolvable dependency** | Create a fix Sprint to resolve the dependency, insert it before the current Sprint, and return `partial`. |

### Sprint completion status

- `success` — all Stories complete, all tests pass
- `partial` — some Stories incomplete; fix Sprints may have been created in the roadmap
- `needs_human` — at least one Story requires human intervention (⚠️ NEEDS_HUMAN flagged)

When a Sprint completes as `partial`:
- Completed Stories remain marked `[x]`
- Incomplete Stories remain `[ ]` with dependency notes or `⚠️ NEEDS_HUMAN`
- Failure details logged to `docs/sprint-logs/{SprintID}/failures.md`
- The Sprint status stays `[IN PROGRESS]`, not `[DONE]`
- The calling skill (autopilot) checks if a fix Sprint was inserted — if so, execute it next, then retry the incomplete Stories

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
