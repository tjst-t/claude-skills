# CLAUDE.md Template

This is the standard CLAUDE.md structure. CLAUDE.md is Layer 1 — always loaded into context — so keep it under ~100 lines and information-dense.

## Format

```markdown
# {Project Name}

> {One-line description of what this project does}

## Tech Stack

{Language}, {framework}, {key libraries/tools — only list what affects how Claude should write code}

## Commands

- `make serve` — Start dev server (portman, background)
- `make test` — Run tests
- `make build` — Build the project
- `make lint` — Run linter

{Only include commands that Claude Code will actually use. Not a comprehensive Makefile reference.}

## Development Rules

{Coding conventions, naming rules, error handling patterns, etc. that Claude Code should follow on EVERY task. Keep these concrete and actionable.}

- {Example: Use structured logging with slog, not fmt.Println}
- {Example: All API endpoints return JSON with `{"error": "..."}` on failure}
- {Example: Database migrations go in `db/migrations/` using goose}
- {Example: Test files use `_test.go` suffix and table-driven tests}

## Server

{Only if the project has a server component.}

- `make serve` starts the server in the background (portman manages the port)
- Re-running `make serve` auto-kills the previous process
- Logs: `/tmp/{project}-dev.log`
- Never hardcode port numbers

## References

For details beyond what's here, read the relevant doc:

- Architecture & system design: `docs/ARCHITECTURE.md`
- Sprint roadmap & task tracking: `docs/ROADMAP.md`
```

## Key Principles

1. **Every line costs tokens on every message.** If Claude Code only needs the info sometimes, move it to `docs/` and add a pointer.
2. **Commands section is for Claude Code, not humans.** Only list commands Claude will run.
3. **Development Rules are the exception.** They belong here even though they could go in a separate doc, because Claude Code needs them on every coding task.
4. **References section enables progressive disclosure.** Claude Code reads Layer 2 docs only when the task requires it.
