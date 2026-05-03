# sprint run

Execute the current Sprint. Stories are parallelized where dependencies allow, using sub-agents with worktree isolation.

1. Read `docs/ROADMAP.json` and identify the current Sprint (same logic as `sprint plan`)

2. **Analyze Story dependencies and build execution waves:**
   - Parse any inter-Story dependencies (explicit in the Dependencies section or implicit from Task descriptions)
   - Group Stories into sequential "waves" — Stories within the same wave have no dependencies on each other and can run in parallel
   - Stories that depend on other Stories in the same Sprint must be in a later wave
   - If no dependencies exist between Stories, all Stories form a single wave

3. **For each wave (sequentially):**

   Execute all Stories in the wave in parallel using sub-agents. Each Story follows this cycle:

   **Step 1 — Implement (sub-agent, sonnet, worktree):**
   - Launch an Agent with `model: "sonnet"` and `isolation: "worktree"` for each Story
   - The agent prompt must include: the Story's Tasks, project context (CLAUDE.md, relevant architecture info), and the instruction to implement all Tasks, run tests, and log output to `docs/sprint-logs/{SprintID}/`. Also instruct the agent to report any out-of-scope issues it discovers (tech debt, bugs in unrelated code, potential improvements) as a separate list in its output — these will be proposed to the user as backlog candidates.
   - **For frontend/UI Stories**: The agent prompt must instruct the agent to invoke the `/frontend-design` skill for building UI components, pages, and screens. This ensures high design quality and avoids generic AI aesthetics. If an approved prototype exists in `prototype/`, include the relevant HTML file path in the prompt with the instruction: "Match the layout, styling, and element structure of the prototype. Use `data-testid` attributes exactly as they appear in the prototype."
   - **For non-GUI Stories with acceptance criteria**: The agent must generate acceptance tests that verify each acceptance criterion from ROADMAP.json. Test files go in `tests/acceptance/` (or the project's convention). Each test must be named with the acceptance criterion reference (e.g., `TestAC_S002_2_1_CreateOrganization`). These tests run against the real application (API calls, DB operations, CLI invocations) — not mocks. The agent runs these tests after implementation and fixes failures before marking the Story complete.
   - **For GUI Stories**: The agent prompt must also include the Playwright mock test file path from `gui-spec` (`{story-slug}.mock.spec.ts`) and the instruction: "Add `data-testid` attributes to all interactive elements. Run `npx playwright test {story-slug}.mock.spec.ts` after implementation. Fix all failures before marking the Story complete. Do not mark the Story as `[x]` if mock tests are failing. E2E tests (`*.e2e.spec.ts`) are NOT run at this stage — they run during `sprint verify` against the real server."
   - **For GUI Stories that call backend APIs**: Before writing any frontend API client code, the agent must read the corresponding backend handler files (e.g., `internal/api/*_handler.go` for Go, `app/controllers/` for Rails, `src/routes/` for Express) to confirm: (1) the exact endpoint path as registered in the router, (2) the exact field names in request and response serialization (JSON struct tags, serializer fields, etc.). Do not infer field names from frontend conventions — always read the actual handler. Mismatches between frontend field names and backend serialization are a common source of silent bugs that Playwright mocks cannot detect.
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
   - Mark each Story and its Tasks as `[x]` in `docs/ROADMAP.json`, with the following additional gate for GUI Stories:
     - Mock tests pass (`*.mock.spec.ts`) ✓
   - **For non-GUI Stories with acceptance criteria**: Verify that acceptance test files exist and pass. If no test file exists, the sub-agent must generate one before marking `[x]`.
   - Log the review results to `docs/sprint-logs/{SprintID}/`

4. **Backlog proposals**: After all waves are complete, collect any out-of-scope issues discovered during implementation or review (e.g., tech debt, missing error handling in unrelated code, potential improvements noticed by sub-agents). Sub-agents should return these as a separate "out-of-scope findings" list alongside their implementation results. Present them to the user as backlog candidates:
   - For each item, provide a short title and one-line description
   - Ask the user which items to add to the Backlog section of `docs/ROADMAP.json`
   - Only add items the user approves
   - If no out-of-scope issues were found, skip this step

5. Present a summary of what was implemented
