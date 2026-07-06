---
name: autopilot
description: Runs multiple Sprints autonomously as developer and product owner. Executes plan-run-verify-done cycles guided by VISION.json and DESIGN_PRINCIPLES.json, stopping at milestones for user review.
when_to_use: The main natural-language entry point for moving a project forward. Triggers on "autopilot", "autopilot start/setup/review/status", "自動実行", "まとめて実行", "次のスプリント", "進めて", "自走して", "次のマイルストーンまで", "機能追加したい", "こういうの欲しい", "ちょっと直して", "ここ直して", "バグ修正", or any hands-off multi-sprint request. Post-milestone fix/add requests are handled here too, via Review Mode (`autopilot review`) — trivial one-line fixes are routed to `sprint fix` without full ceremony. For a single explicit sprint phase, the user types `sprint <command>` directly.
allowed-tools: Read Grep Glob
---

# Autopilot

Runs multiple Sprints autonomously, acting as both developer and product owner. Guided by `docs/VISION.json`, `docs/DESIGN_PRINCIPLES.json`, and (when present) `docs/DESIGN/`. Stops only at milestone boundaries for user review.

## Prerequisites

| File | Required | Purpose |
|------|----------|---------|
| `docs/ROADMAP.json` | Yes | Sprint definitions and execution order |
| `docs/VISION.json` | Yes | Product purpose, target users, success criteria |
| `docs/DESIGN_PRINCIPLES.json` | Yes | Decision-making rules for autonomous execution |
| `docs/DESIGN/` | Optional | Load-bearing architectural decisions (managed by `design` skill). When present, ADRs are treated as binding constraints on autonomous decisions. |

If `VISION.json` or `DESIGN_PRINCIPLES.json` do not exist, **do not proceed**. Suggest one of:

1. **Complex / non-trivial systems (recommended)**: invoke the `design` skill via `design start`. It produces VISION, DESIGN_PRINCIPLES, AND `docs/DESIGN/` through guided dialogue.
2. **Simple projects**: help the user create VISION and PRINCIPLES inline using `references/vision-template.md` and `references/principles-template.md`.

For complex systems with many cross-cutting decisions, the inline templates are not enough — use `design` instead.

## Commands

| Command | Description | Detail |
|---|---|---|
| `autopilot setup` | Create VISION, DESIGN_PRINCIPLES, and required artifacts | See `references/autopilot-setup.md` |
| `autopilot start` | Begin autonomous multi-sprint execution | See `references/autopilot-start.md` |
| `autopilot review` | Triage user requests after a milestone and route them to the right mechanism (idempotent) | See `## Review Mode` below |
| `autopilot status` | Show progress and recent decisions | See below |
| `autopilot help` | Show command list and usage guide | See `references/autopilot-help.md` |

When a command is invoked, read the corresponding reference file before taking any action.

## Milestone Detection

A milestone boundary is any of the following (checked in order, use the earliest match):

1. **Explicit milestone marker** in ROADMAP.json: a Sprint with `"milestone": true`
2. **Dependency boundary**: read the `dependencies` object in ROADMAP.json. If the next Sprint has no dependency on the current Sprint (a new independent track begins), treat the current Sprint as a milestone. Determined by explicit dependency declarations, not by inference.
3. **Every 3 Sprints** as a fallback if no explicit milestones or dependency boundaries are found — prevents unbounded execution
4. **End of roadmap**: all Sprints complete

These same rules define the **detail horizon** used by `sprint roadmap` (rolling-wave planning): sprints up to the first milestone boundary are generated in full detail, sprints beyond it are coarse placeholders elaborated just-in-time at each milestone batch (see `../sprint/references/sprint-roadmap.md` → "Detail horizon" and `references/autopilot-start.md` → "Batch elaboration"). A coarse sprint (`detail_level:"coarse"` / empty `stories`) cannot be run or marked done until elaborated.

## `autopilot status`

Show the state of the most recent autopilot run. Read-only — no active session required.

1. Read `docs/ROADMAP.json` for overall progress (`progress.percentage`, `done` / `in_progress` / `remaining`, current Sprint, next milestone).
2. Read the most recent `docs/sprint-logs/*/decisions.json` files for key decisions.
3. Read the most recent milestone's `docs/sprint-logs/*/compromises.json` (if present) and summarize compromises by severity (`high` first). If absent, show "妥協なし / 記録なし".
4. If `docs/DESIGN/` exists, show ADR counts by status (accepted / tentative / superseded) and the number of open questions (`tentative: true` items), per `design status`.
5. Inspect `.claude/autopilot-*.lock` files and `git worktree list | grep autopilot/` per `references/autopilot-operations.md`.
6. Present a one-screen view: roadmap progress + current Sprint, next milestone, last completed Sprint, recent compromises (by severity), DESIGN/ ADR summary (if present), active sessions, remaining worktrees + merge status, key decisions, and any drift warnings or failure logs.

Backward compatibility: on a project that predates these artifacts, missing fields render as "-" / "N/A" rather than erroring (§2.9).

## Important Behaviors

- **VISION, PRINCIPLES, and DESIGN/ are the authority**: Every autonomous decision must be justifiable by referencing one of these documents. ADRs in `docs/DESIGN/adr/` are binding constraints — autonomous decisions that contradict an accepted ADR must escalate to the user, not proceed. If none address the question, default to the simplest approach and log why.
- **6-Guard Done Judgment**: Before marking any Story as `done`, autopilot must apply all 6 guards defined in `references/autopilot-done-judgment.md`. Any failed guard moves the Story to `needs_user_review`, not `done`. This applies to both sprint-internal verification and the post-merge milestone check.
- **priority_rule 9 exception scope is strict**: The exception clause (障害シナリオへの限定) requires explicit障害シナリオ identifiers (`kill-9` / `停電` / `Shamir-unseal` / `ネットワーク遮断` / `disk-full` / `OOM` / `プロセスクラッシュ`) in the `review_reason`. autopilot rejects exception claims without these markers and falls back to the normal real-VM smoke requirement.
- **Mock-mode does not satisfy real-VM smoke**: Tests that use `MOCK=true`, `--fake-*` flags, `DRY_RUN=1`, in-process FakeCore / InMemoryStore, or `*_fake_*: true` Ansible defaults do not count toward priority_rule 9 "dev VM 実機 smoke" requirement. A separate real-mode smoke is required.
- **Never skip milestones**: Always stop at milestone boundaries. The user's review is the alignment mechanism.
- **Forbidden actions are split into immediate-stop and notify-after**: Autopilot must obey `## Constraints and Forbidden Actions` below. Immediate-stop categories (AC tampering, destructive git, ADR violation, false `done`) halt the run; notify-after categories (test weakening, error swallowing, type-safety relaxation) are recorded to `compromises.json` and surfaced at the milestone.
- **Milestone artifacts are mandatory**: On reaching a milestone, autopilot writes `docs/sprint-logs/{SprintID}/compromises.json` (per `references/COMPROMISES_SCHEMA.json`), then `comprehension-report.md` (per `references/comprehension-report-template.md`), and tells the user to read the comprehension report **before** `autopilot review`.
- **Independent verifier under `--auto`**: When autopilot drives `sprint verify` (always `--auto`), it auto-enables `--with-verifier` — a separate read-only Claude session (`../sprint/references/verifier-agent.md`) re-checks AC, forbidden categories, ADR conformance, and compromise completeness. Its `verification-report.json` is the trust source: where it disagrees with autopilot's self-report, the verifier wins and the gap is recorded as `overlooked_by_autopilot`.
- **Drift logging, not drift blocking**: Log decisions that seem to conflict with VISION/PRINCIPLES; surface them at milestone review. Doc-staleness and VISION-drift health checks (operations.md) are advisory at milestone, never blocking.
- **Preserve user agency**: The user can always interrupt autopilot. Pause and respond before continuing.
- **Context management**: The main autopilot conversation **is the orchestrator and the sole spawner** — Story-level parallelism requires fan-out from the top level, and a sub-agent cannot spawn sub-agents, so a whole Sprint is **never** wrapped in one sub-agent (that would serialize its Stories). Sprints are sequential by nature (each builds on the prior increment), so no Sprint-level parallelism is lost. Context stays thin by **delegation, not by wrapping**: every heavy phase (plan/elaboration, Story implementation, review-fix, verify) runs in a leaf sub-agent that returns a structured summary, while the main conversation retains only wave structure, branch names, decision summaries, and status. Per-sprint working detail lives in leaf sub-agents and on disk (`docs/sprint-logs/`, `docs/ROADMAP.json`), so it does not accumulate across the batch.
- **Incremental commits + branch lifecycle**: Each Sprint on `autopilot/{base-branch}/{SprintID}`; merged branches are deleted (local + remote). Only unmerged branches survive. Per-branch locking lets multiple branches run concurrently. Full procedure: `references/autopilot-operations.md`.

## Constraints and Forbidden Actions

Autopilot runs unattended, so it must never trade away correctness for a green run. Forbidden actions fall into two tiers by **how much damage continuing would do**:

| Category | Examples | On detection |
|---|---|---|
| Effectively disabling a test | adding `it.skip` / `xtest` / `@pytest.mark.skip` / `t.Skip`; rewriting to `expect(true).toBe(true)` | **Notify after completion** |
| Weakening an assertion | `toEqual` → `toBeTruthy`; concrete value → any value; removing assertions | Notify after completion |
| Swallowing errors | newly added `try { ... } catch {}`, `// @ts-ignore`, `# noqa` | Notify after completion |
| Abandoning type safety | changing to `any`, abusive `as` casts | Notify after completion |
| Deleting / loosening acceptance criteria | removing an AC from ROADMAP.json, softening its wording | **Immediate stop** |
| Destructive git | `push --force`, `reset --hard origin`, branch deletion of unmerged work | **Immediate stop** |
| False status in ROADMAP / verification-results | writing `status: "done"`/`"pass"` while tests fail (incl. rationalizing a real failure as "pre-existing"/"out of scope") | **Immediate stop** — deterministically blocked by the machine verdict gate (`../sprint/references/verify-execution.md`) |
| Implicit ADR violation | implementing against an accepted ADR's Decision and justifying it only via `decisions.json` | **Immediate stop** (require an ADR amendment) |

Decision rule:
- **Immediate stop** = the action breaks the *premise of all later work* (AC tampering, git destruction, ADR violation, false done). Continuing is meaningless — halt and escalate to the user now.
- **Notify after completion** = a *local* concession that stays reviewable later. Record it to `docs/sprint-logs/{SprintID}/compromises.json` (per `references/COMPROMISES_SCHEMA.json`) and keep going; stopping the whole run for a local concession costs more than it saves.

The independent verifier (`--auto` always enables it) re-scans the diff for these same categories; an item it finds that autopilot missed is recorded with `overlooked_by_autopilot: true`.

Three defense layers enforce this table: **L1** this prompt (autopilot self-restraint), **L2** the `sprint verify` forbidden-degradation diff scan (`../sprint/references/test-discipline.md` Rule 6), and **L3** the optional PostToolUse hooks `hooks/forbidden-action-guard.py` (blocks test-disabling edits during an autopilot run) and `hooks/verification-integrity-guard.py` (blocks recording a `pass` over a machine-recorded failure). L3 ships with the plugin; see `hooks/README.md`. The "false status" row above is additionally enforced **deterministically**: under `--auto`, `sprint verify` derives test status from the machine verdict (`hooks/run-verify.py` → `verify-run.json`, real exit codes), and `sprint done` refuses to complete a Sprint whose `overall_machine_status` is not `pass` — the model cannot author a passing result over a failing run (`../sprint/references/verify-execution.md`, test-discipline Rule 9).

## Review Mode

`autopilot review` is the **idempotent triage command** invoked after a milestone. It does not implement fixes itself — it classifies each user request and routes it to an existing mechanism. The user only has to remember `autopilot review`; Claude does the classification.

**Idempotency requirement**: every invocation re-reads `docs/ROADMAP.json`, the milestone's `compromises.json`, and `docs/DESIGN/` from scratch. It holds NO internal state between calls. This lets the user loop `touch the app → notice something → autopilot review → fix → touch again` any number of times at one milestone boundary, and across milestones, with identical behavior each time.

### Flow

1. **Comprehension gate** — confirm `docs/sprint-logs/{SprintID}/comprehension-report.md` exists for the milestone's Sprints. If missing, generate it (per `references/comprehension-report-template.md`) before continuing, and ask the user to read it first.
2. **Load context** — ROADMAP.json + the milestone's `compromises.json` + recent Sprint status + `docs/DESIGN/` (if present).
3. **Collect requests** — take all of the user's requests at once (batch).
4. **Classify** each request into ①–④ using the decision tree below; for ④ with DESIGN/, also surface the ADR impact.
5. **Present the classification table** to the user for approval.
6. **Route** each approved request to its mechanism; update ROADMAP.json (and ADRs if needed); leave the project ready for the next `autopilot start`.

### The four classes and where each is routed

| # | Class | Test | Routed to |
|---|---|---|---|
| ① | **AC violation** — an existing AC was not actually met | `sprint verify` failure handling → re-open the Sprint (see below) → `sprint run` to fix |
| ② | **Out-of-AC small fix** — AC met, minor UX/detail, 1–2 tasks | `sprint fix` (a fix-Story; placement chosen by the user, see below) |
| ③ | **Out-of-AC new scope** — Story-sized or larger new work | `sprint idea` → picked up by the next `sprint plan` |
| ④ | **Direction change** — ROADMAP-wide / load-bearing | DESIGN/ present: `design refresh` → `design adr` → `sprint roadmap`. DESIGN/ absent: `sprint roadmap` re-run |

### Decision tree (apply per request)

```
Q0: Does DESIGN/ have a relevant ADR or VISION item?  YES → note ADR impact alongside the class.  NO → continue.
Q1: Should an existing AC already have covered this?  YES → ① AC violation.  NO → Q2.
Q2: Does it complete in 1–2 small tasks?              YES → ② small fix.     NO → Q3.
Q3: Does it fit the existing roadmap direction + ADRs? YES → ③ new scope.    NO → ④ direction change.
```

Conservative bias when a boundary is unclear — always lean toward the costlier-to-miss side:
- ① vs ② → lean **①** (missing an AC violation is worse than an extra check).
- ② vs ③ → lean **③** (don't pollute a done Sprint with creep).
- ③ vs ④ → lean **④** (don't miss a load-bearing decision).

### ① Sprint re-open detail

| Change | Action |
|---|---|
| Sprint status | `done` → `in_progress` |
| Affected AC status | `pass` → `fail`, add `reopened_at: <timestamp>` |
| Fix work | append fix tasks to the Story, or add a fix-Story |
| Log | write `docs/sprint-logs/{SprintID}/reopen.json` (per `../sprint/references/REOPEN_SCHEMA.json`), `triggered_by: "milestone_review"` |
| Progress | recompute `progress.done` |

(Re-opening a *past* Sprint by explicit user request uses the same flow but `triggered_by: "manual_retroactive"`. Autopilot never re-opens a past Sprint on its own — see `## Backward compatibility`.)

### ② Fix-Story placement detail

Adding a Story to a `done` Sprint is normal in agile. **Let the user choose placement**:

| Placement | Behavior |
|---|---|
| Most recent done Sprint (default) | add to that Sprint's `stories` with `added_in_review: "<milestone>"` |
| Next Sprint | add to the next (or a new) Sprint |

The `added_in_review` field keeps "added after the fact" distinguishable from "originally planned" in history.

### ④ Direction-change detail (DESIGN/ present)

1. `autopilot review` classifies ④.
2. Run `design refresh` internally → check ADR contradictions and broken links.
3. Present the impact to the user.
4. On approval, `design adr` adds a new ADR or supersedes an existing one.
5. Re-run `sprint roadmap` (if needed); update downstream Sprints.

Without DESIGN/, ④ is just a `sprint roadmap` re-run. Full handoff contract: `design/SKILL.md` → "`autopilot review` ④ direction-change handoff".

## Backward compatibility

This skill must run cleanly on projects created before these mechanisms existed (§2.9):
- **Never auto-convert existing files.** ROADMAP.json / VISION.json / DESIGN/ / sprint-logs/ are read as-is. No `migrate` command.
- **New fields are optional.** A Story without `added_in_review` / `reopened_at` is read as "originally planned" / a normal `pass` AC. Missing `compromises.json` ⇒ "妥協なし"; missing `comprehension-report.md` ⇒ generated on demand at `autopilot review`, never back-filled for past Sprints; missing `verification-report.json` ⇒ "verifier 未実行".
- **No retroactive rewrites.** Autopilot does not re-open or re-grade a past `done` Sprint on its own. Only an explicit user instruction does, recorded as `triggered_by: "manual_retroactive"`.
- **Offers default to No.** If autopilot offers to tidy an existing ROADMAP.json to the new schema, the default is to leave it alone; only an explicit yes proceeds.

## Reference Files

- `references/autopilot-setup.md` — `autopilot setup` command flow (new project / existing project, DESIGN/ detection, Backfill handoff)
- `references/autopilot-start.md` — `autopilot start` command flow (pre-flight, prototype review, sprint loop, milestone demo, cleanup)
- `references/autopilot-done-judgment.md` — **canonical 6-guard done judgment** (Guard 1–6) applied before any Story can be marked `done`
- `references/autopilot-operations.md` — branch locking, worktree cleanup, sprint branch deletion, milestone health checks (doc staleness, VISION drift)
- `references/COMPROMISES_SCHEMA.json` — `compromises.json` schema (notify-after compromises recorded at a milestone)
- `references/comprehension-report-template.md` — `comprehension-report.md` template + writing guide (generated at every milestone)
- `../sprint/references/verifier-agent.md` — the independent read-only verifier sub-agent spec (auto-enabled under `--auto`)
- `../sprint/references/VERIFICATION_REPORT_SCHEMA.json` — `verification-report.json` schema (verifier output; trust source for compromises)
- `../sprint/references/REOPEN_SCHEMA.json` — `reopen.json` schema (① Sprint re-open in Review Mode)
- `references/getting-started.md` — New project setup guide (with specs / without specs / existing project)
- `../design/references/VISION_SCHEMA.json` — VISION.json schema and example. **Owned by the `design` skill** (the authority that generates VISION). autopilot setup's inline VISION generation reads it but a stricter version is produced by `design`.
- `../design/references/DESIGN_PRINCIPLES_SCHEMA.json` — DESIGN_PRINCIPLES.json schema and example. **Owned by the `design` skill** for the same reason.
- `references/vision-template.md` — VISION setup guidelines (question prompts)
- `references/principles-template.md` — DESIGN_PRINCIPLES setup guidelines (question prompts)
- `references/autopilot-help.md` — help (command list and usage guide)
