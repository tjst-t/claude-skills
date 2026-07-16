#!/usr/bin/env python3
"""
Seeded-violation tests for run-guards.py (the machine-run guard scanner).

Same contract as test_hooks.py: each test SEEDS a known violation into a real
temp git repo, runs run-guards.py as a subprocess (exactly as `sprint verify`
invokes it), and asserts the matching check reports hits — and symmetrically
that a clean repo reports clean. A red test here means the mechanical half of
the done-judgment guards weakened; treat it as a defect in the verification
skill (self-audit item 1). When a detection pattern is added or broadened in
run-guards.py, add its seed here so the net stays honest.

Run:  python3 hooks/tests/test_run_guards.py
  or: python3 -m unittest discover -s hooks/tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent
RUN_GUARDS = HOOKS / "run-guards.py"


class GuardsRepo:
    """A throwaway git repo with a base commit; seed files, commit, scan."""

    def __init__(self, tmp):
        self.root = Path(tmp)
        self._git("init", "-q")
        self._git("config", "user.email", "t@t")
        self._git("config", "user.name", "t")
        self.write("README.md", "seed\n")
        self._git("add", "-A")
        self._git("commit", "-qm", "base")
        self.base = self._git("rev-parse", "HEAD").strip()

    def _git(self, *args):
        proc = subprocess.run(["git", *args], cwd=self.root,
                              capture_output=True, text=True)
        return proc.stdout

    def write(self, rel, content):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def commit(self):
        self._git("add", "-A")
        self._git("commit", "-qm", "seeded change")

    def scan(self, base=None):
        proc = subprocess.run(
            [sys.executable, str(RUN_GUARDS), "--sprint", "Stest01",
             "--base", base if base is not None else self.base,
             "--root", str(self.root)],
            capture_output=True, text=True,
        )
        artifact = self.root / "docs" / "sprint-logs" / "Stest01" / "guards-run.json"
        data = json.loads(artifact.read_text()) if artifact.is_file() else None
        return proc.returncode, data

    def result(self, data, check_id):
        return next(c for c in data["checks"] if c["id"] == check_id)


class TestDiffChecks(unittest.TestCase):
    """Diff-based scans: seeded degradations in added lines are reported."""

    SEEDS = [
        ("forbidden_test_disabled", "tests/a.spec.ts", "it.skip('x', () => {})\n"),
        ("forbidden_test_disabled", "tests/b.spec.ts", "xit('x', () => {})\n"),
        ("forbidden_test_disabled", "tests/c_test.py", "@pytest.mark.skip\ndef test_x():\n    pass\n"),
        ("forbidden_test_disabled", "pkg/a_test.go", "func TestX(t *testing.T) { t.Skip() }\n"),
        ("forbidden_test_disabled", "tests/d.spec.ts", "expect(true).toBe(true)\n"),
        ("forbidden_error_swallowed", "src/a.ts", "try { risky() } catch {}\n"),
        ("forbidden_error_swallowed", "src/b.ts", "// @ts-ignore\nconst x = y\n"),
        ("forbidden_error_swallowed", "src/c.py", "import os  # noqa\n"),
        ("forbidden_type_relaxed", "src/d.ts", "const v = data as any\n"),
        ("guard6_deferred_comments", "internal/x.go", "// TODO: Phase 2 で対応\n"),
        ("guard6_deferred_comments", "cmd/y.go", "// Sprint 3 で本実装を追加\n"),
    ]

    def test_seeded_violations_are_caught(self):
        for check_id, rel, content in self.SEEDS:
            with self.subTest(seed=rel):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = GuardsRepo(tmp)
                    repo.write(rel, content)
                    repo.commit()
                    code, data = repo.scan()
                    self.assertEqual(code, 0)
                    result = repo.result(data, check_id)
                    self.assertEqual(result["status"], "hits",
                                     f"{check_id} missed seed in {rel}")

    def test_guard2_nil_injection(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            body = "\n".join(f"if s.{dep} != nil {{" for dep in
                             ("Vault", "DNS", "Mon")) + "\n"
            repo.write("internal/svc.go", body)
            repo.commit()
            _, data = repo.scan()
            result = repo.result(data, "guard2_nil_injection")
            self.assertEqual(result["hit_count"], 3)

    def test_clean_diff_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write("src/clean.ts", "const n: number = 1\n")
            repo.write("internal/ok.go", "x := compute()\n")
            repo.commit()
            _, data = repo.scan()
            for cid in ("forbidden_test_disabled", "forbidden_error_swallowed",
                        "forbidden_type_relaxed", "guard2_nil_injection",
                        "guard6_deferred_comments"):
                self.assertEqual(repo.result(data, cid)["status"], "clean", cid)

    def test_no_base_skips_diff_checks_visibly(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            code, data = repo.scan(base="")
            self.assertEqual(code, 0)
            self.assertEqual(repo.result(data, "forbidden_test_disabled")["status"],
                             "skipped")

    def test_preexisting_violation_not_counted(self):
        """Only lines ADDED since base are scanned — pre-existing debt is not
        this Sprint's degradation."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write("tests/old.spec.ts", "it.skip('legacy', () => {})\n")
            repo.commit()
            new_base = repo._git("rev-parse", "HEAD").strip()
            repo.write("src/new.ts", "const clean = 1\n")
            repo.commit()
            _, data = repo.scan(base=new_base)
            self.assertEqual(repo.result(data, "forbidden_test_disabled")["status"],
                             "clean")


class TestTreeChecks(unittest.TestCase):
    def test_guard3_mock_mode_smoke(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write("tests/acceptance/devvm/smoke_test.go",
                       'os.Setenv("MOCK", "true")\n')
            repo.commit()
            _, data = repo.scan()
            self.assertEqual(repo.result(data, "guard3_mock_mode_smoke")["status"],
                             "hits")

    def test_guard3_skipped_without_smoke_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write("src/app.ts", "ok\n")
            repo.commit()
            _, data = repo.scan()
            self.assertEqual(repo.result(data, "guard3_mock_mode_smoke")["status"],
                             "skipped")

    def test_guard7_forbidden_and_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write(".claude/guards.json", json.dumps({
                "adr_checks": [
                    {"adr": "ADR-0014", "type": "forbidden_grep",
                     "paths": ["internal/"], "pattern": r"fmt\.Sprintf\(\"tenants/"},
                    {"adr": "ADR-0033", "type": "required_grep",
                     "paths": ["internal/"], "pattern": "func NewPhysicalKey"},
                ]}))
            repo.write("internal/server/key.go",
                       'k := fmt.Sprintf("tenants/%s", id)\n')  # forbidden present
            repo.commit()                                       # required absent
            _, data = repo.scan()
            result = repo.result(data, "guard7_adr_machine_checks")
            self.assertEqual(result["status"], "hits")
            texts = " ".join(h["text"] for h in result["hits"])
            self.assertIn("ADR-0014", texts)
            self.assertIn("ADR-0033", texts)

    def test_guard7_reads_adr_machine_check_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write("docs/DESIGN/adr/ADR-0099-example.md",
                       "# ADR-0099\n\nmachine_check:\n\n```json\n"
                       '[{"type": "forbidden_grep", "paths": ["internal/"], '
                       '"pattern": "legacyCall\\\\("}]\n```\n')
            repo.write("internal/a.go", "legacyCall(x)\n")
            repo.commit()
            _, data = repo.scan()
            self.assertEqual(repo.result(data, "guard7_adr_machine_checks")["status"],
                             "hits")

    def test_guard8_missing_destructive_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write(".claude/guards.json",
                       json.dumps({"data_paths": ["internal/server/"]}))
            repo.write("internal/server/store.go", "func Put() {}\n")
            repo.commit()
            _, data = repo.scan()
            result = repo.result(data, "guard8_destructive_tests")
            self.assertEqual(result["status"], "hits")  # all 3 scenarios missing

    def test_guard8_na_when_data_path_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write(".claude/guards.json",
                       json.dumps({"data_paths": ["internal/server/"]}))
            repo.write("web/ui.tsx", "export const X = 1\n")
            repo.commit()
            _, data = repo.scan()
            self.assertEqual(repo.result(data, "guard8_destructive_tests")["status"],
                             "clean")

    def test_e2e_network_mock_and_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write("tests/e2e/vm.e2e.spec.ts",
                       "await page.route('**/api/**', mock)\n"
                       "await page.waitForTimeout(2000)\n")
            repo.commit()
            _, data = repo.scan()
            self.assertEqual(repo.result(data, "e2e_network_mock")["status"], "hits")
            self.assertEqual(repo.result(data, "e2e_wait_for_timeout")["status"],
                             "hits")

    def test_prototype_testid_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write("prototype/dash.html",
                       '<div data-testid="vm-list"></div>'
                       '<button data-testid="vm-start-btn"></button>\n')
            repo.write("src/Dash.tsx", 'export const l = <ul data-testid="vm-list"/>\n')
            repo.commit()
            _, data = repo.scan()
            result = repo.result(data, "prototype_testid_drift")
            self.assertEqual(result["status"], "hits")
            self.assertIn("vm-start-btn", result["hits"][0]["text"])

    def test_prototype_old_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write("prototype/old/S1/done.html",
                       '<div data-testid="archived-thing"></div>\n')
            repo.commit()
            _, data = repo.scan()
            self.assertEqual(repo.result(data, "prototype_testid_drift")["status"],
                             "skipped")

    def test_call_paths_reports_zero_hit_couplings(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write(".claude/guards.json", json.dumps({
                "call_paths": [
                    {"name": "core->workflow", "paths": ["internal/"],
                     "pattern": "ExecuteWorkflow|SignalWorkflow"}]}))
            repo.write("internal/server/api.go", "func Handle() {}\n")
            repo.commit()
            _, data = repo.scan()
            self.assertEqual(repo.result(data, "call_paths")["status"], "hits")


class TestArtifact(unittest.TestCase):
    def test_artifact_is_machine_marked(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = GuardsRepo(tmp)
            repo.write("src/a.ts", "ok\n")
            repo.commit()
            code, data = repo.scan()
            self.assertEqual(code, 0)
            self.assertTrue(data["$machine_authored"])
            self.assertEqual(data["sprint"], "Stest01")
            self.assertIn("summary", data)

    def test_missing_sprint_id_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            GuardsRepo(tmp)  # no ROADMAP, no --sprint
            proc = subprocess.run(
                [sys.executable, str(RUN_GUARDS), "--root", tmp],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
