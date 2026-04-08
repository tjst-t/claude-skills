# sprint demo

Demonstrate the Sprint's deliverables to the user by running the actual program. Run this after `sprint verify`.

1. Read `docs/ROADMAP.md` and identify the current Sprint
2. Read the Sprint's Stories and Tasks to understand what was built
3. Read `docs/ARCHITECTURE.md` and `CLAUDE.md` to determine the startup command

## Determine the startup command (in priority order)

1. If `Makefile` has a `serve` target → use `make serve` (preferred)
2. If `CLAUDE.md` or `ARCHITECTURE.md` documents a startup command → use that
3. Infer from project type (`go run ./cmd/...`, `npm run dev`, `python -m uvicorn ...`, etc.)

## For each Story in the Sprint

4. Read the Story's user story statement aloud ("As a {role}, {action} is now possible")
5. Start the service if not already running
6. Demonstrate each acceptance criterion one by one:
   - **API/backend**: Send real requests with `curl` or `httpie`, show actual responses
   - **CLI**: Run actual commands, show output
   - **UI**: Start the dev server, tell the user which URL to visit and what to interact with
7. Also demonstrate error cases and edge cases if they appear in the acceptance criteria
8. Highlight anything notable: edge cases handled, performance characteristics, important caveats

## Wrap up

9. Summarize what was demonstrated
10. Ask the user if they want to explore anything further or see additional scenarios

The demo must show a running program, not test code execution. If something fails during the demo, note it as a potential issue to address before `sprint done`.
