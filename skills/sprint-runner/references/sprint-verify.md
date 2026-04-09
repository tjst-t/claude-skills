# sprint verify

Verify the Sprint implementation is complete and correct. Run this after `sprint run`.

## Phase 1: Completeness check

1. Read `docs/ROADMAP.md` and identify the current Sprint
2. Use a subagent to perform a comprehensive review:
   - Compare every Task in the Sprint against the actual code changes and test logs in `docs/sprint-logs/{SprintID}/`
   - Check for any Tasks marked incomplete or missing implementation
   - Check for any Tasks that were implemented but not marked complete
   - **For GUI Stories**: Verify that `npx playwright test` passes for each Story's test file. If any tests are failing, treat this as an incomplete Task and execute the missing work immediately.
   - **API mock contract check**: GUI Story がある場合、Playwright テストのモックが返すデータ形式を `internal/api/` の実装と照合する。特にページネーションレスポンス（`items` ラッパー）の有無を確認する。モックと実 API の形式が乖離している場合、テストを修正する。
3. If gaps are found, execute the missing work immediately

## Phase 1.5: Real-server smoke test (GUI Sprints only)

If the Sprint contains GUI Stories, perform the following before invoking `/review`:

1. Run `make serve` (or the project's startup command) to bring up the real server
2. **Login gate**: Verify that the authentication endpoint the frontend uses (e.g., `POST /api/v1/auth/verify`) exists and returns 200 for the dev token. If it does not exist, create it immediately — a Sprint where the user cannot log in has zero usable acceptance criteria.
3. **Per-Story endpoint check**: For each GUI Story, identify every API endpoint the frontend calls (read the TypeScript API client files in `web/src/api/`). For each endpoint:
   - Confirm it is registered in the router (grep the router file)
   - Send a real `curl` request and confirm the response shape matches what the TypeScript types expect (field names, nesting, pagination wrapper or lack thereof)
4. **Fix all mismatches before proceeding**: Field name mismatches, missing endpoints, or wrong response shapes must be fixed now. These are bugs that Playwright mocks cannot detect.
5. Document the smoke test results in `docs/sprint-logs/{SprintID}/smoke-test.md`

> **Why this step exists**: Playwright tests use `page.route()` mocks, which means they test the frontend in isolation. They cannot detect: missing backend endpoints, wrong JSON field names (e.g., `ram_mb` vs `memory_mb`), wrong URL paths (e.g., `/storage-backends` vs `/admin/storage-backends`), or wrong response structure (array vs paginated object). This step is the only gate that catches frontend-backend contract violations before the demo.

## Phase 2: Sprint-level code review via /review

This is a final review of the entire Sprint's changes as a whole. Story-level reviews during `sprint run` catch issues within each Story, but this Sprint-level review catches cross-Story issues: inconsistencies between Stories, integration problems, duplicated code across Stories, and overall coherence.

4. After all gaps are filled, invoke the `/review` skill directly by using the Skill tool. Do NOT just mention /review or tell the user to run it — you must actually call it yourself as a slash command so that it executes and produces findings. This is a critical step; skipping it or deferring it to the user defeats the purpose of verify.
5. Read ALL findings produced by `/review`. For each finding:
   - If the fix direction is clear (code style, missing error handling, naming issues, refactoring with obvious approach, etc.), fix it immediately and autonomously
   - Only escalate to the user for decisions with significant architectural impact (changing data models, introducing major dependencies, altering public APIs, or deviating from the sprint plan)
6. After fixing findings, re-run `/review` to confirm the fixes are clean. Repeat until no more fixable findings remain.
7. If any findings require user input due to architectural impact, present them all together in a single summary with your recommended approach for each. The user can then confirm or override specific items. Log all autonomous decisions in `docs/sprint-logs/{SprintID}/`.

## Phase 3: Finalize

8. Update `docs/ROADMAP.md` to reflect the verified state
