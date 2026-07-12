#!/usr/bin/env python3
"""
Seeded-violation tests for the claude-skills hooks (the verification net).

Item 2 of docs/skills-self-audit.md — "検証網の健全性テスト". A verification net
that nobody tests rots silently, and a rotted net is invisible precisely when it
matters (the fabrication incident, docs/autopilot-fabrication-report.md, was a
hole in the net that went undetected until it caused damage). Each test here
SEEDS a known violation — a skipped test, a `pass` written over a real failure,
a failing run — and asserts the matching hook catches it; symmetrically, it
asserts the hook stays silent when it should (self-gate off, clean content,
already-admitted failure). A red test here is not a flaky test to silence: it is
the net's enforcement weakening. Treat it as a defect in the *verification* skill
and feed it through the self-audit loop (item 1).

Black-box by construction: every hook is invoked exactly as Claude Code invokes
it — a subprocess reading the event JSON on stdin — so the real contract is
exercised, not internal functions. Stdlib only; no third-party deps.

Run:  python3 hooks/tests/test_hooks.py
  or: python3 -m unittest discover -s hooks/tests
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent
FORBIDDEN = HOOKS / "forbidden-action-guard.py"
INTEGRITY = HOOKS / "verification-integrity-guard.py"
RUN_VERIFY = HOOKS / "run-verify.py"
DOC_SUGGESTER = HOOKS / "sprint-done-doc-suggester.py"


def run_hook(hook, event):
    """Invoke a stdin-JSON hook the way Claude Code does; return (exit_code, stdout)."""
    proc = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def decision(stdout):
    """Parse a hook's stdout into its emitted dict, or {} if it stayed silent."""
    out = stdout.strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except Exception:
        return {}


class TestForbiddenActionGuard(unittest.TestCase):
    """L3 forbidden-action guard: blocks test-disabling / error-swallowing edits
    during an autopilot run, and is silent otherwise."""

    # One seed per degradation category the hook claims to catch. If a new pattern
    # is added to the hook, add its seed here so the net stays honest.
    SEEDS = [
        ("jest/mocha skip", "it.skip('x', () => { expect(f()).toBe(1) })"),
        ("xtest", "xit('x', () => {})"),
        ("pytest skip", "@pytest.mark.skip\ndef test_x():\n    pass"),
        ("go t.Skip", "func TestX(t *testing.T) { t.Skip() }"),
        ("tautological assertion", "expect(true).toBe(true)"),
        ("ts-ignore", "// @ts-ignore\nconst x: number = y"),
        ("noqa", "import os  # noqa"),
        ("type: ignore", "x = foo()  # type: ignore"),
        ("empty catch", "try { risky() } catch {}"),
    ]

    def _project_with_lock(self, tmp):
        claude = Path(tmp) / ".claude"
        claude.mkdir(parents=True, exist_ok=True)
        (claude / "autopilot-main.lock").write_text("pid 123\n2026-07-11\n")
        return tmp

    def test_blocks_each_seeded_violation_during_autopilot(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._project_with_lock(tmp)
            for label, content in self.SEEDS:
                with self.subTest(seed=label):
                    ec, out = run_hook(FORBIDDEN, {
                        "cwd": tmp,
                        "tool_name": "Write",
                        "tool_input": {"file_path": f"{tmp}/x.test.ts", "content": content},
                    })
                    self.assertEqual(decision(out).get("decision"), "block",
                                     f"{label} was not blocked: {out!r}")
                    self.assertEqual(ec, 0, "guard must always exit 0 (fail-safe)")

    def test_self_gate_no_lock_never_blocks(self):
        # No autopilot lock => interactive session => the guard must not interfere.
        with tempfile.TemporaryDirectory() as tmp:
            ec, out = run_hook(FORBIDDEN, {
                "cwd": tmp,
                "tool_name": "Write",
                "tool_input": {"file_path": f"{tmp}/x.test.ts",
                               "content": "it.skip('x', () => {})"},
            })
            self.assertEqual(decision(out), {}, "guard fired without an autopilot lock")
            self.assertEqual(ec, 0)

    def test_clean_content_not_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._project_with_lock(tmp)
            ec, out = run_hook(FORBIDDEN, {
                "cwd": tmp,
                "tool_name": "Write",
                "tool_input": {"file_path": f"{tmp}/x.test.ts",
                               "content": "it('x', () => { expect(f()).toBe(3) })"},
            })
            self.assertEqual(decision(out), {}, "clean content was blocked (false positive)")

    def test_multiedit_new_string_is_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._project_with_lock(tmp)
            ec, out = run_hook(FORBIDDEN, {
                "cwd": tmp,
                "tool_name": "MultiEdit",
                "tool_input": {"file_path": f"{tmp}/x.test.ts",
                               "edits": [{"new_string": "ok()"}, {"new_string": "t.Skip()"}]},
            })
            self.assertEqual(decision(out).get("decision"), "block")


class TestVerificationIntegrityGuard(unittest.TestCase):
    """Anti-fabrication guard: blocks writing a passing verification-results.json
    over a run the machine recorded as failing."""

    def _seed(self, tmp, *, machine, results_claim):
        """machine: 'fail' | 'pass' | None (no machine artifacts). Returns the
        verification-results.json path that the edit event targets."""
        logdir = Path(tmp) / "docs" / "sprint-logs" / "S1"
        logdir.mkdir(parents=True, exist_ok=True)
        if machine is not None:
            exit_code = 1 if machine == "fail" else 0
            (logdir / "verify-run-unit.log").write_text(
                f"$ make test\n...output...\n__VERIFY_EXIT_CODE__:unit:{exit_code}\n")
            (logdir / "verify-run.json").write_text(json.dumps(
                {"overall_machine_status": machine}))
        results = logdir / "verification-results.json"
        results.write_text(json.dumps(results_claim))
        return results

    def _event(self, results_path):
        return {"tool_name": "Write", "tool_input": {"file_path": str(results_path)}}

    def test_blocks_pass_over_machine_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = self._seed(tmp, machine="fail", results_claim={
                "summary": {"pass": 3, "fail": 0},
                "tests": [{"name": "t1", "status": "pass"}]})
            ec, out = run_hook(INTEGRITY, self._event(results))
            self.assertEqual(decision(out).get("decision"), "block",
                             "did NOT block a fabricated pass over a machine failure")
            self.assertEqual(ec, 0)

    def test_allows_when_results_admit_failure(self):
        # The honest path: the machine failed AND the record says so — never block.
        with tempfile.TemporaryDirectory() as tmp:
            results = self._seed(tmp, machine="fail", results_claim={
                "summary": {"pass": 2, "fail": 1},
                "tests": [{"name": "t1", "status": "fail"}]})
            ec, out = run_hook(INTEGRITY, self._event(results))
            self.assertEqual(decision(out), {}, "blocked an honestly-recorded failure")

    def test_self_gate_without_machine_artifacts(self):
        # No run-verify.py artifacts => project hasn't adopted the wrapper => silent.
        with tempfile.TemporaryDirectory() as tmp:
            results = self._seed(tmp, machine=None, results_claim={
                "summary": {"fail": 0}, "tests": [{"status": "pass"}]})
            ec, out = run_hook(INTEGRITY, self._event(results))
            self.assertEqual(decision(out), {})

    def test_allows_pass_over_machine_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = self._seed(tmp, machine="pass", results_claim={
                "summary": {"fail": 0}, "tests": [{"status": "pass"}]})
            ec, out = run_hook(INTEGRITY, self._event(results))
            self.assertEqual(decision(out), {})


class TestRunVerify(unittest.TestCase):
    """Machine-authored verdict tool: status comes from real exit codes + JUnit,
    never from reading output. Unconfigured is a gap (exit 2), never a pass."""

    def _project(self, tmp, verify_cfg):
        root = Path(tmp)
        (root / ".claude").mkdir(parents=True, exist_ok=True)
        (root / ".claude" / "verify.json").write_text(json.dumps(verify_cfg))
        (root / "docs").mkdir(parents=True, exist_ok=True)
        return root

    def _run(self, root):
        proc = subprocess.run(
            [sys.executable, str(RUN_VERIFY), "--sprint", "S1", "--root", str(root)],
            capture_output=True, text=True)
        return proc.returncode

    def _verdict(self, root):
        return json.loads(
            (root / "docs" / "sprint-logs" / "S1" / "verify-run.json").read_text())

    def test_failing_command_is_fail_and_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, {"commands": [{"name": "unit", "command": "exit 1"}]})
            self.assertEqual(self._run(root), 1)
            self.assertEqual(self._verdict(root)["overall_machine_status"], "fail")

    def test_passing_command_is_pass_and_exit_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._project(tmp, {"commands": [{"name": "unit", "command": "exit 0"}]})
            self.assertEqual(self._run(root), 0)
            self.assertEqual(self._verdict(root)["overall_machine_status"], "pass")

    def test_unconfigured_is_exit_2_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir(parents=True)  # no .claude/verify.json, no Makefile
            self.assertEqual(self._run(root), 2, "unconfigured must be a gap, not a pass")

    def test_exit0_but_junit_failure_still_fails(self):
        # Defends against runners that exit 0 despite failing cases.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir(parents=True)
            (root / "reports" / "j.xml").write_text(
                '<testsuite><testcase classname="a" name="b"><failure/></testcase></testsuite>')
            self._project(tmp, {"commands": [
                {"name": "unit", "command": "exit 0", "junit_glob": "reports/j.xml"}]})
            self.assertEqual(self._run(root), 1)
            self.assertEqual(self._verdict(root)["overall_machine_status"], "fail")


@unittest.skipUnless(shutil.which("git"), "git not on PATH")
class TestSprintDoneDocSuggester(unittest.TestCase):
    """Stop-hook nudge after a Sprint is marked done — advisory, deduped once per commit."""

    def _git(self, root, *args):
        return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)

    def _repo_with_done_commit(self, tmp):
        root = Path(tmp)
        self._git(root, "init", "-q")
        self._git(root, "config", "user.email", "t@example.com")
        self._git(root, "config", "user.name", "tester")
        (root / "docs").mkdir()
        (root / "docs" / "ROADMAP.json").write_text(
            json.dumps({"sprints": {"S1": {"status": "done"}}}, indent=2))
        self._git(root, "add", "-A")
        self._git(root, "commit", "-q", "-m", "complete Sprint S1")
        return root

    def test_nudges_after_done_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo_with_done_commit(tmp)
            ec, out = run_hook(DOC_SUGGESTER, {"cwd": str(root)})
            self.assertIn("systemMessage", decision(out))
            self.assertEqual(ec, 0)

    def test_dedup_second_call_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo_with_done_commit(tmp)
            run_hook(DOC_SUGGESTER, {"cwd": str(root)})          # first fires, writes sentinel
            ec, out = run_hook(DOC_SUGGESTER, {"cwd": str(root)})  # same HEAD => deduped
            self.assertEqual(decision(out), {}, "nudge repeated for the same commit")


if __name__ == "__main__":
    unittest.main(verbosity=2)
