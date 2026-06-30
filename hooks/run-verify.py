#!/usr/bin/env python3
"""
run-verify.py — the machine-authored test runner for `sprint verify`.

The verification artifact must be produced by something the model cannot author
or silently re-interpret. This wrapper runs the project's declared verification
command(s), records the real process **exit code** and raw log, parses any
**JUnit XML** the run produced, and writes a machine-authored summary to
`docs/sprint-logs/{SprintID}/verify-run.json`. `sprint done`'s gate and the
verification-integrity hook read THAT, not the model's hand-written status.

Language/framework-agnostic by construction: it relies only on universal
conventions — POSIX exit codes, and (optionally) JUnit XML, which virtually
every test framework can emit. It never hardcodes a framework's output format.

Command resolution (first that applies):
  1. `.claude/verify.json` in the project root — the declared contract:
       {
         "commands": [
           { "name": "unit",        "command": "make test",        "junit_glob": "reports/junit/*.xml" },
           { "name": "devvm-smoke", "command": "make devvm-smoke",  "junit_glob": "docs/sprint-logs/*/junit/*.xml" }
         ]
       }
     Each command may set "cwd" and "junit_glob" (optional). "junit_glob" may
     contain {SprintID} which is expanded.
  2. A `verify:` target in ./Makefile  -> `make verify`
  3. A `test:`   target in ./Makefile  -> `make test`
  4. None found -> exit non-zero with a clear message (machine verification is
     not configured; the project must declare it). The skill treats this as a
     hard gap, not a pass.

Usage:
  run-verify.py [--sprint SxxxxxX] [--root DIR]

Exit code: 0 if every run passed, 1 if any run failed, 2 if nothing could be run
(unconfigured). The authoritative record is the JSON artifact regardless.
"""
import sys
import os
import json
import glob
import argparse
import subprocess
import xml.etree.ElementTree as ET

EXIT_MARKER = "__VERIFY_EXIT_CODE__"


def detect_sprint(root: str) -> str:
    roadmap = os.path.join(root, "docs", "ROADMAP.json")
    try:
        with open(roadmap) as f:
            data = json.load(f)
        return data.get("progress", {}).get("current_sprint", "") or ""
    except Exception:
        return ""


def resolve_commands(root: str):
    cfg = os.path.join(root, ".claude", "verify.json")
    if os.path.isfile(cfg):
        try:
            with open(cfg) as f:
                data = json.load(f)
            cmds = data.get("commands", [])
            if cmds:
                return cmds, "declared (.claude/verify.json)"
        except Exception as e:
            print(f"run-verify: .claude/verify.json is unreadable: {e}", file=sys.stderr)
            return [], "error"
    makefile = os.path.join(root, "Makefile")
    if os.path.isfile(makefile):
        try:
            with open(makefile) as f:
                text = f.read()
        except Exception:
            text = ""
        import re
        if re.search(r"(?m)^verify:", text):
            return [{"name": "verify", "command": "make verify"}], "fallback (make verify)"
        if re.search(r"(?m)^test:", text):
            return [{"name": "test", "command": "make test"}], "fallback (make test)"
    return [], "unconfigured"


def parse_junit(paths):
    """Aggregate JUnit XML files -> counts + per-case statuses. Stdlib only."""
    total = passed = failed = errored = skipped = 0
    cases = []
    for p in paths:
        try:
            root = ET.parse(p).getroot()
        except Exception:
            continue
        suites = [root] if root.tag == "testsuite" else root.iter("testsuite")
        for suite in suites:
            for tc in suite.iter("testcase"):
                total += 1
                name = (tc.get("classname", "") + "." + tc.get("name", "")).strip(".")
                if tc.find("failure") is not None:
                    status = "fail"; failed += 1
                elif tc.find("error") is not None:
                    status = "error"; errored += 1
                elif tc.find("skipped") is not None:
                    status = "skipped"; skipped += 1
                else:
                    status = "pass"; passed += 1
                cases.append({"name": name, "status": status})
    return {
        "total": total, "passed": passed, "failed": failed,
        "errored": errored, "skipped": skipped, "cases": cases,
    }


def run_one(cmd: dict, root: str, sprint: str, logdir: str):
    name = cmd.get("name", "verify")
    command = cmd.get("command", "")
    cwd = os.path.join(root, cmd.get("cwd", "."))
    logpath = os.path.join(logdir, f"verify-run-{name}.log")
    exit_code = 127
    try:
        with open(logpath, "w") as logf:
            logf.write(f"$ {command}\n\n")
            logf.flush()
            proc = subprocess.run(
                command, shell=True, cwd=cwd,
                stdout=logf, stderr=subprocess.STDOUT,
            )
            exit_code = proc.returncode
            # Tamper-evident trailer: the ground-truth exit code lives in the log
            # itself, so the integrity hook can re-derive status even if
            # verify-run.json is edited.
            logf.write(f"\n{EXIT_MARKER}:{name}:{exit_code}\n")
    except Exception as e:
        try:
            with open(logpath, "a") as logf:
                logf.write(f"\nrun-verify: failed to execute: {e}\n{EXIT_MARKER}:{name}:{exit_code}\n")
        except Exception:
            pass

    junit = None
    glob_pat = cmd.get("junit_glob")
    if glob_pat:
        glob_pat = glob_pat.replace("{SprintID}", sprint)
        files = glob.glob(os.path.join(root, glob_pat))
        if files:
            junit = parse_junit(files)

    machine_status = "pass"
    if exit_code != 0:
        machine_status = "fail"
    elif junit and (junit["failed"] > 0 or junit["errored"] > 0):
        # Defends against runners that exit 0 despite failing cases.
        machine_status = "fail"

    return {
        "name": name,
        "command": command,
        "exit_code": exit_code,
        "log": os.path.relpath(logpath, root),
        "machine_status": machine_status,
        "junit": junit,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sprint", default="")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    sprint = args.sprint or detect_sprint(root)
    if not sprint:
        print("run-verify: could not determine SprintID (pass --sprint or set "
              "progress.current_sprint in docs/ROADMAP.json)", file=sys.stderr)
        return 2

    commands, source = resolve_commands(root)
    if not commands:
        print("run-verify: no verification command configured. Declare commands in "
              ".claude/verify.json or add a `verify:`/`test:` target to the Makefile. "
              "Machine verification did NOT run — this is a gap, not a pass.",
              file=sys.stderr)
        return 2

    logdir = os.path.join(root, "docs", "sprint-logs", sprint)
    os.makedirs(logdir, exist_ok=True)

    # Clear prior-run artifacts so the ground truth reflects ONLY this run.
    # Without this, a previous failing run's log would linger and either falsely
    # block a later honest pass or mask a renamed command.
    for stale in glob.glob(os.path.join(logdir, "verify-run-*.log")):
        try:
            os.remove(stale)
        except Exception:
            pass
    stale_json = os.path.join(logdir, "verify-run.json")
    if os.path.isfile(stale_json):
        try:
            os.remove(stale_json)
        except Exception:
            pass

    runs = [run_one(c, root, sprint, logdir) for c in commands]
    overall = "pass" if all(r["machine_status"] == "pass" for r in runs) else "fail"

    artifact = {
        "$machine_authored": True,
        "$comment": "Authored by hooks/run-verify.py. Models MUST NOT edit this file; "
                    "sprint done and the integrity hook treat it as the trust source. "
                    "Ground-truth exit codes are also in each run's log "
                    "(line `" + EXIT_MARKER + ":<name>:<code>`).",
        "sprint": sprint,
        "command_source": source,
        "runs": runs,
        "overall_machine_status": overall,
    }
    out = os.path.join(logdir, "verify-run.json")
    with open(out, "w") as f:
        json.dump(artifact, f, indent=2)
        f.write("\n")

    # Human-facing one-liner.
    for r in runs:
        jr = ""
        if r["junit"]:
            j = r["junit"]
            jr = f"  (junit: {j['passed']}/{j['total']} pass, {j['failed']} fail, {j['errored']} error)"
        print(f"  [{r['machine_status'].upper():4}] {r['name']}: exit={r['exit_code']}{jr}")
    print(f"verify-run.json written: overall = {overall.upper()}  ({out})")

    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"run-verify: internal error: {e}", file=sys.stderr)
        # Unlike the guards, this tool's failure must NOT look like success.
        sys.exit(2)
