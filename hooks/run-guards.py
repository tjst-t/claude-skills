#!/usr/bin/env python3
"""
run-guards.py — the machine-run half of the done-judgment guards and the
forbidden-degradation scan, for `sprint verify` / `sprint done`.

Most guards in `sprint/references/sprint-done-judgment.md` and the Rule 6
forbidden-degradation scan (`sprint/references/test-discipline.md`) are pure
pattern scans. Having the model run those greps by hand costs tokens three
times over (implementer pass, verifier re-derivation, done-gate re-check) and
is less reliable than a script. This wrapper runs every mechanical scan ONCE
and writes a machine-authored fact sheet to
`docs/sprint-logs/{SprintID}/guards-run.json`.

Division of labor (same architecture as run-verify.py):
  - The MACHINE authors the facts: which pattern hit, where, how many times.
    Models MUST NOT edit guards-run.json.
  - The MODEL applies the policy: triage each hit (e.g. a guard6 deferred
    comment is allowed only with a backlog reference; guard2 nil-injection
    needs the >=3-per-Story threshold; forbidden hits become compromises.json
    entries). Policy lives in the skill docs, not here.
  - A `hits` status is therefore NOT automatically a failure — it is a fact
    the model must dispose of explicitly. What the model can no longer do is
    skip a scan, mis-run a grep, or "not notice" a pattern.

Checks (skipped cleanly when their inputs don't exist):
  diff-based (need --base):
    forbidden_test_disabled   it/test/describe.skip, xit/xtest, @pytest.mark.skip/xfail,
                              t.Skip(, expect(true).toBe(true)      [test-discipline Rule 6]
    forbidden_error_swallowed empty catch {}, @ts-ignore/@ts-expect-error, # noqa,
                              # type: ignore                        [Rule 6]
    forbidden_type_relaxed    new `: any` / `as any` in TS/JS       [Rule 6]
    guard2_nil_injection      Go multi-dep nil-guard anti-pattern   [Guard 2]
    guard6_deferred_comments  TODO Phase-N / Sprint-N-で実装 residue [Guard 6]
  tree-based:
    guard3_mock_mode_smoke    MOCK=true / --fake- / DRY_RUN=1 / InMemoryStore
                              in the real-smoke dir                 [Guard 3]
    guard7_adr_machine_checks forbidden/required greps from .claude/guards.json
                              `adr_checks` + `machine_check:` JSON blocks in ADR docs
                                                                    [Guard 7]
    guard8_destructive_tests  destructive multi-version test presence when the
                              diff touches a configured data path   [Guard 8]
    call_paths                configured cross-service grep hit counts (the model
                              judges applicability per AC)          [Guard 5]
    e2e_network_mock          page.route(/MSW/setupServer/vi.mock in *.e2e.spec.*
                                                                    [Rule 2/4]
    e2e_wait_for_timeout      waitForTimeout( in e2e/mock specs (time-domain triage)
    prototype_testid_drift    data-testid in prototype/*.html missing from source

Optional project config `.claude/guards.json` (all keys optional):
  {
    "smoke_dir": "tests/acceptance/devvm/",
    "mock_markers": ["MOCK=true", "--fake-", "DRY_RUN=1", "fake_core: true", "InMemoryStore"],
    "deferred_comment_paths": ["cmd/", "internal/", "ansible/"],
    "adr_glob": "docs/DESIGN/adr/*.md",
    "adr_checks": [
      { "adr": "ADR-0014", "type": "forbidden_grep",
        "paths": ["internal/server/"], "pattern": "fmt\\.Sprintf\\(\"tenants/" }
    ],
    "data_paths": ["internal/server/", "cmd/storage-core/"],
    "destructive_test_dir": "tests/acceptance/devvm/",
    "destructive_patterns": ["version_no\\s*=\\s*1", "Demote.*Recall|Recall.*Demote", "restart|kill -9|systemctl restart"],
    "call_paths": [
      { "name": "storage-core -> workflow", "paths": ["internal/server/"],
        "pattern": "ExecuteWorkflow|SignalWorkflow" }
    ]
  }
ADR-embedded checks: a `machine_check:` line in an ADR markdown followed by a
```json fenced block containing [{"type": "forbidden_grep"|"required_grep",
"paths": [...], "pattern": "..."}] is picked up automatically.

Usage:
  run-guards.py [--sprint SxxxxxX] [--base SHA] [--root DIR]

Exit code: 0 = scans ran and guards-run.json was written (hits or not),
2 = could not run / internal error. Hits never change the exit code — they
are facts for the model to triage, not verdicts.
"""
import sys
import os
import re
import json
import glob
import argparse
import subprocess

MAX_HITS_PER_CHECK = 50

FORBIDDEN_TEST_DISABLED = re.compile(
    r"(?:\b(?:it|test|describe)\.skip\s*\(|\bx(?:it|test|describe)\s*\(|"
    r"@pytest\.mark\.(?:skip|xfail)|\bt\.Skip\(|expect\(true\)\.toBe\(true\))"
)
FORBIDDEN_ERROR_SWALLOWED = re.compile(
    r"(?:catch\s*(?:\([^)]*\))?\s*\{\s*\}|@ts-ignore|@ts-expect-error|"
    r"#\s*noqa|#\s*type:\s*ignore)"
)
FORBIDDEN_TYPE_RELAXED = re.compile(r"(?::\s*any\b|\bas\s+any\b)")
TYPE_RELAXED_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mts", ".cts")

GUARD2_NIL_INJECTION = re.compile(
    r"if\s+[a-zA-Z_][a-zA-Z0-9_]*\.[A-Z][a-zA-Z0-9_]*\s*!=\s*nil\s*\{"
)

GUARD6_DEFERRED = re.compile(
    r"(?://|#)\s*(?:TODO.*Phase\s*[0-9]|Sprint\s*[0-9].*で.*(?:実装|追加)|"
    r"未実装.*Phase|(?:Phase|Sprint)\s*[0-9].*で.*replace)"
)

E2E_NETWORK_MOCK = re.compile(
    r"(?:page\.route\s*\(|\bMSW\b|setupServer|fetch\.mockImplementation|"
    r"vi\.mock\s*\(|jest\.mock\s*\()"
)
E2E_WAIT_FOR_TIMEOUT = re.compile(r"waitForTimeout\s*\(")

DATA_TESTID = re.compile(r'data-testid="([^"]+)"')

DEFAULTS = {
    "smoke_dir": "tests/acceptance/devvm/",
    "mock_markers": ["MOCK=true", 'Setenv("MOCK"', "-fake-", "DRY_RUN=1",
                     "fake_core: true", "InMemoryStore"],
    "deferred_comment_paths": ["cmd/", "internal/", "ansible/"],
    "adr_glob": "docs/DESIGN/adr/*.md",
    "adr_checks": [],
    "data_paths": [],
    "destructive_test_dir": "tests/acceptance/devvm/",
    "destructive_patterns": [
        r"version_no\s*=\s*1",
        r"Demote.*Recall|Recall.*Demote",
        r"restart|kill -9|systemctl restart",
    ],
    "call_paths": [],
}


def detect_sprint(root):
    try:
        with open(os.path.join(root, "docs", "ROADMAP.json")) as f:
            return json.load(f).get("progress", {}).get("current_sprint", "") or ""
    except Exception:
        return ""


def load_config(root):
    cfg_path = os.path.join(root, ".claude", "guards.json")
    cfg = dict(DEFAULTS)
    source = "defaults"
    if os.path.isfile(cfg_path):
        try:
            with open(cfg_path) as f:
                user = json.load(f)
            cfg.update({k: v for k, v in user.items() if k in DEFAULTS})
            source = "declared (.claude/guards.json)"
        except Exception as e:
            source = f"defaults (.claude/guards.json unreadable: {e})"
    return cfg, source


def git(root, *args):
    proc = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True
    )
    return proc.returncode, proc.stdout


def added_lines(root, base):
    """Parse `git diff base..HEAD` into [(file, new_lineno, text)] of added lines."""
    code, out = git(root, "diff", "--no-color", f"{base}..HEAD")
    if code != 0:
        return None
    hits = []
    path, lineno = None, 0
    for raw in out.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
        elif raw.startswith("+++ "):
            path = None  # /dev/null etc.
        elif raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            lineno = int(m.group(1)) - 1 if m else 0
        elif raw.startswith("+") and not raw.startswith("+++"):
            lineno += 1
            if path:
                hits.append((path, lineno, raw[1:]))
        elif not raw.startswith("-") and not raw.startswith("\\"):
            lineno += 1
    return hits


def tracked_files(root, prefix=""):
    code, out = git(root, "ls-files", "--", prefix or ".")
    if code != 0:
        return []
    return [l for l in out.splitlines() if l]


def scan_file(root, relpath, regex):
    hits = []
    try:
        with open(os.path.join(root, relpath), errors="replace") as f:
            for n, line in enumerate(f, 1):
                if regex.search(line):
                    hits.append({"file": relpath, "line": n, "text": line.strip()[:200]})
    except Exception:
        pass
    return hits


def check(check_id, kind, hits, note=None):
    truncated = len(hits) > MAX_HITS_PER_CHECK
    return {
        "id": check_id,
        "kind": kind,
        "status": "hits" if hits else "clean",
        "hit_count": len(hits),
        "hits": hits[:MAX_HITS_PER_CHECK],
        "truncated": truncated,
        "note": note,
    }


def skipped(check_id, kind, note):
    return {"id": check_id, "kind": kind, "status": "skipped", "hit_count": 0,
            "hits": [], "truncated": False, "note": note}


def diff_checks(root, base, cfg):
    """All checks that scan lines ADDED between base and HEAD."""
    results = []
    if not base:
        note = "no --base given; pass the Sprint base SHA to enable diff scans"
        for cid in ("forbidden_test_disabled", "forbidden_error_swallowed",
                    "forbidden_type_relaxed", "guard2_nil_injection",
                    "guard6_deferred_comments"):
            results.append(skipped(cid, "diff", note))
        return results
    lines = added_lines(root, base)
    if lines is None:
        note = f"git diff {base}..HEAD failed; is the base SHA valid?"
        for cid in ("forbidden_test_disabled", "forbidden_error_swallowed",
                    "forbidden_type_relaxed", "guard2_nil_injection",
                    "guard6_deferred_comments"):
            results.append(skipped(cid, "diff", note))
        return results

    def match(regex, file_filter=None):
        return [{"file": f, "line": n, "text": t.strip()[:200]}
                for (f, n, t) in lines
                if (file_filter is None or file_filter(f)) and regex.search(t)]

    results.append(check("forbidden_test_disabled", "diff",
                         match(FORBIDDEN_TEST_DISABLED)))
    results.append(check("forbidden_error_swallowed", "diff",
                         match(FORBIDDEN_ERROR_SWALLOWED)))
    results.append(check("forbidden_type_relaxed", "diff",
                         match(FORBIDDEN_TYPE_RELAXED,
                               lambda f: f.endswith(TYPE_RELAXED_EXTS))))
    results.append(check(
        "guard2_nil_injection", "diff",
        match(GUARD2_NIL_INJECTION, lambda f: f.endswith(".go")),
        note="policy: 3+ hits within one Story's files => warn + user approval (Guard 2)"))
    prefixes = tuple(cfg["deferred_comment_paths"])
    results.append(check(
        "guard6_deferred_comments", "diff",
        match(GUARD6_DEFERRED, lambda f: f.startswith(prefixes)),
        note="policy: each hit needs a backlog entry referencing it, else done is blocked (Guard 6)"))
    return results


def guard3_check(root, cfg):
    smoke_dir = cfg["smoke_dir"]
    files = tracked_files(root, smoke_dir)
    if not files:
        return skipped("guard3_mock_mode_smoke", "tree",
                       f"no tracked files under {smoke_dir}")
    markers = [re.escape(m) for m in cfg["mock_markers"]]
    regex = re.compile("|".join(markers))
    hits = []
    for f in files:
        hits.extend(scan_file(root, f, regex))
    return check("guard3_mock_mode_smoke", "tree", hits,
                 note="policy: any hit => that test does not satisfy priority_rule 9 real-mode smoke (Guard 3)")


def parse_adr_machine_checks(root, adr_glob):
    """Extract machine_check JSON blocks from ADR markdown files."""
    checks, errors = [], []
    for path in sorted(glob.glob(os.path.join(root, adr_glob))):
        rel = os.path.relpath(path, root)
        try:
            with open(path, errors="replace") as f:
                text = f.read()
        except Exception:
            continue
        for m in re.finditer(r"machine_check:\s*\n+```json\s*\n(.*?)\n```",
                             text, re.DOTALL):
            try:
                block = json.loads(m.group(1))
                for item in block if isinstance(block, list) else [block]:
                    item.setdefault("adr", os.path.basename(path))
                    checks.append(item)
            except Exception as e:
                errors.append({"file": rel, "line": 0,
                               "text": f"unparseable machine_check block: {e}"})
    return checks, errors


def run_grep_checks(root, entries, check_id, note):
    """Shared runner for adr_checks (forbidden/required greps)."""
    hits = []
    for entry in entries:
        try:
            regex = re.compile(entry["pattern"])
        except Exception as e:
            hits.append({"file": entry.get("adr", "?"), "line": 0,
                         "text": f"invalid pattern {entry.get('pattern')!r}: {e}"})
            continue
        found = []
        for prefix in entry.get("paths", ["."]):
            for f in tracked_files(root, prefix):
                found.extend(scan_file(root, f, regex))
        kind = entry.get("type", "forbidden_grep")
        label = entry.get("adr", entry.get("name", "?"))
        if kind == "forbidden_grep" and found:
            for h in found[:10]:
                hits.append({"file": h["file"], "line": h["line"],
                             "text": f"[{label}] forbidden pattern present: {h['text']}"})
        elif kind == "required_grep" and not found:
            hits.append({"file": ",".join(entry.get("paths", [])), "line": 0,
                         "text": f"[{label}] required pattern absent: {entry['pattern']}"})
    return check(check_id, "tree", hits, note=note)


def guard7_check(root, cfg):
    adr_entries, parse_errors = parse_adr_machine_checks(root, cfg["adr_glob"])
    entries = list(cfg["adr_checks"]) + adr_entries
    if not entries and not parse_errors:
        return skipped("guard7_adr_machine_checks", "tree",
                       "no adr_checks configured and no machine_check blocks in ADRs")
    result = run_grep_checks(root, entries, "guard7_adr_machine_checks",
                             "policy: any hit blocks done unless recorded in decisions.json guard7_exceptions (Guard 7)")
    result["hits"].extend(parse_errors)
    result["hit_count"] += len(parse_errors)
    if result["hit_count"]:
        result["status"] = "hits"
    return result


def guard8_check(root, base, cfg):
    if not cfg["data_paths"]:
        return skipped("guard8_destructive_tests", "tree", "no data_paths configured")
    if not base:
        return skipped("guard8_destructive_tests", "tree", "no --base given")
    code, out = git(root, "diff", "--name-only", f"{base}..HEAD", "--",
                    *cfg["data_paths"])
    if code != 0:
        return skipped("guard8_destructive_tests", "tree", "git diff failed")
    touched = [l for l in out.splitlines() if l]
    if not touched:
        return check("guard8_destructive_tests", "tree", [],
                     note="diff does not touch configured data paths (n/a)")
    files = tracked_files(root, cfg["destructive_test_dir"])
    missing = []
    for pat in cfg["destructive_patterns"]:
        regex = re.compile(pat)
        if not any(scan_file(root, f, regex) for f in files):
            missing.append({"file": cfg["destructive_test_dir"], "line": 0,
                            "text": f"no destructive test matches: {pat}"})
    return check("guard8_destructive_tests", "tree", missing,
                 note="policy: data-path diff requires >=1 destructive multi-version test unless guard8_rationale: n/a (Guard 8)")


def call_paths_check(root, cfg):
    if not cfg["call_paths"]:
        return skipped("call_paths", "tree", "no call_paths configured")
    counts = []
    for entry in cfg["call_paths"]:
        try:
            regex = re.compile(entry["pattern"])
        except Exception:
            continue
        n = 0
        for prefix in entry.get("paths", ["."]):
            for f in tracked_files(root, prefix):
                n += len(scan_file(root, f, regex))
        counts.append({"file": entry.get("name", entry["pattern"]), "line": n,
                       "text": f"{n} hit(s) for {entry['pattern']}"})
    zero = [c for c in counts if c["line"] == 0]
    result = check("call_paths", "tree", zero,
                   note="policy: model judges applicability per AC; a coupling an AC claims with 0 hits does not exist in code (Guard 5)")
    result["all_counts"] = counts
    return result


def e2e_checks(root):
    e2e = [f for f in tracked_files(root) if re.search(r"\.e2e\.spec\.[jt]sx?$", f)]
    specs = [f for f in tracked_files(root)
             if re.search(r"\.(?:e2e|mock)\.spec\.[jt]sx?$", f)]
    results = []
    if not e2e:
        results.append(skipped("e2e_network_mock", "tree", "no *.e2e.spec.* files"))
    else:
        hits = []
        for f in e2e:
            hits.extend(scan_file(root, f, E2E_NETWORK_MOCK))
        results.append(check("e2e_network_mock", "tree", hits,
                             note="policy: any network mock in an E2E spec is rejected (Rule 2/4)"))
    if not specs:
        results.append(skipped("e2e_wait_for_timeout", "tree", "no spec files"))
    else:
        hits = []
        for f in specs:
            hits.extend(scan_file(root, f, E2E_WAIT_FOR_TIMEOUT))
        results.append(check("e2e_wait_for_timeout", "tree", hits,
                             note="policy: time-domain AC must use a progression sampler, not waitForTimeout + final assert"))
    return results


def prototype_drift_check(root):
    protos = [f for f in tracked_files(root, "prototype/")
              if f.endswith(".html") and not f.startswith("prototype/old/")]
    if not protos:
        return skipped("prototype_testid_drift", "tree", "no prototype/*.html files")
    testids = {}
    for f in protos:
        try:
            with open(os.path.join(root, f), errors="replace") as fh:
                for tid in DATA_TESTID.findall(fh.read()):
                    testids.setdefault(tid, f)
        except Exception:
            pass
    if not testids:
        return check("prototype_testid_drift", "tree", [])
    sources = [f for f in tracked_files(root)
               if not f.startswith(("prototype/", "docs/", "tests/"))
               and not re.search(r"\.(?:e2e|mock)\.spec\.[jt]sx?$", f)]
    corpus = []
    for f in sources:
        try:
            with open(os.path.join(root, f), errors="replace") as fh:
                corpus.append(fh.read())
        except Exception:
            pass
    blob = "\n".join(corpus)
    missing = []
    for tid, origin in sorted(testids.items()):
        # Template placeholders like vm-row-{id} match on their static prefix.
        probe = tid.split("{")[0].rstrip("-_") or tid
        if probe not in blob:
            missing.append({"file": origin, "line": 0,
                            "text": f"data-testid \"{tid}\" not found in implementation source"})
    return check("prototype_testid_drift", "tree", missing,
                 note="policy: missing testids = implementation diverged from approved prototype; fix or update prototype, never silently accept")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sprint", default="")
    ap.add_argument("--base", default="", help="Sprint base SHA/ref for diff scans")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    sprint = args.sprint or detect_sprint(root)
    if not sprint:
        print("run-guards: could not determine SprintID (pass --sprint or set "
              "progress.current_sprint in docs/ROADMAP.json)", file=sys.stderr)
        return 2

    code, head = git(root, "rev-parse", "HEAD")
    if code != 0:
        print("run-guards: not a git repository", file=sys.stderr)
        return 2

    cfg, config_source = load_config(root)

    checks = []
    checks.extend(diff_checks(root, args.base, cfg))
    checks.append(guard3_check(root, cfg))
    checks.append(guard7_check(root, cfg))
    checks.append(guard8_check(root, args.base, cfg))
    checks.append(call_paths_check(root, cfg))
    checks.extend(e2e_checks(root))
    checks.append(prototype_drift_check(root))

    logdir = os.path.join(root, "docs", "sprint-logs", sprint)
    os.makedirs(logdir, exist_ok=True)
    artifact = {
        "$machine_authored": True,
        "$comment": "Authored by hooks/run-guards.py. Models MUST NOT edit this file. "
                    "Statuses are facts (pattern hits), not verdicts: the model triages "
                    "each hit per the policy notes and the skill docs "
                    "(sprint-done-judgment.md / test-discipline.md Rule 6).",
        "sprint": sprint,
        "base": args.base or None,
        "head": head.strip(),
        "config_source": config_source,
        "checks": checks,
        "summary": {
            "clean": sum(1 for c in checks if c["status"] == "clean"),
            "hits": sum(1 for c in checks if c["status"] == "hits"),
            "skipped": sum(1 for c in checks if c["status"] == "skipped"),
        },
    }
    out = os.path.join(logdir, "guards-run.json")
    with open(out, "w") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)
        f.write("\n")

    for c in checks:
        print(f"  [{c['status'].upper():7}] {c['id']}: {c['hit_count']} hit(s)"
              + (f" — {c['note']}" if c["status"] == "skipped" and c["note"] else ""))
    print(f"guards-run.json written ({out})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"run-guards: internal error: {e}", file=sys.stderr)
        # A broken scanner must never look like a clean scan.
        sys.exit(2)
