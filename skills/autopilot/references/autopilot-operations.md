# Autopilot Operations

Operational details for autopilot: branch locking, worktree management, milestone health checks. The SKILL.md focuses on intent and flow; this file is the procedural backstop.

## Branch locking

Autopilot is **per-branch**: one active session per branch, multiple branches can run concurrently (isolated by branch-namespaced worktree paths and `autopilot/{base-branch}/{SprintID}` branch names).

**Acquire lock (Step 1 of `autopilot start`)**:
1. Determine current branch: `git branch --show-current`
2. Sanitize: replace `/` → `-` (e.g., `feature/auth` → `feature-auth`)
3. Check for `.claude/autopilot-{branch-sanitized}.lock`. If it exists, read the PID and start time. Warn the user that another session may be active; offer to proceed (if the previous session crashed) or abort.
4. If no lock or user approves: write the lock file with current PID and timestamp.

**Release lock (Step 4 of `autopilot start` and on any exit path)**: delete `.claude/autopilot-{branch-sanitized}.lock`. Stale locks (PID no longer running) can be overridden by the user.

## Orphan worktree cleanup

Run at the start of every autopilot session AND on exit.

**Identify candidates**: `git worktree list`, filter to paths matching `autopilot/{current-branch-sanitized}/*`. Do not touch worktrees from other branches' sessions.

**For each candidate**:
- If the worktree's branch has been merged into the current branch → remove it (`git worktree remove`, `git branch -d`)
- If unmerged but no active session is using it (check PID files or process list) → warn the user, offer to remove or keep
- Log cleanup actions to console

## Sprint branch deletion (post-merge)

After Step 2 of `autopilot start` successfully merges a Sprint's `autopilot/{base-branch}/{SprintID}` branch into the working branch, **delete the merged branch** (local + remote) — the merge commit is the recovery point; the branch is no longer load-bearing.

- Local: `git branch -d autopilot/{base-branch}/{SprintID}` (lowercase `-d`, NOT `-D`; git refuses to delete unmerged branches, which is the safety net)
- Remote: `git push origin --delete autopilot/{base-branch}/{SprintID}` (skip silently if the branch was never pushed or is already gone)

If `-d` refuses because git considers the branch unmerged (fast-forward edge cases), verify via `git log --oneline {working-branch} | grep {SprintID}` or `git merge-base --is-ancestor`. Only if confirmed merged, proceed; otherwise leave the branch and log a warning.

## Final cleanup (Step 4 of `autopilot start`)

On normal completion, interruption, or error:

1. **Release the branch lock**: delete `.claude/autopilot-{branch-sanitized}.lock`
2. **Final worktree cleanup**: as above, remove merged worktrees from this session
3. **Sweep merged Sprint branches**: list `autopilot/{base-branch-sanitized}/*` locally (`git branch --list`) and remotely (`git branch -r --list`). For each, attempt `git branch -d` and `git push origin --delete`. Anything still present is genuinely unmerged work that needs the user's attention — report the kept list.

## Milestone health checks

Run at every milestone boundary, immediately before invoking `sprint demo`. These are advisory — they warn the user but never block the milestone review.

### Documentation staleness check

ARCHITECTURE.md and CLAUDE.md guide every future sub-agent invocation; if they drift from reality, sub-agents reason from stale truth.

- **ARCHITECTURE.md**: launch a sub-agent to compare the documented directory structure / component list / data flow against the current codebase. Flag any of: (a) directories mentioned in ARCHITECTURE that no longer exist, (b) major top-level directories that exist but aren't mentioned, (c) components described as present but missing from the code, (d) data flows described that no longer match the implementation.
- **CLAUDE.md**: scan for tooling commands (`make ...`, `npm run ...`) and verify they still exist in `Makefile` / `package.json`. Flag any commands mentioned that no longer resolve.

If either has flagged issues, surface a short summary at the milestone review:
> ⚠️ Documentation drift detected: ARCHITECTURE.md mentions `services/billing/` which no longer exists; `make seed-test-data` mentioned in CLAUDE.md is not in the Makefile. Update before continuing?

The user decides whether to fix now or defer.

### VISION drift check

VISION and DESIGN_PRINCIPLES are the authority for autonomous decisions. If recent decisions cannot be justified by either document, that's a signal the documents are incomplete — not that the decisions are wrong.

- Read all `docs/sprint-logs/*/decisions.json` files for Sprints completed since the last milestone.
- Count decisions where `reference` is empty, says "no applicable section", or references neither VISION nor DESIGN_PRINCIPLES.
- If more than **30%** of decisions in this batch fall into that category, surface a warning at the milestone review:

> ⚠️ 8 of 23 autonomous decisions in this batch lacked a VISION/PRINCIPLES reference. Examples: [list 2-3 with their titles]. Consider whether VISION or DESIGN_PRINCIPLES needs expansion to cover these decision areas.

Threshold is a heuristic, not a hard rule. The list of ungrounded decisions is what the user actually reads — the percentage just decides whether to surface it. Do not block the milestone on this check.
