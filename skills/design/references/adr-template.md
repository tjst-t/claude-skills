# adr-template

ADR = Architecture Decision Record. One file per load-bearing decision. The format is a lightweight variant of the Michael Nygard ADR style.

## When to write an ADR

A decision warrants an ADR if **ANY** of the following hold:

- **Cross-cutting**: changing it later touches more than one Sprint
- **Non-trivially reversible**: migration cost is meaningful (hours of refactor across files, or a data migration)
- **Contract-locking**: other parts will depend on the shape of this decision (data model, API contract, protocol, domain boundary)
- **Real trade-off**: there are 2+ viable alternatives with genuinely different consequences

## When NOT to write an ADR

If none of the above hold, do not write an ADR. Examples that do NOT warrant one:

- "Use slog instead of log" — local, reversible, no contract
- "Use snake_case for column names" — convention; goes in DESIGN_PRINCIPLES or CLAUDE.md
- "Throw on validation failure" — local pattern
- "Use chi over gorilla/mux" — within the same router category, easily swappable
- "Use Tailwind for styling" — convention, not architectural

If you find yourself writing ADRs for these, you are over-using the format. Stop.

## The shape of a good ADR

Every ADR records:

- **Context** — what forces are at play? (1-2 paragraphs of prose)
- **Alternatives** — what was considered? (2-4 named options with one-line trade-off each)
- **Decision** — what was chosen? (one sentence, clear and unambiguous)
- **Consequences** — what becomes easier; what becomes harder? (bulleted list of *both*)
- **Reversibility cost** — `low` / `medium` / `high` / `one_way_door`
- **Affects** — which parts of the system this decision constrains (component names from `system.json`, or `["*"]` if truly cross-cutting)
- **Status** — `proposed` / `accepted` / `superseded` / `tentative`
- **Supersedes / Superseded by** — ADR ID references when applicable

## Status semantics

- **proposed**: drafted but not yet adopted. Sprint plan should NOT assume this is binding.
- **accepted**: adopted. Sprint plan / sprint run must respect this or escalate.
- **tentative**: adopted provisionally because the team didn't have enough information to commit. Revisit at the next milestone.
- **superseded**: replaced by a newer ADR. The newer ADR's `supersedes` field points back. Old ADRs are NEVER deleted — they remain as history.

## Reversibility cost — what each value means

| Level | Meaning | Examples |
|---|---|---|
| `low` | Refactor in 1 Sprint, no data migration | API endpoint rename with a versioned alias |
| `medium` | Refactor across multiple Sprints OR small data migration | Switching ORM, changing internal event format |
| `high` | Multi-Sprint refactor AND data migration | Changing primary key strategy, splitting a service |
| `one_way_door` | Effectively permanent | Switching primary database, public API breaking changes after launch |

This field is the most important one for future decisions. It tells future Claude (and the user) how careful to be when considering a revision.

## Example

```json
{
  "id": "ADR-0003",
  "title": "Reservation aggregate owns Payment lifecycle",
  "status": "accepted",
  "date": "2026-05-12",
  "context": "Payments and reservations are tightly coupled: a payment exists only in the context of a reservation, payment state changes are driven by reservation state changes (confirm, cancel, refund). Treating Payment as a separate aggregate would require eventual consistency between them, which is unnecessary complexity for our use case (single-region deployment, single PostgreSQL instance).\n\nWe considered making Payment its own aggregate to support 'payment without reservation' flows (deposits, gift cards), but VISION explicitly excludes these.",
  "alternatives": [
    {
      "name": "Separate Payment aggregate, eventual consistency",
      "tradeoff": "Cleaner aggregate boundaries; adds complexity for no current benefit"
    },
    {
      "name": "Payment as a value object inside Reservation",
      "tradeoff": "Simplest, but cannot evolve Payment lifecycle independently (refunds, retries)"
    },
    {
      "name": "Reservation aggregate owns Payment entity (chosen)",
      "tradeoff": "Single transaction boundary; clear ownership; revisiting requires extracting Payment to its own aggregate"
    }
  ],
  "decision": "Payment is an entity owned by the Reservation aggregate. All Payment state changes happen within the Reservation aggregate's transactional boundary.",
  "consequences": [
    "+ Atomicity guaranteed without distributed transactions",
    "+ Domain code reflects the actual business invariants (no payment exists without a reservation)",
    "- If we later want to support deposits or gift cards, we need to extract Payment to its own aggregate (medium-cost refactor)",
    "- Reservation aggregate is larger (more state to load on every operation); acceptable at current scale"
  ],
  "reversibility_cost": "medium",
  "affects": ["Reservation Service", "Payment Service"],
  "supersedes": null,
  "superseded_by": null,
  "notes": "Revisit if VISION expands to include payment-only flows."
}
```

See `ADR_SCHEMA.json` for the full schema.

## Numbering and naming

- IDs are sequential: `ADR-0001`, `ADR-0002`, ... (zero-padded to 4 digits)
- Filename: `ADR-{NNNN}-{kebab-title}.json` — title is short kebab-case derived from the decision (`event-sourcing-for-orders`, `postgres-not-mongo`)
- IDs are NEVER reused, even if an ADR is deleted (don't delete — supersede)
