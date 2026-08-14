# Implementation Sequence — context-retrieval-phase3

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260729-DETERMINISTIC-CODE-INDEX  (no deps in this batch)
2. TCK-20260729-HYBRID-RETRIEVAL-FUSION  (no deps in this batch)
3. TCK-20260729-RETRIEVAL-CACHE-LEVELS  (no deps in this batch)
4. TCK-20260729-CONTEXT-PACKET-ASSEMBLY  (depends on: TCK-20260729-HYBRID-RETRIEVAL-FUSION, TCK-20260729-RETRIEVAL-CACHE-LEVELS)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.

## Known Gap

Tickets 1-3 (`DETERMINISTIC-CODE-INDEX`, `HYBRID-RETRIEVAL-FUSION`, `RETRIEVAL-CACHE-LEVELS`)
have no dependency between each other and can be implemented in any relative order or in
parallel via separate `/implement-ticket` runs — `implement-epic` runs them sequentially
regardless, per its own "sequential only, not parallel" rule. Ticket 4
(`CONTEXT-PACKET-ASSEMBLY`) has a hard, load-bearing dependency on tickets 1's sibling
`HYBRID-RETRIEVAL-FUSION` (ticket 2 in this list) and `RETRIEVAL-CACHE-LEVELS` (ticket 3):
it consumes their actual return-value shapes and cannot be meaningfully implemented,
let alone tested, before both land — see each ticket's own Investigation findings for why.
