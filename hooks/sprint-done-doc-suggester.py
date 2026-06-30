#!/usr/bin/env python3
"""
Sprint-done documentation suggester (Stop hook).

Implements the "self-improving setup" pattern: when a Sprint has just been
finalized, nudge the user to check whether ARCHITECTURE.md / docs/DESIGN/ drifted
from the code that Sprint changed. ARCHITECTURE.md and the DESIGN/ docs guide every
future sub-agent, so keeping them current compounds.

Advisory only — it never forces Claude to continue and never blocks. It is also
deduplicated (fires at most once per done-commit) and fully fail-safe (any error
exits 0 silently).

Trigger heuristic (no coupling to the skills): the current HEAD commit modified
docs/ROADMAP.json AND that change set a Sprint's status to "done". A sentinel under
.claude/ records the last HEAD it fired on so it never repeats for the same commit.
"""
import sys
import os
import json
import subprocess


def git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10
    )


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    cwd = event.get("cwd") or os.getcwd()

    # Must be a git repo with a ROADMAP.
    if not os.path.isfile(os.path.join(cwd, "docs", "ROADMAP.json")):
        return 0

    head = git(cwd, "rev-parse", "HEAD")
    if head.returncode != 0:
        return 0
    head_sha = head.stdout.strip()
    if not head_sha:
        return 0

    # Dedup: only fire once per HEAD commit.
    sentinel = os.path.join(cwd, ".claude", ".sprint-done-doc-suggester-seen")
    try:
        if os.path.isfile(sentinel):
            with open(sentinel) as f:
                if f.read().strip() == head_sha:
                    return 0
    except Exception:
        pass

    # Did this commit touch ROADMAP.json?
    names = git(cwd, "show", "--name-only", "--format=", head_sha)
    if names.returncode != 0 or "docs/ROADMAP.json" not in names.stdout:
        return 0

    # Did the ROADMAP change add a Sprint status of "done"?
    diff = git(cwd, "show", head_sha, "--", "docs/ROADMAP.json")
    if diff.returncode != 0:
        return 0
    added_done = any(
        line.startswith("+") and '"status": "done"' in line
        for line in diff.stdout.splitlines()
    )
    if not added_done:
        return 0

    # Record the sentinel so we don't repeat for this commit.
    try:
        os.makedirs(os.path.join(cwd, ".claude"), exist_ok=True)
        with open(sentinel, "w") as f:
            f.write(head_sha)
    except Exception:
        pass

    msg = (
        "📐 A Sprint was just marked done. Before moving on, consider whether this "
        "Sprint's changes made ARCHITECTURE.md or docs/DESIGN/ stale — new components, "
        "removed directories, changed data flow, or a decision that should become an ADR. "
        "If so, update them (or run `design refresh`) so future sub-agents reason from "
        "current truth. This is advisory; ignore it if nothing structural changed."
    )
    # Non-blocking advisory. systemMessage surfaces to the user without forcing
    # Claude to keep going; unknown fields are ignored by older Claude Code versions.
    print(json.dumps({"systemMessage": msg}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
