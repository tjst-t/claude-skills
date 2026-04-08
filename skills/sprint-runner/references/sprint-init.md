# sprint init

Initialize or migrate a project's roadmap to the standard format.

1. Check if `docs/ROADMAP.md` already exists
2. If not, search the project for existing roadmap-like files (README, ROADMAP, SPRINT, TODO, etc.)
3. If an existing roadmap is found, read it and migrate its content to the standard format at `docs/ROADMAP.md`
4. If no existing roadmap is found, create a blank template at `docs/ROADMAP.md`
5. Use the template defined in `references/ROADMAP_TEMPLATE.md`

When migrating, preserve all existing information — map it into the Sprint > Story > Task hierarchy as best you can. Tasks that don't clearly belong to a sprint go into the Backlog section.
