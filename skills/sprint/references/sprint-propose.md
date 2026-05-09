# sprint propose

Collaboratively turn a new idea or feature request into Stories and add them to the roadmap. This is the entry point for adding new work — whether the roadmap is complete, mid-execution, or during a milestone review.

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

After the user confirms:

All updates use in-place `jq` mutations (see SKILL.md "Writes") — never Read or rewrite the whole file.

1. **Generate a Sprint ID if creating a new Sprint.** Run `openssl rand -hex 3` and prepend `S` (e.g., output `a3f9c2` → ID `Sa3f9c2`). Verify uniqueness via `jq --arg id "$NEW" '.sprints | has($id)' docs/ROADMAP.json`; regenerate if `true`.
2. **Add the new Sprint** (if applicable) using the "Add new Sprint" filter:
   ```bash
   jq --arg s "$NEW" --argjson body "$BODY" '.sprints[$s] = $body' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
   ```
   `$BODY` is the full Sprint object (title, description, status: "pending", milestone, stories with their AC and tasks). Story IDs follow `{SprintID}-{number}`, Task IDs follow `{SprintID}-{story_number}-{task_number}`.
   For adding Stories to an existing Sprint, replace just that Sprint's `stories` map (or append individual stories with `--arg s --arg sid --argjson story '.sprints[$s].stories[$sid] = $story'`).
3. **Update execution_order** with the "Insert into execution_order at index" filter (use `index` to find the insertion point relative to a known Sprint), or "Append to execution_order" for end placement.
4. **Update dependencies** with the "Add a dependency" filter:
   ```bash
   jq --arg s "$NEW" --argjson dep '{"depends_on":["..."],"reason":"..."}' '.dependencies[$s] = $dep' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
   ```
5. **Update Progress**: combine "Update progress total" and "Recompute progress counts" filters in one jq invocation:
   ```bash
   jq '
     .progress.total = (.sprints | length)
     | .progress.done = ([.sprints[] | select(.status == "done")] | length)
     | .progress.in_progress = ([.sprints[] | select(.status == "in_progress")] | length)
     | .progress.remaining = (.progress.total - .progress.done - .progress.in_progress)
     | .progress.percentage = (if .progress.total > 0 then (.progress.done * 100 / .progress.total | floor) else 0 end)
   ' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
   ```
6. **Set milestone flag** if the new work creates a natural review boundary: `jq --arg s "$NEW" '.sprints[$s].milestone = true' ...`
7. If any existing Sprint references were shifted, verify consistency by re-reading `execution_order` and the `dependencies` map.

### 6. GUI spec (if applicable)

If the new Stories involve GUI work:
- Invoke `gui-spec` to derive scenarios and generate test files
- This follows the same flow as during `sprint plan` (interactive or autonomous depending on context)

### 7. Summary

Present the final state:
- What was added (Stories, Sprints)
- Where in the execution order
- Next steps ("Run `sprint plan` to start the next Sprint, or `autopilot start` to execute autonomously")

## Integration with autopilot

When `sprint propose` is invoked during an autopilot milestone review:
- The refine → propose → VISION update cycle all happens while autopilot is paused
- After the user finishes proposing, autopilot re-reads ROADMAP.json and continues from the updated state
- New Sprints are automatically included in the next autopilot batch

## Important Behaviors

- **Discussion first, roadmap second**: Don't rush to write ROADMAP.json. Make sure the user is satisfied with the story design before committing to the roadmap.
- **Always check VISION scope**: Every new feature must be reconciled with VISION.json. This prevents scope creep.
- **Preserve existing work**: Never modify completed Sprints. Never reorder in a way that breaks dependencies of in-progress work.
- **Minimal disruption**: Prefer appending new Sprints over reshuffling existing ones. Only insert before existing Sprints when there's a real dependency.
- **Batch questions**: Ask clarifying questions in one message, not one at a time.
