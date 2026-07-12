# claude-skills

Reusable [Claude Code](https://code.claude.com/docs/en/overview) skills for standardized project management and the Agile sprint lifecycle.

The model is a **four-layer stack**. You mostly talk to the top layer (`autopilot`); the layers below are the engine.

| Layer | Skill | Responsibility | How often it runs |
|---|---|---|---|
| Design | **design** | Lock load-bearing decisions (VISION, DESIGN_PRINCIPLES, domain/system model, ADRs) | Low — project start, big changes |
| Init | **project-init** | One-time project + docs scaffolding | Once per project |
| Engine | **sprint** | One atomic phase of work (plan / run / verify / done …) | Medium — usually driven by autopilot |
| Orchestrator | **autopilot** | State transitions, looping, branching, milestone review — **the main thing you drive** | High |

They stay separate (not merged) because each works at a different level of abstraction; collapsing them would bloat the SKILL.md files and waste Claude's context.

> `gui-spec` used to be a fifth skill. It is now a reference of `sprint` (`sprint/references/gui-spec.md`), reached only from `sprint plan`.

## The two skills you actually type

Day to day, you mostly say things in natural language and **autopilot** picks them up:

```
進めて / 次のスプリントまで自走して / 機能追加したい / ちょっと直して
```

For a brand-new complex system, you start one layer down with **design**.

## Outward-facing commands

These are the commands meant to be typed directly. Everything else is internal to a layer.

| Command | Role |
|---|---|
| `project init` | Project initial setup (CLAUDE.md, ARCHITECTURE.md, ROADMAP.json) |
| `design start` | Interactive design of load-bearing decisions (complex systems only) |
| `design adr` | Add a new ADR when a load-bearing decision emerges |
| `design refresh` | Check `docs/DESIGN/` for inconsistencies / broken links |
| `design status` | Show design state (artifacts, ADRs, open questions) |
| `autopilot setup` | Create VISION / DESIGN_PRINCIPLES and prerequisites |
| `autopilot start` | **Run autonomously up to the next milestone** (the main operation) |
| `autopilot review` | After a milestone, triage your fix/add requests and route them (idempotent) |
| `autopilot status` | Progress, recent compromises, ADR summary |
| `sprint fix` | One-shot fix, no sprint ceremony (alias: `sprint hotfix`) |
| `sprint idea` | Capture a feature into the backlog (alias: `sprint propose`) |
| `sprint roadmap` | Generate / regenerate the roadmap from VISION + DESIGN/ (rolling-wave: near-term detailed, far-term coarse) |

The remaining sprint phase commands (`plan`, `prototype`, `run`, `verify`, `demo`, `refine`, `done`, `init`, `auto`) still exist for manual / debug use, but they no longer auto-fire on natural language — you invoke them by typing `sprint <command>` explicitly. See **Advanced / debug** below.

## How they work together

1. **`design start`** *(optional, recommended for complex systems)* — guided dialogue from a fuzzy idea to a structured `docs/DESIGN/`: VISION, DESIGN_PRINCIPLES, domain model, system architecture, ADRs, non-functional requirements. Skip it for small projects.
2. **`autopilot setup`** — detects `docs/DESIGN/`. If present, skips its own VISION/PRINCIPLES questions; otherwise asks targeted questions (or routes to `design`). Calls `project init` and `sprint roadmap` as needed. `sprint roadmap` plans **rolling-wave**: sprints up to the first milestone are detailed in full; later sprints are coarse placeholders (title + goal) plus an ordered backlog.
3. **`autopilot start`** — runs Sprints autonomously up to the next milestone, then **stops** for your review. For GUI work it first builds prototypes for you to approve. At each milestone it also **elaborates the next batch** of coarse sprints from the backlog (just-in-time), so far-term detail is written when it's needed, not upfront.
4. **At each milestone** — autopilot writes a `compromises.json` (local concessions it made) and a human-readable `comprehension-report.md` (what changed / why / what to verify / what was assumed). Read the report, then run **`autopilot review`** as many times as you like to triage fixes and additions before continuing.
5. **`design adr`** — add ADRs whenever a load-bearing decision surfaces during planning.

### Safety rails (autonomous runs)

When autopilot runs unattended it never trades correctness for a green run:

- **Forbidden actions** split into *immediate-stop* (AC tampering, destructive git, ADR violation, false `done`) and *notify-after* (test weakening, error swallowing) — the latter are recorded in `compromises.json` and surfaced at the milestone.
- **Machine-derived test status** — `sprint verify` runs the project's declared verification through `hooks/run-verify.py`, which writes the verdict (`verify-run.json`) from real process **exit codes** + JUnit. The model copies that verdict; it can't decide pass/fail by reading output. `sprint done` refuses to complete a Sprint whose machine verdict isn't `pass`. This closes the "record a real failure as pass" hole deterministically and is language-agnostic — declare your command(s) in `.claude/verify.json` (or rely on a `make verify`/`make test` fallback). See `skills/sprint/references/verify-execution.md`.
- **Independent verifier** — `sprint verify` under autopilot runs a *separate* read-only Claude session that re-checks acceptance criteria against real code, reconciles the run logs against the claimed status, scans for forbidden patterns, and confirms ADR conformance. Its `verification-report.json` is the trust source, so the implementing agent can't grade itself leniently.

## Document hierarchy

These skills establish a standard documentation structure optimized for Claude Code's progressive-disclosure pattern:

```
{project-root}/
├── CLAUDE.md                    # Layer 1: Always in context. Minimal tokens.
└── docs/
    ├── VISION.json              # Layer 2: Product intent (design / autopilot setup)
    ├── DESIGN_PRINCIPLES.json   # Layer 2: Judgment rules
    ├── DESIGN/                  # Layer 2: Load-bearing design (managed by design skill)
    │   ├── domain.json          #   Entities, relationships, glossary
    │   ├── system.json          #   Components, boundaries, interfaces
    │   ├── non-functional.json  #   Performance/availability/security targets
    │   ├── data.json            #   (optional) Schemas, API/event contracts
    │   └── adr/                 #   ADR-NNNN-*.json — one per load-bearing decision
    ├── ARCHITECTURE.md          # Layer 2: Auto-generated snapshot of current code
    ├── ROADMAP.json             # Layer 2: Sprint tracking. Managed by sprint
    └── sprint-logs/             # Sprint execution logs
        └── {SprintID}/          #   decisions / verification-results / compromises /
                                 #   comprehension-report / verification-report / reopen …
```

- **Layer 1** (`CLAUDE.md`): loaded on every interaction. Keep under ~100 lines.
- **Layer 2** (`docs/`): read only when needed — architecture, roadmap, design, logs.

## Installation

```bash
ghq get tjst-t/claude-skills
cd $(ghq root)/github.com/tjst-t/claude-skills
chmod +x install.sh
./install.sh
```

This creates symlinks in `~/.claude/skills/` pointing to each skill (and prunes symlinks for skills removed in an upgrade, such as the old `gui-spec`). Claude Code [discovers skills from this directory](https://code.claude.com/docs/en/skills#where-skills-live) automatically across all projects. Restart Claude Code afterward.

The symlink install gives you the **skills**. It does not wire the **hooks** (the L3 forbidden-action guard and the sprint-done documentation suggester) — see `hooks/README.md` to enable those via `settings.json`, or install as a plugin (below) to get both.

### As a plugin (skills + hooks)

This repo is also a Claude Code plugin (`.claude-plugin/plugin.json`). Installing it as a plugin loads the skills **and** wires the hooks automatically. Both hooks are fail-safe and self-gating (the guard activates only during autopilot runs; the suggester only after a sprint-done commit) — see `hooks/README.md` for details and how to disable.

### Verify installation

In a Claude Code session, ask "What skills are available?" — you should see `design`, `project-init`, `sprint`, and `autopilot`.

### Custom install path

```bash
SKILL_DIR=/path/to/skills ./install.sh
```

## Updating

```bash
cd $(ghq root)/github.com/tjst-t/claude-skills
git pull
```

Symlinks mean all projects pick up changes immediately. Re-run `./install.sh` once after an upgrade that removes a skill, so its stale symlink is pruned.

## Usage

### First-time setup — complex system (recommended)

```
design start       # Discuss the idea → docs/DESIGN/, VISION, PRINCIPLES
autopilot setup    # CLAUDE.md, ARCHITECTURE.md, ROADMAP.json (skips VISION qs)
autopilot start    # Run autonomously to the first milestone
```

### First-time setup — simple project

```
autopilot setup    # Asks a few questions inline, then scaffolds
autopilot start
```

(or `project init` alone if you only want the docs/roadmap scaffolding without autonomous execution).

### The main loop

```
autopilot start    # runs to the next milestone, then stops
                   # → read docs/sprint-logs/{SprintID}/comprehension-report.md
autopilot review   # triage fixes/additions (run it as many times as you need)
autopilot start    # continue to the next milestone
```

### Advanced / debug — individual sprint phases

The engine layer is still fully usable when you want manual control. These do **not** auto-fire on natural language; type them explicitly:

```
sprint plan      # plan the next Sprint collaboratively
sprint run       # execute Stories and Tasks
sprint verify    # completeness + /review (add --with-verifier for the independent checker)
sprint done      # finalize, commit, push
sprint fix       # quick fix without ceremony
sprint idea      # capture a new feature into the backlog
sprint roadmap   # (re)generate the roadmap
```

Every sprint command accepts `--auto` (decide-and-proceed instead of stopping to ask). `autopilot` always drives sprint with `--auto`.

## Existing projects

This refactor is backward compatible: existing `ROADMAP.json` / `DESIGN/` / `sprint-logs/` are read as-is, new fields are optional, and nothing is auto-converted or retroactively rewritten. If you are adopting these skills on a project that already has a roadmap, read **[docs/MIGRATION.md](docs/MIGRATION.md)** first.

## Configuration review

Skills, hooks, and prompts accrete cruft as models improve — instructions that compensated for an older model's weakness become dead weight. Review this setup on **two cadences**:

- **Time-driven** — **every 3–6 months, or after a major model release** — the cruft-removal inventory below.
- **Failure-driven** — every sprint / milestone — turning failures and rework into SKILL diffs. This is the job of **[docs/skills-self-audit.md](docs/skills-self-audit.md)**: at each milestone autopilot writes a `skill-retrospective.md` (failure → "which SKILL is defective?" → diff proposal or explicit deferral), and the self-audit is the roll-up that verifies the loop is running, checks the verification net still catches seeded violations (`python3 hooks/tests/test_hooks.py`), and takes proposed SKILL diffs to you for approval. A SKILL that never changes after a failure is the failure mode this guards against — a SKILL can't detect its own staleness.

A quick time-driven inventory pass:

1. **Stale workarounds** — scan the SKILL.md / reference files for guidance that exists only to work around a model limitation that newer models no longer have. Remove it.
2. **Trigger drift** — check each skill's `when_to_use`: is it still firing on the right requests and staying quiet otherwise? Adjust phrases that mis-fire.
3. **Dead references** — confirm every `references/*.md` and schema is still pointed at by its SKILL.md, and every pointer resolves.
4. **Hook noise** — if a hook fires too often or never, retune its gate (see `hooks/README.md`).
5. **Migration doc** — re-read `docs/MIGRATION.md` and update it if any skill spec changed since last review.

## Skill paths in Claude Code

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
