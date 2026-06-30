# sprint auto

Execute a single Sprint autonomously — plan, run, verify, and done — without user interaction. All decisions are made by Claude and logged for post-hoc review.

This command is designed to be called by the `autopilot` skill for multi-sprint execution, but can also be invoked directly by the user for a single autonomous sprint.

## Prerequisites

- `docs/ROADMAP.json` must exist with at least one unfinished Sprint
- `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json` should exist (read them if present — they guide autonomous decisions). If missing, **fall back to interactive mode**: run the normal `sprint plan` → `sprint run` → `sprint verify` → `sprint done` sequence instead, which asks the user for decisions. Log a warning explaining why auto mode was downgraded.

## Execution Flow

### 0. Branch setup

Create a dedicated branch for this Sprint's autonomous work:
- Determine the current base branch name: `git branch --show-current` (e.g., `main`, `feature/auth`)
- Sanitize the branch name for use in paths: replace `/` with `-` (e.g., `feature/auth` → `feature-auth`)
- `git checkout -b autopilot/{base-branch-sanitized}/{SprintID}` from the current branch (e.g., `autopilot/main/Sc7d2a1`, `autopilot/feature-auth/Sc7d2a1`)
- All commits during this Sprint happen on this branch
- The branch is merged back into the base branch during `sprint done` or at the autopilot milestone review
- This naming convention prevents branch collisions when multiple autopilot sessions run on different branches simultaneously

### 1. Autonomous Plan

Same as `sprint plan` but fully autonomous:
- Read `docs/VISION.json`, `docs/DESIGN_PRINCIPLES.json` (full files — these are short)
- Read only the slice you need from `docs/ROADMAP.json` (see SKILL.md "Roadmap Reading Patterns"): top-level structure to find the next unfinished Sprint, then that Sprint's slice
  ```bash
  jq '{progress, execution_order, dependencies, sprints: (.sprints | map_values({title, status, milestone}))}' docs/ROADMAP.json
  jq --arg id "<NextSprintID>" '.sprints[$id]' docs/ROADMAP.json
  ```
- Identify the next unfinished Sprint
- Validate and rewrite user stories autonomously
- Evaluate story granularity — if a Story is overloaded, split it autonomously based on VISION and DESIGN_PRINCIPLES guidance
- Run `gui-spec` in **autonomous mode** (see gui-spec SKILL.md "Autonomous Mode" section — all scenarios are derived and confirmed without user interaction)
- Log all planning decisions to `docs/sprint-logs/{SprintID}/decisions.json`
- Update `docs/ROADMAP.json` with any changes via in-place `jq` mutations — see SKILL.md "Writes" for the named filters (Mark Sprint/Story/Task/AC status, Recompute progress, Add new Sprint, Append to execution_order, Add dependency, Append to backlog, etc.)

**No user confirmation.** All decisions are logged.

### 2. Autonomous Run

Same as `sprint run` but:
- All technical and architectural decisions are made autonomously
- Decisions that would normally be escalated to the user are instead decided by consulting `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json`, then logged to `docs/sprint-logs/{SprintID}/decisions.json` with rationale
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
- Commit and push the `autopilot/{base-branch}/{SprintID}` branch without user confirmation (safe — this is not main)
- Skip the summary presentation (the calling skill or user can read the logs)

#### Done 判定の事前ガード

Story を `status: done` に書き換える前に、以下を順に評価する:

1. `references/sprint-done-judgment.md` の Guard 1–6 を **全て** 評価する
2. fail したガードがあれば、Story を `status: needs_user_review` に書き、`docs/sprint-logs/{SprintID}/done-judgment.json` に各ガードの結果を記録する
3. fail ガードがある Story は **autopilot から done に遷移させない**。次の milestone で user 判断 (sprint demo + 明示承認) を待つ
4. `decisions.json` の `done_judgment` セクションに各 Story の 6 ガード結果を必ず記録する (autopilot 側がこのログを drift check で読む)

ガード fail だけで Sprint 全体を `partial` にする必要はない — `done` Story と `needs_user_review` Story が混在することは想定済み。Sprint の `status` は「全 Story が `done` または `needs_user_review`」で `done`、それ以外 (テスト fail / blocked) で `partial` とする。

## Failure Recovery

Autonomous execution cannot ask the user for help. The default behavior is **keep trying until fixed**. Only give up when further attempts cannot possibly succeed.

### Prohibited shortcuts

Auto mode runs without a human in the loop, so silently degrading verification means the user discovers the regression later. **All five rules in `references/test-discipline.md` apply identically under auto mode** — no exceptions for "the Sprint needs to complete". In addition:

- **Do not delete or weaken an acceptance criterion** to make the implementation match. AC are user-facing intent — only the user drops them.
- **Do not reclassify a GUI Story as non-GUI** to escape the Playwright requirement (see `gui-spec` Phase 1).

If a test cannot pass within these rules, escalate per `test-discipline.md` "Escalation". The temptation to bypass a rule is itself the signal to escalate.

### Test failures (mock tests, E2E tests, acceptance tests)

**Loop until fixed:**
1. Read the failure output carefully
2. Analyze the root cause (frontend bug, backend bug, integration mismatch, test data issue, timing issue)
3. Fix the issue
4. Re-run the failing tests
5. If still failing, go back to step 1 with a different approach

**When the fix is outside the current Sprint's scope:**

If the root cause is in code that belongs to a different Sprint (e.g., missing DB migration, incomplete API from a prior Sprint, infrastructure not yet set up):
1. Append a fix description to the Backlog of `docs/ROADMAP.json` via the "Append to backlog" filter (see SKILL.md "Writes"):
   ```bash
   jq --argjson item "$ITEM" '.backlog += [$item]' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
   ```
2. Insert a new Sprint (or add the fix Story to the next unfinished Sprint) in the execution order, **before** the current Sprint, using the "Add new Sprint" + "Insert into execution_order at index" filters from SKILL.md.
3. Mark the current Story as `pending` with a dependency note: `--arg s --arg st --arg dep '.sprints[$s].stories[$st].status = "pending" | .sprints[$s].stories[$st].depends_on = $dep'`
4. Mark the current Sprint as `partial` (`.sprints[$s].status = "partial"` filter) and return — autopilot will execute the fix Sprint next, then retry the current Sprint

This ensures scope-external problems are resolved autonomously rather than escalated to the user.

**Escalate to the user only when Claude Code genuinely cannot resolve the issue:**
- The fix requires information that is not available in the codebase AND cannot be derived (e.g., external API credentials, third-party service secrets, paid service account setup)
- The fix requires human judgment on a real-world constraint that has no representation in code, VISION, or DESIGN_PRINCIPLES (e.g., legal compliance question, business rule that was never documented)

When escalating:
- Log the full diagnosis to `docs/sprint-logs/{SprintID}/failures.json`: what was tried, why each attempt failed, and why Claude Code cannot resolve it
- Mark the Story as incomplete via in-place `jq` mutation:
  ```bash
  jq --arg s "$SPRINT" --arg st "$STORY" --arg r "$REASON" \
    '.sprints[$s].stories[$st].status = "blocked" | .sprints[$s].stories[$st].needs_human = $r' \
    docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
  ```
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
- Failure details logged to `docs/sprint-logs/{SprintID}/failures.json`
- The Sprint status stays `[IN PROGRESS]`, not `[DONE]`
- The calling skill (autopilot) checks if a fix Sprint was inserted — if so, execute it next, then retry the incomplete Stories

## Decision Logging

All autonomous decisions MUST be logged to `docs/sprint-logs/{SprintID}/decisions.json` in this format:

```markdown
# Sprint {SprintID} — Autonomous Decisions

## Planning Decisions
- **Story Sa3f9c2-3 split**: Split into Sa3f9c2-3 and Sa3f9c2-4 because the original had CRUD + search in one story. Guided by DESIGN_PRINCIPLES: "one story = one user-facing behavior".
- **GUI spec: login form entry point**: Auto-selected direct URL `/login` — standard pattern, no ambiguity.

## Implementation Decisions
- **Auth middleware approach**: Chose JWT over session cookies. Rationale: VISION.json specifies stateless API, DESIGN_PRINCIPLES prefers "existing library > custom".
- **Backlog added**: "Refactor legacy error handler" — found during Story Sa3f9c2-2 implementation.

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
