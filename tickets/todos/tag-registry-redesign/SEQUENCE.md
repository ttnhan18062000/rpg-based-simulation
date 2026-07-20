# Implementation Sequence — tag-registry-redesign

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260720-TAG-REGISTRY-RELOCATE  (no deps in this batch)
2. TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY  (depends on: TCK-20260720-TAG-REGISTRY-RELOCATE)
3. TCK-20260720-SKILL-MAPPING-DEDUP  (depends on: TCK-20260720-TAG-REGISTRY-RELOCATE)
4. TCK-20260720-TAG-CATEGORY-REGISTRY  (depends on: TCK-20260720-TAG-REGISTRY-RELOCATE)
5. TCK-20260720-TAG-CORPUS-REPAIR-SWEEP  (depends on: TCK-20260720-TAG-REGISTRY-RELOCATE, TCK-20260720-TAG-CATEGORY-REGISTRY)
6. TCK-20260720-TAG-TOUCHPOINT-CLEANUP  (depends on: TCK-20260720-TAG-REGISTRY-RELOCATE, TCK-20260720-TAG-CATEGORY-REGISTRY)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place — most
notably, everything else in this batch reads from the new `registries/` directory that
TAG-REGISTRY-RELOCATE creates, and the repair sweep and touchpoint cleanup both also need the
category registry TAG-CATEGORY-REGISTRY establishes. Re-run `/implement-epic` with the same
folder after any gate failure — already-done tickets are skipped automatically.

## Related, Not Duplicated

`TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX` (in `tickets/todos/`, standalone) is a separate,
already-filed hotfix for `create-tickets.js`'s Structure-phase tag-category restriction. Every
ticket in this batch explicitly excludes it from scope — it can be implemented independently, in
any order relative to this batch.

## Known Open Decisions (deliberately not pre-resolved)

Several tickets in this batch carry explicit open questions that must be resolved during that
ticket's own Investigate/Plan phase, not assumed from this planning session:
- **TAG-CATEGORY-REGISTRY**: whether the new registry seeds all 5 categories or only the 4
  currently-addable ones.
- **TAG-CORPUS-REPAIR-SWEEP**: the exact intended semantics of the "invalid_category" flag type,
  which has no direct precedent today.
- **SKILL-MAPPING-DEDUP**: which of 3 candidate resolutions closes the conflict between
  `tag_registry.jsonl`'s append-only design and the need to edit 4 already-registered rows.
- **TAG-TOUCHPOINT-CLEANUP**: whether `implement-ticket.js`'s intentionally hand-synced string-match
  mirror (kept to avoid shell quote-corruption) gets updated in lockstep or explicitly stays as-is.
