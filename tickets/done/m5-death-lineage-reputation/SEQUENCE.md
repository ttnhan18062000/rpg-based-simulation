# Implementation Sequence — m5-death-lineage-reputation

Tickets must be implemented in this order. Generated from intra-batch dependency analysis.
`implement-epic` reads this file to override alphabetical order.

tracking_doc: docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md

## Order

1. TCK-20260904-LINEAGE-DEATH-DISPATCH  (no deps in this batch — independent of the reputation branch)
2. TCK-20260904-REPUTATION-LOCALITY-SCOPE  (no deps in this batch — must land before 3 and 4 per the epic's own sequencing constraint, since it changes the shape of SocialComponent.public_reputation)
3. TCK-20260904-INHERITED-REPUTATION-SEED  (depends on: TCK-20260904-REPUTATION-LOCALITY-SCOPE)
4. TCK-20260904-CLAN-REPUTATION-ASSOCIATION  (depends on: TCK-20260904-REPUTATION-LOCALITY-SCOPE)

## Why This Order Matters

Idea 60 (TCK-20260904-REPUTATION-LOCALITY-SCOPE) may change `SocialComponent.public_reputation`'s
shape (flat float → region-keyed structure). Ideas 53 and 54 both write to that same field family
and must account for whatever shape idea 60 leaves it in, per the M5 epic doc's own explicit
sequencing constraint ("idea 60 must sequence before or alongside idea 53/54"). Death-and-lineage
(ticket 1) is fully independent of the reputation branch and can run in parallel with it, but is
listed first here since it has no dependency on anything else in this batch.

Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
