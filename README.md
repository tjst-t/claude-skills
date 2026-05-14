# claude-skills

Reusable [Claude Code](https://code.claude.com/docs/en/overview) skills for standardized project management and sprint lifecycle.

## Skills

| Skill | Purpose | Trigger |
|---|---|---|
| **design** | Front-load load-bearing architectural decisions through dialogue | `design start`, `design adr` |
| **project-init** | Project documentation & environment setup | `project init` |
| **sprint** | Agile Sprint lifecycle management | `sprint plan`, `sprint run`, `sprint verify`, `sprint done` |
| **autopilot** | Multi-sprint autonomous execution | `autopilot start`, `autopilot setup` |
| **gui-spec** | Derive GUI scenarios and Playwright tests from UI Stories | invoked by `sprint plan` |

## How They Work Together

1. **`design start`** — (Optional, recommended for complex systems.) Run first. Guided dialogue from fuzzy idea to a structured `docs/DESIGN/` set: VISION, DESIGN_PRINCIPLES, domain model, system architecture, ADRs, non-functional requirements.
2. **`autopilot setup`** — Detects `docs/DESIGN/`. If present, skips its VISION/PRINCIPLES question phase. Otherwise asks targeted questions to create them.
3. **`project init`** — Run once at project start. Generates `CLAUDE.md`, `docs/ARCHITECTURE.md`, integrates portman, and calls `sprint init` to create `docs/ROADMAP.json`.
4. **`sprint plan` → `sprint run` → `sprint verify` → `sprint done`** — Repeat each Sprint. `sprint plan` consults `docs/DESIGN/adr/` for any ADR affecting upcoming Stories.
5. **`design adr`** — Add new ADRs when load-bearing decisions emerge during sprint planning.

## Document Hierarchy

These skills establish a standard documentation structure optimized for Claude Code's progressive disclosure pattern:

```
{project-root}/
├── CLAUDE.md                    # Layer 1: Always in context. Minimal tokens.
└── docs/
    ├── VISION.json              # Layer 2: Product intent (design / autopilot setup).
    ├── DESIGN_PRINCIPLES.json   # Layer 2: Judgment rules.
    ├── DESIGN/                  # Layer 2: Load-bearing design (managed by design skill)
    │   ├── domain.json          #   Entities, relationships, glossary
    │   ├── system.json          #   Components, boundaries, interfaces
    │   ├── non-functional.json  #   Performance/availability/security targets
    │   ├── data.json            #   (optional) Schemas, API/event contracts
    │   └── adr/                 #   ADR-NNNN-*.json — one per load-bearing decision
    ├── ARCHITECTURE.md          # Layer 2: Auto-generated snapshot of current code.
    ├── ROADMAP.json             # Layer 2: Sprint tracking. Managed by sprint.
    └── sprint-logs/             # Sprint execution logs.
        └── {SprintID}/
```

- **Layer 1** (`CLAUDE.md`): Loaded on every interaction. Keep under ~100 lines. Contains tech stack, commands, dev rules, and pointers to Layer 2.
- **Layer 2** (`docs/*.md`): Read by Claude Code only when needed. Architecture, roadmap, and other reference docs.
- **Layer 3** (`docs/*.md`): Project-specific docs added as needed. Flat in `docs/`, no subdirectories.

## Installation

```bash
ghq get tjst-t/claude-skills
cd $(ghq root)/github.com/tjst-t/claude-skills
chmod +x install.sh
./install.sh
```

This creates symlinks in `~/.claude/skills/` pointing to each skill. Claude Code [discovers skills from this directory](https://code.claude.com/docs/en/skills#where-skills-live) automatically across all projects.

After installation, restart Claude Code to pick up the new skills.

### Verify installation

In a Claude Code session:

```
What skills are available?
```

You should see `design`, `project-init`, `sprint`, `autopilot`, and `gui-spec` in the list.

### Custom install path

```bash
SKILL_DIR=/path/to/skills ./install.sh
```

## Updating

```bash
cd $(ghq root)/github.com/tjst-t/claude-skills
git pull
```

Symlinks ensure all projects pick up changes immediately. No reinstall needed.

## Usage

### First-time project setup (complex system — recommended)

```
design start       # Discuss the idea, produce docs/DESIGN/, VISION, PRINCIPLES
autopilot setup    # CLAUDE.md, ARCHITECTURE.md, ROADMAP.json (skips VISION ?qs)
autopilot start    # Begin autonomous execution
```

### First-time project setup (simple project)

```
project init
```

This scans the project, generates documentation, integrates portman (if applicable), and initializes the sprint roadmap.

### Sprint workflow

```
sprint plan      # Review next Sprint, discuss design decisions
sprint run       # Execute all Stories and Tasks
sprint verify    # Verify completeness, run /review, fix issues
sprint done      # Update roadmap, summarize achievements
```

### Roadmap management

```
sprint init      # Initialize or migrate roadmap (also called by project init)
```

Sprints use permanent IDs (S001, S002, ...) assigned in creation order. Execution order is defined separately, so inserting a Sprint never requires renumbering.

## Skill paths in Claude Code

Claude Code discovers skills from these locations ([docs](https://code.claude.com/docs/en/skills#where-skills-live)):

| Location | Path | Scope |
|---|---|---|
| Personal | `~/.claude/skills/` | All your projects |
| Project | `.claude/skills/` | That project only |
| Enterprise | Managed settings | Organization-wide |

This repository installs to the **Personal** location by default.

## Requirements

- [Claude Code](https://code.claude.com/docs/en/overview)
- [portman](https://github.com/tjst-t/port-manager) (optional, for dev server management)

## License

MIT
