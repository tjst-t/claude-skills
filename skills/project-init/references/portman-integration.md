# portman integration

How to add portman-managed dev server startup during `project init`. Only applies if the project has a web server, API, or dev server.

## Prerequisites check

1. Run `which portman`. If not installed:
   - Warn the user: "portman is not installed. You can install it from https://github.com/tjst-t/port-manager or skip this step."
   - If the user chooses to skip, create a basic `make serve` target without portman (direct process launch) and continue.

## Pattern selection

Try to fetch the current integration guide:

```
https://raw.githubusercontent.com/tjst-t/port-manager/main/docs/CLAUDE_INTEGRATION.md
```

If the fetch fails (network error, 404, etc.), fall back to **Pattern 6 (background + PID file)** below.

## Pattern 6 — background + PID file (default)

Use this as the default for Claude Code compatibility. Re-running `make serve` auto-kills the previous process.

```makefile
serve:
	@portman acquire --name $(PROJECT_NAME) --pid-file .server.pid -- \
		$(START_COMMAND)

stop:
	@portman release --name $(PROJECT_NAME) --pid-file .server.pid
```

## Steps

1. Check if a Makefile exists; create one if not.
2. Add `make serve` and `make stop` targets using Pattern 6.
3. For projects with multiple services (e.g., API + frontend), create separate targets: `make serve`, `make serve-frontend`, etc.
4. Add the server startup section to `CLAUDE.md` (Server section in `CLAUDE_TEMPLATE.md`).
5. Add `.env` to `.gitignore` if not already present.

## When the project has no server component

Skip this entire step.
