# design help

Help text for `design help`.

```
design — Front-load load-bearing design decisions through guided dialogue.

USAGE
  design start       Interactive design dialogue (3 phases). Produces:
                       docs/VISION.json
                       docs/DESIGN_PRINCIPLES.json
                       docs/DESIGN/domain.json
                       docs/DESIGN/system.json
                       docs/DESIGN/non-functional.json
                       docs/DESIGN/adr/ADR-NNNN-*.json
                       docs/DESIGN/data.json (optional)
  design adr         Add a new ADR after the initial design exists.
  design refresh     Re-read all DESIGN/ docs and surface inconsistencies.
  design status      Show current design state (artifacts, ADR list, open questions).
  design help        Show this help.

WHEN TO USE
  - Starting a new complex project: run `design start` BEFORE `autopilot setup`.
  - During a project: run `design adr` when a load-bearing decision emerges.
  - At a milestone: run `design refresh` to surface drift.

WHAT BELONGS HERE (vs. sprint plan / sprint run)
  IN  : decisions that span Sprints, are non-trivially reversible, or lock contracts.
  OUT : library choices, naming, code style, file layout, sprint-local error handling.

OUTPUT LAYOUT
  docs/VISION.json             — product intent
  docs/DESIGN_PRINCIPLES.json  — judgment rules
  docs/DESIGN/
    ├── domain.json            — entities, relationships, glossary
    ├── system.json            — components, boundaries, key interfaces, data flow
    ├── non-functional.json    — performance/availability/security targets
    ├── data.json              — (optional) schemas, API/event contracts
    └── adr/                   — one file per load-bearing decision

INTEGRATION
  - autopilot setup       reads DESIGN/ and skips VISION/PRINCIPLES question phase
  - sprint roadmap        reads DESIGN/system.json and ADRs as planning input
  - sprint plan           consults DESIGN/adr/ for any ADR affecting upcoming Stories
  - sprint run / auto     autonomous decisions must respect ADRs or escalate
```
