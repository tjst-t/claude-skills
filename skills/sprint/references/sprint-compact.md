# sprint compact

Bulk-compact every already-completed Sprint in `docs/ROADMAP.json` that has not yet been compacted. Use this once per project to migrate an existing ROADMAP that grew before the compaction feature existed; afterwards `sprint done` keeps things compact going forward.

## When to run

- A long-running project's `docs/ROADMAP.json` has accumulated many `status: "done"` Sprints in their full form (with `description`, `user_story`, `acceptance_criteria`, `tasks`).
- Token usage of every sprint command is being inflated by historical detail that is no longer actively edited.

Skip if every done Sprint already has a `snapshot` field — there is nothing to compact.

## Flow

1. Read `docs/ROADMAP.json`.
2. **Identify candidates.** Iterate over `sprints`; a Sprint is a candidate if BOTH:
   - `status == "done"`
   - `snapshot` field is absent (already-compacted Sprints have it)
   Sprints with status `partial`, `blocked`, `needs_human`, `in_progress`, or `pending` are skipped — they may still need full-form access.
3. **For each candidate, snapshot then compact** (same as `sprint done` step 5; see `sprint-done.md`):
   1. Write `docs/sprint-logs/{SprintID}/sprint.json` with the full Sprint entry — title, description, milestone, every story (user_story, acceptance_criteria with statuses, tasks), plus the matching `dependencies[SprintID]` entry if present. Use the `sprint` schema in `SPRINT_LOGS_SCHEMA.json`.
   2. Read it back, confirm it is valid JSON, and confirm every Story ID from the source is present in the snapshot. If verification fails, STOP and skip this Sprint — log a warning to the user. Data preservation is non-negotiable.
   3. Replace the entry in `sprints[SprintID]` with the compact form: `{title, status, milestone, snapshot, stories: {<StoryID>: {title, status}, ...}}`. Drop `description`, `stories[].user_story`, `stories[].acceptance_criteria`, `stories[].tasks`, `stories[].blocked_reason`. Leave `dependencies[SprintID]` and `backlog[].added_in` untouched.
4. **Write `docs/ROADMAP.json` once at the end** after all candidates are processed (avoid intermediate writes).
5. **Report**: list each compacted SprintID with the byte-size delta of its entry, the total bytes saved, and the count of any Sprints skipped due to verification failure (with the reason). If a Sprint had no Stories or already had `snapshot`, do not list it.

## Important Behaviors

- **Idempotent**: Running compact twice is a no-op the second time.
- **Read-only on the snapshot path**: If `docs/sprint-logs/{SprintID}/sprint.json` already exists from a prior partial run, read it back and verify it matches the current ROADMAP entry before reusing it; if it diverges (e.g. someone edited the ROADMAP entry afterwards), overwrite with the current source. The ROADMAP is the source of truth at compaction time.
- **No git commit**: Leave the changes uncommitted so the user can review before committing. Show a summary diff hint (`git diff docs/ROADMAP.json`).
- **Never compact non-done Sprints**: Even if a Sprint looks "stable", only `done` is safe to compact.
