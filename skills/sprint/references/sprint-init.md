# sprint init

Initialize or migrate a project's roadmap to the standard format.

1. Check if `docs/ROADMAP.json` already exists
2. If not, search the project for existing roadmap-like files:
   - Common locations: `README.md` (roadmap sections), `ROADMAP.md`, `TODO.md`, `SPRINT.md`, `docs/TODO.md`
   - Also check for issue trackers or project boards mentioned in the repo
3. If an existing roadmap is found, read it and migrate its content to the standard format at `docs/ROADMAP.json`:
   - Map top-level groupings → Sprints
   - Map individual items → Stories (rewrite as user stories if they are task-style)
   - Map sub-items → Tasks under the appropriate Story
   - Items that don't clearly belong to a sprint go into the Backlog section
   - Preserve all existing information — do not silently drop items
   - **Sprint IDs**: If the source uses sequential IDs (S001, S002, ...) keep them as-is — they are valid and permanent. If the source has no Sprint IDs, generate random ones using `openssl rand -hex 3` (prepend `S`, e.g., `Sa3f9c2`). Do not renumber existing IDs.
4. If no existing roadmap is found, create a blank template at `docs/ROADMAP.json`. Generate any new Sprint IDs with `openssl rand -hex 3` (prepend `S`).
5. Use the schema defined in `references/ROADMAP_SCHEMA.json`
6. Create the `docs/` directory if it doesn't exist
7. Add `docs/sprint-logs/` to `.gitignore` if not already present (logs are ephemeral)

When migrating, present a summary of what was mapped and ask the user to confirm before writing.

## Migration from Markdown to JSON

If `docs/ROADMAP.md` exists but `docs/ROADMAP.json` does not:
1. Read `docs/ROADMAP.md` and parse its content
2. Convert to JSON structure following `references/ROADMAP_SCHEMA.json`
3. Write `docs/ROADMAP.json`
4. Rename `docs/ROADMAP.md` to `docs/ROADMAP.md.bak`
5. Log: "Migrated ROADMAP.md → ROADMAP.json (backup at ROADMAP.md.bak)"

Similarly migrate if found:
- `docs/VISION.md` → `docs/VISION.json` (following VISION_SCHEMA.json from autopilot skill)
- `docs/DESIGN_PRINCIPLES.md` → `docs/DESIGN_PRINCIPLES.json` (following DESIGN_PRINCIPLES_SCHEMA.json from autopilot skill)
- `docs/sprint-logs/{SprintID}/decisions.md` → `decisions.json`
- `docs/sprint-logs/{SprintID}/acceptance-matrix.md` → `acceptance-matrix.json`
- `docs/sprint-logs/{SprintID}/e2e-results.md` → `e2e-results.json`
- `docs/sprint-logs/{SprintID}/refine.md` → `refine.json`
- `docs/sprint-logs/{SprintID}/failures.md` → `failures.json`
- `docs/sprint-logs/{SprintID}/gui-spec-*.md` → `gui-spec-*.json`

All .md originals are renamed to .md.bak.
