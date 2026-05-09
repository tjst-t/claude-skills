---
name: sprint
description: Manages Agile Sprint lifecycle — plan, prototype, run, verify, demo, refine, done. Generates roadmaps, executes sprints autonomously, and tracks progress via docs/ROADMAP.json.
when_to_use: Use for sprint commands (plan/run/verify/demo/done/refine/prototype/hotfix/auto/roadmap/propose/init), story/task workflows, roadmap management. Also triggers on "次のスプリント", "スプリント開始", "ロードマップ作成", "ここ直して", "機能追加したい", "こういうの欲しい", "モック見せて", "プロトタイプ", "ちょっと直して", "バグ修正".
allowed-tools: Read Grep Glob Bash(git *) Bash(make *) Bash(jq *)
---

# Sprint Runner

Manages the Agile Sprint lifecycle: plan → prototype → run → verify → demo → refine → done.

## Roadmap Location

The roadmap file is always at `docs/ROADMAP.json` in the project root. If it doesn't exist, prompt the user to run `sprint init` first. If `docs/ROADMAP.md` exists but `ROADMAP.json` does not, run `sprint init` to migrate.

## Commands

| Command | Description | Detail |
|---|---|---|
| `sprint init` | Initialize or migrate the roadmap | See `references/sprint-init.md` |
| `sprint plan` | Prepare the next sprint collaboratively | See `references/sprint-plan.md` |
| `sprint prototype` | Generate HTML prototype for GUI review | See `references/sprint-prototype.md` |
| `sprint run` | Execute the current sprint | See `references/sprint-run.md` |
| `sprint verify` | Verify completeness and quality | See `references/sprint-verify.md` |
| `sprint demo` | Demonstrate deliverables by running the program | See `references/sprint-demo.md` |
| `sprint refine` | Interactive UI/UX refinement with user | See `references/sprint-refine.md` |
| `sprint done` | Finalize and commit the sprint | See `references/sprint-done.md` |
| `sprint hotfix` | Quick fix without full sprint ceremony | See `references/sprint-hotfix.md` |
| `sprint help` | Show command list and usage guide | See `references/sprint-help.md` |
| `sprint auto` | Execute one sprint fully autonomously | See `references/sprint-auto.md` |
| `sprint propose` | Discuss and add new features to roadmap | See `references/sprint-propose.md` |
| `sprint roadmap` | Generate full roadmap from VISION | See `references/sprint-roadmap.md` |

When a command is invoked, read the corresponding reference file before taking any action.

## Important Behaviors

- **Auto-decide, confirm once**: During `sprint plan` and reviews, auto-select the recommended approach when there is a clear best practice. Present a single summary with all decisions (auto-decided + open questions) for the user to confirm or adjust. Only ask individual questions for genuinely ambiguous design decisions with meaningful trade-offs.
- **Enforce user stories**: During `sprint plan`, verify all Stories follow the "{役割}として、{やりたいこと}をしたい。なぜなら、{理由}だから。" format. Autonomously rewrite task-decomposition Stories as proper user stories.
- **Autonomous technical decisions**: During `sprint run`, make technical decisions autonomously when there is a clear best practice. Only escalate for significant architectural impact. Log autonomous decisions in `docs/sprint-logs/{SprintID}/`.
- **Log everything**: Test output, build output, and verification results go to `docs/sprint-logs/{SprintID}/`.
- **Roadmap is the source of truth**: Always read `docs/ROADMAP.json` before taking action.
- **Respect dependencies**: Flag incomplete prior Sprints as blockers during `sprint plan`.
- **Actually invoke /review**: During `sprint run` (per-Story) and `sprint verify` (Sprint-level), call the `/review` skill yourself via the Skill tool. Never skip or delegate this.
- **Two-level review**: Story-level review in `sprint run` + Sprint-level review in `sprint verify`. Both are mandatory.
- **Parallel execution with worktrees**: Independent Stories run in parallel via sub-agents with worktree isolation. Ensure `.claude/worktrees/` and `.claude/autopilot-*.lock` are in `.gitignore` before first worktree creation.
- **Sub-agent model**: Implementation and review sub-agents use `model: "sonnet"`. Main agent uses the default model.
- **Sub-agent prompts must be self-contained**: Include all necessary context in each sub-agent prompt — never assume prior conversation is available.
- **Demo with running program**: `sprint demo` runs `make serve` (or equivalent) and demonstrates acceptance criteria live. Never substitute test code execution.
- **Refine is interactive only**: `sprint refine` requires the user to look at the running app and provide feedback. It is skipped in `sprint auto`. In autopilot, it runs at milestone boundaries after the demo.
- **Always commit and push on done**: `sprint done` must leave a clean working tree.
- **GUI spec is mandatory in sprint plan**: Always invoke `gui-spec` during `sprint plan`. Let `gui-spec` determine whether GUI work exists.
- **Prototype before implementation**: For GUI Stories, run `sprint prototype` after `sprint plan` and before `sprint run`. The approved HTML prototype in `prototype/` is the visual reference for implementation sub-agents. In autopilot, prototyping covers all GUI Stories up to the next milestone.
- **Two-tier testing**: GUI Stories produce two test files — mock tests (`*.mock.spec.ts`) for error/edge cases, E2E tests (`*.e2e.spec.ts`) for acceptance criteria against the real server. Non-GUI Stories produce acceptance tests in `tests/acceptance/`.
- **Mock tests gate Story completion in sprint run**: A GUI Story cannot be marked `[x]` in sprint run unless its mock tests pass. E2E tests run later in sprint verify.
- **E2E tests gate Sprint completion in sprint verify**: All E2E tests and acceptance tests must pass against the real server before the Sprint can proceed to done.
- **Acceptance criteria traceability**: Every acceptance criterion in ROADMAP.json must have a corresponding test tagged with `[AC-{StoryID}-{N}]`. sprint verify checks this mapping and creates missing tests.
- **Auto mode logs all decisions**: During `sprint auto`, every decision (planning, implementation, review) must be logged to `docs/sprint-logs/{SprintID}/decisions.json` with rationale referencing VISION.json or DESIGN_PRINCIPLES.json. Work happens on an `autopilot/{base-branch}/{SprintID}` branch, not directly on the base branch.
- **All data files are JSON**: ROADMAP, VISION, DESIGN_PRINCIPLES, and all sprint-logs use JSON format. See `references/ROADMAP_SCHEMA.json` and `references/SPRINT_LOGS_SCHEMA.json` for structure. ARCHITECTURE.md and CLAUDE.md remain Markdown.

## Roadmap Reading Patterns

To minimize tokens, sprint commands MUST read only the slice they need from `docs/ROADMAP.json` via `jq` (Bash tool), NOT the whole file via Read. Reading the entire ROADMAP just to look at one Sprint is the single largest source of avoidable token waste in this skill.

| Pattern | Command | Use cases |
|---|---|---|
| Current Sprint slice | `jq '.sprints[.progress.current_sprint]' docs/ROADMAP.json` | sprint run / verify / demo / refine / done / prototype / auto |
| Sprint by ID | `jq --arg id "<SprintID>" '.sprints[$id]' docs/ROADMAP.json` | targeted lookups (dependencies, history) |
| Top-level structure (no Sprint bodies) | `jq '{progress, execution_order, dependencies, sprints: (.sprints \| map_values({title, status, milestone}))}' docs/ROADMAP.json` | sprint plan (initial scan), sprint propose (placement decision) |
| Backlog only | `jq '.backlog' docs/ROADMAP.json` | backlog operations (sprint hotfix, propose) |
| Single Story | `jq --arg s "<SprintID>" --arg st "<StoryID>" '.sprints[$s].stories[$st]' docs/ROADMAP.json` | single-Story workflows |
| Acceptance criteria of current Sprint | `jq '.sprints[.progress.current_sprint].stories \| to_entries[] \| {story: .key, ac: .value.acceptance_criteria}' docs/ROADMAP.json` | sprint verify Phase 1.5 traceability |
| Whole file (legitimate) | Read tool | sprint init / roadmap only — these rewrite the whole file |

**Writes**: ALWAYS use in-place `jq` mutation with output redirected to /tmp and moved back. Never Read the whole file just to modify one field, and never echo the full updated JSON back through the Bash output (that would burn tokens equal to the file size). The redirect-and-move envelope means token cost scales with the *size of the change*, not the file.

Envelope:
```bash
jq <FILTER> docs/ROADMAP.json > /tmp/roadmap.json && mv /tmp/roadmap.json docs/ROADMAP.json
```

Named filters (combine multiple with `|` in a single jq invocation when updating several fields atomically):

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

Example — mark Sprint+Stories+Tasks done and recompute progress in one shot:

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

When passing JSON values as arguments, prefer single-quoted heredocs or shell vars to avoid escaping headaches:
```bash
ITEM=$(cat <<'EOF'
{"title":"Refactor X","description":"...","added_in":"hotfix","reason":"User request","status":"done"}
EOF
)
jq --argjson item "$ITEM" '.backlog += [$item]' docs/ROADMAP.json > /tmp/r.json && mv /tmp/r.json docs/ROADMAP.json
```

When a reference file says "Read `docs/ROADMAP.json`", interpret it as "Read the relevant slice via the appropriate Reading Pattern above". When it says "update ROADMAP.json", use the appropriate Write filter above.

## Reference Files

- `references/sprint-init.md` — init command details
- `references/sprint-plan.md` — plan command details
- `references/sprint-prototype.md` — prototype (HTML mockup for GUI review) command details
- `references/sprint-run.md` — run command details
- `references/sprint-verify.md` — verify command details
- `references/sprint-demo.md` — demo command details
- `references/sprint-refine.md` — refine (interactive UI/UX adjustment) command details
- `references/sprint-done.md` — done command details
- `references/sprint-hotfix.md` — hotfix (quick fix without sprint ceremony) command details
- `references/sprint-help.md` — help (command list and usage guide)
- `references/sprint-auto.md` — auto (fully autonomous single sprint) command details
- `references/sprint-propose.md` — propose (add new features to roadmap) command details
- `references/sprint-roadmap.md` — roadmap generation from VISION command details
- `references/ROADMAP_SCHEMA.json` — roadmap JSON schema and example
- `references/SPRINT_LOGS_SCHEMA.json` — sprint log JSON schemas (decisions, e2e-results, acceptance-matrix, refine, failures, gui-spec)
