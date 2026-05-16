# autopilot setup

Project setup for autopilot-driven development. Detects whether this is a new project or an existing sprint project and adapts accordingly.

## Detection

First, check what already exists:

- `CLAUDE.md` — project-init already run?
- `docs/ARCHITECTURE.md` — architecture documented?
- `docs/ROADMAP.json` — sprints defined? Any `[IN PROGRESS]` or `[DONE]` sprints?
- `docs/VISION.json` — vision exists?
- `docs/DESIGN_PRINCIPLES.json` — principles exist?
- `docs/DESIGN/` — load-bearing design artifacts (managed by `design` skill) exist?

Based on this, follow the **new project flow** or the **existing project flow**.

### DESIGN/ branching

If `docs/DESIGN/` is present:

- **Both VISION and PRINCIPLES present**: Read them and skip Phase 1's question dialogue entirely — they are already authoritative.
- **VISION or PRINCIPLES missing** (one or both): The `design` skill handles this via its **Backfill mode** — it derives the missing files from DESIGN/ content (ADRs encode tradeoffs that map to priority_rules; system.json + ADRs supply most VISION fields). Invoke `design start` and let it auto-detect Backfill mode. Do NOT proceed with `autopilot setup`'s own question dialogue, and do NOT block the user — `design start` produces the missing files and returns.

---

## New project flow

When `CLAUDE.md` and `docs/ROADMAP.json` do not exist (or ROADMAP has no defined Sprints).

### Phase 1: VISION and DESIGN_PRINCIPLES

**If `docs/DESIGN/` exists and VISION + PRINCIPLES exist** (the `design` skill was already run end-to-end):
- Read `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json` — they are authoritative.
- Skip the question dialogue. Do NOT ask the user to re-confirm fields.
- Continue to Phase 2.

**If `docs/DESIGN/` exists but VISION OR PRINCIPLES is missing**:
- Invoke `design start` via the Skill tool. It auto-detects Backfill mode and derives the missing files from DESIGN/. It will surface only the non-derivable fields to the user.
- After `design start` returns, re-check VISION and PRINCIPLES exist, then continue to Phase 2.

**If `docs/DESIGN/` does not exist**:
- **Recommend the `design` skill first** for any non-trivial system: "This project looks like it would benefit from `design start` to lock load-bearing decisions before implementation. Run `design start`, then come back to `autopilot setup`. Or, if this is a small project, I can ask you a few questions inline now."
- If the user opts for inline (small project) or proceeds without `design`:
  1. Check if `docs/VISION.json` or `docs/DESIGN_PRINCIPLES.json` already exist. If so, read them and ask the user whether to update or overwrite.
  2. Read the templates in `references/vision-template.md` and `references/principles-template.md`.
  3. Ask the user targeted questions to fill in each section (batch questions, don't ask one at a time).
  4. Write `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json`.

### Phase 2: Project initialization

Invoke `/project-init` to generate `CLAUDE.md`, `docs/ARCHITECTURE.md`, and `Makefile`. Since VISION.json now exists, project-init can reference it for better ARCHITECTURE.md generation. If `docs/DESIGN/system.json` exists, project-init should also reference it — it describes the *intended* architecture, while ARCHITECTURE.md captures what the code currently looks like.

### Phase 3: Roadmap generation

Invoke `/sprint roadmap` to generate `docs/ROADMAP.json` from VISION + ARCHITECTURE + (if present) DESIGN/.

- The generated roadmap includes `[MILESTONE]` markers at natural review points.
- If `docs/DESIGN/` exists, the roadmap generation reads `system.json` and ADRs as additional planning input. Stories are aligned to system components, and ADRs constrain implementation choices.

---

## Existing project flow

When `docs/ROADMAP.json` already exists with defined Sprints (typical for projects already using sprint).

### Phase 1: VISION and DESIGN_PRINCIPLES

1. Read the existing codebase, `CLAUDE.md`, `docs/ARCHITECTURE.md`, and `docs/ROADMAP.json` to understand the project context.
2. Read the templates in `references/vision-template.md` and `references/principles-template.md`.
3. Ask the user targeted questions, but **pre-fill answers where possible** from existing documentation:
   - Tech stack → from CLAUDE.md / ARCHITECTURE.md
   - Project purpose → from ROADMAP.json sprint descriptions and README
   - Existing patterns → from codebase conventions already established
4. Write `docs/VISION.json` and `docs/DESIGN_PRINCIPLES.json`.

### Phase 2: Project initialization → Skip

Existing project already has `CLAUDE.md` and `docs/ARCHITECTURE.md`. Skip this phase entirely.

### Phase 3: Roadmap generation → Skip

Existing project already has a populated `docs/ROADMAP.json`. Do NOT regenerate it.

### Phase 4: Alignment check (existing projects only)

1. **VISION ↔ ROADMAP alignment**: Compare the newly created VISION with the existing ROADMAP.
   - Flag any Stories or Sprints that fall outside VISION's scope
   - Flag any VISION goals that have no corresponding Sprint
   - Present findings to the user and ask if adjustments are needed
2. **Milestone injection**: Check if `docs/ROADMAP.json` has `[MILESTONE]` markers.
   - If no milestones exist, propose milestone placements based on the Milestone Detection rules (dependency boundaries, every 3 sprints) and apply them
   - Present proposed milestones to the user for confirmation
3. **ARCHITECTURE.md refresh**: If ARCHITECTURE.md was generated before VISION existed, offer to regenerate it with VISION context for improved accuracy. Ask the user — do not auto-overwrite.

---

## Result

After `autopilot setup` completes, the project is ready for `/autopilot start`. All prerequisites are satisfied:

- `docs/VISION.json` ✓
- `docs/DESIGN_PRINCIPLES.json` ✓
- `docs/DESIGN/` ✓ (optional — recommended for complex systems; populated by the `design` skill)
- `CLAUDE.md` ✓
- `docs/ARCHITECTURE.md` ✓
- `docs/ROADMAP.json` ✓ (with Sprints, Stories, milestones)
