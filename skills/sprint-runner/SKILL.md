---
name: sprint-runner
description: Manages Agile Sprint lifecycle — plan, run, verify, demo, refine, done. Generates roadmaps, executes sprints autonomously, and tracks progress via docs/ROADMAP.md.
when_to_use: Use for sprint commands (plan/run/verify/demo/done/refine/auto/roadmap/propose/init), story/task workflows, roadmap management. Also triggers on "次のスプリント", "スプリント開始", "ロードマップ作成", "ここ直して", "機能追加したい", "こういうの欲しい".
allowed-tools: Read Grep Glob Bash(git *) Bash(make *)
---

# Sprint Runner

Manages the Agile Sprint lifecycle: plan → run → verify → demo → refine → done.

## Roadmap Location

The roadmap file is always at `docs/ROADMAP.md` in the project root. If it doesn't exist, prompt the user to run `sprint init` first.

## Commands

| Command | Description | Detail |
|---|---|---|
| `sprint init` | Initialize or migrate the roadmap | See `references/sprint-init.md` |
| `sprint plan` | Prepare the next sprint collaboratively | See `references/sprint-plan.md` |
| `sprint run` | Execute the current sprint | See `references/sprint-run.md` |
| `sprint verify` | Verify completeness and quality | See `references/sprint-verify.md` |
| `sprint demo` | Demonstrate deliverables by running the program | See `references/sprint-demo.md` |
| `sprint refine` | Interactive UI/UX refinement with user | See `references/sprint-refine.md` |
| `sprint done` | Finalize and commit the sprint | See `references/sprint-done.md` |
| `sprint auto` | Execute one sprint fully autonomously | See `references/sprint-auto.md` |
| `sprint propose` | Discuss and add new features to roadmap | See `references/sprint-propose.md` |
| `sprint roadmap` | Generate full roadmap from VISION | See `references/sprint-roadmap.md` |

When a command is invoked, read the corresponding reference file before taking any action.

## Important Behaviors

- **Auto-decide, confirm once**: During `sprint plan` and reviews, auto-select the recommended approach when there is a clear best practice. Present a single summary with all decisions (auto-decided + open questions) for the user to confirm or adjust. Only ask individual questions for genuinely ambiguous design decisions with meaningful trade-offs.
- **Enforce user stories**: During `sprint plan`, verify all Stories follow the "{役割}として、{やりたいこと}をしたい。なぜなら、{理由}だから。" format. Autonomously rewrite task-decomposition Stories as proper user stories.
- **Autonomous technical decisions**: During `sprint run`, make technical decisions autonomously when there is a clear best practice. Only escalate for significant architectural impact. Log autonomous decisions in `docs/sprint-logs/{SprintID}/`.
- **Log everything**: Test output, build output, and verification results go to `docs/sprint-logs/{SprintID}/`.
- **Roadmap is the source of truth**: Always read `docs/ROADMAP.md` before taking action.
- **Respect dependencies**: Flag incomplete prior Sprints as blockers during `sprint plan`.
- **Actually invoke /review**: During `sprint run` (per-Story) and `sprint verify` (Sprint-level), call the `/review` skill yourself via the Skill tool. Never skip or delegate this.
- **Two-level review**: Story-level review in `sprint run` + Sprint-level review in `sprint verify`. Both are mandatory.
- **Parallel execution with worktrees**: Independent Stories run in parallel via sub-agents with worktree isolation. Ensure `.claude/worktrees/` is in `.gitignore` before first worktree creation.
- **Sub-agent model**: Implementation and review sub-agents use `model: "sonnet"`. Main agent uses the default model.
- **Sub-agent prompts must be self-contained**: Include all necessary context in each sub-agent prompt — never assume prior conversation is available.
- **Demo with running program**: `sprint demo` runs `make serve` (or equivalent) and demonstrates acceptance criteria live. Never substitute test code execution.
- **Refine is interactive only**: `sprint refine` requires the user to look at the running app and provide feedback. It is skipped in `sprint auto`. In autopilot, it runs at milestone boundaries after the demo.
- **Always commit and push on done**: `sprint done` must leave a clean working tree.
- **GUI spec is mandatory in sprint plan**: Always invoke `gui-spec` during `sprint plan`. Let `gui-spec` determine whether GUI work exists.
- **Two-tier testing**: GUI Stories produce two test files — mock tests (`*.mock.spec.ts`) for error/edge cases, E2E tests (`*.e2e.spec.ts`) for acceptance criteria against the real server. Non-GUI Stories produce acceptance tests in `tests/acceptance/`.
- **Mock tests gate Story completion in sprint run**: A GUI Story cannot be marked `[x]` in sprint run unless its mock tests pass. E2E tests run later in sprint verify.
- **E2E tests gate Sprint completion in sprint verify**: All E2E tests and acceptance tests must pass against the real server before the Sprint can proceed to done.
- **Acceptance criteria traceability**: Every acceptance criterion in ROADMAP.md must have a corresponding test tagged with `[AC-{StoryID}-{N}]`. sprint verify checks this mapping and creates missing tests.
- **Auto mode logs all decisions**: During `sprint auto`, every decision (planning, implementation, review) must be logged to `docs/sprint-logs/{SprintID}/decisions.md` with rationale referencing VISION.md or DESIGN_PRINCIPLES.md. Work happens on an `autopilot/{SprintID}` branch, not directly on main.

## Reference Files

- `references/sprint-init.md` — init command details
- `references/sprint-plan.md` — plan command details
- `references/sprint-run.md` — run command details
- `references/sprint-verify.md` — verify command details
- `references/sprint-demo.md` — demo command details
- `references/sprint-refine.md` — refine (interactive UI/UX adjustment) command details
- `references/sprint-done.md` — done command details
- `references/sprint-auto.md` — auto (fully autonomous single sprint) command details
- `references/sprint-propose.md` — propose (add new features to roadmap) command details
- `references/sprint-roadmap.md` — roadmap generation from VISION command details
- `references/ROADMAP_TEMPLATE.md` — roadmap format specification and template
