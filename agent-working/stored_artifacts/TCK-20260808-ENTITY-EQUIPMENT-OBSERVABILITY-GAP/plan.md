---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP
artifact_type: plan
tags: [observability, world]
---

# Plan — TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP

## Steps

1. `src/observability/event_extractor.py`: two new diff-based events, `item_equipped`/
   `item_unequipped` (per-slot `entity.equipment.slots` diff) and `equipment_durability_changed`
   (per-slot `entity.equipment.durability` diff, severity per the 0/50/100 real-scale bands from
   investigation.md), inserted in the same vitals/attributes block, same `_is_real_number`-style
   defensive guard pattern for the durability floats.
2. `tests/unit/observability/test_event_extractor_equipment.py`: the 9 tests from test_plan.md.
3. `docs/simulation_quality/event_type_coverage.md`: register `item_equipped`, `item_unequipped`,
   `equipment_durability_changed` in §5 Unscored Intentional.
4. `docs/event_ledger/entity.yaml`: flip `ENTITY-014` from `silent` to `observed`.
5. Parity: equipment mutation is entity-core state — new entry in `docs/parity_ledger/
   substrate.yaml` (same `SUB-` domain as SUB-375/SUB-376), next ID after `SUB-376`.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies every real mutation source | Done |
| New event(s) wired and confirmed via real Kernel.tick_once() loop (or documented fallback) | Step 2 |
| event_type_coverage.md and entity.yaml updated | Steps 3-4 |
| Scoped pytest passes | Step 2 |
