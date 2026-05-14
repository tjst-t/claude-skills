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
| `docs/DESIGN/` | Optional | Load-bearing architectural decisions (managed by `design` skill). When present, ADRs are treated as constraints on autonomous decisions. |

If `VISION.json` or `DESIGN_PRINCIPLES.json` do not exist, **do not proceed**. Instead, suggest one of:

1. **For complex / non-trivial systems (recommended)**: invoke the `design` skill via `design start`. It produces VISION, DESIGN_PRINCIPLES, AND a `docs/DESIGN/` set (domain model, system architecture, ADRs, non-functional requirements) through guided dialogue. Then return to `autopilot setup`.
2. **For simple projects**: help the user create VISION and PRINCIPLES inline using `references/vision-template.md` and `references/principles-template.md`.

These documents are essential — without them, autonomous decisions have no guiding criteria and the output will drift from the user's intent. For systems with many cross-cutting design decisions, the lightweight inline templates are not enough; use the `design` skill instead.

## Commands

| Command | Description |
|---|---|
| `autopilot start` | Begin autonomous multi-sprint execution |
| `autopilot status` | Show progress and recent decisions |
| `autopilot setup` | Create VISION.json and DESIGN_PRINCIPLES.json interactively |
| `autopilot help` | Show command list and usage guide |

## `autopilot setup`

Project setup for autopilot-driven development. Detects whether this is a new project or an existing sprint project and adapts accordingly.

### Detection

First, check what already exists:
- `CLAUDE.md` — project-init already run?
- `docs/ARCHITECTURE.md` — architecture documented?
- `docs/ROADMAP.json` — sprints defined? Any `[IN PROGRESS]` or `[DONE]` sprints?
- `docs/VISION.json` — vision exists?
- `docs/DESIGN_PRINCIPLES.json` — principles exist?
- `docs/DESIGN/` — load-bearing design artifacts (managed by `design` skill) exist?

Based on this, follow the **new project flow** or the **existing project flow**.

> **If `docs/DESIGN/` is present**:
>
> - **Both VISION and PRINCIPLES present**: Read them and skip Phase 1's question dialogue entirely — they are already authoritative.
> - **VISION or PRINCIPLES missing** (one or both): The `design` skill handles this via its **Backfill mode** — it derives the missing files from DESIGN/ content (ADRs encode tradeoffs that map to priority_rules; system.json + ADRs supply most VISION fields). Invoke `design start` and let it auto-detect Backfill mode. Do NOT proceed with `autopilot setup`'s own question dialogue, and do NOT block the user — `design start` will produce the missing files and return.

---

### New project flow

When `CLAUDE.md` and `docs/ROADMAP.json` do not exist (or ROADMAP has no defined Sprints).

#### Phase 1: VISION and DESIGN_PRINCIPLES

**If `docs/DESIGN/` exists and VISION + PRINCIPLES exist** (the `design` skill was already run end-to-end):
- Read `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json` — they are authoritative.
- Skip the question dialogue. Do NOT ask the user to re-confirm fields.
- Continue to Phase 2.

**If `docs/DESIGN/` exists but VISION OR PRINCIPLES is missing**:
- Invoke `design start` via the Skill tool. It auto-detects Backfill mode and derives the missing files from DESIGN/. It will surface only the non-derivable fields to the user.
- After `design start` returns, re-check VISION and PRINCIPLES exist, then continue to Phase 2.

**If `docs/DESIGN/` does not exist**:
- **Recommend the `design` skill first** for any non-trivial system: "This project looks like it would benefit from `design start` to lock load-bearing decisions before implementation. Run `design start`, then come back to `autopilot setup`. Or, if this is a small project, I can ask you a few questions inline now."
- If the user opts for inline (small project) or proceeds without `design`:
  1. Check if `docs/VISION.json` or `docs/DESIGN_PRINCIPLES.json` already exist. If so, read them and ask the user whether to update or overwrite.
  2. Read the templates in `references/vision-template.md` and `references/principles-template.md`
  3. Ask the user targeted questions to fill in each section (batch questions, don't ask one at a time)
  4. Write `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json`

#### Phase 2: Project initialization

5. Invoke `/project-init` to generate `CLAUDE.md`, `docs/ARCHITECTURE.md`, and `Makefile`. Since VISION.json now exists, project-init can reference it for better ARCHITECTURE.md generation. If `docs/DESIGN/system.json` exists, project-init should also reference it (it describes the *intended* architecture, while ARCHITECTURE.md captures what the code currently looks like).

#### Phase 3: Roadmap generation

6. Invoke `/sprint roadmap` to generate `docs/ROADMAP.json` from VISION + ARCHITECTURE + (if present) DESIGN/.
   - The generated roadmap includes `[MILESTONE]` markers at natural review points.
   - If `docs/DESIGN/` exists, the roadmap generation reads `system.json` and ADRs as additional planning input. Stories are aligned to system components, and ADRs constrain implementation choices.

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
- `docs/DESIGN/` ✓ (optional — recommended for complex systems; populated by the `design` skill)
- `CLAUDE.md` ✓
- `docs/ARCHITECTURE.md` ✓
- `docs/ROADMAP.json` ✓ (with Sprints, Stories, milestones)

## `autopilot start`

### Step 1: Pre-flight check

1. Verify prerequisites (ROADMAP, VISION, DESIGN_PRINCIPLES)
2. **Acquire branch lock** and **clean up orphan worktrees** per `references/autopilot-operations.md`
3. Read all three documents, count remaining unfinished Sprints, identify the next milestone boundary (see Milestone Detection below)
4. Present a brief execution plan and ask for confirmation:
   > "Will execute Sprints {list} autonomously, stopping at milestone: {milestone description}"

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
6. **Delete the merged Sprint branch** (local + remote) per `references/autopilot-operations.md` — the merge commit is the recovery point
7. Proceed to the next Sprint

### Step 3: Milestone demo and refine

When a milestone boundary is reached:

1. **Run milestone health checks** per `references/autopilot-operations.md` "Milestone health checks":
   - **Documentation staleness**: compare ARCHITECTURE.md / CLAUDE.md against current codebase, flag drift
   - **VISION drift**: scan recent `decisions.json` files for decisions without VISION/PRINCIPLES rationale, warn if >30%
   These are advisory — they surface to the user at the milestone summary but never block.
2. Invoke `sprint demo` for the most recently completed Sprint (this shows the cumulative state)
3. Present a **milestone summary**:
   - Sprints completed in this autopilot run
   - Key decisions made (from all decision logs)
   - Any drift warnings flagged during the run (including doc-staleness and VISION-drift from health checks)
   - Backlog items added
   - Current state of the roadmap progress
4. **Refine phase**: Invoke `sprint refine`. The user interacts with the running application and requests adjustments. This is the user's opportunity to fine-tune UI, UX, spacing, colors, wording, and other visual/interactive details that only human eyes can judge. The refine loop continues until the user is satisfied.
5. After refine, ask the user:
   - "Are there any decisions you want to revise?"
   - "Do you want to update VISION or DESIGN_PRINCIPLES based on what you see?" (especially if VISION drift was flagged in step 1)
   - "Do you want to update ARCHITECTURE.md / CLAUDE.md?" (especially if doc staleness was flagged in step 1)
   - "Continue to next milestone, or stop here?"
6. If the user wants to revise decisions: make the changes, then re-verify affected code if needed
7. If the user updates VISION/PRINCIPLES or ARCHITECTURE.md/CLAUDE.md: re-read them before continuing
8. If continuing: return to Step 2 for the next batch of Sprints

### Step 4: Cleanup

When autopilot finishes (all milestones reached, user stops, or error), run the "Final cleanup" procedure in `references/autopilot-operations.md`: release the branch lock, sweep merged worktrees, delete merged Sprint branches (local + remote), and report any unmerged branches that survived.

## Milestone Detection

A milestone boundary is any of the following (checked in order, use the earliest match):

1. **Explicit milestone marker** in ROADMAP.json: A Sprint with `"milestone": true`
2. **Dependency boundary**: Read the `dependencies` object in ROADMAP.json. If the next Sprint has no dependency on the current Sprint (i.e., a new independent track begins), treat the current Sprint as a milestone. This is determined by the explicit dependency declarations, not by inference.
3. **Every 3 Sprints** as a fallback if no explicit milestones or dependency boundaries are found — prevents unbounded execution
4. **End of roadmap**: All Sprints complete

## `autopilot status`

Show the state of the most recent autopilot run. Read-only — no active session required.

1. Read `docs/ROADMAP.json` for overall progress
2. Read the most recent `docs/sprint-logs/*/decisions.json` files
3. Inspect `.claude/autopilot-*.lock` files and `git worktree list | grep autopilot/` per `references/autopilot-operations.md`
4. Present: last completed Sprint, total Sprints in the run, active sessions, remaining worktrees + merge status, next milestone, key decisions, any drift warnings or failure logs

## Important Behaviors

- **VISION, PRINCIPLES, and DESIGN/ are the authority**: Every autonomous decision must be justifiable by referencing one of these documents. ADRs in `docs/DESIGN/adr/` are binding constraints — autonomous decisions that contradict an accepted ADR must escalate to the user, not proceed. If none address the question, default to the simplest approach and log why.
- **Never skip milestones**: Always stop at milestone boundaries. The user's review is the alignment mechanism.
- **Drift logging, not drift blocking**: Log decisions that seem to conflict with VISION/PRINCIPLES; surface them at milestone review. Doc-staleness and VISION-drift health checks (operations.md) are advisory at milestone, never blocking.
- **Preserve user agency**: The user can always interrupt autopilot. Pause and respond before continuing.
- **Context management**: Each Sprint runs in a dedicated sub-agent to prevent context exhaustion. The main autopilot conversation tracks only Sprint-level status, decision summaries, and drift flags.
- **Incremental commits + branch lifecycle**: Each Sprint on `autopilot/{base-branch}/{SprintID}`; merged branches are deleted (local + remote). Only unmerged branches survive. Per-branch locking lets multiple branches run concurrently. Full procedure: `references/autopilot-operations.md`.

## Reference Files

- `references/getting-started.md` — New project setup guide (with specs / without specs / existing project)
- `references/autopilot-operations.md` — branch locking, worktree cleanup, sprint branch deletion, milestone health checks (doc staleness, VISION drift)
- `references/VISION_SCHEMA.json` — VISION.json schema and example
- `references/DESIGN_PRINCIPLES_SCHEMA.json` — DESIGN_PRINCIPLES.json schema and example
- `references/vision-template.md` — VISION setup guidelines (question prompts)
- `references/principles-template.md` — DESIGN_PRINCIPLES setup guidelines (question prompts)
- `references/autopilot-help.md` — help (command list and usage guide)
