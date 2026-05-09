# sprint roadmap

Generate a full multi-sprint roadmap from VISION.json and ARCHITECTURE.md. This command creates or replaces the contents of `docs/ROADMAP.json` with a complete set of Sprints, Stories, and Tasks.

Unlike `sprint init` (which creates a blank template or migrates existing files), this command **generates substantive content** — it designs the entire development plan.

## Prerequisites

- `docs/VISION.json` must exist (provides the "what" and "why")
- `docs/ARCHITECTURE.md` should exist (provides technical context for task breakdown)
- `docs/DESIGN_PRINCIPLES.json` should exist (guides granularity and priority decisions)

If VISION.json does not exist, refuse to proceed and suggest running `autopilot setup` first.

## Execution Flow

### 1. Read context

Read the following files:
- `docs/VISION.json` — product goals, target users, scope, constraints
- `docs/ARCHITECTURE.md` — system components, tech stack, data flow (if exists)
- `docs/DESIGN_PRINCIPLES.json` — priority rules, constraints (if exists)
- `docs/ROADMAP.json` — check if one already exists (may have backlog items to preserve)

### 2. Design the sprint structure

Based on VISION and ARCHITECTURE, design a roadmap following these principles:

**Sprint ordering**:
- Start with the smallest deployable increment (MVP). The first Sprint must produce something runnable and demonstrable.
- Build foundation before features (auth, data models, core API before UI polish)
- Group related Stories into the same Sprint (minimize cross-sprint dependencies)
- Place `[MILESTONE]` markers at natural review points (MVP ready, core features complete, etc.)

**Story design**:
- Every Story must be a proper user story: `{役割}として、{やりたいこと}をしたい。なぜなら、{理由}だから。`
- Each Story must be independently deliverable and verifiable
- Include acceptance criteria for every Story
- A Story should be completable within a single sprint (if not, split it)

**Task breakdown**:
- Tasks are implementation steps within a Story
- Each Task should be 1-4 hours of work for an AI agent
- Tasks should be specific enough that a sub-agent can execute without ambiguity

**Scope control**:
- Only include what is in VISION.json scope
- Anything listed in VISION's "スコープ外" must NOT appear in the roadmap
- If VISION is ambiguous about scope, default to excluding it (add to Backlog instead)

### 3. Generate the roadmap

Write `docs/ROADMAP.json` using the format defined in `references/ROADMAP_SCHEMA.json`. Include:
- Progress section (initial state: all sprints at 0%)
- Execution order with milestone markers (the `execution_order` array is the source of truth for ordering — IDs themselves are random and unordered)
- All Sprints with Stories and Tasks
- Dependencies section
- Backlog section (include any items from existing ROADMAP if present, plus anything that's in-scope but not yet prioritized)

**Sprint ID generation**: For each new Sprint, generate a random ID with `openssl rand -hex 3` and prepend `S` (e.g., `Sa3f9c2`). Random IDs prevent collisions when multiple worktrees create Sprints in parallel. Verify each generated ID is unique within the roadmap before using it. If migrating from an existing ROADMAP that uses sequential IDs (S001, S002...), keep those IDs unchanged — only generate random IDs for newly created Sprints.

### 4. Present for review

Present the generated roadmap summary to the user:
- Total number of Sprints
- Sprint titles and milestone markers
- First Sprint's Stories (in detail, since this will execute first)
- Key design decisions made (e.g., "auth before UI", "API-first approach")

Ask the user to confirm or adjust before writing the file.

**In autonomous mode** (called from `sprint auto` or `autopilot`): Skip user confirmation, write the file directly, and log the roadmap design decisions to `docs/sprint-logs/roadmap-generation.md`.

## Guidelines for Sprint count

| Project size | Typical Sprint count | First Sprint scope |
|---|---|---|
| Small (1 feature, no auth) | 2-3 | Core feature working end-to-end |
| Medium (3-5 features, auth) | 4-7 | Auth + 1 core feature |
| Large (many features, complex) | 8-15 | Infrastructure + auth + 1 demo flow |

Prefer fewer, well-scoped Sprints over many granular ones. Each Sprint should deliver visible progress.
