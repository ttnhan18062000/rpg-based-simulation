# Implementation Sequence — m9-corpus-test-coverage

No child ticket in this batch has a hard cross-ticket dependency on another — each targets a
different, independent slice of corpus/SimQ coverage. Order below is by priority (highest-value/
most-actionable first), not a hard build-order constraint. `implement-epic` reads this file to
override alphabetical order; re-run after any gate failure — already-done tickets are skipped
automatically.

## Order

1. TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS  (P1, highest value, fully specified)
2. TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST  (P1, real tooling bug, fantasy-year correction)
3. TCK-20260906-ENTITY-EVOLVED-EVENT-GAP  (P2, small and independent)
4. TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS  (P2, ideas 32+43/51/52/54/60/65)
5. TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS  (P2, ideas 4/10/13/14/22/30/33/36/40/39/44/49 —
   idea 30's own assertion depends on idea 13's landing first, within this one ticket)
6. TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS  (P2, idea 48 ready / idea 57 deferred)
7. TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED  (P3, ideas 50/64 — doc-correction only, both mechanisms
   unshipped, no real corpus-test work possible yet)
8. TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION  (P3, investigative, idea 37)

## Why This Order Matters

Tickets 1-2 close the highest-value, most concretely-actionable gaps (a real Campaign-mode testing
blind spot for 4 already-shipped mechanics, and a real tooling bug that has silently no-op'd every
long-run age-tier observation since the fantasy-year migration landed). Tickets 7-8 are lowest
priority: ticket 7 does no real corpus-test authoring (both target mechanisms were found unshipped
during this scoping pass), and ticket 8 is purely investigative pending its own registry-shape
decision.
