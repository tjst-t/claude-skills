---
name: project-init
description: Generates CLAUDE.md, docs/ARCHITECTURE.md, and Makefile for mid-to-large projects. Sets up standardized project documentation and development environment with progressive disclosure.
when_to_use: Use when the user says "project init", asks to set up documentation structure, wants to generate CLAUDE.md, or mentions portman integration. Also triggers on "プロジェクト初期化", "ドキュメント整備", "CLAUDE.md作成". For projects large enough for sprint-based development.
allowed-tools: Read Grep Glob Write Bash(make *) Bash(which *)
---

# Project Init

Sets up standardized project documentation and development environment.

## What It Does

1. Generates `CLAUDE.md` with progressive disclosure pattern (minimal tokens)
2. Auto-generates `docs/ARCHITECTURE.md` by reading the project source
3. Integrates portman (port-manager) for dev server startup
4. Calls `sprint init` from the sprint skill to set up `docs/ROADMAP.md`

## Command

### `project init`

Run at the root of a project. Can be run on new or existing projects.

#### Step 1: Scan the Project

Read the project's source code, configs, and any existing documentation to understand:
- Language and framework (go.mod, package.json, Cargo.toml, pyproject.toml, etc.)
- Project structure (directory layout, entry points)
- Existing CLAUDE.md, README, docs/ contents
- Existing Makefile targets
- Whether the project has a web server or API that needs portman

#### Step 2: Generate `docs/ARCHITECTURE.md`

Read the source code and generate an architecture document. See `references/ARCHITECTURE_TEMPLATE.md` for the format.

If `docs/ARCHITECTURE.md` already exists, ask the user whether to overwrite, merge, or skip. This is a scope decision (existing documentation may contain intentional content), not a routine auto-decision.

The goal is for Claude Code to understand the system without reading every source file. Focus on:
- What the major components are and how they relate
- Where the entry points are
- How data flows through the system

Keep it concise. This document will be read by Claude Code on demand (Layer 2), so it should be information-dense without filler.

#### Step 3: Generate or Update `CLAUDE.md`

Create or update CLAUDE.md following the template in `references/CLAUDE_TEMPLATE.md`. Always read the template first — it defines the required structure including the References section with pointers to all Layer 2 docs.

Key principles:
- CLAUDE.md is always in context (Layer 1), so every line costs tokens on every interaction
- Only include information Claude Code needs on EVERY task
- Everything else goes in docs/ with a pointer from CLAUDE.md
- Development rules and coding conventions belong in CLAUDE.md (frequently referenced)

If CLAUDE.md already exists:
- Read the existing CLAUDE.md in its entirety first
- Read `references/CLAUDE_TEMPLATE.md` and use it as the target structure
- **Merge, don't replace**: the goal is to reorganize existing content into the template structure, not to discard it. Every piece of information in the existing CLAUDE.md must either appear in the updated version or be explicitly flagged to the user for a decision.
- Existing content that fits a template section (e.g., existing dev rules → Development Rules) should be moved there
- Existing content that doesn't fit any template section should be kept in a project-specific section rather than silently dropped
- Show the user a diff or summary of what changed, what was added, and what was reorganized. Ask the user to confirm before writing the file.

#### Step 4: Integrate portman (optional)

Only if the project has a web server, API, or dev server:

1. Check if `portman` is available (`which portman`). If not installed:
   - Warn the user: "portman is not installed. You can install it from https://github.com/tjst-t/port-manager or skip this step."
   - If the user chooses to skip, create a basic `make serve` target without portman (direct process launch) and continue.
2. Check if a Makefile exists; create one if not
3. Add `make serve` target using portman
4. For the correct portman pattern, try to fetch the guide at:
   https://raw.githubusercontent.com/tjst-t/port-manager/main/docs/CLAUDE_INTEGRATION.md
   If the fetch fails (network error, 404, etc.), fall back to **Pattern 6 (background + PID file)** with this template:
   ```makefile
   serve:
   	@portman acquire --name $(PROJECT_NAME) --pid-file .server.pid -- \
   		$(START_COMMAND)
   stop:
   	@portman release --name $(PROJECT_NAME) --pid-file .server.pid
   ```
5. Use **Pattern 6 (background + PID file)** as the default for Claude Code compatibility
6. Add the server startup section to CLAUDE.md
7. Add `.env` to `.gitignore` if not already present

If the project has no server component, skip this step entirely.

If the project has multiple services (e.g., API + frontend), create separate Makefile targets (`make serve`, `make serve-frontend`, etc.).

#### Step 5: Initialize Roadmap

1. If `docs/ROADMAP.md` already exists, skip this step (it may have been or will be generated by `sprint roadmap`).
2. Otherwise, call `sprint init` from the sprint skill to set up a blank `docs/ROADMAP.md`.
3. If the sprint skill is not available, create `docs/ROADMAP.md` manually with a blank template.

> **Note**: When called from `autopilot setup`, roadmap content generation is handled separately by `sprint roadmap` after project-init completes. project-init only creates the blank template if needed.

#### Step 6: Summary

Present to the user:
- What files were created or modified
- The project structure that was set up
- Any manual steps the user needs to take (e.g., installing portman if not present)

## Document Hierarchy

```
{project-root}/
├── CLAUDE.md                    # Layer 1: Always in context. Minimal.
└── docs/
    ├── ARCHITECTURE.md          # Layer 2: System design. Read on demand.
    ├── ROADMAP.md               # Layer 2: Sprint tracking. Managed by sprint.
    └── sprint-logs/             # Sprint execution logs. Managed by sprint.
        └── {SprintID}/
```

Layer 1 (CLAUDE.md) should be under ~100 lines. If it's growing beyond that, content should be moved to Layer 2 documents.

## Templates

- `references/CLAUDE_TEMPLATE.md` — CLAUDE.md structure and format
- `references/ARCHITECTURE_TEMPLATE.md` — ARCHITECTURE.md structure and format
