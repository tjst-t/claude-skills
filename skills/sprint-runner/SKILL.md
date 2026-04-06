---
name: sprint-runner
description: Agile Sprint lifecycle management for software projects. Use this skill whenever the user mentions sprint commands like "sprint plan", "sprint run", "sprint verify", "sprint done", "sprint demo", "sprint init", or references sprint/story/task workflows, roadmap management, or agile-style development cycles. Also trigger when the user says things like "次のスプリント", "スプリント開始", "実装完了", "レビュー完了", "デモ", or asks to update a roadmap. This skill manages the full sprint lifecycle from planning through completion.
---

# Sprint Runner

Manages the Agile Sprint lifecycle: plan → run → verify → demo → done.

## Roadmap Location

The roadmap file is always at `docs/ROADMAP.md` in the project root. If it doesn't exist, prompt the user to run `sprint init` first.

## Commands

### `sprint init`

Initialize or migrate a project's roadmap to the standard format.

1. Check if `docs/ROADMAP.md` already exists
2. If not, search the project for existing roadmap-like files (README, ROADMAP, SPRINT, TODO, etc.)
3. If an existing roadmap is found, read it and migrate its content to the standard format at `docs/ROADMAP.md`
4. If no existing roadmap is found, create a blank template at `docs/ROADMAP.md`
5. Use the template defined in `references/ROADMAP_TEMPLATE.md`

When migrating, preserve all existing information — map it into the Sprint > Story > Task hierarchy as best you can. Tasks that don't clearly belong to a sprint go into the Backlog section.

### `sprint plan`

Prepare the next sprint. This is a collaborative phase with the user.

1. Read `docs/ROADMAP.md`
2. Identify the next unfinished Sprint according to the **Execution Order** (not document order or ID order)
3. Present to the user:
   - The Sprint's goal and scope (Stories and Tasks to execute)
   - Any dependencies on prior Sprints that are not yet complete (flag as blockers)
   - Design decisions or architectural questions that should be resolved before implementation
4. Discuss with the user **one item at a time**. Wait for the user's response before moving to the next item.
5. After all items are resolved, update `docs/ROADMAP.md` if any changes were agreed upon (scope changes, task additions, etc.)
6. **Update the Progress section** if any changes were made (new tasks, scope changes, etc.)

### `sprint run`

Execute the current Sprint. Stories are parallelized where dependencies allow, using sub-agents with worktree isolation.

1. Read `docs/ROADMAP.md` and identify the current Sprint (same logic as `sprint plan`)

2. **Analyze Story dependencies and build execution waves:**
   - Parse any inter-Story dependencies (explicit in the Dependencies section or implicit from Task descriptions)
   - Group Stories into sequential "waves" — Stories within the same wave have no dependencies on each other and can run in parallel
   - Stories that depend on other Stories in the same Sprint must be in a later wave
   - If no dependencies exist between Stories, all Stories form a single wave

3. **For each wave (sequentially):**

   Execute all Stories in the wave in parallel using sub-agents. Each Story follows this cycle:

   **Step 1 — Implement (sub-agent, sonnet, worktree):**
   - Launch an Agent with `model: "sonnet"` and `isolation: "worktree"` for each Story
   - The agent prompt must include: the Story's Tasks, project context (CLAUDE.md, relevant architecture info), and the instruction to implement all Tasks, run tests, and log output to `docs/sprint-logs/{SprintID}/`
   - All Stories in the wave launch in parallel (single message with multiple Agent tool calls)
   - Wait for all implementation agents to complete. Each returns the worktree path and branch name.

   **Step 2 — Review (sub-agent, sonnet):**
   - For each completed implementation, launch a new Agent with `model: "sonnet"` (no worktree — it reviews the branch diff)
   - The review agent's prompt must include: the branch name from Step 1, instruction to check out that branch, invoke `/review` via the Skill tool, and return all findings categorized as auto-fixable vs. design-decision-required
   - All review agents for the wave launch in parallel

   **Step 3 — Fix (SendMessage to implementation agent, sonnet):**
   - For each review that returned auto-fixable findings, use SendMessage to the original implementation agent (which still has its worktree context) with the list of findings to fix
   - The implementation agent fixes all auto-fixable findings in its worktree
   - For findings that involve technical decisions: if there is a clear best practice or obvious recommendation, the agent makes the decision autonomously and proceeds. Only escalate to the user when the decision has significant architectural impact (e.g., changing data models, introducing new dependencies, altering public APIs, or fundamentally changing the approach agreed upon in sprint plan)
   - After fixes, send another review cycle (Step 2 → Step 3) until no more findings remain

   **Step 4 — Merge and complete:**
   - The main agent merges each Story's worktree branch into the current branch (e.g., `git merge --no-ff {branch}`)
   - Resolve any merge conflicts (if parallel Stories touched the same files, fix conflicts and re-run tests)
   - Mark each Story and its Tasks as `[x]` in `docs/ROADMAP.md`
   - Log the review results to `docs/sprint-logs/{SprintID}/`

4. After all waves are complete, present a summary of what was implemented

### `sprint verify`

Verify the Sprint implementation is complete and correct. Run this after `sprint run`.

**Phase 1: Completeness check**

1. Read `docs/ROADMAP.md` and identify the current Sprint
2. Use a subagent to perform a comprehensive review:
   - Compare every Task in the Sprint against the actual code changes and test logs in `docs/sprint-logs/{SprintID}/`
   - Check for any Tasks marked incomplete or missing implementation
   - Check for any Tasks that were implemented but not marked complete
3. If gaps are found, execute the missing work immediately

**Phase 2: Sprint-level code review via /review**

This is a final review of the entire Sprint's changes as a whole. Story-level reviews during `sprint run` catch issues within each Story, but this Sprint-level review catches cross-Story issues: inconsistencies between Stories, integration problems, duplicated code across Stories, and overall coherence.

4. After all gaps are filled, invoke the `/review` skill directly by using the Skill tool. Do NOT just mention /review or tell the user to run it — you must actually call it yourself as a slash command so that it executes and produces findings. This is a critical step; skipping it or deferring it to the user defeats the purpose of verify.
5. Read ALL findings produced by `/review`. For each finding:
   - If the fix direction is clear (code style, missing error handling, naming issues, refactoring with obvious approach, etc.), fix it immediately and autonomously
   - Only escalate to the user for decisions with significant architectural impact (changing data models, introducing major dependencies, altering public APIs, or deviating from the sprint plan)
6. After fixing findings, re-run `/review` to confirm the fixes are clean. Repeat until no more fixable findings remain.
7. If any findings require user input due to architectural impact, present them to the user **one item at a time** and wait for the user's response before proceeding to the next. Log all autonomous decisions in `docs/sprint-logs/{SprintID}/`.

**Phase 3: Finalize**

8. Update `docs/ROADMAP.md` to reflect the verified state

### `sprint demo`

Demonstrate the Sprint's deliverables to the user. Run this after `sprint verify`.

1. Read `docs/ROADMAP.md` and identify the current Sprint (the most recent `[IN PROGRESS]` or fully verified Sprint)
2. Read the Sprint's Stories and Tasks to understand what was built
3. Read `docs/ARCHITECTURE.md` and `CLAUDE.md` to understand the project type

**Determine the demo approach based on the project:**

Analyze the project and choose the most effective combination of the following demo methods:

- **Web/API server projects**: Start the server with `make serve` (or the project's serve command). Demonstrate key endpoints or pages using `curl`, `httpie`, or by telling the user which URLs to visit. Show request/response examples for new or changed API endpoints.
- **CLI tool projects**: Run the tool with representative arguments. Show before/after for changed behavior. Demonstrate new subcommands or flags.
- **Library projects**: Write and execute a small demo script that imports the library and exercises the new functionality. Show the output.
- **Infrastructure/config projects**: Show the relevant config diffs, run validation commands, or demonstrate that services come up correctly.
- **UI projects**: Start the dev server and tell the user which pages/routes to check. Describe what they should see and what to interact with.

**For each Story in the Sprint:**

4. Briefly explain what the Story delivers (1-2 sentences)
5. Execute the demo for that Story — actually run commands, show real output. Do not just describe what would happen.
6. Highlight anything notable: edge cases handled, performance characteristics, important caveats

**Wrap up:**

7. Summarize what was demonstrated
8. Ask the user if they want to explore anything further or see additional scenarios

The demo should feel like a live walkthrough, not a written report. Run real commands with real output. If something fails during the demo, note it as a potential issue to address before `sprint done`.

### `sprint done`

Finalize the Sprint and update tracking.

1. Read `docs/ROADMAP.md`
2. Mark the current Sprint as complete (change status to `[DONE]`)
3. Update all Stories and Tasks to `[x]` if not already
4. **Update the Progress section** at the top of the roadmap (counts, progress bar, current marker in Execution Order)
5. **Check if `docs/ARCHITECTURE.md` needs updating.** Review the Sprint's changes — if new components were added, data flow changed, directory structure changed, or infrastructure was modified, update ARCHITECTURE.md accordingly. If the Sprint was only bug fixes, refactoring, or UI tweaks with no architectural impact, skip this.
6. **Commit and push all uncommitted changes.** Run `git status` to check for uncommitted or unstaged files. If any exist:
   - Stage all changes: `git add -A`
   - Commit with message: `chore: complete Sprint {SprintID} — {Sprint Title}`
   - Push to the current branch: `git push`
   - If the push fails (e.g., no upstream branch), set upstream and push: `git push -u origin {branch}`
   - Report to the user what was committed (file count, branch name)
7. Present a summary to the user:
   - Sprint goal and whether it was achieved
   - List of completed Stories and key Tasks
   - Any deviations from the original plan
   - Git commit hash and branch pushed to
   - What the next Sprint covers (preview)

## Important Behaviors

- **One item at a time**: During `sprint plan` and reviews (when discussing with the user), always present and resolve one item before moving to the next. Don't dump a list of 10 questions at once.
- **Autonomous technical decisions**: During `sprint run`, make technical decisions autonomously when there is a clear best practice or obvious recommendation (e.g., error handling strategy, naming conventions, library choice among equivalent options, implementation patterns). Only escalate to the user for decisions with significant architectural impact — changing data models, introducing major dependencies, altering public APIs, or deviating from the approach agreed upon in `sprint plan`. Log autonomous decisions in `docs/sprint-logs/{SprintID}/` for traceability.
- **Log everything**: Test output, build output, and verification results go to `docs/sprint-logs/{SprintID}/`. This creates an audit trail.
- **Roadmap is the source of truth**: Always read `docs/ROADMAP.md` before taking action. Never assume you know the current state from memory.
- **Respect dependencies**: If a Sprint depends on another Sprint that isn't complete, flag it as a blocker during `sprint plan`.
- **Backlog awareness**: During `sprint plan`, if a Backlog item becomes relevant, suggest promoting it to the current Sprint.
- **Actually invoke /review**: During `sprint run` (per-Story) and `sprint verify` (Sprint-level), you must call the `/review` skill yourself via the Skill tool. Never skip this step, never just describe what /review would do, and never ask the user to run it separately.
- **Two-level review**: Story-level review during `sprint run` catches local issues. Sprint-level review during `sprint verify` catches cross-Story and integration issues. Both are mandatory.
- **Parallel execution with worktrees**: During `sprint run`, independent Stories run in parallel via sub-agents with worktree isolation. This prevents file conflicts between parallel implementations. Always merge worktree branches sequentially after a wave completes to catch conflicts early. Before the first worktree is created, ensure `.claude/worktrees/` is listed in the project's `.gitignore` (create the file if it doesn't exist). This prevents worktree contents from appearing as untracked files.
- **Sub-agent model selection**: Implementation and review sub-agents use `model: "sonnet"` for speed and cost efficiency. The main (orchestrating) agent remains on the default model to handle dependency analysis, merge conflicts, and user interaction.
- **Sub-agent prompts must be self-contained**: Each sub-agent starts fresh with no conversation context. Include all necessary information in the prompt: Story/Task details, project conventions (from CLAUDE.md), file paths, and expected behavior. Never assume the sub-agent knows what happened in prior steps.
- **Demo with real output**: During `sprint demo`, always execute real commands and show actual output. Never just describe what would happen or show hypothetical output.
- **Always commit and push on done**: `sprint done` must leave a clean working tree. If there are uncommitted changes, commit and push them. Never finish a sprint with dirty state.

## Roadmap Format Reference

See `references/ROADMAP_TEMPLATE.md` for the complete roadmap format specification and template.
