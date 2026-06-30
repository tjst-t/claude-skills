#!/usr/bin/env python3
"""
verification-integrity-guard.py — PostToolUse hook (fabrication-specific L3).

Blocks the exact incident this phase targets: a model writing a passing
`verification-results.json` over a run that actually failed. It compares the
just-written verification-results.json against the **machine ground truth**
produced by run-verify.py:

  - the `__VERIFY_EXIT_CODE__:<name>:<code>` trailer in each
    `docs/sprint-logs/{SprintID}/verify-run-*.log` (cannot be faked without
    editing the logs themselves, which is visible in git), and
  - `verify-run.json`'s `overall_machine_status`.

If the machine recorded a failure (any non-zero exit / overall=fail) but the
written verification-results.json claims no failures (`summary.fail == 0` and no
failing test entries), the hook blocks with a reason.

Self-gating: does nothing unless run-verify.py has produced artifacts for this
Sprint (so projects that haven't adopted the wrapper are unaffected). Fully
fail-safe: any unexpected condition exits 0.
"""
import sys
import os
import json
import glob
import re

EXIT_RE = re.compile(r"__VERIFY_EXIT_CODE__:[^:]+:(-?\d+)\s*$")


def machine_failure(logdir: str):
    """Return (failure: bool, evidence: str) from the machine ground truth."""
    reasons = []
    # 1) Ground truth: exit-code trailers in the run logs.
    for logf in sorted(glob.glob(os.path.join(logdir, "verify-run-*.log"))):
        try:
            with open(logf, errors="replace") as f:
                tail = f.readlines()[-5:]
        except Exception:
            continue
        for line in tail:
            m = EXIT_RE.search(line.strip())
            if m and int(m.group(1)) != 0:
                reasons.append(f"{os.path.basename(logf)} exit={m.group(1)}")
    # 2) Corroborate with the machine artifact.
    art = os.path.join(logdir, "verify-run.json")
    if os.path.isfile(art):
        try:
            with open(art) as f:
                data = json.load(f)
            if data.get("overall_machine_status") == "fail":
                reasons.append("verify-run.json overall=fail")
        except Exception:
            pass
    return (len(reasons) > 0, "; ".join(sorted(set(reasons))))


def claims_no_failure(results_path: str):
    """Read the on-disk verification-results.json and decide if it claims a clean pass."""
    try:
        with open(results_path) as f:
            data = json.load(f)
    except Exception:
        return None  # unparseable / partial — don't judge
    summary = data.get("summary", {})
    if isinstance(summary, dict) and isinstance(summary.get("fail"), int):
        if summary["fail"] > 0:
            return False  # already admits failure — fine
    tests = data.get("tests", [])
    if isinstance(tests, list):
        for t in tests:
            if isinstance(t, dict) and t.get("status") in ("fail", "error"):
                return False  # admits a failing test — fine
    return True  # claims everything passed


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0

    tool_name = event.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return 0
    tool_input = event.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""
    if os.path.basename(file_path) != "verification-results.json":
        return 0
    if not os.path.isfile(file_path):
        return 0

    logdir = os.path.dirname(file_path)
    # Self-gate: only act when run-verify.py produced artifacts here.
    if not (glob.glob(os.path.join(logdir, "verify-run-*.log"))
            or os.path.isfile(os.path.join(logdir, "verify-run.json"))):
        return 0

    failed, evidence = machine_failure(logdir)
    if not failed:
        return 0
    claims_pass = claims_no_failure(file_path)
    if claims_pass is not True:
        return 0  # the record admits the failure, or couldn't be parsed

    reason = (
        "Verification integrity: the machine test runner recorded a FAILURE for this "
        f"Sprint ({evidence}), but the verification-results.json you just wrote claims no "
        "failures (summary.fail == 0, no failing test entries). This is the exact "
        "fabrication pattern from docs/autopilot-fabrication-report.md: do NOT record a "
        "real failure as pass. Set the affected AC/test status to fail from the machine "
        "result, do not rationalize the failure as 'pre-existing' or 'out of scope', and "
        "stop the Sprint as `sprint verify failed` for the user to decide. The "
        "machine-authored verify-run.json is the trust source — never override it."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
