# sprint plan

Prepare the next sprint. This is a collaborative phase with the user.

1. **Read only what is needed from `docs/ROADMAP.json`** (see SKILL.md "Roadmap Reading Patterns"):
   - Top-level structure to find the next Sprint and check dependencies:
     ```bash
     jq '{progress, execution_order, dependencies, sprints: (.sprints | map_values({title, status, milestone}))}' docs/ROADMAP.json
     ```
   - Then the slice of the next unfinished Sprint:
     ```bash
     jq --arg id "<NextSprintID>" '.sprints[$id]' docs/ROADMAP.json
     ```
2. Identify the next unfinished Sprint according to the **Execution Order** (not document order or ID order)
3. Present to the user:
   - The Sprint's goal and scope (Stories and Tasks to execute)
   - Any dependencies on prior Sprints that are not yet complete (flag as blockers)
   - Design decisions or architectural questions that should be resolved before implementation
4. **User Story validation and granularity check**: Verify that each Story follows the format:
   ```
   {役割}として、{やりたいこと}をしたい。なぜなら、{理由・価値}だから。
   ```
   If any Story is written as a task decomposition ("〜を実装する", "〜コンポーネントを作る", etc.), autonomously rewrite it as a proper user story with acceptance criteria.

   After rewriting, evaluate each Story's **granularity**. A Story is too large if it:
   - Contains multiple distinct user-facing behaviors that could be independently delivered and verified
   - Has acceptance criteria spanning unrelated concerns (e.g., CRUD + search + export in one Story)
   - Would require touching many unrelated modules or layers to implement

   If a Story is clearly overloaded, propose a split into smaller, independently deliverable Stories. Each split Story must still be a proper user story with its own acceptance criteria. Splitting may affect the Sprint scope and roadmap structure, so **always present the proposed split to the user for confirmation** — this is a scope change, not a routine auto-decision.

5. **Auto-decide, then confirm once**: For design decisions and architectural questions, first determine if there is a clear recommended approach. If so, auto-select it and note the rationale. Only ask the user for decisions that are genuinely ambiguous (multiple viable approaches with real trade-offs). Present the full sprint plan — including all auto-decided items, rewritten stories, proposed Story splits (if any), and any open questions — in a single summary for the user to confirm or adjust.
6. **Story scenario derivation (mandatory, every Story)**: For each Story, classify the entry point (`cli` / `api` / `gui` / `library` / `mixed`) and produce a scenario artifact before `sprint run` begins. Format and per-type templates live in `references/story-scenarios.md`; the rules tests must follow live in `references/test-discipline.md`.

   - **GUI / mixed-with-GUI**: invoke the `gui-spec` skill via the Skill tool. Output → `docs/sprint-logs/{SprintID}/gui-spec-{StoryID}.json`.
   - **CLI / API / Library**: derive inline from the templates in `story-scenarios.md`. Output → `docs/sprint-logs/{SprintID}/scenario-{StoryID}.json`. Each scenario must link to its AC(s) via `linked_ac` and end with observations available through the user's entry point.
   - Every AC must be exercised by at least one scenario step. AC that cannot be observed through any user-facing surface are invalid — flag them.
   - In autonomous mode (`sprint auto`): auto-derive without user confirmation, log to `decisions.json`.
7. After all items are resolved, update `docs/ROADMAP.json` with the agreed changes via targeted `jq` mutations (see SKILL.md "Writes"). Concrete filters depending on what changed:
   - **Story rewritten**: `--arg s --arg st --argjson body '.sprints[$s].stories[$st] = $body'`
   - **Story split into N**: replace the original story with the new ones using a single jq with `del` + multiple `=`, then increment any task numbering as needed
   - **Tasks added**: "Add Task to a Story" filter
   - **AC added by gui-spec**: "Append AC to a Story" filter (per Story)
   - Do NOT Read the whole file then rewrite it.
8. **Update the Progress section** if Sprint count or status changed: use the "Recompute progress counts" filter (and "Update progress total" if `total` itself changed).
