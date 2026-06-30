# Story Scenarios

Every Story has a **user scenario**: a step-by-step description of what the user actually does once the Story is implemented. The E2E test for the Story is a literal mechanical execution of this scenario.

This file defines the scenario format and per-type templates. The rules about what tests must look like (entry-point fidelity, no skips, real-browser GUI, etc.) live in `test-discipline.md` — refer to that for enforcement.

## Story type classification

Every Story has exactly one **primary user entry point**. Pick the one that matches *how the end user invokes the feature*, not which layer holds the most code.

| Type | The user actually | E2E test must drive |
|---|---|---|
| `cli` | Types a command in a shell | Subprocess invocation of the real binary; assert on stdout, stderr, exit code, files written |
| `api` | Sends an HTTP request (from another service, an SDK consumer, or `curl`) | Real HTTP client against the running server (no calls into internal handlers) |
| `gui` | Clicks/types in a browser | Playwright against the real frontend (see `gui-spec.md`) |
| `library` | Imports the package and calls its public API from their own program | A separate consumer-style test program that imports the package as an external user would |
| `mixed` | Multiple of the above as part of one user goal | Each entry point has its own scenario block, all of which must execute |

If a Story exposes both an API and a UI for the same feature, classify it `gui` — the UI scenario implicitly exercises the API. Classify as `api` only when no UI consumes the endpoint in this Sprint.

If you cannot decide between `api` and `library` (e.g., an internal package that is also exposed via HTTP), pick the surface a user *outside the project* would use first.

## Scenario template

Per Story, write one or more scenarios. Each scenario is linked to one or more acceptance criteria and is a list of numbered steps. Each step has an `action` (what the user does, in user terms) and an `expected` (what the user observes, in observable terms).

```json
{
  "story": "Sb1e4d8-1",
  "story_type": "cli",
  "user_role": "operator running deploys from their laptop",
  "entry_point": "myapp binary on $PATH",
  "scenarios": [
    {
      "id": "scenario-1",
      "linked_ac": ["AC-Sb1e4d8-1-1", "AC-Sb1e4d8-1-2"],
      "description": "Operator starts a stopped VM and confirms it is running",
      "preconditions": ["A VM named vm-123 exists in stopped state"],
      "steps": [
        {
          "n": 1,
          "action": "user runs `myapp vm start vm-123`",
          "expected": "exit code 0; stdout contains `started vm-123`"
        },
        {
          "n": 2,
          "action": "user runs `myapp vm status vm-123`",
          "expected": "exit code 0; stdout contains `state: running`"
        }
      ],
      "cleanup": ["stop vm-123"]
    }
  ]
}
```

### Per-type templates

#### CLI scenario

- `entry_point`: the exact command name as the user types it (e.g., `myapp`, `kubectl mything`)
- Each `action` is a literal command line, written as the user would type it
- Each `expected` covers stdout, stderr, exit code, and any files/state mutations the user can observe
- Test implementation: spawn the real binary as a subprocess. Do not import its `main()` function or call internal packages. If the binary is built by the project, the test must run `make build` (or equivalent) first and invoke the produced artifact.

#### API scenario

- `entry_point`: the base URL and auth scheme the consumer uses (e.g., `https://api.local/api/v1` with `Authorization: Bearer <token>`)
- Each `action` is a literal HTTP request: method, path, headers (especially auth and content-type), and JSON body
- Each `expected` covers status code, response body shape, and any side effects observable via a follow-up GET
- Test implementation: use a real HTTP client (Go `net/http`, `fetch`, `requests`, etc.) against the running server. Do not call handler functions directly, do not bypass routing or middleware. The server must be the same one a real consumer would hit.

#### GUI scenario

Delegated to the GUI spec process (`gui-spec.md`). It produces the state diagram, endpoint contracts, and Playwright tests; this document does not duplicate that. The GUI scenario in `scenario-{StoryID}.json` simply records the user-facing steps in the same format as CLI/API so that all Stories share one shape; the canonical artifact for GUI Stories is `gui-spec-{StoryID}.json`.

#### Library scenario

- `entry_point`: the import path / package name as a consumer would write it
- Each `action` is sample consumer code (a few lines) that exercises the public API
- Each `expected` covers return values, mutations to inputs, errors raised
- Test implementation: a separate test binary / file that imports the package as a consumer would. The test must NOT live inside the package's own `_test.go` files using package-internal access — it must use only the exported surface.

## Where scenarios are stored

- Non-GUI Stories: `docs/sprint-logs/{SprintID}/scenario-{StoryID}.json` (this template)
- GUI Stories: `docs/sprint-logs/{SprintID}/gui-spec-{StoryID}.json` (produced by the GUI spec process, `gui-spec.md`)

The scenario file is the source of truth that `sprint run` reads when generating tests, and that `sprint verify` reads when validating that tests actually drive the user's entry point.

## Enforcement

What counts as a valid test driven from a scenario — and what disqualifies one — is defined in `test-discipline.md`. `sprint run` writes tests to that standard; `sprint verify` rejects tests that don't meet it.
