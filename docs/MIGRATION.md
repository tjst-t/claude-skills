# Migrating an existing project to the v0.5 skills

This guide is for projects that already have a `docs/ROADMAP.json` (and maybe `docs/DESIGN/` and `docs/sprint-logs/`) from an earlier version of these skills. The v0.5 refactor is designed so **your existing data carries over untouched**. You should be able to upgrade the skills and keep working without converting anything.

## Backward-compatibility policy

| Principle | What it means |
|---|---|
| **Existing files are never auto-rewritten** | ROADMAP.json / VISION.json / DESIGN/ / sprint-logs/ are read as-is. There is no `sprint migrate` command, by design — irreversible bulk conversion is the thing we avoid. |
| **New fields are optional** | Every field added by v0.5 is optional. If it's absent, the default interpretation applies (see below). |
| **New files are on-demand** | `compromises.json`, `reopen.json`, `verification-report.json`, `comprehension-report.md` are created only when first needed. They are never back-filled for past Sprints. |
| **No retroactive rewrites** | autopilot never re-opens or re-grades a `done` Sprint on its own. Only an explicit user instruction does. |
| **Offers default to No** | If a skill offers to tidy your ROADMAP.json into the new shape, the default is to leave it alone; only an explicit yes proceeds. |

There is intentionally **no schema version field**. Compatibility is held by a single rule: *add fields, never remove them.*

## What changed that you might notice

- **Commands renamed** (old names still work as deprecated aliases): `sprint hotfix` → `sprint fix`, `sprint propose` → `sprint idea`.
- **`sprint auto` is deprecated** in favor of `autopilot` (still works; prints a one-line note).
- **`gui-spec` is no longer a separate skill** — it moved into `sprint/references/gui-spec.md`. Re-run `./install.sh` once so the stale `~/.claude/skills/gui-spec` symlink is pruned.
- **Triggers narrowed/expanded**: natural-language project requests now route to `autopilot`; `sprint` fires only on an explicit `sprint <command>`; `design` fires only on load-bearing/complexity signals.
- **Schemas moved owner**: `VISION_SCHEMA.json` and `DESIGN_PRINCIPLES_SCHEMA.json` now live under the `design` skill. This is internal to the skills — your `docs/VISION.json` / `docs/DESIGN_PRINCIPLES.json` are unaffected.

## Optional fields and their defaults

| File | New field | If absent |
|---|---|---|
| ROADMAP.json → Story | `added_in_review` | treated as an originally-planned Story |
| ROADMAP.json → Story | `reopened_at` | never re-opened |
| ROADMAP.json → AC | `reopened_at` | a normal `pass` AC |
| ROADMAP.json → Sprint | `corrections` | empty array (no corrections) |
| sprint-logs/{SprintID}/ | `compromises.json` | "妥協なし" / not recorded for this historical Sprint |
| sprint-logs/{SprintID}/ | `reopen.json` | no re-open history |
| sprint-logs/{SprintID}/ | `verification-report.json` | verifier not run |
| sprint-logs/{SprintID}/ | `comprehension-report.md` | generated on demand at `autopilot review`; never back-filled |

## Migration steps

1. **Back up** `docs/` (e.g. `git commit` your current state, or copy the directory). Nothing here rewrites your files, but a known-good snapshot is cheap insurance.
2. **Update the skills**: `git pull` in the claude-skills repo, then `./install.sh` (this prunes the old `gui-spec` symlink).
3. **Sanity check**: run `autopilot status`. It should read your existing ROADMAP.json fine; new fields it doesn't find render as `-` / `N/A`.
4. **Keep going**: the new rules apply from your **next** Sprint onward. Past Sprints are left exactly as they are.

## Behavior on an existing project

| Scenario | Behavior |
|---|---|
| `autopilot status` on an existing ROADMAP.json | Reads normally; missing new fields show as `-` / `N/A`. |
| `autopilot review` on an old `done` Sprint | "この Sprint の compromises.json / comprehension-report.md は存在しません。新ルールは次の Sprint から適用されます。" |
| `sprint verify --auto` on an in-progress Sprint | Works as before; the independent verifier also runs. |
| `autopilot review` ④ direction-change with existing DESIGN/ | Runs `design refresh` as usual. |
| ROADMAP.json present but VISION.json missing | Generates a simple VISION via `autopilot setup`, or suggests `design start`. |

## Re-opening a past Sprint on purpose

If you later realize a past Sprint was actually an AC violation, autopilot will **not** fix it silently. You re-open it explicitly:

1. Tell the skill, e.g. *"Sprint S004 を再オープンしたい"* (name the Sprint).
2. It applies the standard re-open flow: Sprint `done` → `in_progress`; affected AC `pass` → `fail` with `reopened_at`; fix tasks/Stories appended; `progress.done` recomputed.
3. It writes `docs/sprint-logs/S004/reopen.json` with `triggered_by: "manual_retroactive"` — distinguishing a deliberate retroactive re-open from one driven by a milestone review.

The policy is **"protect the past, be strict about the future."** Old decisions were made in their own context; they are not re-graded by today's rules unless you ask.

## Troubleshooting

- **A skill mis-fires or doesn't fire on natural language.** Project work routes to `autopilot`; `sprint` only fires on an explicit `sprint <command>`; `design` only on load-bearing/complexity signals. Type the explicit command if auto-routing isn't what you want.
- **`gui-spec` "skill not found".** Expected — it's now `sprint/references/gui-spec.md`, reached from `sprint plan`. Re-run `./install.sh` to clear the old symlink.
- **`autopilot status` shows lots of `-` / `N/A`.** Normal for a pre-v0.5 project: those fields are populated from the next Sprint onward.
- **You want the old behavior of a renamed command.** The aliases (`sprint hotfix`, `sprint propose`, `sprint auto`) still run; they just print a deprecation note.

> Keep this file in sync when the skill specs change. Re-read it at the periodic configuration review (every 3–6 months, or after a major model release).
