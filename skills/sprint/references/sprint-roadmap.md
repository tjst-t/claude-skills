# sprint roadmap

Generate a multi-sprint roadmap from VISION.json and ARCHITECTURE.md, using **rolling-wave (progressive-elaboration) planning**: the near-term sprints (up to the next milestone) are detailed with full Stories, acceptance criteria, and Tasks; everything past that horizon is kept **coarse** (a titled placeholder with a one-line goal, no Stories/Tasks yet) plus an ordered backlog. This command creates or replaces the contents of `docs/ROADMAP.json`.

Unlike `sprint init` (which creates a blank template or migrates existing files), this command **generates substantive content** — it designs the development plan's near-term detail and its coarse forward arc.

**Why not detail everything upfront?** Detailed Task breakdowns for far-future sprints are almost always discarded or reworked by the time you reach them (the code and the learnings have moved on), and a complete-looking plan invites plowing ahead on stale detail instead of re-deciding. Detail is elaborated just-in-time at each milestone boundary — the seam where autopilot already stops for user review — from the coarse goal + backlog + current code state. See "Detail horizon" below.

## Prerequisites

- `docs/VISION.json` must exist (provides the "what" and "why")
- `docs/ARCHITECTURE.md` should exist (provides technical context for task breakdown)
- `docs/DESIGN_PRINCIPLES.json` should exist (guides granularity and priority decisions)
- `docs/DESIGN/` is optional but **strongly recommended** for complex systems. When present, its contents shape the Sprint structure.

If VISION.json does not exist, refuse to proceed and suggest running `design start` (for complex systems) or `autopilot setup` (for simpler ones) first.

## Detail horizon (rolling-wave threshold)

The **detail horizon** decides how many sprints are generated in full detail versus kept coarse. There is **no new numeric threshold to tune** — it reuses the existing **Milestone Detection** rules from `../../autopilot/SKILL.md` (checked in order, earliest match wins):

1. an explicit `"milestone": true` sprint,
2. else a dependency boundary (the next sprint starts a new independent track),
3. else the every-3-sprints fallback,
4. else the end of the roadmap.

**Rule: detail the sprints from the start up to and including the first milestone boundary, capped at 3 detailed sprints. Everything beyond the horizon is coarse.**

Consequences:

- **Small project** (≤3 sprints, roadmap ends before any milestone) → the end-of-roadmap boundary comes first → **every sprint is detailed, no coarse tier** → behaviour is identical to the pre-rolling-wave roadmap. Small stays simple, automatically — do not emit a coarse tier or a `detail_level` field in this case.
- **Larger project** → detail the first batch (default 3 sprints, or up to a sooner explicit milestone), and emit the rest as coarse sprints.
- The cap of **3** is not a new magic constant — it is the same number as the every-3-sprints fallback milestone. It bounds upfront detail even when an explicit milestone is placed far out (e.g. a milestone at sprint 7 still only details ~3 sprints; sprints 4–7 stay coarse and are elaborated as you approach them).

Elaboration of a coarse sprint (filling in its Stories/AC/Tasks and flipping `detail_level` to `detailed`) happens later, just-in-time — interactively in `sprint plan`, or autonomously at each autopilot milestone batch. A coarse sprint MUST NOT be run or marked done until elaborated (see `ROADMAP_SCHEMA.json` → `coarse_sprint_constraint`).

## Execution Flow

### 1. Read context

Read the following files:
- `docs/VISION.json` — product goals, target users, scope, constraints
- `docs/ARCHITECTURE.md` — system components, tech stack, data flow (if exists)
- `docs/DESIGN_PRINCIPLES.json` — priority rules, constraints (if exists)
- `docs/DESIGN/system.json` — intended component structure (if exists). When present, this is more authoritative than ARCHITECTURE.md for *planning* purposes (ARCHITECTURE.md describes current code; system.json describes intended design).
- `docs/DESIGN/domain.json` — entity vocabulary (if exists). Use these names in Story descriptions for consistency.
- `docs/DESIGN/non-functional.json` — non-functional targets (if exists). These may require dedicated Stories (perf testing, observability setup).
- `docs/DESIGN/adr/*.json` — accepted ADRs (if exist). Treat as constraints; the roadmap must not produce Sprints that violate accepted ADRs.
- `docs/ROADMAP.json` — check if one already exists (may have backlog items to preserve)

### 2. Design the sprint structure

Based on VISION and ARCHITECTURE, design a roadmap following these principles:

**Sprint ordering** (design the full arc first — titles, goals, dependencies, milestone markers — then split by the detail horizon):
- Start with the smallest deployable increment (MVP). The first Sprint must produce something runnable and demonstrable.
- Build foundation before features (auth, data models, core API before UI polish)
- Group related Stories into the same Sprint (minimize cross-sprint dependencies)
- Place `[MILESTONE]` markers at natural review points (MVP ready, core features complete, etc.). These markers also set the detail horizon (see "Detail horizon" above).

**Detailed vs coarse** (apply the detail horizon):
- Sprints **within the horizon** (start → first milestone, capped at 3) get the full Story + acceptance-criteria + Task treatment below.
- Sprints **beyond the horizon** are emitted **coarse**: `{title, description(one-line goal), milestone, status:"pending", detail_level:"coarse", stories:{}}`. Do NOT invent Stories/AC/Tasks for them — that detail would be discarded before it is reached. Their goal + the backlog are the raw material for later just-in-time elaboration.
- If the whole roadmap fits within the horizon (small project), skip the coarse tier entirely and omit `detail_level` (stays byte-compatible with pre-rolling-wave roadmaps).

**Story design** (detailed sprints only):
- Every Story must be a proper user story: `{役割}として、{やりたいこと}をしたい。なぜなら、{理由}だから。`
- Each Story must be independently deliverable and verifiable
- Include acceptance criteria for every Story
- A Story should be completable within a single sprint (if not, split it)

**Task breakdown** (detailed sprints only):
- Tasks are implementation steps within a Story
- Each Task should be 1-4 hours of work for an AI agent
- Tasks should be specific enough that a sub-agent can execute without ambiguity

**Backlog** (the elaboration input):
- Anything in-scope but past the horizon that isn't yet obviously slotted into a specific coarse sprint goes to the ordered `backlog` as a Story/Epic-sized item. This is the pool later elaboration draws from — not a deferral dump.
- Tag each item with its `kind` (`bug` | `enhancement` | `feature` | `chore`; see `references/ROADMAP_SCHEMA.json` → `backlog_kind`). This records the type/size — a `feature` is Epic-sized and anchors its own sprint, an `enhancement`/`bug`/`chore` is a single Story/fix-Story — so elaboration sizes the item without re-deriving it from the prose. Omit `kind` only for the `enhancement` default.

**Scope control**:
- Only include what is in VISION.json scope
- Anything listed in VISION's "スコープ外" must NOT appear in the roadmap
- If VISION is ambiguous about scope, default to excluding it (add to Backlog instead)

### 3. Generate the roadmap

Write `docs/ROADMAP.json` using the format defined in `references/ROADMAP_SCHEMA.json`. Include:
- Progress section (initial state: all sprints at 0%). `progress.total` counts **all** sprints, coarse included — the percentage is honest about how much un-done work remains; coarse sprints contribute 0% until elaborated and completed.
- Execution order with milestone markers (the `execution_order` array is the source of truth for ordering — IDs themselves are random and unordered). Both detailed and coarse sprints appear here, so the full arc stays visible.
- Detailed sprints (within the detail horizon) with Stories and Tasks; coarse sprints (beyond it) as goal-only placeholders — `detail_level:"coarse"`, `stories:{}`. (Omit the coarse tier and the `detail_level` field entirely for small projects whose whole roadmap fits within the horizon.)
- Dependencies section (coarse sprints may still declare sprint-level `depends_on`)
- Backlog section — the ordered elaboration input (include any items from existing ROADMAP if present, plus in-scope work past the horizon that isn't slotted into a specific coarse sprint)

**Sprint ID generation**: For each new Sprint, generate a random ID with `openssl rand -hex 3` and prepend `S` (e.g., `Sa3f9c2`). Random IDs prevent collisions when multiple worktrees create Sprints in parallel. Verify each generated ID is unique within the roadmap before using it. If migrating from an existing ROADMAP that uses sequential IDs (S001, S002...), keep those IDs unchanged — only generate random IDs for newly created Sprints.

### 4. Present for review

Present the generated roadmap summary to the user:
- Total number of Sprints, and **which are detailed vs coarse** (e.g. "5 sprints total; first 3 detailed, last 2 coarse — the coarse ones get elaborated at the first milestone")
- Sprint titles and milestone markers
- First Sprint's Stories (in detail, since this will execute first)
- Coarse sprints listed by title + one-line goal only (make clear their Stories are intentionally deferred, not forgotten)
- Key design decisions made (e.g., "auth before UI", "API-first approach")

Ask the user to confirm or adjust before writing the file.

**In autonomous mode** (called from `sprint auto` or `autopilot`): Skip user confirmation, write the file directly, and log the roadmap design decisions to `docs/sprint-logs/roadmap-generation.md`.

## Guidelines for Sprint count

"Typical Sprint count" is a **coarse total estimate** for the whole arc. Only the "Detailed now" column is generated in full (Stories/AC/Tasks); the remainder are emitted coarse and elaborated just-in-time.

| Project size | Typical Sprint count (coarse total) | Detailed now (≤ first milestone, cap 3) | First Sprint scope |
|---|---|---|---|
| Small (1 feature, no auth) | 2-3 | all of them (no coarse tier) | Core feature working end-to-end |
| Medium (3-5 features, auth) | 4-7 | first 3 (or to first milestone) | Auth + 1 core feature |
| Large (many features, complex) | 8-15 | first 3 (or to first milestone) | Infrastructure + auth + 1 demo flow |

Prefer fewer, well-scoped Sprints over many granular ones. Each Sprint should deliver visible progress. For Small projects the "coarse total" *is* the detailed count — everything fits within the horizon, so there is no coarse tier and `detail_level` is omitted (identical to a pre-rolling-wave roadmap).
