#!/usr/bin/env python3
"""
L3 forbidden-action guard (PostToolUse hook).

The third defense layer from the skills' Constraints and Forbidden Actions
(autopilot/SKILL.md). L1 is the autopilot prompt; L2 is the sprint verify diff
scan; this hook is the deterministic backstop: it inspects Edit/Write/MultiEdit
content and, when an autonomous run is in progress, blocks edits that introduce
test-disabling or error-swallowing patterns.

Self-gating: this hook does NOTHING unless an autopilot lock file
(`.claude/autopilot-*.lock`) exists in the project. That ties the guard to
unattended execution — interactive sessions where a human deliberately adds a
skip are never blocked. It is also fully fail-safe: any unexpected condition
exits 0 (allow) so it can never break a session.

Reads the PostToolUse JSON event on stdin. On a match it emits
{"decision": "block", "reason": ...} so Claude is told to revert the change or
record it as a compromise.
"""
import sys
import os
import json
import glob
import re

# (label, compiled regex, tier) — tier: "stop" = immediate-stop, "notify" = notify-after
PATTERNS = [
    ("test skip (it/test/describe.skip)", re.compile(r"\b(?:it|test|describe)\.skip\b"), "notify"),
    ("test skip (xit/xtest/xdescribe)", re.compile(r"\b(?:xit|xtest|xdescribe)\b"), "notify"),
    ("pytest skip", re.compile(r"@pytest\.mark\.(?:skip|xfail)\b"), "notify"),
    ("go test skip", re.compile(r"\bt\.Skip(?:Now)?\("), "notify"),
    ("tautological assertion", re.compile(r"expect\(\s*true\s*\)\.toBe\(\s*true\s*\)"), "notify"),
    ("suppressed type error (@ts-ignore)", re.compile(r"//\s*@ts-(?:ignore|expect-error)\b"), "notify"),
    ("suppressed lint (noqa)", re.compile(r"#\s*noqa\b"), "notify"),
    ("suppressed type error (type: ignore)", re.compile(r"#\s*type:\s*ignore\b"), "notify"),
    ("empty catch block", re.compile(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}"), "notify"),
]


def autopilot_running(cwd: str) -> bool:
    """True iff an autopilot lock file is present — the gate for this hook."""
    try:
        return bool(glob.glob(os.path.join(cwd, ".claude", "autopilot-*.lock")))
    except Exception:
        return False


def extract_new_content(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Write":
        return tool_input.get("content", "") or ""
    if tool_name == "Edit":
        return tool_input.get("new_string", "") or ""
    if tool_name == "MultiEdit":
        return "\n".join(
            (e.get("new_string", "") or "") for e in tool_input.get("edits", []) if isinstance(e, dict)
        )
    return ""


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0  # fail-safe: unparseable input never blocks

    cwd = event.get("cwd") or os.getcwd()
    if not autopilot_running(cwd):
        return 0  # only active during autonomous runs

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}
    if not isinstance(tool_input, dict):
        return 0

    file_path = tool_input.get("file_path", "") or ""
    content = extract_new_content(tool_name, tool_input)
    if not content:
        return 0

    hits = [label for (label, rx, _tier) in PATTERNS if rx.search(content)]
    if not hits:
        return 0

    reason = (
        "L3 forbidden-action guard: this edit to "
        + (file_path or "a file")
        + " introduces "
        + "; ".join(hits)
        + ". During an autopilot run these are notify-after compromises, not silent edits. "
        "Either revert the change, or — if it is a genuine, justified local concession — "
        "record it in docs/sprint-logs/{SprintID}/compromises.json "
        "(autopilot/references/COMPROMISES_SCHEMA.json) before continuing. "
        "Deleting/loosening an acceptance criterion or a destructive git op is an immediate-stop "
        "category: stop and escalate to the user instead."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Absolute fail-safe: never break the session on an internal error.
        sys.exit(0)
