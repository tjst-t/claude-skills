# domain-template

The Domain Model captures the **vocabulary** of the system: what things exist, how they relate, what they mean. This is the most-referenced design artifact during sprint planning because every Story will use these names.

## What goes in

- **Entities**: the nouns of the system. Things that have identity and a lifecycle.
- **Value objects**: things that are defined by their values, not identity (e.g., "Money", "DateRange"). Optional — include if the distinction matters in this domain.
- **Relationships**: how entities reference each other (cardinality, ownership).
- **Glossary**: domain-specific terms with definitions. Capture any term that has a non-obvious or domain-specific meaning.

## What does NOT go in

- Database schema details (column types, indexes) — those go in `data.json` if needed
- API field names — those belong in the API design layer
- UI labels — those are presentation, not domain

## Writing guide

- **Use the user's vocabulary, not engineering vocabulary.** If the user says "case", do not rename it to "ticket" or "issue".
- **Each entity gets a one-sentence definition** that a domain expert would agree with.
- **Lifecycle states** are valuable if the entity has them (e.g., Order: draft → submitted → fulfilled → archived). Include if applicable.
- **Aggregates / ownership boundaries** matter for distributed systems. If Entity A always belongs to Entity B (cannot exist without it), mark that.
- **Keep it under ~10 main entities** for the initial pass. More than that usually means the domain hasn't been narrowed enough.

## Example (booking system)

```json
{
  "entities": [
    {
      "name": "Reservation",
      "definition": "予約された滞在の単位。1ゲスト × 1物件 × 1期間。",
      "identity": "reservation_id",
      "lifecycle": ["draft", "confirmed", "checked_in", "checked_out", "cancelled"],
      "owns": ["Payment"]
    },
    {
      "name": "Property",
      "definition": "宿泊できる物件。一つのオーナーに属する。",
      "identity": "property_id",
      "lifecycle": ["draft", "listed", "delisted"]
    }
  ],
  "value_objects": [
    {
      "name": "Money",
      "definition": "金額と通貨のペア。常に通貨単位とセットで扱う。"
    }
  ],
  "relationships": [
    {
      "from": "Reservation",
      "to": "Property",
      "kind": "many_to_one",
      "label": "予約は1つの物件に対して行われる"
    },
    {
      "from": "Reservation",
      "to": "Guest",
      "kind": "many_to_one",
      "label": "予約は1人のゲストが行う"
    }
  ],
  "glossary": [
    {
      "term": "ノーショー",
      "definition": "予約後にチェックインに来なかった状態。キャンセルとは扱いが異なる。"
    }
  ]
}
```

See `DOMAIN_SCHEMA.json` for the full schema.
