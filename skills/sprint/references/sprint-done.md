# sprint done

Finalize the Sprint and update tracking.

0. **Test execution gate (mandatory)** — enforces `references/test-discipline.md` Rules 3, 5, and 6:
   - `verification-results.json` exists with `summary.skip == 0` and `summary.fail == 0`. Missing file → verify did not complete; refuse to proceed.
   - Every AC of every Story in the Sprint is listed in `acceptance_criteria` of at least one test entry whose `status` is `pass`. Any AC without such an entry blocks `sprint done`.
   - Every Story has a scenario artifact (`scenario-{StoryID}.json` or `gui-spec-{StoryID}.json`) whose scenarios' `linked_ac` are all covered by passing tests in `verification-results.json`.
   - `verification-results.json` contains a `diff_coverage` block (Rule 6) with every entry's `resolution` set to `covered` or `added_test`. Any entry with `resolution: "needs_human"` or absent block `sprint done`.
   - On failure: surface the specific gap, do NOT downgrade or fabricate, stop. User decides between escalating as `needs_human` or fixing the gap.

1. Read only the current Sprint slice (see SKILL.md "Roadmap Reading Patterns"):
   ```bash
   jq '.sprints[.progress.current_sprint]' docs/ROADMAP.json
   ```
2. Mark the current Sprint, all its Stories, all their Tasks, and all AC as `done`/`pass` in one atomic `jq` invocation (see SKILL.md "Writes"):
   ```bash
   SPRINT=$(jq -r '.progress.current_sprint' docs/ROADMAP.json)
   jq --arg s "$SPRINT" '
     .sprints[$s].status = "done"
     | .sprints[$s].stories |= map_values(
         .status = "done"
         | .tasks |= map_values(.status = "done")
         | .acceptance_criteria |= map(.status = (if .status == "fail" then "fail" else "pass" end))
       )
   ' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
   ```
   (AC that already failed stay `fail`; everything else becomes `pass`. If you have AC explicitly marked `pending` or `no_test` that should stay that way, refine the filter accordingly.)
3. **Update the Progress section** with the "Recompute progress counts" filter from SKILL.md (and clear `current_sprint` or set it to the next pending Sprint). Combined:
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
