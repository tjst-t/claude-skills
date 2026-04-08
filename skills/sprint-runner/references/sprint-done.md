# sprint done

Finalize the Sprint and update tracking.

1. Read `docs/ROADMAP.md`
2. Mark the current Sprint as complete (change status to `[DONE]`)
3. Update all Stories and Tasks to `[x]` if not already
4. **Update the Progress section** at the top of the roadmap (counts, progress bar, current marker in Execution Order)
5. **Check if `docs/ARCHITECTURE.md` needs updating.** Review the Sprint's changes — if new components were added, data flow changed, directory structure changed, or infrastructure was modified, update ARCHITECTURE.md accordingly. If the Sprint was only bug fixes, refactoring, or UI tweaks with no architectural impact, skip this.
6. **Commit and push all uncommitted changes.** Run `git status` to check for uncommitted or unstaged files. If any exist:
   - Stage all changes: `git add -A`
   - Commit with message: `chore: complete Sprint {SprintID} — {Sprint Title}`
   - Push to the current branch: `git push`
   - If the push fails (e.g., no upstream branch), set upstream and push: `git push -u origin {branch}`
   - Report to the user what was committed (file count, branch name)
7. Present a summary to the user:
   - Sprint goal and whether it was achieved
   - List of completed Stories and key Tasks
   - Any deviations from the original plan
   - Git commit hash and branch pushed to
   - What the next Sprint covers (preview)
