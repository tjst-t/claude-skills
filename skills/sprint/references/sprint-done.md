# sprint done

Finalize the Sprint and update tracking.

0. **Test execution gate (mandatory)** — enforces `references/test-discipline.md` Rules 3, 5, 6, and 7:
   - **Machine verdict gate (authoritative)**: read `docs/sprint-logs/{SprintID}/verify-run.json` (machine-authored by `hooks/run-verify.py`; see `references/verify-execution.md`). If `overall_machine_status != "pass"` (any run's `exit_code != 0`, or JUnit failures), **refuse `done`** regardless of what `verification-results.json` claims — this is the deterministic backstop against recording a real failure as pass. If `verify-run.json` is absent but the project has a verify command (`.claude/verify.json`, or a `verify:`/`test:` Makefile target), machine verification did not run → refuse `done` and re-run `sprint verify`. (Only when no verify command exists at all does this check fall back to the self-reported summary below.)
   - `verification-results.json` exists with `summary.skip == 0` and `summary.fail == 0`. Missing file → verify did not complete; refuse to proceed.
   - Every AC of every Story in the Sprint is listed in `acceptance_criteria` of at least one test entry whose `status` is `pass`. Any AC without such an entry blocks `sprint done`.
   - Every Story has a scenario artifact (`scenario-{StoryID}.json` or `gui-spec-{StoryID}.json`) whose scenarios' `linked_ac` are all covered by passing tests in `verification-results.json`.
   - `verification-results.json` contains a `diff_coverage` block (Rule 6) with every entry's `resolution` set to `covered` or `added_test`. Any entry with `resolution: "needs_human"` or absent block `sprint done`.
   - On failure: surface the specific gap, do NOT downgrade or fabricate, stop. User decides between escalating as `needs_human` or fixing the gap.

0.5. **8-Guard done-judgment re-evaluation (mandatory)** — enforces `references/sprint-done-judgment.md`. `sprint verify` already produced a `done_judgment` block per Story in `verification-results.json`; `sprint done` re-reads it as the final gate and additionally re-runs the machine-checkable Guards 4–6 against the post-merge tree to catch anything that drifted between verify and done:
   - Read `verification-results.json` → `done_judgment[]`. Any Story with `overall: "needs_user_review"` is NOT eligible for `done`.
   - Re-run Guard 4 against the Story's `review_reason` and any `decisions.json` rationale that invokes the priority_rule 9 exception. The exception requires an explicit障害シナリオ identifier (`kill-9` / `停電` / `Shamir-unseal` / `ネットワーク遮断` / `disk-full` / `OOM` / `プロセスクラッシュ`); unmatched claims are invalid and require a real-mode smoke.
   - Re-run Guard 5 (call-path grep) against the current HEAD. Zero hits ⇒ the Story does not earn `done`.
   - Re-run Guard 6 (deferred-comment residue) against `git diff {Sprint base SHA}..HEAD -- 'cmd/' 'internal/' 'ansible/'`. Matches without a backlog reference block `done` for the owning Story.
   - Stories that fail any guard at this re-evaluation are marked `status: "needs_user_review"` (NOT `done`) in the Step 2 atomic mutation below, and the Sprint's overall status reflects this — see Step 2 note.

1. Read only the current Sprint slice (see `references/roadmap-jq.md` → Reading patterns):
   ```bash
   jq '.sprints[.progress.current_sprint]' docs/ROADMAP.json
   ```
2. Mark each Story's terminal status based on the Step 0.5 8-guard re-evaluation, then set the Sprint status accordingly. Stories with `done_judgment.overall: "needs_user_review"` MUST NOT be flipped to `done` here. Read the per-Story `overall` flag and branch:
   ```bash
   SPRINT=$(jq -r '.progress.current_sprint' docs/ROADMAP.json)
   # Build a map of {story_id: "done" | "needs_user_review"} from verification-results.json
   STATUS_MAP=$(jq -c 'reduce .done_judgment[] as $j ({};
     .[$j.story_id] = (if $j.overall == "ok" then "done" else "needs_user_review" end)
   )' docs/sprint-logs/$SPRINT/verification-results.json)
   jq --arg s "$SPRINT" --argjson sm "$STATUS_MAP" '
     .sprints[$s].stories |= with_entries(
       .value.status = ($sm[.key] // "done")
       | .value.tasks |= map_values(
           if ($sm[.key] // "done") == "done" then .status = "done" else . end
         )
       | .value.acceptance_criteria |= map(
           .status = (if .status == "fail" then "fail" else "pass" end)
         )
     )
     | .sprints[$s].status = (
         if any(.sprints[$s].stories[]; .status == "needs_user_review")
         then "partial"
         else "done"
         end
       )
   ' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
   ```
   - Stories that passed the 8 guards (`overall: "ok"`) become `done`. Their Tasks also become `done`.
   - Stories that failed any guard (`overall: "needs_user_review"`) keep their pre-existing status — usually `pending` or `in_progress` — but with a `needs_user_review` marker. Their Tasks are NOT auto-completed.
   - AC that already failed stay `fail`; everything else becomes `pass`. (If you have AC explicitly marked `pending` or `no_test` that should stay that way, refine the filter accordingly.)
   - The Sprint becomes `done` only if every Story is `done`. If ANY Story is `needs_user_review`, the Sprint becomes `partial` and surfaces at the milestone demo.
3. **Update the Progress section** with the "Recompute progress counts" filter from `references/roadmap-jq.md` (and clear `current_sprint` or set it to the next pending Sprint). Combined below — the four `.progress.*` lines are verbatim that canonical filter; keep them in sync with `roadmap-jq.md` if the progress formula changes:
   ```bash
   NEXT=$(jq -r '.progress.current_sprint as $cur | (.execution_order | index($cur)) as $idx | .execution_order[$idx + 1] // ""' docs/ROADMAP.json)
   jq --arg next "$NEXT" '
     .progress.current_sprint = (if $next == "" then null else $next end)
     | .progress.done = ([.sprints[] | select(.status == "done")] | length)
     | .progress.in_progress = ([.sprints[] | select(.status == "in_progress")] | length)
     | .progress.remaining = (.progress.total - .progress.done - .progress.in_progress)
     | .progress.percentage = (if .progress.total > 0 then (.progress.done * 100 / .progress.total | floor) else 0 end)
   ' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
   ```
4. **Check if `docs/ARCHITECTURE.md` needs updating.** Review the Sprint's changes — if new components were added, data flow changed, directory structure changed, or infrastructure was modified, update ARCHITECTURE.md accordingly. If the Sprint was only bug fixes, refactoring, or UI tweaks with no architectural impact, skip this.
5. **Archive completed prototype files.** If `docs/sprint-logs/{SprintID}/prototype-review.json` exists, move every prototype file whose `screens[].story` belongs to this Sprint from `prototype/` into `prototype/old/{SprintID}/` (preserve relative paths under `prototype/`, e.g. `prototype/dashboard.html` → `prototype/old/{SprintID}/dashboard.html`). Use `git mv` so history is preserved. This keeps `prototype/` focused on screens still pending implementation. Skip silently if the Sprint had no GUI Stories or no prototype files exist for it. Do NOT touch files belonging to other Sprints (still pending) or shared assets like `prototype/index.html`, `styles.css`, `assets/` — leave them in place.
6. **Clean up worktrees.** List all git worktrees (`git worktree list`). Only clean up worktrees that belong to the **current branch's** autopilot session (matching `autopilot/{current-branch-sanitized}/*` or created by this Sprint's sub-agents). Do not touch worktrees from other branches' autopilot sessions.
   - For each matching worktree:
     - If its branch has been merged into the current branch → remove it (`git worktree remove`, `git branch -d`)
     - If NOT merged: warn the user that the worktree branch `{branch}` has unmerged changes and ask whether to force-delete or keep it. Do not silently discard unmerged work.
7. **Commit and push all uncommitted changes.** Run `git status` to check for uncommitted or unstaged files. If any exist:
   - Review `git status` output and stage files explicitly by name. Do NOT use `git add -A` or `git add .` — verify that no sensitive files (`.env`, credentials, secrets) or unintended files are included. If `.gitignore` is missing common exclusions, warn the user.
   - Commit with message: `chore: complete Sprint {SprintID} — {Sprint Title}`
   - Show the user a summary of what will be pushed (branch name, commit count, file count) and confirm before pushing.
   - Push to the current branch: `git push`
   - If the push fails (e.g., no upstream branch), set upstream and push: `git push -u origin {branch}`
8. Present a summary to the user:
   - Sprint goal and whether it was achieved
   - List of completed Stories and key Tasks
   - Any deviations from the original plan
   - Git commit hash and branch pushed to
   - What the next Sprint covers (preview)
