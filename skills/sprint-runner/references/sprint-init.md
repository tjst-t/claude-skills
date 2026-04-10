# sprint init

Initialize or migrate a project's roadmap to the standard format.

1. Check if `docs/ROADMAP.md` already exists
2. If not, search the project for existing roadmap-like files:
   - Common locations: `README.md` (roadmap sections), `ROADMAP.md`, `TODO.md`, `SPRINT.md`, `docs/TODO.md`
   - Also check for issue trackers or project boards mentioned in the repo
3. If an existing roadmap is found, read it and migrate its content to the standard format at `docs/ROADMAP.md`:
   - Map top-level groupings → Sprints
   - Map individual items → Stories (rewrite as user stories if they are task-style)
   - Map sub-items → Tasks under the appropriate Story
   - Items that don't clearly belong to a sprint go into the Backlog section
   - Preserve all existing information — do not silently drop items
4. If no existing roadmap is found, create a blank template at `docs/ROADMAP.md`
5. Use the template defined in `references/ROADMAP_TEMPLATE.md`
6. Create the `docs/` directory if it doesn't exist
7. Add `docs/sprint-logs/` to `.gitignore` if not already present (logs are ephemeral)

When migrating, present a summary of what was mapped and ask the user to confirm before writing.
