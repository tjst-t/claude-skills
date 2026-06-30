---
name: design
description: Front-loads architectural design for complex systems. Guides a user from a fuzzy idea through dialogue to a structured set of design documents (VISION, DESIGN_PRINCIPLES, domain model, system architecture, ADRs, non-functional requirements) before implementation begins. The output feeds autopilot setup and sprint planning.
when_to_use: Use ONLY when load-bearing decisions must be settled — decisions that span multiple Sprints, are non-trivially reversible, lock a contract others depend on, or carry a real trade-off. Triggers on an explicit `design <command>` (design start / adr / refresh / status), or on complexity-signaling requests: "複雑な", "本格的な", "load-bearing", "アーキテクチャを固めたい", "設計判断", "ADR", "複数 Sprint にまたがる設計", "complex system design". Does NOT trigger on light "アプリ作りたい" / "アイデアある" / "新規プロジェクト" — those go to autopilot or sprint. Run BEFORE `autopilot setup` for non-trivial systems.
allowed-tools: Read Grep Glob Write Bash(jq *) Bash(openssl rand *) Bash(mkdir *) Bash(ls *)
---

# Design

Front-loads **load-bearing** design decisions for complex systems through guided dialogue. Produces VISION, DESIGN_PRINCIPLES, and a `docs/DESIGN/` set of architectural artifacts that sprint and autopilot read as authority.

## Philosophy

The sprint/autopilot workflow defers technical decisions to implementation time. That is correct for **reversible, locally-scoped** decisions. For complex systems (hydra-class) it breaks down: cross-cutting and irreversible decisions made locally cause drift, integration pain, and expensive rework.

This skill identifies and locks the **load-bearing** decisions before implementation starts. It deliberately does NOT decide reversible things (library choice, naming, file layout) — those stay autonomous in `sprint run`.

## Scope discriminator

A decision belongs in this skill if ANY of:

- It spans multiple Sprints (changing it later touches >1 Sprint)
- It is non-trivially reversible (migration cost is meaningful)
- It locks a contract other parts will rely on (data model, API, protocol, domain boundary)
- It has a real trade-off between viable alternatives

If none of the above hold, the decision belongs in `sprint plan` or `sprint run`, not here.

| In | Out |
|---|---|
| Product intent (VISION) | Library selection |
| Judgment rules (DESIGN_PRINCIPLES) | Code style, naming, file layout |
| Domain model (entities, relationships, glossary) | Sprint-local error handling |
| System architecture (components, boundaries, key interfaces, data flow) | Test framework choice |
| Non-functional requirements (perf, consistency, security targets) | Single-Sprint local design |
| Load-bearing decisions (ADR) | Reversible per-Story decisions |
| Data model / protocol contracts (when stateful/distributed) | UI micro-copy |

## Commands

| Command | Purpose |
|---|---|
| `design start` | Interactive design dialogue (3 phases). Produces all artifacts. |
| `design adr` | Add a new ADR when a load-bearing decision emerges later |
| `design refresh` | Re-read all DESIGN/ docs and find inconsistencies or stale items |
| `design status` | Show design state (artifacts present, ADR list, open questions) |
| `design help` | Command list |

When a command is invoked, read the corresponding reference file before taking any action.

## Output layout

```
docs/
├── VISION.json                      # Product intent (autopilot schema)
├── DESIGN_PRINCIPLES.json           # Judgment rules (autopilot schema)
└── DESIGN/
    ├── domain.json                  # Entities, relationships, glossary
    ├── system.json                  # Components, boundaries, key interfaces, data flow
    ├── non-functional.json          # Performance/availability/security targets
    ├── data.json                    # (optional) Schema / protocol contracts
    └── adr/
        ├── ADR-0001-{kebab-title}.json
        ├── ADR-0002-{kebab-title}.json
        └── ...
```

All files are JSON for the same reasons ROADMAP.json is JSON: machine-readable, easy to slice with `jq`, integrates with the rest of the toolchain.

## `design start`

A three-phase dialogue: **発散 (Divergence)** → **収束 (Convergence)** → **構造化 (Structuring)**. The full prompt set, exit signals, and per-phase patterns live in `references/design-flow.md`. Read it before starting.

Before Phase 1, detect existing state and pick the mode:

```bash
have_vision=$([ -f docs/VISION.json ] && echo 1 || echo 0)
have_principles=$([ -f docs/DESIGN_PRINCIPLES.json ] && echo 1 || echo 0)
have_design_dir=$([ -d docs/DESIGN ] && [ -n "$(ls -A docs/DESIGN 2>/dev/null)" ] && echo 1 || echo 0)
```

| Mode | Trigger | Behavior |
|---|---|---|
| **Fresh** | no VISION, no PRINCIPLES, no DESIGN/ | Full Phase 1 → 2 → 3 |
| **Backfill** | DESIGN/ exists, VISION OR PRINCIPLES missing | Skip Phase 1. Derive missing files from DESIGN/ per `design-flow.md` "Backfill mode", ask only for non-derivable fields, write missing files only |
| **Update** | VISION exists, DESIGN/ absent or partial | Read VISION/PRINCIPLES as context. Run shortened Phase 1 (only gaps), then Phase 3 for missing DESIGN/ artifacts |
| **All present** | VISION, PRINCIPLES, DESIGN/ all exist | Stop and route the user to `design refresh` or `design adr`. Confirm before anything destructive |

State the detected mode to the user before proceeding, so they can correct if it's wrong.

### Output layout (Fresh / Update modes write some/all of these)

```
docs/
├── VISION.json                      references/VISION_SCHEMA.json
├── DESIGN_PRINCIPLES.json           references/DESIGN_PRINCIPLES_SCHEMA.json
└── DESIGN/
    ├── domain.json                  references/DOMAIN_SCHEMA.json
    ├── system.json                  references/SYSTEM_SCHEMA.json
    ├── non-functional.json          references/NON_FUNCTIONAL_SCHEMA.json
    ├── data.json (optional)         references/DATA_SCHEMA.json
    └── adr/
        └── ADR-NNNN-{kebab-title}.json   references/ADR_SCHEMA.json
```

All files are JSON for the same reasons ROADMAP.json is JSON: machine-readable, easy to slice with `jq`, integrates with the rest of the toolchain.

Generate artifacts in dependency order (VISION → PRINCIPLES → domain → system → non-functional → ADRs → data). Present each draft to the user for confirmation before writing. For each load-bearing decision surfaced during Phase 2, walk through context / alternatives / decision / consequences / reversibility cost — see `references/adr-template.md` for the heuristic on what warrants an ADR.

## `design adr`

Add a single new ADR after the initial design is established. Typical trigger: a load-bearing decision emerges during `sprint plan`.

1. Compute next ADR number: `ls docs/DESIGN/adr/ 2>/dev/null | grep -oE '^ADR-[0-9]+' | sort -V | tail -1 | sed 's/ADR-0*//'` (treat empty as 0), then +1.
2. Ask the user: title, context, alternatives, decision, consequences, reversibility cost.
3. Write `docs/DESIGN/adr/ADR-{NNNN}-{kebab-title}.json` per `references/ADR_SCHEMA.json`.
4. If the ADR contradicts an existing one, prompt: "Should ADR-XXXX be marked superseded?"

## `design refresh`

Read all `docs/DESIGN/*.json` and the ADR set. Report (do NOT auto-fix):

- ADRs whose Decision conflicts with another ADR
- ADRs marked `tentative: true` that haven't been resolved
- References to entities/components in ADRs that don't exist in domain.json/system.json (broken links)
- Non-functional targets not referenced by any ADR (possibly orphaned)

## `design status`

Read `docs/DESIGN/` and present a one-screen view: artifact presence, ADR counts by status, open questions (from `tentative: true` items). See `references/design-help.md` for the exact format.

## Important behaviors

- **Front-load, don't over-design**: Only put decisions in DESIGN/ that meet the scope discriminator. Anything not meeting it stays in sprint plan/run.
- **Dialogue first, structure last**: Phase 1 is conversation, not a questionnaire. The structured artifacts come at Phase 3.
- **Always confirm before writing**: Each artifact gets a draft presented to the user. The user has veto power on every file.
- **ADRs are append-only**: Never edit an accepted ADR to change its meaning. Supersede it with a new ADR that references the old one.
- **JSON for tooling, prose where it matters**: Schemas are JSON, but `context` / `decision` / `consequences` fields are free-form prose. The point is to write down *reasoning*, not fill in cells.
- **Reversibility cost is a first-class field**: Every ADR records this. It's how future Claude (and the user) decides whether to revisit a decision.
- **Living documents**: `design refresh` is meant to be run periodically — at every milestone in autopilot, or whenever the architecture feels off.

## Connection to sprint and autopilot

- **autopilot setup**: When invoked, detects existing `docs/DESIGN/`. If present, skip the VISION/PRINCIPLES question phase (they're already authoritative). `sprint roadmap` reads `docs/DESIGN/system.json` and ADRs as additional context when generating Sprints.
- **sprint plan**: First step is now to consult `docs/DESIGN/adr/` for any ADR whose `affects` field overlaps with the upcoming Sprint's Stories. Surfaced ADRs are read in full and treated as constraints. Decisions in the Sprint plan that contradict an ADR must either (a) revise the Sprint plan, or (b) be escalated to the user as an ADR amendment.
- **sprint run / sprint auto**: When making an autonomous technical decision, check whether it touches anything in DESIGN/. If yes, the decision must respect the ADR or escalate. If no, proceed and log to `decisions.json` as before.
- **decisions.json**: Each entry should include an optional `adr_ref` field pointing to the ADR(s) the decision is based on, or `"none"` if it's a sprint-local decision.

### ADR-necessity auto-check during `sprint plan`

During `sprint plan` / `sprint idea`, Claude must actively watch for a load-bearing decision surfacing without a covering ADR. The signals that should prompt an `"ADR が必要では？"` suggestion to the user are in `references/adr-template.md` → **"Signals that an ADR is required"**. If any signal fires and no existing ADR covers it, suggest `design adr` *before* `sprint run` starts. If no signal fires, the decision stays autonomous and is logged to `decisions.json` only.

### `autopilot review` ④ direction-change handoff

When `autopilot review` classifies a user request as **④ direction change** (see `autopilot/SKILL.md` → Review Mode) AND `docs/DESIGN/` exists, it hands off to this skill in a fixed order:

1. `autopilot review` calls **`design refresh`** internally to check consistency — existing-ADR contradictions and broken links (entities/components that the change would orphan).
2. The impact (which ADRs conflict, what would break) is presented to the user.
3. On approval, **`design adr`** adds a new ADR or supersedes an existing one (ADRs are append-only — never edit an accepted ADR's meaning).
4. Finally `sprint roadmap` is re-run so downstream Sprints reflect the new decision.

If `docs/DESIGN/` does NOT exist, ④ skips this handoff and `autopilot review` re-runs `sprint roadmap` directly. This skill and `autopilot review` are not mutually exclusive — on ④ they compose, with `autopilot review` as the caller.

## Reference files

- `references/design-flow.md` — Phase 1/2/3 dialogue patterns, sample prompts, and "when to move to next phase" heuristics
- `references/domain-template.md` — Domain model template and writing guide
- `references/system-template.md` — System architecture template and writing guide
- `references/adr-template.md` — ADR template, identification heuristics, "what does and does not warrant an ADR"
- `references/non-functional-template.md` — Non-functional requirements template
- `references/data-template.md` — Data / protocol design template (used when applicable)
- `references/VISION_SCHEMA.json` — VISION.json schema and example. **Owned here** — `design` is the authority that generates VISION; `autopilot setup` reads this schema for its inline (simpler) VISION generation.
- `references/DESIGN_PRINCIPLES_SCHEMA.json` — DESIGN_PRINCIPLES.json schema and example. **Owned here** for the same reason.
- `references/DOMAIN_SCHEMA.json` — Domain JSON schema and example
- `references/SYSTEM_SCHEMA.json` — System JSON schema and example
- `references/ADR_SCHEMA.json` — ADR JSON schema and example
- `references/NON_FUNCTIONAL_SCHEMA.json` — Non-functional JSON schema and example
- `references/DATA_SCHEMA.json` — Data / protocol JSON schema and example
- `references/design-help.md` — Help text shown by `design help`
