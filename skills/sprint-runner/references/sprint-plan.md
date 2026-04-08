# sprint plan

Prepare the next sprint. This is a collaborative phase with the user.

1. Read `docs/ROADMAP.md`
2. Identify the next unfinished Sprint according to the **Execution Order** (not document order or ID order)
3. Present to the user:
   - The Sprint's goal and scope (Stories and Tasks to execute)
   - Any dependencies on prior Sprints that are not yet complete (flag as blockers)
   - Design decisions or architectural questions that should be resolved before implementation
4. **User Story validation**: Verify that each Story follows the format:
   ```
   {役割}として、{やりたいこと}をしたい。なぜなら、{理由・価値}だから。
   ```
   If any Story is written as a task decomposition ("〜を実装する", "〜コンポーネントを作る", etc.), collaborate with the user to rewrite it as a user story and confirm acceptance criteria.
5. Discuss with the user **one item at a time**. Wait for the user's response before moving to the next item.
6. **GUI Spec phase**: After scope is confirmed, invoke the `gui-spec` skill via the Skill tool.
   - The `gui-spec` skill will detect whether the Sprint contains GUI Stories.
   - If GUI Stories are found, it conducts dialogue with the user to elicit scenarios, generate a state diagram, and produce Playwright acceptance tests.
   - If no GUI Stories are found, it returns immediately and `sprint plan` continues.
   - Do NOT skip this step even if the Sprint seems straightforward — let `gui-spec` make the determination.
7. After all items are resolved, update `docs/ROADMAP.md` if any changes were agreed upon (scope changes, task additions, acceptance criteria added by `gui-spec`, etc.)
8. **Update the Progress section** if any changes were made.
