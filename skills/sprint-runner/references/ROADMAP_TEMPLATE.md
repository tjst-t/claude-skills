# Roadmap Format Specification

This document defines the standard roadmap format used by the sprint-runner skill.

## File Location

Always: `docs/ROADMAP.md` in the project root.

## Structure

```markdown
# Project Roadmap: {Project Name}

> {One-line project description}

## Progress

- Total: 3 Sprints | Done: 1 | In Progress: 1 | Remaining: 1
- [██████░░░░░░░░░░░░░░] 33%

## Execution Order

S001 → S002 → S003
        ↑ current

---

## Sprint S001: {Sprint Title} [DONE]

{Sprint description — what this sprint achieves and why.}

### Story S001-1: {Story Title} [x]

{Story description — the user-facing outcome or capability this story delivers.}

- [x] **Task S001-1-1**: {Task title}
  {Task description — what specifically needs to be implemented.}
- [x] **Task S001-1-2**: {Task title}
  {Task description.}

### Story S001-2: {Story Title} [x]

{Story description.}

- [x] **Task S001-2-1**: {Task title}
  {Task description.}

## Sprint S002: {Sprint Title} [IN PROGRESS]

{Sprint description.}

### Story S002-1: {Story Title} [ ]

{Story description.}

- [x] **Task S002-1-1**: {Task title}
  {Task description.}
- [ ] **Task S002-1-2**: {Task title}
  {Task description.}

## Sprint S003: {Sprint Title} [ ]

{Sprint description.}

### Story S003-1: {Story Title} [ ]

{Story description.}

- [ ] **Task S003-1-1**: {Task title}
  {Task description.}

---

## Dependencies

{Define inter-Sprint dependencies and execution order rationale. The Execution Order section above shows the sequence; this section explains *why*.}

- S003 depends on S002 (Story S002-1 provides the API that Story S003-1 consumes)

---

## Backlog

{Unscheduled items. Ideas, future work, or tasks not yet prioritized into a Sprint. May or may not ever be implemented.}

- [ ] **{Task title}**
  {Description. Include enough context so future-you understands why this was noted.}
- [ ] **{Task title}**
  {Description.}
```

## Sprint IDs

Sprints use sequential IDs in creation order: `S001`, `S002`, `S003`, etc.

- IDs reflect **creation order**, NOT execution order
- Execution order is defined in the **Execution Order** section at the top
- When inserting a new Sprint, assign the next available ID (e.g., if S001–S004 exist, the new Sprint is S005) and place it in the document at the appropriate position in execution order
- Never renumber existing Sprints

Example — inserting a Sprint between S002 and S003:

```markdown
## Execution Order

S001 → S002 → S005 → S003 → S004
                ↑ newly inserted
```

The document order of Sprint sections should match the Execution Order for readability. When inserting S005 between S002 and S003, move the `## Sprint S005` section to appear between them in the file.

## Story and Task IDs

- Story IDs: `{SprintID}-{number}` (e.g., `S002-1`, `S002-2`)
- Task IDs: `{SprintID}-{story}-{task}` (e.g., `S002-1-3`)

Story and Task numbers are sequential within their parent and never change.

## Status Markers

- Sprint level: `[DONE]`, `[IN PROGRESS]`, `[ ]` (not started)
- Story level: `[x]` (complete), `[ ]` (incomplete)
- Task level: `[x]` (complete), `[ ]` (incomplete)

A Story is `[x]` only when ALL its Tasks are `[x]`.
A Sprint is `[DONE]` only when ALL its Stories are `[x]`.

## Progress Section

The Progress section is at the top of the roadmap and is **automatically maintained** by `sprint done` and `sprint plan`. It contains:

1. **Summary line**: count of total, done, in-progress, and remaining Sprints
2. **Progress bar**: visual indicator (using block characters, 20 chars wide)
3. **Execution Order**: the full Sprint sequence with a marker on the current Sprint

Progress percentage = (Done Sprints / Total Sprints) × 100, rounded to nearest integer.

## Rules

1. **Sprint IDs are permanent**: once assigned, never change.
2. **Document order matches Execution Order**: Sprint sections appear in the file in the same order as the Execution Order line. This keeps the file readable top-to-bottom.
3. **Descriptions are mandatory** at every level — Sprint, Story, and Task. A title alone is not enough context for implementation.
4. **Only one Sprint can be `[IN PROGRESS]`** at a time.
5. **Dependencies section** explains the rationale behind the Execution Order. Only include non-obvious relationships.
6. **Backlog** is always the last section. Items here have no Sprint assignment and no ID prefix.
7. **Progress section** is always the first section after the title. Updated automatically; do not edit manually.
