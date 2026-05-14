# data-template

The Data / Protocol design captures **the shape of state and contracts** — the parts of the system where the migration cost of changing a decision is highest. Only write this file if the system has meaningful state (database) or external contracts (API, message protocol).

## When to write data.json

Write it if any apply:

- The system has a persistent data store with non-trivial schema
- The system exposes a public API (versioned, used by external clients)
- The system communicates via a message protocol (events, RPC) with other systems
- The system has external integrations whose contracts you depend on

If the system is purely UI / single-binary CLI / experimental script, skip this file.

## What goes in

- **Datastores**: which stores hold what data
- **Schemas (sketch)**: high-level shape of the main entities-as-stored. Not full DDL — that lives in migrations. Enough to know what fields and types exist for each main entity.
- **Indexes (rationale only)**: indexes whose existence is part of the design (e.g., "unique constraint on (property_id, date_range) to prevent double-booking"). Not query-tuning indexes.
- **API contracts (sketch)**: endpoint groups, request/response shapes for the load-bearing ones. Not full OpenAPI.
- **Event contracts (sketch)**: event types, payload shape, ordering/idempotency guarantees
- **Migration / versioning policy**: how breaking changes are handled

## What does NOT go in

- Full column definitions with constraints — that's migration files
- Query-tuning indexes — operational, not architectural
- Every endpoint's exact JSON — that's API spec
- Internal struct definitions — that's code

## Writing guide

- **Schemas as sketches**: 5-10 fields per entity. The point is to communicate shape, not be authoritative.
- **Call out invariants**: "reservation.status transitions only forward" — these are the rules that data structure alone doesn't enforce.
- **Versioning policy is critical for public APIs**: how do you handle breaking changes? URL-versioned (`/v1/`, `/v2/`)? Header? Sunset policy?

## Example

```json
{
  "datastores": [
    {
      "name": "PostgreSQL primary",
      "purpose": "All transactional data: reservations, properties, payments, users",
      "consistency": "Strong (single instance, serializable for booking flow)",
      "backup": "Daily full + WAL streaming to S3; PITR window 7 days"
    }
  ],
  "schemas": [
    {
      "entity": "Reservation",
      "stored_in": "PostgreSQL primary",
      "table": "reservations",
      "fields": [
        {"name": "reservation_id", "type": "uuid", "notes": "primary key"},
        {"name": "property_id", "type": "uuid", "notes": "FK to properties"},
        {"name": "guest_id", "type": "uuid", "notes": "FK to users"},
        {"name": "check_in", "type": "date"},
        {"name": "check_out", "type": "date"},
        {"name": "status", "type": "enum", "notes": "draft|confirmed|checked_in|checked_out|cancelled"},
        {"name": "total_amount_cents", "type": "bigint"},
        {"name": "currency", "type": "char(3)"},
        {"name": "created_at", "type": "timestamptz"},
        {"name": "updated_at", "type": "timestamptz"}
      ],
      "invariants": [
        "status transitions forward only: draft → confirmed → checked_in → checked_out (cancelled is terminal from any state)",
        "check_out > check_in",
        "(property_id, [check_in, check_out)) must not overlap with any other confirmed reservation for the same property"
      ]
    }
  ],
  "design_indexes": [
    {
      "name": "reservations_no_overlap_idx",
      "purpose": "Enforce no-double-booking invariant",
      "kind": "exclusion constraint",
      "note": "GiST + btree_gist; covers (property_id, daterange(check_in, check_out)) WHERE status = 'confirmed'"
    }
  ],
  "api_contracts": [
    {
      "group": "Reservation API",
      "base_path": "/api/v1/reservations",
      "summary": "REST endpoints for reservation CRUD",
      "endpoints": [
        {"method": "POST", "path": "/", "summary": "Create a draft reservation"},
        {"method": "POST", "path": "/{id}/confirm", "summary": "Confirm and capture payment"},
        {"method": "POST", "path": "/{id}/cancel", "summary": "Cancel and refund per policy"},
        {"method": "GET", "path": "/{id}", "summary": "Read"}
      ]
    }
  ],
  "event_contracts": [],
  "versioning_policy": "URL-versioned (/api/v1/...). Breaking changes increment the version. Old versions deprecated for 6 months after a new version ships. Non-breaking additions (new fields, new endpoints) do not require a version bump."
}
```

See `DATA_SCHEMA.json` for the full schema.
