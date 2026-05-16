# autopilot start

Begin autonomous multi-sprint execution, stopping at milestone boundaries for user review.

## Pre-flight check

1. Verify prerequisites (ROADMAP, VISION, DESIGN_PRINCIPLES).
2. **Acquire branch lock** and **clean up orphan worktrees** per `references/autopilot-operations.md`.
3. Read all three documents, count remaining unfinished Sprints, identify the next milestone boundary (see Milestone Detection in SKILL.md).
4. Present a brief execution plan and ask for confirmation:
   > "Will execute Sprints {list} autonomously, stopping at milestone: {milestone description}"

## Prototype review (GUI Stories only)

If the upcoming Sprints (up to the next milestone) contain GUI Stories:

1. Collect all GUI Stories from the Sprints that will execute before the next milestone.
2. Invoke `sprint prototype` — this generates static HTML mockups in `prototype/` covering all collected GUI Stories.
3. **Pause for user review** — the user opens the HTML files and provides feedback.
4. Iterate until the user approves the prototype.
5. Commit the approved prototype.

If no GUI Stories exist in the upcoming batch, skip this step entirely.

> This is an interactive phase — autopilot pauses here. The approved prototype prevents costly UI rework during the sprint loop.

## Sprint loop

Each Sprint is executed as an **independent sub-agent** to manage context window usage. The main autopilot conversation stays lightweight and delegates heavy work.

For each Sprint until the next milestone boundary:

1. Launch an Agent to invoke `sprint auto` via the Skill tool. The agent prompt must include:
   - The Sprint ID to execute
   - The full contents of `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json`
   - Instruction to return: completion status, decision summary, and any warnings
2. When the agent completes, read the decision log (`docs/sprint-logs/{SprintID}/decisions.json`).
3. **Drift check**: Review the decisions against VISION and DESIGN_PRINCIPLES. If any decision contradicts these documents, flag it but continue (it will be reviewed at the milestone demo).
4. **Failure handling**: If `sprint auto` returns `partial` or `needs_human`:
   - `partial` with fix Sprint inserted → execute the fix Sprint next (it was added to the roadmap by sprint auto), then retry the incomplete Stories from the original Sprint
   - `partial` without fix Sprint → continue to next Sprint, log incomplete Stories
   - `needs_human` → stop and trigger milestone demo early so the user can address the blocker
5. Merge the Sprint's `autopilot/{base-branch}/{SprintID}` branch into the working branch.
6. **Delete the merged Sprint branch** (local + remote) per `references/autopilot-operations.md` — the merge commit is the recovery point.
7. Proceed to the next Sprint.

## Milestone demo and refine

When a milestone boundary is reached:

1. **Run milestone health checks** per `references/autopilot-operations.md` "Milestone health checks":
   - **Documentation staleness**: compare ARCHITECTURE.md / CLAUDE.md against current codebase, flag drift
   - **VISION drift**: scan recent `decisions.json` files for decisions without VISION/PRINCIPLES rationale, warn if >30%
   These are advisory — they surface to the user at the milestone summary but never block.
2. Invoke `sprint demo` for the most recently completed Sprint (this shows the cumulative state).
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
6. If the user wants to revise decisions: make the changes, then re-verify affected code if needed.
7. If the user updates VISION/PRINCIPLES or ARCHITECTURE.md/CLAUDE.md: re-read them before continuing.
8. If continuing: return to Sprint loop for the next batch of Sprints.

## Cleanup

When autopilot finishes (all milestones reached, user stops, or error), run the "Final cleanup" procedure in `references/autopilot-operations.md`: release the branch lock, sweep merged worktrees, delete merged Sprint branches (local + remote), and report any unmerged branches that survived.
