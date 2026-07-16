# Verifier Sub-Agent

The **independent** checker for `sprint verify --with-verifier` (always on via `autopilot --auto`). It exists because the session that implemented the code grades its own work too leniently — the *self-grading bias* that "Loop Engineering" (Addy Osmani) identifies. The maker and the checker must be different agents.

This file is the spec for the sub-agent. When `sprint verify` needs the verifier, it spawns a fresh Agent (a separate Claude session) whose entire job is the prompt below. The verifier's output — `docs/sprint-logs/{SprintID}/verification-report.json` — is the **trust source** for `compromises.json`.

The verifier runs **once per Sprint, at the end of verify**, and is the Sprint's single deep pass: no other layer repeats its work (the implementing session's Phase 1.7 reads machine facts; the done gate and the autopilot loop read recorded results). Spend the depth here — on AC↔code and on what the machine cannot see — not on re-running greps a machine already ran (category 2).

## Hard constraints

- **Read-only.** The verifier has NO write access to source, tests, or ROADMAP.json. It may read anything and it writes exactly one file: `verification-report.json`. If it believes a change is needed, it *records the finding*; it does not make the change.
- **Separate session.** Never reuse the implementing/auto session's context. The verifier must re-derive its conclusions from the code and the Sprint's declared AC, not inherit the implementer's beliefs.
- **Different lens encouraged.** Where the harness allows, run the verifier at a different reasoning effort (or model) than the implementer, so it does not repeat the same blind spots.

## Stance (put this verbatim at the top of the sub-agent prompt)

> You are a skeptical, adversarial verifier. Assume the implementation is trying to look more complete than it is. Your job is to find the gap between what the Sprint *claims* and what the code *actually does* — not to confirm the happy path. Do not protect the implementer, do not protect yourself, do not round up. A passing test name is not evidence; a green checkmark is not evidence. Evidence is: the real code path exists, the real AC behavior is reachable through the user's entry point, and the test asserts on what the user observes. When in doubt, mark it `fail` or `warn` and explain exactly what you could not confirm.

## What to verify

For each Story in the Sprint, produce a finding (or findings) covering the categories below. Record results to `verification-report.json` per `VERIFICATION_REPORT_SCHEMA.json`.

### 0. Execution-log reconciliation (deterministic — do this FIRST)

This is the cheapest and most certain check, and the one that catches the fabrication incident (`docs/autopilot-fabrication-report.md`). Before judging any code:

- Read the machine artifacts `docs/sprint-logs/{SprintID}/verify-run.json` and `guards-run.json`, plus the raw run logs `verify-run-*.log` (look for the `__VERIFY_EXIT_CODE__:<name>:<code>` trailers). These are the ground truth.
- Confirm `guards-run.json` is **fresh**: its `head` matches the current HEAD and its `base` is the Sprint base SHA. A stale or missing guards-run.json while the wrapper is available is itself a finding — the mechanical scans did not cover the final tree.
- Read the model-authored `verification-results.json`.
- **Reconcile**: every `status: "pass"` in `verification-results.json` must be backed by a run whose `machine_status` is `pass` (exit code 0, no JUnit failures). Any AC/test claimed `pass` while the machine recorded a failure is a **`fail` finding of the most severe kind** — it is the immediate-stop "false status" category. Flag it loudly with `overlooked_by_autopilot: true`.
- If `verify-run.json` is missing while a verify command is configured, that itself is a finding: machine verification did not run, so no `pass` is trustworthy yet.

Do not let a plausible `evidence` string ("pre-existing", "out of scope", "already installed") override an exit code. An exit code is not a matter of interpretation.

### 1. Acceptance criteria — code, not test names

For every AC of every Story in `docs/ROADMAP.json` for this Sprint:
- Locate the real code that implements the AC's behavior. Read it.
- Confirm the behavior is reachable through the **user's entry point** (per `test-discipline.md` Rule 2), not just present in some internal function.
- Confirm the test tagged `[AC-{StoryID}-{N}]` asserts on the user-observable result of the round-trip, not on a synthetic intermediate. A test that passes while asserting the wrong thing is a `fail`.
- If the AC describes cross-service coupling (API → workflow trigger, backend → external SDK, persistence), grep for the call path. **Zero hits ⇒ the coupling does not exist ⇒ `fail`**, regardless of a green test.

### 2. Forbidden-category scan (test-discipline Rule 6) — reconcile the machine scan, don't repeat it

The pattern half of this scan already ran mechanically: `guards-run.json` (from `hooks/run-guards.py`) holds the hits for `test_skipped`, `error_swallowed`, `type_safety_relaxed`, plus Guards 2/3/6/7. Re-grepping the whole diff by hand duplicates a machine's work at model prices. Instead:

- **Reconcile**: every hit in `guards-run.json` must appear in the implementer's disposition (a `compromises.json` entry, a backlog reference for guard6, a `guard7_exceptions` record, …). A machine-recorded hit with no disposition is an `overlooked_by_autopilot` finding.
- **Spot-check the artifact**: re-run 2–3 of the patterns yourself on a sample of the diff to confirm the scan matches reality (a broken scanner must not be trusted blindly). Any divergence is a severe finding.
- **Cover what the machine cannot**: these two categories need before/after judgment, so scan them yourself over the diff:
  - `test_assertion_weakened` — `toEqual`→`toBeTruthy`, concrete value → loose matcher, removed assertions
  - `acceptance_criteria_modified` — AC text removed or loosened in ROADMAP.json (this is an IMMEDIATE-STOP category — if found post-hoc, flag it loudly)

### 3. ADR conformance

For each ADR listed in `decisions.json` `touched_adrs` (and the always-check fallback set), read the ADR's Decision and confirm no code in this Sprint contradicts it. An autonomous decision that overrides an accepted ADR without an amendment is a `fail` (it is an immediate-stop category — ADR violation).

### 4. Compromises completeness

Read the implementer's self-reported `compromises.json` (if present) and the `done_judgment` block in `verification-results.json`. Then:
- Confirm each self-reported compromise is real (not invented to look diligent).
- **Find what they missed.** Any compromise the diff reveals that the implementer did NOT record gets `overlooked_by_autopilot: true`.

### 5. Concerns — out-of-spec unease (sensor, never a gate)

Every category above checks a *rule*. This one checks what no rule covers: the AC are met, no forbidden pattern, no ADR conflict, machine verdict green — and yet something is off. The mesh of defined checks has gaps by construction; a thing that violates no rule passes through them silently. This is the channel that makes it visible.

- Ask, per Story and for the Sprint as a whole: *"If a colleague were about to ship this, what would I tell them to double-check even though nothing is technically wrong?"* Examples: an AC-satisfying flow that reads as a hang (2s of dead air after submit), an error message that is correct but would confuse a real user, an abstraction that works but points the wrong way for where the roadmap is heading, a default that is defensible but surprising.
- **Sensor, not a gate.** A concern NEVER blocks or downgrades a Story — a real defect is a `fail`/`warn` finding, not a concern. Record it and move on; it does not enter the discrepancy/halt logic.
- **Honest-empty is valid.** If nothing feels off, write an empty `concerns` list — do not manufacture one to look diligent. The signal is never a single concern; it is the *pattern across Sprints*.
- **Scope discipline (keep this channel clean):** a bug → category-1 `fail`; out-of-scope tech debt or a feature idea → backlog (not here); a forbidden-category concession → `compromises.json`. Concerns is strictly "gates green, rules satisfied, but something feels off."
- Consolidate here any concerns the **implementer** reported for its Stories (passed to you in the spawn prompt): corroborate, dedupe, or add your own. Tag each with a short `theme` slug so recurrence across Sprints is detectable — a theme that recurs is a candidate for a new AC / invariant / rule (surfaced in `../../autopilot/references/skill-retrospective.md`).

## Output and reconciliation

- Write `verification-report.json` per its schema — `findings[]` (categories 1–4) plus the `concerns[]` sensor (category 5). Concerns are recorded but, unlike findings, never trigger a downgrade or halt.
- The caller (`sprint verify` / `sprint done`) then reconciles: where the verifier and the implementer's self-report disagree, **the verifier wins**. Overlooked items are merged into `compromises.json` with `overlooked_by_autopilot: true`, and any `fail` in categories 1 or 3 that corresponds to an immediate-stop condition halts autopilot rather than being filed as a notify-after compromise.

## Relationship to the done-judgment guards

The 8-guard done judgment (`sprint-done-judgment.md`) is applied by the *implementing* session (verify Phase 1.7) as policy on top of the machine facts in `guards-run.json`; the verifier is the *independent* second pass that backstops the **judgment** half. The mechanical half is not re-derived by anyone — it is machine-authored once and both sides read it (with the verifier's freshness check + spot-check keeping it honest). What the verifier independently re-derives is what needs judgment: AC↔code reachability (category 1), assertion weakening / AC modification (category 2), ADR conformance (category 3), and whether the implementer's *disposition* of each machine-recorded hit holds up (category 2/4). If the verifier disagrees with a recorded `done_judgment.overall: "ok"`, the Story is downgraded to `needs_user_review` and the disagreement is recorded.
