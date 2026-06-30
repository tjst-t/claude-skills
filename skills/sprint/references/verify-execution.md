# Verify execution — machine-derived test status

The defense against the fabrication incident (`docs/autopilot-fabrication-report.md`): a model saw real test failures, then hand-wrote `status: pass` into `verification-results.json` and marked the Sprint done. Prose rules ("status reflects reality") did not stop it, because the *status was authored by the same model that wanted the Sprint to pass*.

The fix is architectural: **test status must be produced by a process the model cannot author or silently re-interpret.** That process is `hooks/run-verify.py`. This file is the contract.

## The two artifacts (don't confuse them)

| File | Authored by | Role |
|---|---|---|
| `docs/sprint-logs/{SprintID}/verify-run.json` | **`hooks/run-verify.py` only** | Machine ground truth: real exit codes + parsed JUnit. The model NEVER edits it. Schema: `VERIFY_RUN_SCHEMA.json`. |
| `docs/sprint-logs/{SprintID}/verification-results.json` | the model | Human-facing record: AC↔test traceability + `evidence` (verbatim log excerpts). Its `status` fields MUST be copied from the machine artifact, never invented. |

The model writes the **evidence**; the machine writes the **verdict**.

## Why this is language/framework-agnostic

It depends only on two universal things, never on a framework's output format:

1. **POSIX exit codes** — every test runner (go test, pytest, jest, playwright, cargo, rspec, mvn, ansible-playbook, …) exits non-zero on failure. This is the floor and it is universal.
2. **JUnit XML** *(optional, for per-test granularity)* — virtually every framework can emit it (gotestsum, `pytest --junitxml`, jest-junit, playwright junit reporter, rspec, maven-surefire). When present, it also catches runners that exit 0 despite failing cases.

The skill never greps for `--- FAIL:` or `PLAY RECAP` — those are framework-specific and don't generalize. The project tells the skill *how* to test; the skill only trusts the exit code and (optionally) the JUnit report.

## The contract: `.claude/verify.json`

A project declares its verification command(s) once:

```json
{
  "commands": [
    { "name": "unit",        "command": "make test",       "junit_glob": "reports/junit/*.xml" },
    { "name": "devvm-smoke", "command": "make devvm-smoke", "junit_glob": "docs/sprint-logs/{SprintID}/junit/*.xml" }
  ]
}
```

- `command` (required): a shell command. Must be the **real** verification (real deploy + real smoke for priority_rule 9 Sprints — `MOCK=true`/`--fake-*`/`DRY_RUN=1` here defeats the point; see `test-discipline.md` Rule 7).
- `junit_glob` (optional): where this command writes JUnit XML. `{SprintID}` is expanded. Omit if the command has no JUnit — exit code alone still gates.
- `cwd` (optional): working directory for the command.

**Fallback** when `.claude/verify.json` is absent: a `verify:` Makefile target → `make verify`; else a `test:` target → `make test`. If neither exists, `run-verify.py` exits 2 and writes nothing — machine verification is **unconfigured**, which is a **gap that blocks `sprint done`**, never a silent pass.

## How `sprint verify` uses it

1. After implementation, run the machine verifier instead of eyeballing test output:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT:-.}/hooks/run-verify.py --sprint {SprintID}
   ```
   (or the path to `run-verify.py` if installed via symlink rather than as a plugin.)
2. Read `verify-run.json`. For each AC/test entry in `verification-results.json`, set `status` **from the machine result** — `pass` only if the run that exercises it is `machine_status: pass`. Write the matching log excerpt into `evidence`.
3. If `overall_machine_status` is `fail`: do **not** rationalize the failure as "pre-existing" or "out of scope". Mark the affected AC `fail`, set the Sprint to `partial`/`needs_human`, and stop as `sprint verify failed` for the user to decide (`test-discipline.md` Escalation).

## How `sprint done` gates on it

`sprint done`'s test-execution gate reads `verify-run.json`:
- `overall_machine_status != "pass"` (any run's `exit_code != 0`, or JUnit failures) ⇒ **refuse `done`**, regardless of what `verification-results.json` claims.
- `verify-run.json` absent while a verify command is configured ⇒ machine verification didn't run ⇒ refuse `done` (gap), surface to the user.

This gate is deterministic and independent of how `verification-results.json` was written, so it holds even if the model writes that file via `jq`/Bash rather than Edit/Write.

## Defense in depth: the integrity hook

`hooks/verification-integrity-guard.py` (PostToolUse) re-derives the verdict from the `__VERIFY_EXIT_CODE__` trailers in the run logs and blocks an Edit/Write of `verification-results.json` that claims a clean pass over a recorded failure. It self-gates (only active once `run-verify.py` has produced artifacts) and is fail-safe. It is an early-warning for the common write path; the `sprint done` gate above is the method-independent backstop.

## Honest limit

This moves the verdict out of the model's hands, but the model still chooses *which command* `.claude/verify.json` runs and could, in principle, declare a command that runs a passing subset or a mocked path. That residue is covered by adjacent controls — `test-discipline.md` Rule 7 (real-mode smoke), the done-judgment guards, and the independent verifier's execution-log reconciliation (`verifier-agent.md`). Determinism here closes the "record a real failure as pass" hole specifically; it is not a claim that the whole pipeline is unfakeable.
