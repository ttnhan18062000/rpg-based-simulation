---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP
artifact_type: test_plan
tags: [observability, world]
---

# Test Plan — TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP

New file: `tests/unit/observability/test_event_extractor_equipment.py`

1. `test_item_equipped_fires_on_fresh_equip` — hand-built `EquipmentComponent` slot goes from
   `None` to an item id; assert `item_equipped` fires, `previous_item_id is None`.
2. `test_item_equipped_fires_on_swap_with_previous_item_id` — slot goes from item A to item B;
   assert `item_equipped` fires with `previous_item_id == "A"`.
3. `test_item_unequipped_fires_when_slot_cleared` — slot goes from an item id to `None`; assert
   `item_unequipped` fires.
4. `test_equipment_durability_changed_severity_info_above_50` — durability delta staying `>= 50.0`;
   assert severity `INFO`.
5. `test_equipment_durability_changed_severity_warning_below_50` — delta crossing below `50.0`;
   assert severity `WARNING`.
6. `test_equipment_durability_changed_severity_critical_at_zero` — delta reaching `0.0`; assert
   severity `CRITICAL`.
7. `test_equipment_durability_changed_severity_info_on_repair_increase` — positive delta (repair);
   assert severity `INFO` regardless of resulting value.
8. `test_no_event_on_zero_delta` — identical `EquipmentComponent` before/after; assert no events.
9. `test_equipment_events_suppressed_in_light_and_long_run_modes` — same suppression pattern as
   sibling tickets.
10. Attempt (Implement phase, not a fixed test): a real `Kernel.tick_once()` loop to check whether
    the narrow goblin-evolution path is reachable within a reasonable budget; add a real-kernel
    test only if it actually fires, otherwise document the attempt in investigation.md/ticket
    Implementation Notes and rely on tests 1-9.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies every real `EquipmentUpdate` mutation source | Done — 1 live-narrow, 3 gated off, 2 dead code |
| New event(s) wired and confirmed via a real `Kernel.tick_once()` loop | Attempted per item 10; falls back to hand-built-state pattern (tests 1-9) if unreachable, matching sibling tickets |
| `event_type_coverage.md` and `docs/event_ledger/entity.yaml` updated | Document-Update phase |
| Scoped pytest passes | Tests 1-9 |
