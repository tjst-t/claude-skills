# sprint done

Finalize the Sprint and update tracking.

1. Read only the current Sprint slice (see SKILL.md "Roadmap Reading Patterns"):
   ```bash
   jq '.sprints[.progress.current_sprint]' docs/ROADMAP.json
   ```
   The full slice is needed here because step 5 will snapshot it.
2. Mark the current Sprint as complete via `jq` mutation (change status to `done`)
3. Update all Stories and Tasks to `done` if not already (in-place `jq` mutations — do not rewrite the whole file)
4. **Update the Progress section** at the top of the roadmap (counts, progress bar, current marker in Execution Order)
5. **Snapshot and compact the completed Sprint in ROADMAP.json.** Done Sprints accumulate in ROADMAP.json and inflate the file Claude reads on every sprint command. To keep ROADMAP.json focused on active work without losing any historical detail:
   1. **Snapshot first (mandatory before compaction).** Write `docs/sprint-logs/{SprintID}/sprint.json` containing the full Sprint entry exactly as it was in ROADMAP.json — title, description, milestone flag, every story with its user_story / acceptance_criteria (with statuses) / tasks, plus the matching `dependencies[SprintID]` entry if one exists. Use the `sprint` schema in `references/SPRINT_LOGS_SCHEMA.json`. If writing the snapshot fails for any reason (disk error, permission, validation), STOP — do not proceed to compaction. Data preservation is non-negotiable.
   2. **Verify the snapshot.** Read it back and confirm it parses as valid JSON and contains the same Story IDs as the ROADMAP entry. Only if the verification passes, proceed.
   3. **Compact the ROADMAP entry.** Replace the Sprint's entry in `sprints[SprintID]` with the compact form: `{title, status, milestone, snapshot: "docs/sprint-logs/{SprintID}/sprint.json", stories: {<StoryID>: {title, status}, ...}}`. Drop `description`, `stories[].user_story`, `stories[].acceptance_criteria`, `stories[].tasks`, `stories[].blocked_reason`. Keep `dependencies[SprintID]` in the top-level `dependencies` map untouched — it is needed for ordering. Keep `backlog[].added_in` references untouched.
   4. **Only compact `done` Sprints.** Sprints with status `partial`, `blocked`, or `needs_human` keep their full structure — they may still need manual fixes that read from the full body.
6. **Check if `docs/ARCHITECTURE.md` needs updating.** Review the Sprint's changes — if new components were added, data flow changed, directory structure changed, or infrastructure was modified, update ARCHITECTURE.md accordingly. If the Sprint was only bug fixes, refactoring, or UI tweaks with no architectural impact, skip this.
7. **Archive completed prototype files.** If `docs/sprint-logs/{SprintID}/prototype-review.json` exists, move every prototype file whose `screens[].story` belongs to this Sprint from `prototype/` into `prototype/old/{SprintID}/` (preserve relative paths under `prototype/`, e.g. `prototype/dashboard.html` → `prototype/old/{SprintID}/dashboard.html`). Use `git mv` so history is preserved. This keeps `prototype/` focused on screens still pending implementation. Skip silently if the Sprint had no GUI Stories or no prototype files exist for it. Do NOT touch files belonging to other Sprints (still pending) or shared assets like `prototype/index.html`, `styles.css`, `assets/` — leave them in place.
8. **Clean up worktrees.** List all git worktrees (`git worktree list`). Only clean up worktrees that belong to the **current branch's** autopilot session (matching `autopilot/{current-branch-sanitized}/*` or created by this Sprint's sub-agents). Do not touch worktrees from other branches' autopilot sessions.
   - For each matching worktree:
     - If its branch has been merged into the current branch → remove it (`git worktree remove`, `git branch -d`)
     - If NOT merged: warn the user that the worktree branch `{branch}` has unmerged changes and ask whether to force-delete or keep it. Do not silently discard unmerged work.
9. **Commit and push all uncommitted changes.** Run `git status` to check for uncommitted or unstaged files. If any exist:
   - Review `git status` output and stage files explicitly by name. Do NOT use `git add -A` or `git add .` — verify that no sensitive files (`.env`, credentials, secrets) or unintended files are included. If `.gitignore` is missing common exclusions, warn the user.
   - Commit with message: `chore: complete Sprint {SprintID} — {Sprint Title}`
   - Show the user a summary of what will be pushed (branch name, commit count, file count) and confirm before pushing.
   - Push to the current branch: `git push`
   - If the push fails (e.g., no upstream branch), set upstream and push: `git push -u origin {branch}`
10. Present a summary to the user:
   - Sprint goal and whether it was achieved
   - List of completed Stories and key Tasks
   - Any deviations from the original plan
   - Git commit hash and branch pushed to
   - What the next Sprint covers (preview)
