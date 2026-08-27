# Implementation Sequence — semantic-entity-index

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20260822-SEMANTIC-ENTITY-INDEX  (no deps in this batch)
2. TCK-20260822-SCAN-POLICY-DOC-FIX  (no deps in this batch)
3. TCK-20260822-PAID-INFO-INDEX-RETROFIT  (depends on: TCK-20260822-SEMANTIC-ENTITY-INDEX)
4. TCK-20260822-GUARD-SCAN-INDEX-RETROFIT  (depends on: TCK-20260822-SEMANTIC-ENTITY-INDEX)

## Why This Order Matters

**Written by hand, not auto-generated** — the naive "any batch ID mentioned in Related Tickets is
a prerequisite" heuristic would misread this batch's dependency graph as circular.
`TCK-20260822-SEMANTIC-ENTITY-INDEX`'s own `## Related Tickets` section lists both
`TCK-20260822-PAID-INFO-INDEX-RETROFIT` and `TCK-20260822-GUARD-SCAN-INDEX-RETROFIT` — but those
are forward-references to its future consumers, not prerequisites of it. The real, unambiguous
direction is: `SEMANTIC-ENTITY-INDEX` is the foundational ticket (the index data structure and its
query API); `PAID-INFO-INDEX-RETROFIT` and `GUARD-SCAN-INDEX-RETROFIT` each wire that index into
one already-shipped, real O(N)-scan call site and cannot start before the index exists.
`SCAN-POLICY-DOC-FIX` is a small, fully independent doc-only hotfix (correcting two stale claims in
`docs/plans/idea_semantic_entity_index.md`) — it can run at any point in this sequence; placement
here is arbitrary.

Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
