---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260824-WOUND-HEALING-DECISION
phase: open
date: 2026-08-24
tags: [combat]
---

# TCK-20260824-WOUND-HEALING-DECISION

## Title
Decide Whether Wound Healing Should Ever Fire

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
No wound has ever healed in production because `WoundUpdate.wounds_heal` has zero producers. The author wants a decision on whether healing should be implemented, or whether wounds are intentionally permanent until a Scar forms -- separate from the penalty-formula fix.

## Scope
- Record an explicit decision in both Mechanics Bible sections (`docs/mechanics/02_combat_laws.md` Section 5, `docs/mechanics/01_entity_anatomy.md` Section 6): (a) healing is active with a defined trigger, or (b) wounds are intentionally permanent and scars form via a different path
- If (a): implement a real production code path that constructs `WoundUpdate(wounds_heal=[...])` under a deterministic condition, verified via a non-mocked `Kernel.tick_once()` run
- If (b): remove or explicitly annotate `heal_wound()` and `MedicalService.get_diagnosis_quality()` as dead-by-design, and add a `docs/guidelines/intentional_divergences.md` entry
- Correct `docs/parity_ledger/combat_movement.yaml` COMB-296 and `docs/event_ledger/entity.yaml` ENTITY-018 to reflect that `wound_healed` currently has zero production producers, regardless of which option is chosen
- State explicitly whether `MedicalService.get_diagnosis_quality()` (also dead, zero callers) belongs to the healing pipeline or is separately dead

## Out of Scope
- The severity-scaled penalty-formula fix (owned by TCK-20260824-WOUND-PENALTY-FORMULA-WIRING) -- this ticket is explicitly independent of that fix
- The `should_inflict_wound()` 40% threshold dead-code decision (owned by TCK-20260824-WOUND-THRESHOLD-DECISION)

## Acceptance Criteria
- [ ] An explicit decision is recorded in both Mechanics Bible sections, replacing the current ambiguous "when a wound heals" phrasing
- [ ] If healing is made active: a real production code path constructs `WoundUpdate(wounds_heal=[...])` under a deterministic condition, verified via non-mocked `Kernel.tick_once()`
- [ ] If wounds are declared permanent: `heal_wound()`/`MedicalService.get_diagnosis_quality()` are removed or annotated dead-by-design, with an `intentional_divergences.md` entry added
- [ ] COMB-296 and ENTITY-018 are corrected to reflect zero production producers regardless of the gate state chosen

## Related Tickets
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
- TCK-20260619-PARITY-P0-BUGS
- TCK-20260429-E3-MISSING-LOGIC
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY
- TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX
- TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX
- TCK-20260824-WOUND-THRESHOLD-DECISION
- TCK-20260824-WOUND-PENALTY-FORMULA-WIRING

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/mechanics/01_entity_anatomy.md
- docs/parity_ledger/combat_movement.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/rpg_depth.py
- src/core/updates.py
- src/engine/combat.py
- src/engine/patches.py
- src/observability/event_extractor.py

## Assumptions / Open Questions
- This is a genuine open design question with no documented trigger condition anywhere in the Mechanics Bible -- no partial implementation exists to build from
- Coordinate sequencing with TCK-20260824-WOUND-THRESHOLD-DECISION (C2), since a "wounds are permanent" verdict here would further narrow C2's `should_inflict_wound()`/`heal_wound()` cleanup scope

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
