# Implementation Sequence — kgmcp-efficiency-remediation

`implement-epic` reads this file to override alphabetical order.

## Order

1. ~~TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX~~ — **closed as no-op 2026-08-18**, already
   `tickets/done/`. Its premise (cache write-size cap broken) was already fixed same-day by
   `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`, before this epic was scoped. `/
   implement-epic`'s automatic done-skip will pass over it; left listed here only for the
   ordering history.
2. TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING  (no deps — independent)
3. TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP  (no deps — pipeline fix, independent)
4. TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON  (no longer depends on #1 — its "working cache"
   precondition is already satisfied by the pre-existing recalibration hotfix; rescoped to the
   still-missing warm-path comparison, see the ticket's own Request Summary)

## Why This Order Matters

The original dependency (#4 needs #1's cap fix landed) turned out to already be satisfied before
this epic existed — see `TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX`'s Completion Summary for
the full correction. #2 (budget JSON-overhead accounting) and #3 (Verify-phase scoping gap) remain
independent of everything else and of each other. #4 is now also unblocked and can run any time —
sequenced last here only because it's the most measurement-methodology-heavy of the three
remaining tickets.

Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.

## Final Status (2026-08-18)

All child tickets are done (1 closed as an honest no-op, 3 with real, measured results). Epic
closed. See `tickets/done/kgmcp-efficiency-remediation/TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-
EPIC.md`'s own Completion Summary for the full result.
