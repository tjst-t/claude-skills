# sprint prototype

Generate a clickable HTML prototype of all GUI Stories up to the next milestone. The user reviews and approves the design before implementation begins, preventing costly rework.

## When to Use

- After `sprint plan` / `gui-spec`, before `sprint run`
- In autopilot: automatically runs after pre-flight, before the sprint loop
- Can be invoked standalone: `/sprint prototype`

## Prerequisites

- `docs/ROADMAP.json` must exist with GUI Stories identified
- gui-spec should have been run (state diagrams and scenarios inform the prototype)

## Flow

### 1. Identify GUI scope

1. Read `docs/ROADMAP.json`
2. Determine the scope:
   - If called from autopilot: collect all GUI Stories from the current Sprint up to the next milestone
   - If called standalone: collect GUI Stories from the current Sprint only
3. For each GUI Story, read the gui-spec file (`docs/sprint-logs/{SprintID}/gui-spec-{StoryID}.json`) if it exists — use scenarios, state diagrams, and endpoint contracts to inform the prototype
4. If no GUI Stories exist in scope, skip and return immediately

### 2. Generate prototype

Generate static HTML files in `prototype/` at the project root. Use the `/frontend-design` skill for high design quality.

**Structure:**
```
prototype/
├── index.html          # Entry point — links to all screens
├── {screen-name}.html  # One file per screen/page
├── styles.css          # Shared styles (or inline — keep it simple)
└── assets/             # Images, icons if needed
```

**Requirements:**
- **Hardcoded data** — no API calls, no JavaScript fetch. Use realistic sample data that matches the endpoint contracts from gui-spec.
- **Page navigation works** — links between pages use relative paths (`href="dashboard.html"`)
- **Layout and styling match production intent** — use the project's design system if one exists (check DESIGN_PRINCIPLES.json for UI/UX guidelines, design references). If no design system, use clean, modern defaults.
- **All UI states represented** — for each screen, show the primary state. If the gui-spec identified important states (empty, error), create separate HTML files: `{screen-name}.html`, `{screen-name}-empty.html`, `{screen-name}-error.html`
- **Interactive elements are visible** — buttons, forms, inputs should be present and styled. They don't need to function (no JS handlers required) but should look correct.
- **data-testid attributes included** — add `data-testid` to all interactive elements, matching what the Playwright tests will expect. This ensures the prototype and tests are aligned.
- **Responsive** — use responsive CSS so the prototype looks reasonable on different screen sizes

**What NOT to include:**
- No build tools (no npm, no bundler)
- No frameworks (no React, no Vue) — plain HTML/CSS only
- No backend calls
- No complex JavaScript (simple show/hide toggles are OK)

### 3. User review

Present the prototype to the user:
- "Prototype generated in `prototype/`. Please open the files to review."
- List all generated screens with brief descriptions
- Highlight key design decisions made

Then enter a **refinement loop** (same pattern as `sprint refine`):
1. User views the prototype and provides feedback
2. Fix the HTML/CSS immediately
3. User re-checks
4. Repeat until the user approves

### 4. Commit approved prototype

After user approval:
1. Commit the prototype: `feat: approved GUI prototype for {Sprint range}`
2. Log the approval to `docs/sprint-logs/{SprintID}/prototype-review.json`:

```json
{
  "sprint_range": ["Sc7d2a1", "Sd9b2f1", "Se8a4c3"],
  "screens": [
    {
      "file": "prototype/dashboard.html",
      "story": "Sc7d2a1-1",
      "feedback_rounds": 2,
      "approved": true
    }
  ],
  "design_decisions": [
    "Sidebar navigation instead of top nav — per DESIGN_PRINCIPLES",
    "Blue primary color — per VISION design references"
  ]
}
```

### 5. Inform implementation

The approved prototype serves as the design reference for sprint run:
- Implementation sub-agents receive the prototype path in their prompt
- Instruction: "Match the layout, styling, and element structure of `prototype/{screen}.html`. Use `data-testid` attributes exactly as they appear in the prototype."
- The prototype is the visual source of truth — if there's ambiguity in the Story description, the prototype wins

## Autonomous Mode

When called from autopilot (no user present for review):
- Generate the prototype but **stop for user review** — this is an inherently interactive phase
- autopilot pauses and presents the prototype to the user
- This is one of the few phases where autopilot requires user interaction (along with milestone demo/refine)

## Important Behaviors

- **Plain HTML only**: No build tools, no frameworks, no npm. The prototype must be viewable by opening the HTML file directly.
- **Realistic data**: Use sample data that matches the endpoint contract tables from gui-spec. Don't use "Lorem ipsum" for data fields — use plausible values.
- **data-testid alignment**: The prototype establishes the `data-testid` contract. Implementation and Playwright tests must match these.
- **Prototype is a design reference, not production code**: The `prototype/` directory is not deployed. Once a Sprint completes, its prototype files are archived to `prototype/old/{SprintID}/` by `sprint done` (see `sprint-done.md`). This keeps the top of `prototype/` focused on screens still pending implementation, while preserving past designs as a viewable reference.
- **Design quality matters**: Use `/frontend-design` skill. The prototype should look like a real product, not a wireframe. This is what the user is approving.
