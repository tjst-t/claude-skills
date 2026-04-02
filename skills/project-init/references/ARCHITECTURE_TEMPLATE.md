# ARCHITECTURE.md Template

This is the standard ARCHITECTURE.md structure. This is a Layer 2 document — read by Claude Code on demand when it needs to understand the system design.

## Format

```markdown
# Architecture: {Project Name}

## Overview

{2-3 sentences: what the system does, who it's for, and the high-level approach.}

## Components

{List each major component/package/module, its responsibility, and its key interfaces. Focus on what Claude Code needs to know to work on any part of the system.}

### {Component Name}

- **Responsibility**: {What it does}
- **Location**: `{path/to/package}`
- **Key interfaces**: {Main types, functions, or endpoints exposed}
- **Depends on**: {Other components it calls}
- **Details**: `docs/{design-doc}.md` ← only if a Layer 3 doc exists for this component

### {Component Name}

...

## Data Flow

{Describe the main data paths through the system. For a web API, this might be: request → router → handler → service → repository → DB. For a data pipeline, it might be: ingest → transform → store → query.}

### {Flow Name} (e.g., "API Request Flow", "Event Processing")

{Step-by-step description of how data moves through the components.}

## Directory Structure

{Map the top-level directories to their purpose. Only include directories that are architecturally significant.}

```
{project}/
├── cmd/           # Entry points
├── internal/      # Core business logic
│   ├── handler/   # HTTP handlers
│   ├── service/   # Business logic
│   └── store/     # Data access
├── pkg/           # Reusable libraries
└── docs/          # Documentation
```

## Infrastructure

{Only if applicable. External services, databases, message queues, etc.}

- **Database**: {Type, what it stores}
- **Cache**: {Type, what it caches}
- **Message Queue**: {Type, what events flow through it}
- **External APIs**: {What services are called}

## Related Documents

{List all Layer 3 documents in docs/ that provide detailed design or specification beyond what's covered here. This section serves as a discovery index — Claude Code reads this to know what detailed docs exist before deciding whether to load them.}

{Only include documents that actually exist. Remove this section if there are no Layer 3 documents.}

- `docs/{filename}.md` — {One-line description of what it covers}
- `docs/{filename}.md` — {One-line description}
```

## Guidelines for Auto-Generation

When generating ARCHITECTURE.md from source code:

1. **Read broadly, write concisely.** Scan the full directory tree and key files (entry points, config, main modules) but produce a document that's quick to read.
2. **Focus on relationships, not implementation.** Claude Code can read the source for implementation details. The architecture doc should explain how pieces fit together.
3. **Skip obvious things.** Don't document that `main.go` is the entry point if it's a single-binary Go project. Focus on what's non-obvious or would take time to figure out from source.
4. **Use the actual names.** Reference real package names, file paths, and type names from the project.
5. **Keep it under 150 lines.** If it's growing beyond that, the project may need sub-architecture docs for major subsystems (link from here).
6. **Scan docs/ for existing documents.** When generating or updating, list any `.md` files in `docs/` (excluding ROADMAP.md and ARCHITECTURE.md itself) in the Related Documents section. Add a Details pointer in the relevant Component section if a doc clearly belongs to a specific component.
