# skill-retrospective template

The template and writing guide for `docs/sprint-logs/{SprintID}/skill-retrospective.md`. autopilot generates this at every milestone boundary, immediately after `comprehension-report.md`. It is the structural home for **item 1 of the self-audit** (`docs/skills-self-audit.md` → "SKILL 改訂ループの制度化"): the circuit that turns a failure or rework into a *SKILL diff*, instead of a fix that lands on the task and leaves the law that allowed the failure unchanged.

## Why this exists (don't delete this intent)

- A SKILL cannot detect its own staleness. The only signal that a SKILL is wrong is a failure downstream of it — and that signal is lost the moment the failure is fixed task-locally and forgotten. This artifact forces the question **before** the fix is forgotten.
- The fabrication incident (`docs/autopilot-fabrication-report.md`) is the archetype: a real test failure was rationalized away; the *fix* was not "re-run the Sprint" but a change to `sprint verify` / `sprint done` / the hooks (Phase 6, machine-derived verdict). That loop worked once, informally. This file makes it routine.
- **This is a proposal surface, not an apply surface.** Revising a SKILL is load-bearing (it changes the law every future run obeys), so autopilot never edits a SKILL from here. It writes the proposed diff; the PO approves it through the self-audit flow. Advisory, like the milestone drift checks — it never blocks the milestone.

## Inputs (this batch = Sprints since the last milestone)

Scan, for every Sprint in the batch:

- `compromises.json` — notify-after concessions autopilot made (weakened assertion, swallowed error, …). Each is a candidate SKILL defect: *did a SKILL permit or fail to prevent this?*
- `verification-report.json` — verifier findings with `overlooked_by_autopilot: true`, and any `fail` / `warn` the implementer missed. An overlooked item is doubly interesting: the escape AND the reason a gate didn't catch it.
- `reopen.json` — ① AC-violation re-opens from `autopilot review` (`triggered_by: "milestone_review"`). An AC that passed verification but failed the PO's eyes is a hole in the *verification* law.
- `decisions.json` — decisions with an empty / "no applicable section" `reference` (also surfaced by the VISION-drift check). Recurring ones mean VISION / DESIGN_PRINCIPLES is incomplete — a documentation defect, which is in scope here too.
- `verification-report.json` → `concerns[]` — the "out-of-spec unease" sensor (rules satisfied, gates green, but something felt off). Treat these differently from the signals above: a **single** concern is not a SKILL defect and gets no diff — it just logs. But concerns sharing a `theme` slug **across 2+ Stories/Sprints** are a candidate for a new AC / invariant / rule (the mesh has a recurring gap) — that recurrence IS a signal, routed like any other. Also watch the **empty rate**: if `concerns[]` is empty across essentially every Sprint and role, the sensor is not being elicited (a prompt weakness, self-audit item 3), not proof that nothing is ever off — note it.
- `run-metrics.json` — the token-budget sensor (agents spawned, review cycles, caps hit, verifier/guards flags). Efficiency signals route through the same loop as quality signals: a Story that hits the review-cycle cap every Sprint, an agent-count spike, or `guards_machine_run: false` (the mechanical scans ran at model prices — or not at all) is a candidate SKILL/process defect. A one-off is noise; a pattern across the batch gets a diff proposal.

If all inputs are empty this batch, still write the file with the count line set to zero and the table empty (see template). Absence of the file must not be ambiguous with "checked, nothing to feed back"; the self-audit reads presence-with-zero as "loop ran, clean".

## Classification rule (apply per failure/rework signal)

For each signal, answer one question: **is the root cause task-local, or a defect in a SKILL / harness / hook?**

```
Would a competent run, following the current SKILLs exactly, have still hit this?
  NO  → task-local. The SKILL was right; the run erred. Note it, no diff.
  YES → SKILL/harness defect. The law permitted (or failed to prevent) it.
        → propose a diff to the named SKILL/reference/hook, OR
        → record an explicit reason for deferral (never leave it blank).
```

Bias: when unsure whether it's task-local or a SKILL defect, lean **SKILL defect** — the cost of one unnecessary diff proposal is a line the PO declines; the cost of a missed one is the same class of failure recurring silently. A blank "diff or deferral" cell is the one disallowed state — it is exactly the "タスクを直して終わり" the loop exists to prevent.

## Generation timing

- At milestone arrival, right after `comprehension-report.md` is written.
- `autopilot review` does **not** gate on this file (unlike the comprehension report) — it is a maintenance artifact for the PO, read on the SKILL-maintenance cadence (`docs/skills-self-audit.md`), not required before triaging fixes. But if it is missing for a milestone, `autopilot status` notes it, and the next self-audit generates it from the batch's logs.

## Template

```markdown
# Skill Retrospective — {Milestone label} (Sprints {list})

_Generated at milestone arrival. Failure/rework → SKILL diff, or an explicit reason not to._

**Signals this batch:** {N} (compromises {c}, overlooked {o}, reopens {r}, ungrounded decisions {d}, recurring concern themes {t}); concerns empty rate {e}% (high ⇒ sensor under-elicited, not "all clear")

| # | Signal (source) | What happened | Root cause | Diff proposal — or reason for deferral |
|---|---|---|---|---|
| 1 | compromise · Sa3f9c2-3 | OAuth assertion weakened to `toBeTruthy` to avoid mock work | SKILL defect — `test-discipline.md` Rule 6 scan doesn't flag assertion *weakening* inside a new test file | Propose: extend the L2 diff scan to compare before/after matcher specificity. Target: `sprint/references/test-discipline.md` + `sprint verify` Phase 1.5. |
| 2 | reopen · AC-Sb1e4d8-2-1 | "saved to localStorage" passed tests but no persistence in code | SKILL defect — verifier checked the round-trip but not client-side persistence surfaces | Propose: add a persistence-surface check to `verifier-agent.md`. |
| 3 | compromise · Sc11a-1 | one-off flaky timing in an unrelated module | task-local — no SKILL implicated | Deferral: environmental flake, filed to backlog; no law change. |
| 4 | concerns · theme `latency-feedback` (×3: Sa3f9c2-2, Sb1e4d8-1, Sc11a-2) | recurring unease: AC-satisfying flows with no feedback during a 1–2s wait — each passed, but the pattern repeats | SKILL/spec gap — no AC or DESIGN_PRINCIPLE requires latency feedback, so the mesh lets it through every time | Propose: add a "perceived-latency feedback" acceptance guideline to `DESIGN_PRINCIPLES` (or a default AC in `sprint plan`). One-off concerns get no diff; this one recurs. |

## Deferred (carried from prior milestones)

<!-- Signals classified as SKILL defects in a past retrospective whose diff has not
     yet been applied/declined. If the same defect appears here across 2+ milestones,
     the loop is stalling — flag it to the PO (self-audit item 1 基準). -->
- (none)
```

## Cross-references

- `docs/skills-self-audit.md` — the periodic roll-up and PO-approval gate this artifact feeds. Item 1's 基準 ("失敗が SKILL に還元されない状態が 2 sprint 以上続いたら報告") is checked by reading these retrospectives across milestones; the **Deferred** section is what makes a stall visible.
- `comprehension-report-template.md` — the PO-facing "what changed" report written just before this one. Different audience: that one is for understanding the *product*; this one is for maintaining the *law*. Keep them separate; do not merge.
- `COMPROMISES_SCHEMA.json` / `../../sprint/references/VERIFICATION_REPORT_SCHEMA.json` / `../../sprint/references/REOPEN_SCHEMA.json` — the machine-readable inputs enumerated above.
- `../../../hooks/README.md` → "Seeded-violation drill" — item 2's net-health check; a drill that lets a violation through is itself a signal for this retrospective.
