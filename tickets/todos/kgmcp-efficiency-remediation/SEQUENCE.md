# Implementation Sequence — kgmcp-efficiency-remediation

`implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX  (no deps in this batch — root blocker, do first)
2. TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING  (no deps in this batch — independent of #1)
3. TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP  (no deps in this batch — pipeline fix, independent of #1/#2)
4. TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON  (depends on: TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX)

## Why This Order Matters

TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX must land before
TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON — the recomparison ticket's entire premise (a warm
path that actually caches) is meaningless without the cap fix landed first. The other two
tickets (budget JSON-overhead accounting, Verify-phase scoping gap) are independent of the cap
fix and of each other — they can run in any order relative to #1, but are sequenced after it here
only so the highest-priority (P0) root blocker lands first.

Running alphabetically would attempt the recomparison before its dependency is in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
