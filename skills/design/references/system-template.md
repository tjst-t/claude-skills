# system-template

The System Architecture captures the **shape** of the implementation: what components exist, what each is responsible for, and how they communicate. Unlike `ARCHITECTURE.md` (auto-generated descriptive snapshot of existing code), this is the **prospective** design — what you intend to build.

## What goes in

- **Components**: major modules, services, or layers. Each has a single responsibility.
- **Boundaries**: where one component ends and another begins. Especially important if they have separate lifecycles (different process / service / repo).
- **Key interfaces**: the contracts between components (API shape, message format, function signature category). Not the full spec — just enough to know "component A talks to component B via X".
- **Data flow**: how a representative request / event moves through the system.
- **External dependencies**: services or libraries the system depends on, and what for.

## What does NOT go in

- Class-level design — that's implementation
- Library choices for utility functions — sprint-local
- File layout — convention, not architecture

## Writing guide

- **A component is worth listing if losing it would break a major capability.** Otherwise it's a module inside another component.
- **Boundaries should be justified.** If you split A from B, the reason should be explicit (deploy independently / different team / different scaling / different language).
- **One representative data flow is worth ten generic component descriptions.** Always include at least one.
- **External dependencies should be explicit** — they are the dependencies you can't change.

## Example (booking system)

```json
{
  "components": [
    {
      "name": "Web API",
      "responsibility": "HTTP entry point. Authentication, request validation, routing to domain services.",
      "language_or_stack": "Go + chi",
      "deploys_as": "single binary, stateless",
      "key_interfaces": [
        {"kind": "http", "summary": "REST endpoints under /api/v1/*"}
      ],
      "depends_on": ["Reservation Service", "Property Service", "Auth Service"]
    },
    {
      "name": "Reservation Service",
      "responsibility": "Reservation lifecycle. Holds the Reservation aggregate.",
      "language_or_stack": "Go",
      "deploys_as": "in-process module (initially)",
      "key_interfaces": [
        {"kind": "function", "summary": "ReservationService interface: Create / Confirm / Cancel / Get"}
      ],
      "depends_on": ["PostgreSQL"],
      "notes": "Module-level boundary now; may split to its own service when load demands."
    }
  ],
  "boundaries": [
    {
      "between": ["Web API", "Reservation Service"],
      "justification": "Web API is a thin HTTP layer; domain logic lives in services. Keeps domain testable without HTTP."
    }
  ],
  "data_flows": [
    {
      "name": "Reservation creation",
      "steps": [
        "Guest submits booking form → POST /api/v1/reservations",
        "Web API validates request, extracts auth identity",
        "Web API calls ReservationService.Create(...)",
        "Reservation Service checks Property availability via PropertyService",
        "Reservation Service writes to PostgreSQL in a transaction",
        "Reservation Service emits ReservationCreated event (internal)",
        "Web API returns 201 with reservation_id"
      ]
    }
  ],
  "external_dependencies": [
    {
      "name": "PostgreSQL 16",
      "purpose": "Primary datastore for all aggregates",
      "swappable": false
    },
    {
      "name": "Stripe",
      "purpose": "Payment processing",
      "swappable": true,
      "notes": "Abstracted behind a PaymentGateway interface so it can be replaced."
    }
  ]
}
```

See `SYSTEM_SCHEMA.json` for the full schema.
