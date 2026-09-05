# Implementation Sequence — m6-political-identity

Tickets must be implemented in this order. Generated from the M6 epic's own 2026-08-29 plan-owner
decision (idea 39 first establishes the affiliation mutation primitive; idea 56 derives a signal
that requests/uses that path), resolving the epic doc's own prior internal sequencing contradiction
(see `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY`). `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE  (idea 39, no deps in this batch — land first)
2. TCK-20260905-HOME-EXILE-REFUGEE-THREADS  (idea 59+65, no hard dependency on (1) — may land here
   or in parallel with (1)/(3); listed second only for read ordering)
3. TCK-20260905-DRIFTING-LOYALTY-SIGNAL  (idea 56, depends on: TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE)

## Why This Order Matters

Idea 56's derived loyalty-pressure signal is meant to request/influence idea 39's affiliation
mutation trigger — it needs a real trigger condition to plug into, so it must land after idea 39.
Idea 59+65 shares no hard code dependency with either sibling and may be reordered by the
implementer if convenient, but is listed here for completeness. Re-run `/implement-epic` with the
same folder after any gate failure — already-done tickets are skipped automatically.
