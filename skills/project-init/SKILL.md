---
name: project-init
description: Generates CLAUDE.md, docs/ARCHITECTURE.md, and Makefile for mid-to-large projects. Sets up standardized project documentation and development environment with progressive disclosure.
when_to_use: Use when the user says "project init", asks to set up documentation structure, wants to generate CLAUDE.md, or mentions portman integration. Also triggers on "プロジェクト初期化", "ドキュメント整備", "CLAUDE.md作成". For projects large enough for sprint-based development.
allowed-tools: Read Grep Glob Write Bash(make *) Bash(which *)
---

# Project Init

Sets up standardized project documentation and development environment. Run at the root of a project — new or existing.

## What gets produced

1. `CLAUDE.md` — Layer 1, always-in-context project overview, under ~100 lines (template at `references/CLAUDE_TEMPLATE.md`)
2. `docs/ARCHITECTURE.md` — Layer 2, on-demand system design (template at `references/ARCHITECTURE_TEMPLATE.md`)
3. `Makefile` — `make serve` / `make stop` targets using portman if applicable (details at `references/portman-integration.md`). Also include a `test` (and/or `verify`) target — `sprint verify`'s machine verdict (`run-verify.py`) falls back to `make verify`/`make test`, so this gives the project deterministic, machine-derived test status for free. For per-AC granularity, have that target emit JUnit XML and declare it in `.claude/verify.json` (see `sprint/references/verify-execution.md`).
4. `docs/ROADMAP.json` — blank template via `sprint init` (or skipped if it already exists)

## Command — `project init`

### 1. Scan

Read the project's source code, configs, and existing documentation to understand:

- Language and framework (go.mod, package.json, Cargo.toml, pyproject.toml, etc.)
- Project structure (directory layout, entry points)
- Existing CLAUDE.md, README, docs/ contents
- Existing Makefile targets
- Whether the project has a web server or API (→ portman integration applies)

### 2. Generate `docs/ARCHITECTURE.md`

Read the source code and generate an architecture document following `references/ARCHITECTURE_TEMPLATE.md`. Focus on: what the major components are and how they relate, where the entry points are, how data flows through the system. The goal is for Claude Code to understand the system without reading every source file.

If `docs/ARCHITECTURE.md` already exists, ask the user whether to overwrite, merge, or skip. This is a scope decision, not a routine auto-decision.

If `docs/DESIGN/system.json` exists, also reference it — it describes the *intended* architecture, while ARCHITECTURE.md captures what the code currently looks like.

### 3. Generate or update `CLAUDE.md`

Create or update CLAUDE.md following `references/CLAUDE_TEMPLATE.md`. Always read the template first — it defines the required structure including the References section with pointers to all Layer 2 docs.

If CLAUDE.md already exists, **merge, don't replace**: reorganize existing content into the template structure rather than discarding it. Every piece of information must either appear in the updated version or be explicitly flagged to the user for a decision. Show the user a diff or summary of what changed before writing the file.

### 4. Integrate portman (if applicable)

Only if the project has a web server, API, or dev server. See `references/portman-integration.md` for the full procedure (prerequisites check, pattern selection, Makefile targets, CLAUDE.md updates, .gitignore).

If the project has no server component, skip this step.

### 5. Initialize roadmap

If `docs/ROADMAP.json` already exists, skip. Otherwise, call `sprint init` from the sprint skill to set up a blank template. If the sprint skill is not available, create a blank `docs/ROADMAP.json` manually.

When called from `autopilot setup`, roadmap content generation is handled separately by `sprint roadmap` after project-init completes. project-init only creates the blank template if needed.

### 6. Summary

Present to the user: files created or modified, project structure that was set up, any manual steps still needed (e.g., installing portman).

## Document Hierarchy

```
{project-root}/
├── CLAUDE.md                    # Layer 1: Always in context. Minimal.
└── docs/
    ├── ARCHITECTURE.md          # Layer 2: System design. Read on demand.
    ├── ROADMAP.json             # Layer 2: Sprint tracking. Managed by sprint.
    └── sprint-logs/             # Sprint execution logs. Managed by sprint.
        └── {SprintID}/
```

Layer 1 (CLAUDE.md) should be under ~100 lines. If it's growing beyond that, content should be moved to Layer 2 documents.

## Important Behaviors

- **CLAUDE.md is Layer 1 — every line costs tokens on every interaction**. Only include information Claude Code needs on EVERY task. Everything else goes in `docs/` with a pointer from CLAUDE.md.
- **Merge, don't replace existing CLAUDE.md**. The user has invested in their existing documentation; the goal is to reorganize it into the template structure, not to silently overwrite. Always show a diff or summary before writing.
- **Development rules belong in CLAUDE.md** even though they could go in a separate doc — Claude Code needs them on every coding task.
- **Existing ARCHITECTURE.md overwrite is a scope decision**, not a routine auto-decision. Always ask the user (overwrite / merge / skip).
- **portman is opt-in**. If unavailable and the user skips, fall back to a basic Makefile target — never block the project setup on a missing tool.

## Reference Files

- `references/CLAUDE_TEMPLATE.md` — CLAUDE.md structure and format
- `references/ARCHITECTURE_TEMPLATE.md` — ARCHITECTURE.md structure and format
- `references/portman-integration.md` — portman prerequisites, pattern selection, Makefile targets
