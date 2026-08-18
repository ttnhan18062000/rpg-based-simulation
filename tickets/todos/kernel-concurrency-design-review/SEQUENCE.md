# Implementation Sequence — kernel-concurrency-design-review

Tickets must be implemented in this order. Generated from intra-batch dependency analysis
(with two hallucinated cross-references from the Structure phase corrected to canonical ticket
IDs, and one resulting circular dependency between the design-doc ticket and the concurrency-fix
ticket resolved before this file was written — see the ticket-creation session notes).
`implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT  (no deps in this batch)
2. TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION  (no deps in this batch)
3. TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE  (no deps in this batch)
4. TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION  (no deps in this batch)
5. TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION  (no deps in this batch)
6. TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC  (depends on: TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION, TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION)
7. TCK-20260817-RUNTIMEMODE-BENCH-SCOPING  (no deps in this batch)
8. TCK-20260817-STATE-DESIGN-PRIORITY-ORDER  (depends on: TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC)

## Why This Order Matters

TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC lands a "Known documentation drift" section that
narrates the exact two contradictions TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION and
TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION fix — if the design doc lands first, that section is
stale on arrival. TCK-20260817-STATE-DESIGN-PRIORITY-ORDER's lawbook edit is meant to cross-link
the design doc's "Part 1 — Design Philosophy" as the single source of truth for the reconstructed
priority order, rather than independently drafting near-duplicate prose, so it should follow the
design doc. The other five tickets are independent of each other and of this chain.

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
