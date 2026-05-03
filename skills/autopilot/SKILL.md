---
name: autopilot
description: Runs multiple Sprints autonomously as developer and product owner. Executes plan-run-verify-done cycles guided by VISION.json and DESIGN_PRINCIPLES.json, stopping at milestones for user review.
when_to_use: Use when user says "autopilot", "autopilot start/setup/status", "自動実行", "まとめて実行", or wants hands-off multi-sprint execution.
allowed-tools: Read Grep Glob
---

# Autopilot

Runs multiple Sprints autonomously, acting as both developer and product owner. Guided by `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json`, stops only at milestone boundaries for user review.

## Prerequisites

Before starting, verify these files exist:

| File | Required | Purpose |
|------|----------|---------|
| `docs/ROADMAP.json` | Yes | Sprint definitions and execution order |
| `docs/VISION.json` | Yes | Product purpose, target users, success criteria |
| `docs/DESIGN_PRINCIPLES.json` | Yes | Decision-making rules for autonomous execution |

If `VISION.json` or `DESIGN_PRINCIPLES.json` do not exist, **do not proceed**. Instead, help the user create them using `references/vision-template.md` and `references/principles-template.md`. These documents are essential — without them, autonomous decisions have no guiding criteria and the output will drift from the user's intent.

## Commands

| Command | Description |
|---|---|
| `autopilot start` | Begin autonomous multi-sprint execution |
| `autopilot status` | Show progress and recent decisions |
| `autopilot setup` | Create VISION.json and DESIGN_PRINCIPLES.json interactively |

## `autopilot setup`

Project setup for autopilot-driven development. Detects whether this is a new project or an existing sprint project and adapts accordingly.

### Detection

First, check what already exists:
- `CLAUDE.md` — project-init already run?
- `docs/ARCHITECTURE.md` — architecture documented?
- `docs/ROADMAP.json` — sprints defined? Any `[IN PROGRESS]` or `[DONE]` sprints?
- `docs/VISION.json` — vision exists?
- `docs/DESIGN_PRINCIPLES.json` — principles exist?

Based on this, follow the **new project flow** or the **existing project flow**.

---

### New project flow

When `CLAUDE.md` and `docs/ROADMAP.json` do not exist (or ROADMAP has no defined Sprints).

#### Phase 1: VISION and DESIGN_PRINCIPLES

1. Check if `docs/VISION.json` or `docs/DESIGN_PRINCIPLES.json` already exist. If so, read them and ask the user whether to update or overwrite.
2. Read the templates in `references/vision-template.md` and `references/principles-template.md`
3. Ask the user targeted questions to fill in each section (batch questions, don't ask one at a time)
4. Write `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json`

#### Phase 2: Project initialization

5. Invoke `/project-init` to generate `CLAUDE.md`, `docs/ARCHITECTURE.md`, and `Makefile`. Since VISION.json now exists, project-init can reference it for better ARCHITECTURE.md generation.

#### Phase 3: Roadmap generation

6. Invoke `/sprint roadmap` to generate `docs/ROADMAP.json` from VISION + ARCHITECTURE.
   - The generated roadmap includes `[MILESTONE]` markers at natural review points.

---

### Existing project flow

When `docs/ROADMAP.json` already exists with defined Sprints (typical for projects already using sprint).

#### Phase 1: VISION and DESIGN_PRINCIPLES

1. Read the existing codebase, `CLAUDE.md`, `docs/ARCHITECTURE.md`, and `docs/ROADMAP.json` to understand the project context
2. Read the templates in `references/vision-template.md` and `references/principles-template.md`
3. Ask the user targeted questions, but **pre-fill answers where possible** from existing documentation:
   - Tech stack → from CLAUDE.md / ARCHITECTURE.md
   - Project purpose → from ROADMAP.json sprint descriptions and README
   - Existing patterns → from codebase conventions already established
4. Write `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json`

#### Phase 2: Project initialization → Skip

Existing project already has `CLAUDE.md` and `docs/ARCHITECTURE.md`. Skip this phase entirely.

#### Phase 3: Roadmap generation → Skip

Existing project already has a populated `docs/ROADMAP.json`. Do NOT regenerate it.

#### Phase 4: Alignment check (existing projects only)

7. **VISION ↔ ROADMAP alignment**: Compare the newly created VISION with the existing ROADMAP.
   - Flag any Stories or Sprints that fall outside VISION's scope
   - Flag any VISION goals that have no corresponding Sprint
   - Present findings to the user and ask if adjustments are needed

8. **Milestone injection**: Check if `docs/ROADMAP.json` has `[MILESTONE]` markers.
   - If no milestones exist, propose milestone placements based on the Milestone Detection rules (dependency boundaries, every 3 sprints) and apply them
   - Present proposed milestones to the user for confirmation

9. **ARCHITECTURE.md refresh**: If ARCHITECTURE.md was generated before VISION existed, offer to regenerate it with VISION context for improved accuracy. Ask the user — do not auto-overwrite.

---

### Result

After `autopilot setup` completes, the project is ready for `/autopilot start`. All prerequisites are satisfied:
- `docs/VISION.json` ✓
- `docs/DESIGN_PRINCIPLES.json` ✓
- `CLAUDE.md` ✓
- `docs/ARCHITECTURE.md` ✓
- `docs/ROADMAP.json` ✓ (with Sprints, Stories, milestones)

## `autopilot start`

### Step 1: Pre-flight check

1. Verify prerequisites (ROADMAP, VISION, DESIGN_PRINCIPLES)
2. **Branch lock**: Determine the current branch (`git branch --show-current`). Check if a lock file exists at `.claude/autopilot-{branch-sanitized}.lock`. If it does, read the lock file — it contains the PID and start time. Warn the user that another autopilot session may be active on this branch and ask whether to proceed (the previous session may have crashed). If no lock exists, create one with the current PID and timestamp.
3. **Orphan worktree cleanup**: Run `git worktree list` and identify any worktrees matching the pattern `autopilot/{current-branch-sanitized}/*`. For each:
   - If the worktree's branch has been merged into the current branch → remove it (`git worktree remove`, `git branch -d`)
   - If unmerged but no active Claude Code session is using it (check PID files or process list) → warn the user and offer to remove or keep
   - Log cleanup actions to console
4. Read all three documents
5. Count remaining unfinished Sprints
6. Identify milestone boundaries (see Milestone Detection below)
7. Present a brief execution plan to the user:
   - "Will execute Sprints {list} autonomously, stopping at milestone: {milestone description}"
   - Ask for confirmation before starting

### Step 1.5: Prototype review (GUI Stories only)

If the upcoming Sprints (up to the next milestone) contain GUI Stories:

1. Collect all GUI Stories from the Sprints that will execute before the next milestone
2. Invoke `sprint prototype` — this generates static HTML mockups in `prototype/` covering all collected GUI Stories
3. **Pause for user review** — the user opens the HTML files and provides feedback
4. Iterate until the user approves the prototype
5. Commit the approved prototype

If no GUI Stories exist in the upcoming batch, skip this step entirely.

> This is an interactive phase — autopilot pauses here. The approved prototype prevents costly UI rework during the sprint loop.

### Step 2: Sprint loop

Each Sprint is executed as an **independent sub-agent** to manage context window usage. The main autopilot conversation stays lightweight and delegates heavy work.

For each Sprint until the next milestone boundary:

1. Launch an Agent to invoke `sprint auto` via the Skill tool. The agent prompt must include:
   - The Sprint ID to execute
   - The full contents of `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json`
   - Instruction to return: completion status, decision summary, and any warnings
2. When the agent completes, read the decision log (`docs/sprint-logs/{SprintID}/decisions.json`)
3. **Drift check**: Review the decisions against VISION and DESIGN_PRINCIPLES. If any decision contradicts these documents, flag it but continue (it will be reviewed at the milestone demo)
4. **Failure handling**: If `sprint auto` returns `partial` or `needs_human`:
   - `partial` with fix Sprint inserted → execute the fix Sprint next (it was added to the roadmap by sprint auto), then retry the incomplete Stories from the original Sprint
   - `partial` without fix Sprint → continue to next Sprint, log incomplete Stories
   - `needs_human` → stop and trigger milestone demo early so the user can address the blocker
5. Merge the Sprint's `autopilot/{base-branch}/{SprintID}` branch into the working branch
6. Proceed to the next Sprint

### Step 3: Milestone demo and refine

When a milestone boundary is reached:

1. Invoke `sprint demo` for the most recently completed Sprint (this shows the cumulative state)
2. Present a **milestone summary**:
   - Sprints completed in this autopilot run
   - Key decisions made (from all decision logs)
   - Any drift warnings flagged during the run
   - Backlog items added
   - Current state of the roadmap progress
3. **Refine phase**: Invoke `sprint refine`. The user interacts with the running application and requests adjustments. This is the user's opportunity to fine-tune UI, UX, spacing, colors, wording, and other visual/interactive details that only human eyes can judge. The refine loop continues until the user is satisfied.
4. After refine, ask the user:
   - "Are there any decisions you want to revise?"
   - "Do you want to update VISION or DESIGN_PRINCIPLES based on what you see?"
   - "Continue to next milestone, or stop here?"
5. If the user wants to revise decisions: make the changes, then re-verify affected code if needed
6. If the user updates VISION/PRINCIPLES: re-read them before continuing
7. If continuing: return to Step 2 for the next batch of Sprints

### Step 4: Cleanup

When autopilot finishes (all milestones reached, user stops, or error):

1. **Release branch lock**: Delete `.claude/autopilot-{branch-sanitized}.lock`
2. **Final worktree cleanup**: Run `git worktree list` and remove any remaining worktrees from this autopilot session that were already merged

## Milestone Detection

A milestone boundary is any of the following (checked in order, use the earliest match):

1. **Explicit milestone marker** in ROADMAP.json: A Sprint with `"milestone": true`
2. **Dependency boundary**: Read the `dependencies` object in ROADMAP.json. If the next Sprint has no dependency on the current Sprint (i.e., a new independent track begins), treat the current Sprint as a milestone. This is determined by the explicit dependency declarations, not by inference.
3. **Every 3 Sprints** as a fallback if no explicit milestones or dependency boundaries are found — prevents unbounded execution
4. **End of roadmap**: All Sprints complete

## `autopilot status`

Show the state of the most recent autopilot run. This command reads logs — it does not require an active autopilot session.

1. Read `docs/ROADMAP.json` to determine overall progress
2. Find the most recent `docs/sprint-logs/*/decisions.json` files
3. **Check for active locks**: List any `.claude/autopilot-*.lock` files. If found, show which branches have active (or stale) autopilot sessions.
4. **List worktrees**: Run `git worktree list` and show any worktrees matching `autopilot/*`. Flag orphaned worktrees (no active session) for cleanup.
5. Present:
   - Last completed Sprint and its status
   - Total Sprints completed in the most recent autopilot run
   - Active autopilot sessions (from lock files) and their branches
   - Remaining worktrees and their merge status
   - Next milestone boundary (based on current roadmap state)
   - Key decisions from the latest `decisions.json`
   - Any drift warnings or failure logs

## Important Behaviors

- **VISION and PRINCIPLES are the authority**: Every autonomous decision must be justifiable by referencing one of these documents. If neither document addresses the question, default to the simplest approach and log why.
- **Never skip milestones**: Even if everything looks fine, always stop at milestone boundaries. The user's review is the alignment mechanism.
- **Drift logging, not drift blocking**: If a decision seems to conflict with VISION/PRINCIPLES, log the concern but don't stop execution. The milestone review handles corrections.
- **Preserve user agency**: The user can always interrupt autopilot. If the user sends any message during execution, pause and respond before continuing.
- **Incremental commits**: Each Sprint is committed and pushed on its own `autopilot/{base-branch}/{SprintID}` branch. If autopilot is interrupted, all completed Sprints are preserved and can be merged independently.
- **Context management**: Each Sprint runs in a dedicated sub-agent to prevent context window exhaustion. The main autopilot conversation only tracks Sprint-level status, decision summaries, and drift flags — it does not accumulate implementation details.
- **Branch-level locking**: Only one autopilot session per branch. Multiple branches can run autopilot concurrently — they are isolated by branch-namespaced worktree paths and branch names (`autopilot/{base-branch}/{SprintID}`).
- **Always release the lock**: On normal completion, interruption, or error, delete the lock file. If the lock is stale (process no longer running), allow override.

## Reference Files

- `references/getting-started.md` — New project setup guide (with specs / without specs / existing project)
- `references/VISION_SCHEMA.json` — VISION.json schema and example
- `references/DESIGN_PRINCIPLES_SCHEMA.json` — DESIGN_PRINCIPLES.json schema and example
- `references/vision-template.md` — VISION setup guidelines (question prompts)
- `references/principles-template.md` — DESIGN_PRINCIPLES setup guidelines (question prompts)
