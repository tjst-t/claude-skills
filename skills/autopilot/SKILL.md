---
name: autopilot
description: Autonomous multi-sprint execution with PO role. Runs sprints continuously until milestone, guided by VISION.md and DESIGN_PRINCIPLES.md. Use when user says "autopilot", "自動実行", "まとめて実行", or wants hands-off sprint execution.
---

# Autopilot

Runs multiple Sprints autonomously, acting as both developer and product owner. Guided by `docs/VISION.md` and `docs/DESIGN_PRINCIPLES.md`, stops only at milestone boundaries for user review.

## Prerequisites

Before starting, verify these files exist:

| File | Required | Purpose |
|------|----------|---------|
| `docs/ROADMAP.md` | Yes | Sprint definitions and execution order |
| `docs/VISION.md` | Yes | Product purpose, target users, success criteria |
| `docs/DESIGN_PRINCIPLES.md` | Yes | Decision-making rules for autonomous execution |

If `VISION.md` or `DESIGN_PRINCIPLES.md` do not exist, **do not proceed**. Instead, help the user create them using `references/vision-template.md` and `references/principles-template.md`. These documents are essential — without them, autonomous decisions have no guiding criteria and the output will drift from the user's intent.

## Commands

| Command | Description |
|---|---|
| `autopilot start` | Begin autonomous multi-sprint execution |
| `autopilot status` | Show progress and recent decisions |
| `autopilot setup` | Create VISION.md and DESIGN_PRINCIPLES.md interactively |

## `autopilot setup`

Guide the user through creating `docs/VISION.md` and `docs/DESIGN_PRINCIPLES.md`:

1. Read the templates in `references/vision-template.md` and `references/principles-template.md`
2. Ask the user targeted questions to fill in each section (batch questions, don't ask one at a time)
3. Write the files
4. If a `docs/ROADMAP.md` exists, review it against the new VISION and flag any misalignment

## `autopilot start`

### Step 1: Pre-flight check

1. Verify prerequisites (ROADMAP, VISION, DESIGN_PRINCIPLES)
2. Read all three documents
3. Count remaining unfinished Sprints
4. Identify milestone boundaries (see Milestone Detection below)
5. Present a brief execution plan to the user:
   - "Will execute Sprints {list} autonomously, stopping at milestone: {milestone description}"
   - Ask for confirmation before starting

### Step 2: Sprint loop

For each Sprint until the next milestone boundary:

1. Invoke `sprint auto` from the sprint-runner skill
2. Read the decision log (`docs/sprint-logs/{SprintID}/decisions.md`)
3. **Drift check**: Review the decisions against VISION and DESIGN_PRINCIPLES. If any decision contradicts these documents, flag it but continue (it will be reviewed at the milestone demo)
4. Proceed to the next Sprint

### Step 3: Milestone demo

When a milestone boundary is reached:

1. Invoke `sprint demo` for the most recently completed Sprint (this shows the cumulative state)
2. Present a **milestone summary**:
   - Sprints completed in this autopilot run
   - Key decisions made (from all decision logs)
   - Any drift warnings flagged during the run
   - Backlog items added
   - Current state of the roadmap progress
3. Ask the user:
   - "Are there any decisions you want to revise?"
   - "Do you want to update VISION or DESIGN_PRINCIPLES based on what you see?"
   - "Continue to next milestone, or stop here?"
4. If the user wants to revise decisions: make the changes, then re-verify affected code if needed
5. If the user updates VISION/PRINCIPLES: re-read them before continuing
6. If continuing: return to Step 2 for the next batch of Sprints

## Milestone Detection

A milestone boundary is any of the following:

1. **Explicit milestone marker** in ROADMAP.md: A Sprint description or comment containing `[MILESTONE]` or `[マイルストーン]`
2. **Natural boundaries**: The last Sprint before a major dependency shift (e.g., Sprint N builds the API, Sprint N+1 builds the frontend that consumes it)
3. **Every 3 Sprints** as a fallback if no explicit milestones are defined — prevents unbounded execution
4. **End of roadmap**: All Sprints complete

When multiple rules apply, use the earliest boundary.

## `autopilot status`

Read the current state and present:
- Current Sprint being executed (or last completed)
- Sprints completed in this autopilot run
- Next milestone boundary
- Recent decisions from the latest `decisions.md`
- Any drift warnings

## Important Behaviors

- **VISION and PRINCIPLES are the authority**: Every autonomous decision must be justifiable by referencing one of these documents. If neither document addresses the question, default to the simplest approach and log why.
- **Never skip milestones**: Even if everything looks fine, always stop at milestone boundaries. The user's review is the alignment mechanism.
- **Drift logging, not drift blocking**: If a decision seems to conflict with VISION/PRINCIPLES, log the concern but don't stop execution. The milestone review handles corrections.
- **Preserve user agency**: The user can always interrupt autopilot. If the user sends any message during execution, pause and respond before continuing.
- **Incremental commits**: Each Sprint is committed and pushed independently. If autopilot is interrupted, all completed Sprints are preserved.
