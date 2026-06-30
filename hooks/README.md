# Hooks

This directory ships with the `claude-skills` plugin (see `.claude-plugin/plugin.json`). It contains the **hooks** (deterministic backstops the SKILL.md files describe in prose; wiring is in `hooks.json`) plus one **tool** invoked by `sprint verify` (`run-verify.py`).

All hooks are **fail-safe**: any unexpected condition exits 0 (do nothing), so they can never break a session.

## `forbidden-action-guard.py` — PostToolUse (L3 defense)

The third defense layer from `autopilot/SKILL.md` → "Constraints and Forbidden Actions". L1 is the autopilot prompt, L2 is the `sprint verify` diff scan; this is the deterministic last line.

- **Matches**: `Edit` / `Write` / `MultiEdit`.
- **Self-gate**: does nothing unless an autopilot lock (`.claude/autopilot-*.lock`) exists in the project. So it is active only during unattended runs — a human deliberately adding a skip in an interactive session is never blocked.
- **Detects** (in the new content): `it/test/describe.skip`, `xit/xtest/xdescribe`, `@pytest.mark.skip/xfail`, `t.Skip(`, `expect(true).toBe(true)`, `// @ts-ignore` / `@ts-expect-error`, `# noqa`, `# type: ignore`, empty `catch {}`.
- **On a hit**: emits `{"decision": "block", "reason": ...}` so Claude is told to revert the change or record it in `compromises.json` (notify-after), and to stop+escalate for immediate-stop categories.

It does NOT try to detect assertion *weakening* (e.g. `toEqual` → `toBeTruthy`) — that needs the before/after diff, which is the `sprint verify` L2 scan's job (`test-discipline.md` Rule 6). The hook covers the patterns visible in a single edit's new content.

## `verification-integrity-guard.py` — PostToolUse (anti-fabrication)

Blocks the fabrication incident (`docs/autopilot-fabrication-report.md`): a model writing a passing `verification-results.json` over a run that actually failed.

- **Matches**: `Edit` / `Write` / `MultiEdit`, but only acts when the edited file is `verification-results.json`.
- **Self-gate**: does nothing unless `run-verify.py` has produced machine artifacts for that Sprint (`verify-run-*.log` / `verify-run.json`).
- **Ground truth**: re-derives the verdict from the `__VERIFY_EXIT_CODE__:<name>:<code>` trailers in the run logs (and `verify-run.json`). If the machine recorded a failure but the written record claims a clean pass, emits `{"decision": "block", "reason": ...}`.
- It is the early-warning for the direct-write path; the **method-independent** backstop is the `sprint done` machine gate (`sprint/references/verify-execution.md`), which refuses `done` on `overall_machine_status != "pass"` no matter how the file was written.

## `run-verify.py` — tool (machine-authored test verdict), not a hook

Invoked by `sprint verify` (Step 2.0), not wired in `hooks.json`. Runs the project's declared verification (`.claude/verify.json`, or a `verify:`/`test:` Makefile target) and writes the machine-authored `docs/sprint-logs/{SprintID}/verify-run.json` from real **exit codes** + optional **JUnit XML**. Language/framework-agnostic. Full contract: `sprint/references/verify-execution.md`. Run it directly with:

```bash
python3 hooks/run-verify.py --sprint {SprintID}   # exit 0 = all pass, 1 = a run failed, 2 = unconfigured (a gap)
```

## `sprint-done-doc-suggester.py` — Stop (self-improving setup)

Nudges the user to keep ARCHITECTURE.md / `docs/DESIGN/` current after a Sprint completes.

- **Advisory only**: emits a `systemMessage`; never blocks, never forces Claude to continue.
- **Trigger heuristic** (no coupling to the skills): HEAD commit modified `docs/ROADMAP.json` and that change added a Sprint `"status": "done"`.
- **Dedup**: records the HEAD sha in `.claude/.sprint-done-doc-suggester-seen` so it fires at most once per done-commit.

## Enabling the hooks

**As a plugin (recommended)** — install the plugin and the hooks are wired automatically via `hooks.json` (using `${CLAUDE_PLUGIN_ROOT}`).

**Manually (symlink install of the skills only)** — the symlink `install.sh` installs skills but not hooks. To enable the hooks, add them to your `~/.claude/settings.json` (adjust the absolute path):

```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "/abs/path/to/claude-skills/hooks/forbidden-action-guard.py" },
          { "type": "command", "command": "/abs/path/to/claude-skills/hooks/verification-integrity-guard.py" }
        ] }
    ],
    "Stop": [
      { "matcher": "",
        "hooks": [{ "type": "command", "command": "/abs/path/to/claude-skills/hooks/sprint-done-doc-suggester.py" }] }
    ]
  }
}
```

**Disabling** — remove the entries from settings.json, or disable the plugin. Because every hook self-gates (autopilot lock / machine artifacts present / done-commit) and fails safe, leaving them enabled is low-risk, but they are opt-out at any time.

## Requirements

- `python3` on `PATH` (no third-party packages).
- The Stop hook calls `git`; outside a git repo it simply does nothing.

> These hooks are newer than the skill prose and have not been battle-tested across many projects yet. Validate them in a real project before relying on them in CI-like automation.
