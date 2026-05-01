# sprint done

Finalize the Sprint and update tracking.

1. Read `docs/ROADMAP.md`
2. Mark the current Sprint as complete (change status to `[DONE]`)
3. Update all Stories and Tasks to `[x]` if not already
4. **Update the Progress section** at the top of the roadmap (counts, progress bar, current marker in Execution Order)
5. **Check if `docs/ARCHITECTURE.md` needs updating.** Review the Sprint's changes — if new components were added, data flow changed, directory structure changed, or infrastructure was modified, update ARCHITECTURE.md accordingly. If the Sprint was only bug fixes, refactoring, or UI tweaks with no architectural impact, skip this.
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
