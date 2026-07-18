# Implementation Sequence — canonical-field-enums

Tickets must be implemented in this order. Generated from intra-batch
dependency analysis. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM  (no deps in this batch) — DONE
2. TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP  (depends on: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM) — DONE
3. TCK-20260718-LAYER-REGISTRY-CONVERSION  (depends on: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM — inserted mid-epic per a user design decision to make Layer registry-backed like Tag)
4. TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL  (depends on: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM, TCK-20260718-LAYER-REGISTRY-CONVERSION)
5. TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE  (depends on: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM, TCK-20260718-LAYER-REGISTRY-CONVERSION, TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL)

## Why This Order Matters

TIER-PRIORITY-CANONICAL-ENUM must land first — it defines the canonical
enums and check function every other ticket in this batch consumes.
TIER-PRIORITY-CORPUS-CLEANUP is independent of the Layer-registry work and
was completed before the Layer-registry ticket was inserted.
LAYER-REGISTRY-CONVERSION must land before DASHBOARD-FACETS-FULLY-CANONICAL,
since that ticket needs a stable, final `LAYER_VALUES` source (registry-
backed, not the old hardcoded literal) before treating it as canonical.
CANONICAL-ENUM-DOCS-UPDATE runs last since it documents the final, landed
state of everything else, including the Layer-registry mechanism.

Re-run `/implement-epic` with the same epic_id after any gate failure —
already-done tickets are skipped automatically.
