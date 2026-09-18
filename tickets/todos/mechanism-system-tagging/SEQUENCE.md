# Implementation Sequence — mechanism-system-tagging

tracking_doc: docs/plans/mechanism_tier_model_initiative.md

Tickets must be implemented in this order. `implement-epic` reads this file to override alphabetical
order. `TCK-20260918-EPIC-MECHANISM-SYSTEM-TAGGING` is the epic-tier parent and is not implemented
directly — it tracks the children below.

## Order

1. TCK-20260918-MECHANISM-SYSTEM-TAGGING-VALUE-INVESTIGATION  (no deps in this batch)
2. TCK-20260918-MECHANISM-SYSTEM-TAGGING-FOUNDATION  (depends on: the investigation — its system
   vocabulary is seeded from the investigation's broad pass, and its many-to-many design may be
   simplified away by the investigation's multi-membership count)
3. Rollup views  (named, not drafted — scoped after the foundation lands, per the user's call)

## Why This Order Matters

**Investigation first, and the question is value rather than feasibility.** The previous tier
investigation (`TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION`) tested whether
*derived* membership produced recognisable sets — it did not, and that "do not build" saved three
tickets and a schema. Declared-by-intent sets will be sensible by construction, so feasibility is not
in doubt here. What is in doubt is whether the grouping delivers review value proportionate to
hand-maintaining tags across 93 mechanisms with no mechanical backing.

**The foundation's shape is not yet known**, which is why it must not run first. Two of the
investigation's outputs change it directly: the system vocabulary it seeds from, and the count of
mechanisms belonging to more than one system — if almost none do, the many-to-many design is
unnecessary complexity and the foundation simplifies.

**Rollups are deliberately last and undrafted.** The user deferred them until the mapping and
registry exist. Their one known constraint is already recorded in the epic's Assumptions #3 — counts,
never a single badge — so the follow-up does not have to rediscover it.

## Note on the tier this replaces

This epic revives the `system` tier that `TCK-20260917-EPIC-MECHANISM-TIER-MODEL` closed. That is
deliberate, not an oversight: the closure rejected membership **derived** from `depends_on`
traversal, on the root cause that `depends_on` encodes *prerequisite* while a system encodes
*collaboration*. Tagging does not consult edges at all, which removes all three blockers the
investigation found. The rejection stands for derivation and is recorded in
`docs/plans/mechanism_tier_model_initiative.md` as history, not reversed.
