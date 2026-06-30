---
name: autopilot
description: Runs multiple Sprints autonomously as developer and product owner. Executes plan-run-verify-done cycles guided by VISION.json and DESIGN_PRINCIPLES.json, stopping at milestones for user review.
when_to_use: Use when user says "autopilot", "autopilot start/setup/status", "自動実行", "まとめて実行", or wants hands-off multi-sprint execution.
allowed-tools: Read Grep Glob
---

# Autopilot

Runs multiple Sprints autonomously, acting as both developer and product owner. Guided by `docs/VISION.json`, `docs/DESIGN_PRINCIPLES.json`, and (when present) `docs/DESIGN/`. Stops only at milestone boundaries for user review.

## Prerequisites

| File | Required | Purpose |
|------|----------|---------|
| `docs/ROADMAP.json` | Yes | Sprint definitions and execution order |
| `docs/VISION.json` | Yes | Product purpose, target users, success criteria |
| `docs/DESIGN_PRINCIPLES.json` | Yes | Decision-making rules for autonomous execution |
| `docs/DESIGN/` | Optional | Load-bearing architectural decisions (managed by `design` skill). When present, ADRs are treated as binding constraints on autonomous decisions. |

If `VISION.json` or `DESIGN_PRINCIPLES.json` do not exist, **do not proceed**. Suggest one of:

1. **Complex / non-trivial systems (recommended)**: invoke the `design` skill via `design start`. It produces VISION, DESIGN_PRINCIPLES, AND `docs/DESIGN/` through guided dialogue.
2. **Simple projects**: help the user create VISION and PRINCIPLES inline using `references/vision-template.md` and `references/principles-template.md`.

For complex systems with many cross-cutting decisions, the inline templates are not enough — use `design` instead.

## Commands

| Command | Description | Detail |
|---|---|---|
| `autopilot setup` | Create VISION, DESIGN_PRINCIPLES, and required artifacts | See `references/autopilot-setup.md` |
| `autopilot start` | Begin autonomous multi-sprint execution | See `references/autopilot-start.md` |
| `autopilot status` | Show progress and recent decisions | See below |
| `autopilot help` | Show command list and usage guide | See `references/autopilot-help.md` |

When a command is invoked, read the corresponding reference file before taking any action.

## Milestone Detection

A milestone boundary is any of the following (checked in order, use the earliest match):

1. **Explicit milestone marker** in ROADMAP.json: a Sprint with `"milestone": true`
2. **Dependency boundary**: read the `dependencies` object in ROADMAP.json. If the next Sprint has no dependency on the current Sprint (a new independent track begins), treat the current Sprint as a milestone. Determined by explicit dependency declarations, not by inference.
3. **Every 3 Sprints** as a fallback if no explicit milestones or dependency boundaries are found — prevents unbounded execution
4. **End of roadmap**: all Sprints complete

## `autopilot status`

Show the state of the most recent autopilot run. Read-only — no active session required.

1. Read `docs/ROADMAP.json` for overall progress
2. Read the most recent `docs/sprint-logs/*/decisions.json` files
3. Inspect `.claude/autopilot-*.lock` files and `git worktree list | grep autopilot/` per `references/autopilot-operations.md`
4. Present: last completed Sprint, total Sprints in the run, active sessions, remaining worktrees + merge status, next milestone, key decisions, any drift warnings or failure logs

## Important Behaviors

- **VISION, PRINCIPLES, and DESIGN/ are the authority**: Every autonomous decision must be justifiable by referencing one of these documents. ADRs in `docs/DESIGN/adr/` are binding constraints — autonomous decisions that contradict an accepted ADR must escalate to the user, not proceed. If none address the question, default to the simplest approach and log why.
- **6-Guard Done Judgment**: Before marking any Story as `done`, autopilot must apply all 6 guards defined in `references/autopilot-done-judgment.md`. Any failed guard moves the Story to `needs_user_review`, not `done`. This applies to both sprint-internal verification and the post-merge milestone check.
- **priority_rule 9 exception scope is strict**: The exception clause (障害シナリオへの限定) requires explicit障害シナリオ identifiers (`kill-9` / `停電` / `Shamir-unseal` / `ネットワーク遮断` / `disk-full` / `OOM` / `プロセスクラッシュ`) in the `review_reason`. autopilot rejects exception claims without these markers and falls back to the normal real-VM smoke requirement.
- **Mock-mode does not satisfy real-VM smoke**: Tests that use `MOCK=true`, `--fake-*` flags, `DRY_RUN=1`, in-process FakeCore / InMemoryStore, or `*_fake_*: true` Ansible defaults do not count toward priority_rule 9 "dev VM 実機 smoke" requirement. A separate real-mode smoke is required.
- **Never skip milestones**: Always stop at milestone boundaries. The user's review is the alignment mechanism.
- **Drift logging, not drift blocking**: Log decisions that seem to conflict with VISION/PRINCIPLES; surface them at milestone review. Doc-staleness and VISION-drift health checks (operations.md) are advisory at milestone, never blocking.
- **Preserve user agency**: The user can always interrupt autopilot. Pause and respond before continuing.
- **Context management**: Each Sprint runs in a dedicated sub-agent to prevent context exhaustion. The main autopilot conversation tracks only Sprint-level status, decision summaries, and drift flags.
- **Incremental commits + branch lifecycle**: Each Sprint on `autopilot/{base-branch}/{SprintID}`; merged branches are deleted (local + remote). Only unmerged branches survive. Per-branch locking lets multiple branches run concurrently. Full procedure: `references/autopilot-operations.md`.

## Reference Files

- `references/autopilot-setup.md` — `autopilot setup` command flow (new project / existing project, DESIGN/ detection, Backfill handoff)
- `references/autopilot-start.md` — `autopilot start` command flow (pre-flight, prototype review, sprint loop, milestone demo, cleanup)
- `references/autopilot-done-judgment.md` — **canonical 6-guard done judgment** (Guard 1–6) applied before any Story can be marked `done`
- `references/autopilot-operations.md` — branch locking, worktree cleanup, sprint branch deletion, milestone health checks (doc staleness, VISION drift)
- `references/getting-started.md` — New project setup guide (with specs / without specs / existing project)
- `references/VISION_SCHEMA.json` — VISION.json schema and example
- `references/DESIGN_PRINCIPLES_SCHEMA.json` — DESIGN_PRINCIPLES.json schema and example
- `references/vision-template.md` — VISION setup guidelines (question prompts)
- `references/principles-template.md` — DESIGN_PRINCIPLES setup guidelines (question prompts)
- `references/autopilot-help.md` — help (command list and usage guide)
