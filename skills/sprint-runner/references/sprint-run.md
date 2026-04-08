# sprint run

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
   - **For GUI Stories**: The agent prompt must also include the Playwright test file path from `gui-spec` and the instruction: "Add `data-testid` attributes to all interactive elements. Run `npx playwright test {test-file}` after implementation. Fix all failures before marking the Story complete. Do not mark the Story as `[x]` if any Playwright tests are failing."
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
