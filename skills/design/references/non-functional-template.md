# non-functional-template

Non-functional requirements (NFRs) are the constraints that shape *how* the system works, beyond *what* it does. These often drive ADRs — many architecture decisions exist because of an NFR.

## What goes in

Only NFRs that have a concrete target the user has named or implicitly committed to. Empty sections are fine — better than fabricated targets.

- **Performance**: latency, throughput, response time targets
- **Availability**: uptime targets, acceptable downtime windows
- **Consistency / Durability**: data loss tolerance, replication, backup requirements
- **Scalability**: expected load, growth assumptions
- **Security**: authn/authz model, data classification, audit requirements
- **Compliance**: regulations (GDPR, SOC2, HIPAA, etc.) if applicable
- **Operational**: deployment frequency, observability needs, runbook expectations

## What does NOT go in

- Aspirational "we want it fast and reliable" — that's noise. If there's no target, omit the section.
- Library-level concerns ("we want low memory") — those go in coding conventions
- Generic best practices — those go in DESIGN_PRINCIPLES

## Writing guide

- **Targets must be measurable**. "P99 latency under 200ms" — yes. "Fast response" — no.
- **Be honest about what's been decided vs. what's a guess**. Mark guesses with `confidence: "low"` so future decisions know.
- **Link to ADRs**. If an NFR drove an ADR, reference it.
- **Capture the "why"**. A target like "RPO = 0 minutes" needs justification — it's expensive.

## Example

```json
{
  "performance": [
    {
      "metric": "API P99 latency",
      "target": "< 200ms for read endpoints, < 500ms for write endpoints",
      "rationale": "Booking funnel drop-off measurements suggest 1s+ response halves conversion",
      "confidence": "medium",
      "drives_adr": ["ADR-0005"]
    }
  ],
  "availability": [
    {
      "metric": "Monthly uptime",
      "target": "99.5%",
      "rationale": "Industry standard for non-critical SaaS; equivalent to ~3.6h downtime/month",
      "confidence": "high"
    }
  ],
  "consistency": [
    {
      "metric": "Reservation booking",
      "target": "Strong consistency — no double-booking under concurrent requests",
      "rationale": "Double-booking is a business-killing UX failure",
      "confidence": "high",
      "drives_adr": ["ADR-0002"]
    }
  ],
  "scalability": [
    {
      "metric": "Concurrent users",
      "target": "Initial: 100 concurrent. 12-month projection: 5000 concurrent.",
      "rationale": "From product roadmap projections",
      "confidence": "low"
    }
  ],
  "security": [
    {
      "metric": "Authentication",
      "target": "Email + password with TOTP MFA optional. Sessions expire after 30 days inactive.",
      "rationale": "Industry standard for consumer SaaS",
      "confidence": "high"
    },
    {
      "metric": "Data classification",
      "target": "Reservation data is personal data under GDPR. Payment data never stored (Stripe handles).",
      "rationale": "GDPR compliance + reducing PCI scope",
      "confidence": "high"
    }
  ],
  "compliance": [],
  "operational": [
    {
      "metric": "Deploy frequency",
      "target": "On-demand, multiple times per day during active development",
      "rationale": "Small team, fast iteration",
      "confidence": "high"
    },
    {
      "metric": "Observability",
      "target": "Structured logs (slog) + per-request trace ID. No APM initially.",
      "rationale": "Logs sufficient at current scale; revisit at 1000+ daily users",
      "confidence": "medium"
    }
  ]
}
```

See `NON_FUNCTIONAL_SCHEMA.json` for the full schema.

## Confidence levels

- `high` — user explicitly stated this target with reasoning
- `medium` — derived from user statements with reasonable inference
- `low` — Claude's best guess; surface for user confirmation at next milestone

The `confidence` field is what makes this document *honest* — distinguishing what's been committed to from what's a working assumption.
