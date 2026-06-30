# sprint idea

Collaboratively turn a new idea or feature request into Stories and add them to the roadmap. This is the entry point for adding new work — whether the roadmap is complete, mid-execution, or during a milestone review.

> Renamed from `sprint propose`. The old name still works as a deprecated alias — `sprint propose` runs this flow and prints a one-line deprecation note ("`sprint propose` is now `sprint idea`"). This command is the routing target for autopilot Review Mode class ③ (out-of-AC new scope).

## When to Use

- User has a new feature idea and wants to discuss it
- Roadmap is complete and the user wants to add more work
- During a milestone review, the user says "I also want X"
- User wants to move a Backlog item into a Sprint

## Flow

### 1. Hear the idea

Let the user describe what they want in their own words. No specific format required — it can be vague ("I want notifications") or specific ("email notifications when a VM goes down, with configurable thresholds").

Ask clarifying questions in a **single batch** (not one at a time):
- Who is this for? (if not obvious from context)
- What's the core behavior? (what does the user see/do?)
- What problem does this solve? (why is it needed?)
- Any constraints? (performance, compatibility, specific tech)

If the user answers "I don't know" to any question, propose a reasonable default based on VISION.json and DESIGN_PRINCIPLES.json.

### 2. Scope check

Read `docs/VISION.json` and check:
- Is this within the defined scope?
- Does it contradict anything in "スコープ外" (out of scope)?

**If in scope**: Proceed to story design.

**If out of scope**: Tell the user:
- "This is currently listed as out of scope in VISION.json. Would you like to update the VISION to include it, or add it to the Backlog for future consideration?"
- If the user wants to update VISION: edit `docs/VISION.json` accordingly, then proceed
- If the user wants to backlog it: add to the Backlog section with a description and stop

### 3. Design Stories

Convert the idea into one or more user stories. For each Story:

1. Write in the standard format: `{役割}として、{やりたいこと}をしたい。なぜなら、{理由}だから。`
2. Define acceptance criteria (concrete, verifiable behaviors)
3. Break into Tasks (implementation steps for sub-agents)
4. Check granularity — each Story should be independently deliverable
5. **Identify touched ADRs**: If `docs/DESIGN/adr/` (or `docs/design/adr/`) exists, list every ADR ID that the Story's implementation will touch (via `affects` field overlap, or by inspection of the components involved). These IDs will be written to `touched_adrs` in `decisions.json` at Sprint plan time, and Guard 7 (ADR conformance grep) will run each touched ADR's `machine_check:` section against the Sprint's diff during verify. Surfacing this at propose time prevents Stories from being scoped without their ADR constraints in mind.

Present the Stories to the user for feedback:
- "Here's how I'd break this down. Does this match what you had in mind?"
- Adjust based on user feedback
- Repeat until the user is satisfied

### 4. Place in roadmap

Read the top-level structure (no Sprint bodies) — see SKILL.md "Roadmap Reading Patterns":
```bash
jq '{progress, execution_order, dependencies, backlog, sprints: (.sprints | map_values({title, status, milestone}))}' docs/ROADMAP.json
```
This is enough to decide placement. If a specific Sprint's body is needed for closer inspection, fetch that Sprint by ID separately. Determine where to insert the new work:

**Analyze dependencies:**
- Does the new work depend on existing Stories/Sprints?
- Do any existing unfinished Stories depend on this new work?
- What's the minimum prerequisite set?

**Placement options (propose to user):**

| Option | When to use |
|--------|-------------|
| **Add to existing unfinished Sprint** | New work is small (1-2 Stories) and related to an existing Sprint's scope |
| **Create a new Sprint** | New work is distinct enough to be its own Sprint (3+ Stories or different concern) |
| **Insert before an existing Sprint** | New work is a prerequisite for planned work |
| **Append at the end** | No dependencies on existing work, can wait |

Present the proposed placement with rationale:
- "I recommend creating a new Sprint (proposed ID `Sd9b2f1`) after `Sc7d2a1` because it depends on the API from `Sc7d2a1` but is independent of `Sb1e4d8`. Here's the updated execution order: `Sa3f9c2` → `Sb1e4d8` → `Sc7d2a1` → **`Sd9b2f1`** → ..."
- Ask the user to confirm or adjust

### 5. Update ROADMAP.json

After the user confirms, apply all changes via in-place `jq` mutations using the named filters in SKILL.md "Writes". Concretely:

1. **Generate Sprint ID** (if creating a new Sprint): `openssl rand -hex 3` prepended with `S`; verify uniqueness with `jq --arg id "$NEW" '.sprints | has($id)' docs/ROADMAP.json` and regenerate on collision.
2. **Add Sprint or Stories**: "Add new Sprint" filter for a whole Sprint, or "Add Task to a Story" / direct `.sprints[$s].stories[$sid] = $story` for appending Stories to an existing Sprint. Story IDs are `{SprintID}-{n}`, Task IDs `{SprintID}-{n}-{m}`.
3. **Execution order**: "Insert into execution_order at index" (use jq's `index` to find a reference Sprint) or "Append to execution_order".
4. **Dependencies**: "Add a dependency" filter when the new work depends on existing Sprints.
5. **Progress recount**: combine "Update progress total" + "Recompute progress counts" in one jq invocation.
6. **Milestone flag**: set with `--arg s "$NEW" '.sprints[$s].milestone = true'` if this creates a review boundary.
7. **Consistency**: if existing Sprint references shifted, re-read `execution_order` and `dependencies` to confirm no dangling refs.

### 6. GUI spec (if applicable)

If the new Stories involve GUI work:
- Follow the GUI spec process in `references/gui-spec.md` to derive scenarios and generate test files
- This follows the same flow as during `sprint plan` (interactive or autonomous depending on context)

### 7. Summary

Present the final state:
- What was added (Stories, Sprints)
- Where in the execution order
- Next steps ("Run `sprint plan` to start the next Sprint, or `autopilot start` to execute autonomously")

## Integration with autopilot

When `sprint idea` is invoked during an autopilot milestone review (the routing target for Review Mode class ③ — out-of-AC new scope):
- The refine → idea → VISION update cycle all happens while autopilot is paused
- After the user finishes, autopilot re-reads ROADMAP.json and continues from the updated state
- New Sprints are automatically included in the next autopilot batch

## Important Behaviors

- **Discussion first, roadmap second**: Don't rush to write ROADMAP.json. Make sure the user is satisfied with the story design before committing to the roadmap.
- **Always check VISION scope**: Every new feature must be reconciled with VISION.json. This prevents scope creep.
- **Preserve existing work**: Never modify completed Sprints. Never reorder in a way that breaks dependencies of in-progress work.
- **Minimal disruption**: Prefer appending new Sprints over reshuffling existing ones. Only insert before existing Sprints when there's a real dependency.
- **Batch questions**: Ask clarifying questions in one message, not one at a time.
