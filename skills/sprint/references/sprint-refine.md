# sprint refine

Interactive refinement loop — the user sees the running application, points out issues, and Claude fixes them immediately. Run this after `sprint demo`, before `sprint done`.

This phase is **always interactive**. It cannot run in auto mode. During autopilot, this is the one phase where the user actively participates.

## Prerequisites

- The server must be running (`make serve` or equivalent — sprint demo should have started it)
- The current Sprint must have been verified (`sprint verify` completed)

## Flow

### 1. Start the refinement session

1. Read `docs/ROADMAP.md` to identify the current Sprint and its Stories
2. Confirm the server is running. If not, start it.
3. Tell the user:
   - Which URL(s) to visit
   - "Please interact with the application. When you find something you want changed, describe it here. Say '完了' or 'done' when you're satisfied."

### 2. Refinement loop

For each piece of feedback from the user:

1. **Understand the request**: The user may provide:
   - Text description ("this button is too small", "spacing feels off")
   - Screenshot (read and analyze the image)
   - Specific element reference ("the header on /dashboard")
   - UX flow issue ("after submitting, nothing happens for 2 seconds")

2. **Assess scope**: Is this a quick fix or a larger change?
   - **Quick fix** (CSS, text, spacing, colors, small component tweaks, minor logic): Fix immediately.
   - **Large change** (layout restructure, new component, significant behavior change): Inform the user that this is better handled as a Story in the next Sprint. Offer to add it to the Backlog. If the user insists, proceed but warn it may take longer.

3. **Implement the fix**:
   - For frontend/UI changes: use the `/frontend-design` skill
   - For backend changes: edit directly
   - Keep changes minimal and focused — fix exactly what was requested, nothing more

4. **Prompt the user to verify**:
   - "Fixed. Please reload the page and check."
   - If the project supports hot reload, mention that the change should appear automatically

5. **Repeat** until the user says they're done

### 3. Post-refinement

After the user signals completion:

1. **Log all changes** to `docs/sprint-logs/{SprintID}/refine.md`:
   ```markdown
   # Sprint {SprintID} — Refinement Log

   | # | User feedback | Change made | Files modified |
   |---|--------------|-------------|----------------|
   | 1 | "Login button too small" | Increased button padding and font size | web/src/components/LoginForm.tsx |
   | 2 | "Error message not visible enough" | Changed error text to red with icon | web/src/components/Alert.tsx |
   ```

2. **Re-run affected tests**:
   - Identify which test files cover the modified components
   - Run mock tests: `npx playwright test {affected}.mock.spec.ts`
   - Run E2E tests: `npx playwright test {affected}.e2e.spec.ts`
   - If any tests fail due to the refinement changes (e.g., element size changed, new element added), update the tests to match the new behavior
   - If tests still fail after update, fix the implementation

3. **Commit the refinement changes**:
   - Stage only the files modified during refine
   - Commit with message: `refine: Sprint {SprintID} — UI adjustments from user feedback`

## Important Behaviors

- **Minimal changes**: Fix exactly what the user asked for. Do not refactor surrounding code, add features, or "improve" things the user didn't mention.
- **Fast feedback**: The user is watching. Keep fixes small and quick. If a fix takes more than a few minutes, give a progress update.
- **Respect the tests**: After all refinements, tests must still pass. Update tests if the intended behavior changed, but never delete test coverage.
- **Backlog large requests**: If the user requests something that would take significant time or affect multiple Stories, propose adding it to the Backlog rather than fixing inline. Respect the user's decision if they insist.
- **Screenshots are first-class input**: If the user provides a screenshot, analyze it carefully. The visual context often communicates more than text.
- **No auto mode**: This phase requires human eyes on the application. It is skipped entirely in `sprint auto`. In autopilot, it runs only at milestone boundaries.
