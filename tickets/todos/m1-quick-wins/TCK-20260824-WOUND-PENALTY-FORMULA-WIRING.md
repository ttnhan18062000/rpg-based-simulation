---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260824-WOUND-PENALTY-FORMULA-WIRING
phase: open
date: 2026-08-24
tags: [combat]
---

# TCK-20260824-WOUND-PENALTY-FORMULA-WIRING

## Title
Wire In the Severity-Scaled Wound/Scar Penalty Formula

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
The severity-scaled penalty formula originally described for wounds/scars is dead code; live combat instead applies a flat penalty=5.0 to attack/defense only. The author wants the severity-scaled formula wired in for real, replacing the flat placeholder.

## Scope
- Change combat.py's `_get_wound_infliction()` to construct a `WoundState` via `WoundService.create_wound()` instead of the current hardcoded flat penalty=5.0 (combat.py:604-622)
- Ensure the live path produces `atk_penalty=int(severity*3)`, `def_penalty=int(severity*2)`, `speed_penalty=int(severity*2)`, `max_hp_penalty=int(severity*10)`
- Ensure `wound.max_hp_penalty` (currently always 0) becomes non-zero and reduces effective max_hp for severe wounds
- Add a test asserting two wounds of different severity produce measurably different penalties through the live path
- Correct `docs/mechanics/01_entity_anatomy.md:117` and `docs/mechanics/02_combat_laws.md:77` (currently document the flat -5/-5 bug) and `docs/parity_ledger/combat_movement.yaml` COMB-072/073/102/103/104 to reflect the real live-wired formula

## Out of Scope
- The unreachable 40% `should_inflict_wound()` threshold branch and `WOUND_THRESHOLD_RATIO` cleanup (owned by TCK-20260824-WOUND-THRESHOLD-DECISION)
- The wound-healing trigger decision (owned by TCK-20260824-WOUND-HEALING-DECISION)
- Wiring `speed_penalty` into `get_effective_stats` -- flag as an explicit follow-up decision, not silently included in this fix

## Acceptance Criteria
- [ ] combat.py's `_get_wound_infliction()` constructs `WoundState` via `WoundService.create_wound()` instead of a flat penalty=5.0
- [ ] Two wounds of different severity produce measurably different penalties through the live path, verified by a new test
- [ ] `wound.max_hp_penalty` is non-zero for severe wounds and reduces effective max_hp
- [ ] Test asserts live wound penalties scale with severity, not a pinned constant of 5.0
- [ ] docs/mechanics/01_entity_anatomy.md, docs/mechanics/02_combat_laws.md, and COMB-072/073/102/103 are corrected to match the live-wired formula

## Related Tickets
- TCK-20260429-E3-MISSING-LOGIC
- TCK-20260613-DOC-MECHANICS-SUBCONTRACTS
- TCK-20260619-PARITY-P0-BUGS
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
- TCK-20260824-WOUND-THRESHOLD-DECISION
- TCK-20260824-WOUND-HEALING-DECISION
- TCK-20260824-TACTICAL-WOUND-SCAR-WIRING

## Related Docs
- docs/mechanics/01_entity_anatomy.md
- docs/mechanics/02_combat_laws.md
- docs/mechanics/damage_formula_contract.md
- docs/parity_ledger/combat_movement.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/combat.py
- src/engine/rpg_depth.py
- src/core/state.py
- src/engine/apply.py
- src/core/updates.py
- src/engine/patches.py

## Assumptions / Open Questions
- Recommended to land BEFORE TCK-20260824-WOUND-THRESHOLD-DECISION (C2) is finalized, since this wiring narrows C2's dead-code scope
- Whether speed_penalty should be wired into get_effective_stats in this ticket or as a separate follow-up is an open decision -- currently deferred as out of scope
- Must not accidentally swap in should_inflict_wound()'s 40% gating threshold -- only the penalty formula is in scope here, not the infliction threshold (C2's territory)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
