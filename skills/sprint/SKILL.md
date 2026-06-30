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
- **Test discipline is the source of truth**: All seven rules — every Story has a user scenario, tests drive the user's entry point (CLI subprocess / real HTTP client / real-browser Playwright / library public API), no silent skips, GUI E2E observes UI state through the real backend, status reflects reality, what you ship is what you test (Rule 6: the Sprint's diff scan ensures every implemented user-observable surface has a passing test, not just declared AC), **and 実機検証は本番モードで (Rule 7: priority_rule 9 smoke must run in production mode — no `MOCK=true` / `--fake-*` / `DRY_RUN=1` / in-process Fake)** — live in `references/test-discipline.md`. plan / run / verify / done / auto all defer to it. When something feels ambiguous about what a test must look like, read that file.
- **Acceptance criteria traceability**: Every acceptance criterion in ROADMAP.json must have a corresponding test tagged with `[AC-{StoryID}-{N}]`. sprint verify checks this mapping and creates missing tests.
- **Auto mode logs all decisions**: During `sprint auto`, every decision (planning, implementation, review) must be logged to `docs/sprint-logs/{SprintID}/decisions.json` with rationale referencing VISION.json or DESIGN_PRINCIPLES.json. Work happens on an `autopilot/{base-branch}/{SprintID}` branch, not directly on the base branch.
- **All data files are JSON**: ROADMAP, VISION, DESIGN_PRINCIPLES, and all sprint-logs use JSON format. See `references/ROADMAP_SCHEMA.json` and `references/SPRINT_LOGS_SCHEMA.json` for structure. ARCHITECTURE.md and CLAUDE.md remain Markdown.
- **DESIGN/ is binding when present**: `docs/DESIGN/` is managed by the `design` skill. When the directory exists, sprint plan / run / roadmap must read the relevant ADRs and respect them as constraints. Accepted ADRs are not negotiable in sprint commands — if a Sprint needs to contradict one, escalate to the user via `design adr` (amend / supersede) before proceeding. Tentative ADRs are advisory.
- **6-Guard Done Judgment**: Before marking any Story as `done` in `sprint verify` / `sprint done` / `sprint auto`, apply all 6 guards defined in `references/sprint-done-judgment.md`. Any failed guard moves the Story to `needs_user_review`, not `done`. Record each guard's pass/fail/warn outcome in `verification-results.json` under `done_judgment`.
- **priority_rule 9 exception scope is strict**: The exception clause (障害シナリオへの限定) requires explicit障害シナリオ identifiers (`kill-9` / `停電` / `Shamir-unseal` / `ネットワーク遮断` / `disk-full` / `OOM` / `プロセスクラッシュ`) in the Story's `review_reason`. sprint rejects exception claims without these markers and falls back to the normal real-mode smoke requirement.
- **Mock-mode does not satisfy real-mode smoke** (test-discipline Rule 7): Tests that use `MOCK=true`, `--fake-*` flags, `DRY_RUN=1`, in-process FakeCore / InMemoryStore, or `*_fake_*: true` defaults do not count toward priority_rule 9 "dev VM 実機 smoke" requirement.

## Roadmap I/O — Token discipline

Sprint commands MUST read only the slice they need from `docs/ROADMAP.json` via `jq` (Bash tool), NOT the whole file via Read. Writes MUST use in-place `jq` mutation with redirect-and-move, NOT Read + Write of the whole file. Reading or rewriting the whole ROADMAP for a small change is the single largest source of avoidable token waste in this skill.

See `references/roadmap-jq.md` for the complete reading patterns, write envelope, and named filter table. When a reference file says "Read `docs/ROADMAP.json`", interpret it as "read the relevant slice"; when it says "update ROADMAP.json", use the appropriate write filter from that table.

## Reference Files

- `references/roadmap-jq.md` — **read this when first touching ROADMAP.json** — full jq read/write patterns and named filter table
- `references/sprint-done-judgment.md` — **canonical 6-guard done judgment** (Guard 1–6) applied before any Story can be marked `done` (mirror of `autopilot/references/autopilot-done-judgment.md`)
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
- `references/test-discipline.md` — **canonical rules** for tests: user scenarios, entry-point-driven testing, no-silent-skip, real-browser GUI E2E, status truthfulness. Shared by plan / run / verify / done / auto.
- `references/story-scenarios.md` — user scenario taxonomy and templates (CLI / API / GUI / library), referenced from `test-discipline.md` Rule 1
- `references/ROADMAP_SCHEMA.json` — roadmap JSON schema and example
- `references/SPRINT_LOGS_SCHEMA.json` — sprint log JSON schemas (decisions, verification-results, refine, failures, scenario, gui-spec)
