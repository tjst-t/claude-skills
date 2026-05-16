# Roadmap Reading and Writing Patterns

To minimize tokens, sprint commands MUST read only the slice they need from `docs/ROADMAP.json` via `jq` (Bash tool), NOT the whole file via Read. Reading the entire ROADMAP just to look at one Sprint is the single largest source of avoidable token waste.

## Reading patterns

| Pattern | Command | Use cases |
|---|---|---|
| Current Sprint slice | `jq '.sprints[.progress.current_sprint]' docs/ROADMAP.json` | sprint run / verify / demo / refine / done / prototype / auto |
| Sprint by ID | `jq --arg id "<SprintID>" '.sprints[$id]' docs/ROADMAP.json` | targeted lookups (dependencies, history) |
| Top-level structure (no Sprint bodies) | `jq '{progress, execution_order, dependencies, sprints: (.sprints \| map_values({title, status, milestone}))}' docs/ROADMAP.json` | sprint plan (initial scan), sprint propose (placement decision) |
| Backlog only | `jq '.backlog' docs/ROADMAP.json` | backlog operations (sprint hotfix, propose) |
| Single Story | `jq --arg s "<SprintID>" --arg st "<StoryID>" '.sprints[$s].stories[$st]' docs/ROADMAP.json` | single-Story workflows |
| Acceptance criteria of current Sprint | `jq '.sprints[.progress.current_sprint].stories \| to_entries[] \| {story: .key, ac: .value.acceptance_criteria}' docs/ROADMAP.json` | sprint verify Phase 1.5 traceability |
| Whole file (legitimate) | Read tool | sprint init / roadmap only — these rewrite the whole file |

## Write envelope

ALWAYS use in-place `jq` mutation with output redirected to /tmp and moved back. Never Read the whole file just to modify one field, and never echo the full updated JSON back through the Bash output (that would burn tokens equal to the file size). The redirect-and-move envelope means token cost scales with the *size of the change*, not the file.

```bash
jq <FILTER> docs/ROADMAP.json > /tmp/roadmap.json && mv /tmp/roadmap.json docs/ROADMAP.json
```

## Named write filters

Combine multiple with `|` in a single jq invocation when updating several fields atomically.

| Operation | jq filter |
|---|---|
| Mark Sprint status | `--arg s "$SPRINT" '.sprints[$s].status = "done"'` |
| Mark Story status | `--arg s "$SPRINT" --arg st "$STORY" '.sprints[$s].stories[$st].status = "done"'` |
| Mark Task status | `--arg s "$SPRINT" --arg st "$STORY" --arg t "$TASK" '.sprints[$s].stories[$st].tasks[$t].status = "done"'` |
| Mark AC status | `--arg s "$SPRINT" --arg st "$STORY" --arg ac "$AC_ID" '(.sprints[$s].stories[$st].acceptance_criteria[] \| select(.id == $ac)).status \|= "pass"'` |
| Set current Sprint | `--arg s "$SPRINT" '.progress.current_sprint = $s'` |
| Recompute progress counts | `'.progress.done = ([.sprints[] \| select(.status == "done")] \| length) \| .progress.in_progress = ([.sprints[] \| select(.status == "in_progress")] \| length) \| .progress.remaining = (.progress.total - .progress.done - .progress.in_progress) \| .progress.percentage = (if .progress.total > 0 then (.progress.done * 100 / .progress.total \| floor) else 0 end)'` |
| Add new Sprint | `--arg s "$NEW" --argjson body "$BODY_JSON" '.sprints[$s] = $body'` |
| Replace whole Sprint entry | `--arg s "$SPRINT" --argjson new "$NEW_JSON" '.sprints[$s] = $new'` |
| Append to execution_order | `--arg s "$SPRINT" '.execution_order += [$s]'` |
| Insert into execution_order at index | `--arg s "$SPRINT" --argjson i 2 '.execution_order = .execution_order[:$i] + [$s] + .execution_order[$i:]'` |
| Add a dependency | `--arg s "$SPRINT" --argjson dep "$DEP_JSON" '.dependencies[$s] = $dep'` |
| Append to backlog | `--argjson item "$ITEM_JSON" '.backlog += [$item]'` |
| Append AC to a Story | `--arg s "$SPRINT" --arg st "$STORY" --argjson ac "$AC_JSON" '.sprints[$s].stories[$st].acceptance_criteria += [$ac]'` |
| Add Task to a Story | `--arg s "$SPRINT" --arg st "$STORY" --arg tid "$TASK_ID" --argjson task "$TASK_JSON" '.sprints[$s].stories[$st].tasks[$tid] = $task'` |
| Update progress total (when adding/removing Sprints) | `'.progress.total = (.sprints \| length)'` |
| Increment Progress total | `'.progress.total += 1'` |

## Combined example

Mark Sprint+Stories+Tasks done and recompute progress in one shot:

```bash
SPRINT="Sb1e4d8"
jq --arg s "$SPRINT" '
  .sprints[$s].status = "done"
  | .sprints[$s].stories |= map_values(.status = "done" | .tasks |= map_values(.status = "done"))
  | .progress.done = ([.sprints[] | select(.status == "done")] | length)
  | .progress.in_progress = ([.sprints[] | select(.status == "in_progress")] | length)
  | .progress.remaining = (.progress.total - .progress.done - .progress.in_progress)
  | .progress.percentage = (if .progress.total > 0 then (.progress.done * 100 / .progress.total | floor) else 0 end)
' docs/ROADMAP.json > /tmp/roadmap.json && mv /tmp/roadmap.json docs/ROADMAP.json
```

## Passing JSON values

When passing JSON values as arguments, prefer single-quoted heredocs or shell vars to avoid escaping headaches:

```bash
ITEM=$(cat <<'EOF'
{"title":"Refactor X","description":"...","added_in":"hotfix","reason":"User request","status":"done"}
EOF
)
jq --argjson item "$ITEM" '.backlog += [$item]' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
```

## Interpretation

When a reference file says "Read `docs/ROADMAP.json`", interpret it as "Read the relevant slice via the appropriate Reading Pattern above". When it says "update ROADMAP.json", use the appropriate Write filter above.
