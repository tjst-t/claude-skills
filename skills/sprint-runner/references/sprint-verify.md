# sprint verify

Verify the Sprint implementation is complete and correct. Run this after `sprint run`.

## Phase 1: Completeness check

1. Read `docs/ROADMAP.md` and identify the current Sprint
2. Use a subagent to perform a comprehensive review:
   - Compare every Task in the Sprint against the actual code changes and test logs in `docs/sprint-logs/{SprintID}/`
   - Check for any Tasks marked incomplete or missing implementation
   - Check for any Tasks that were implemented but not marked complete
   - **For GUI Stories**: Verify that `npx playwright test` passes for each Story's test file. If any tests are failing, treat this as an incomplete Task and execute the missing work immediately.
3. If gaps are found, execute the missing work immediately

## Phase 2: Sprint-level code review via /review

This is a final review of the entire Sprint's changes as a whole. Story-level reviews during `sprint run` catch issues within each Story, but this Sprint-level review catches cross-Story issues: inconsistencies between Stories, integration problems, duplicated code across Stories, and overall coherence.

4. After all gaps are filled, invoke the `/review` skill directly by using the Skill tool. Do NOT just mention /review or tell the user to run it — you must actually call it yourself as a slash command so that it executes and produces findings. This is a critical step; skipping it or deferring it to the user defeats the purpose of verify.
5. Read ALL findings produced by `/review`. For each finding:
   - If the fix direction is clear (code style, missing error handling, naming issues, refactoring with obvious approach, etc.), fix it immediately and autonomously
   - Only escalate to the user for decisions with significant architectural impact (changing data models, introducing major dependencies, altering public APIs, or deviating from the sprint plan)
6. After fixing findings, re-run `/review` to confirm the fixes are clean. Repeat until no more fixable findings remain.
7. If any findings require user input due to architectural impact, present them to the user **one item at a time** and wait for the user's response before proceeding to the next. Log all autonomous decisions in `docs/sprint-logs/{SprintID}/`.

## Phase 3: Finalize

8. Update `docs/ROADMAP.md` to reflect the verified state
