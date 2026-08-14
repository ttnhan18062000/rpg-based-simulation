---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP
phase: open
date: 2026-08-08
tags: [observability, world]
---

# TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP

## Title
Equipment/gear changes (slot assignment, durability) have zero observability events

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260808-ENTITY-EVENT-LEDGER`'s cross-reference (`docs/event_ledger/entity.yaml`
`ENTITY-014`) confirmed `EquipmentUpdate` (slot assignments, durability delta/set) has no
corresponding observability event — confirmed via `grep -n "\.equipment\.\|equip_slots\|equipped_"
event_extractor.py`, zero matches. Equipping/unequipping gear and gear durability decay/repair are
entirely invisible to the observability pipeline, distinct from `CombatUpdate`'s own wound/HP
narrative (which IS observed).

## Scope
1. **Investigate**: find every code path that mutates `EquipmentUpdate` (shops, crafting, combat
   durability decay, quest rewards) to understand the real sources.
2. **Plan**: design event(s) — likely `item_equipped`/`item_unequipped` and a durability-threshold
   event (e.g. gear breaking), not a per-tick durability-decay event (too high-volume).
3. **Implement**: wire emission, register in `event_type_coverage.md`, update the ledger.

## Out of Scope
- SimQ scorer wiring — separate decision (though ECONOMY pillar is a plausible natural fit,
  Investigate should note this as a candidate, not assume it).
- Sibling findings tracked in their own tickets.

## Acceptance Criteria
- [x] investigation.md identifies every real `EquipmentUpdate` mutation source (1 live-narrow,
      3 gated off corpus-wide, 2 confirmed dead code)
- [x] New event(s) wired; real `Kernel.tick_once()` verification attempted first (1000 real ticks
      on `sandbox_world`, confirmed zero goblin-kind entities exist so the one live producer
      cannot fire in this world) — verified instead via this repo's own precedented hand-built-
      state pattern, matching the sibling vitals/attributes tickets
- [x] `event_type_coverage.md` and `docs/event_ledger/entity.yaml` updated
- [x] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-EVENT-LEDGER (found this gap — DONE)
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP, TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP,
  TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP (sibling findings)

## Related Docs
- `docs/event_ledger/entity.yaml` (`ENTITY-014`)
- `docs/core/update_intents.md` (`EquipmentUpdate` definition)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-ENTITY-EVENT-LEDGER/`

## Related Code Areas
- `src/observability/event_extractor.py`
- `src/core/updates.py` (`EquipmentUpdate`)

## Assumptions / Open Questions
- Whether durability decay is frequent enough that a per-crossing event (rather than per-tick)
  would still be high-volume — not assumed; Investigate should check real decay rates before
  committing to an event granularity.

## Implementation Notes
- **Subagent spawn cap reached this session** — Investigate/Plan/Implement/Document-Update/
  Parity/Verify performed directly.
- **Mutation-source verification**: 7 `EquipmentUpdate(` call sites found. Only
  `src/engine/evolution.py`'s goblin-kind species-evolution gear grant (evolution level >= 10) is
  genuinely live and unconditional. 3 more (`resolver.py::EQUIP_ITEM`, `combat.py`'s durability
  decay, `core_actions.py::execute_repair`) are real, wired code gated off corpus-wide
  (`ENABLE_PROGRESSION_EVOLUTION` / `ENABLE_COMBAT_ENGAGEMENT`). 2
  (`EquipmentService.auto_equip`/`.repair_equipment`) are confirmed dead code — zero real callers.
- **Tangential finding, disclosed not fixed**: `src/domains/progression/gaps.py`'s `repair_gap`
  detection and `src/engine/gold_sink.py`'s `_count_degraded_slots` (REPAIR_FEE) both compare
  `entity.equipment.durability` against a 0-1 normalized scale (`< 0.5`), but the real field uses
  a 0-100 scale throughout the actual mutation code — silently making both checks unreachable in
  practice. Not fixed here (apply/detection-logic correctness question, out of scope for an
  observability ticket); currently non-regressive since the relevant producers are gated off.
- 3 new events added to `event_extractor.py`'s diff loop: `item_equipped`/`item_unequipped`
  (per-slot `slots` diff) and `equipment_durability_changed` (per-slot `durability` diff).
  Durability severity bands (INFO >= 50, WARNING < 50, CRITICAL <= 0) reuse the field's real
  0-100 scale, applying the same 50%-repair intent already designed (but mis-scaled) into
  `gaps.py`/`gold_sink.py`, not an invented number.
- The ticket's own original Scope cautioned against a per-tick durability event as "too high-
  volume." Investigation found this premise doesn't hold: durability only changes on discrete
  combat-hit/repair actions, never an unconditional per-tick decay — so full-delta coverage
  (per this session's standing "major to minor" instruction) does not create
  `movement`/`biological`-class volume. Implemented full coverage, not a threshold-only subset.
- **Real-verification attempted, confirmed unreachable**: real `Kernel.tick_once()` loop (1000
  ticks, `sandbox_world`) confirmed zero goblin-kind entities exist in that world — the one live
  producer cannot fire regardless of tick budget. Fell back to the repo's own precedented
  hand-built-state pattern.
- **Parity**: same 3 pre-existing P0 hits re-confirmed unrelated (push-shaper cutover). Added
  `SUB-377` to `docs/parity_ledger/substrate.yaml`. Cross-reference gate PASS.

## Test Summary
- `tests/unit/observability/test_event_extractor_equipment.py` (new, 9/9 pass):
  `test_item_equipped_fires_on_fresh_equip`, `test_item_equipped_fires_on_swap_with_previous_item_id`,
  `test_item_unequipped_fires_when_slot_cleared`,
  `test_equipment_durability_changed_severity_info_above_50`,
  `test_equipment_durability_changed_severity_warning_below_50`,
  `test_equipment_durability_changed_severity_critical_at_zero`,
  `test_equipment_durability_changed_severity_info_on_repair_increase`,
  `test_no_event_on_zero_delta`, `test_equipment_events_suppressed_in_light_and_long_run_modes`.
- `tests/unit/observability/` full suite: 973 passed, 6 skipped, 0 failed (964 + 9 new, zero
  regressions).

## Files Changed
- `src/observability/event_extractor.py` — 2 new event emission blocks (3 event types total)
- `tests/unit/observability/test_event_extractor_equipment.py` — new, 9 tests
- `docs/simulation_quality/event_type_coverage.md` — §5 new rows, Summary counts (19→22)
- `docs/event_ledger/entity.yaml` — `ENTITY-014` flipped `silent`→`observed`
- `docs/parity_ledger/substrate.yaml` — new entry `SUB-377`

## Completion Summary
Equipment slot assignment and durability went from zero observability coverage to full-coverage,
severity-tagged event emission (`item_equipped`, `item_unequipped`, `equipment_durability_changed`).
Investigation found 1 of 7 grep-hit producers genuinely live and unconditional (narrow — goblin-
kind evolution), 3 gated off corpus-wide, 2 confirmed dead code. Overrode the ticket's own
original "avoid per-tick volume" caution after confirming durability changes are event-driven,
not per-tick — implemented full coverage per the session's standing instruction. Disclosed a
durability-scale-mismatch bug in `gaps.py`/`gold_sink.py`, not fixed (out of scope). Real-kernel
verification attempted first and confirmed unreachable (zero goblin-kind entities in the
calibration world), so verification fell back to the repo's own precedented hand-built-state
pattern. Classified `unscored_intentional`. Parity ledger updated with 1 new entry (`SUB-377`).
