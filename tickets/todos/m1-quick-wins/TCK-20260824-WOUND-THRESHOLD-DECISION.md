---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260824-WOUND-THRESHOLD-DECISION
phase: open
date: 2026-08-24
tags: [combat]
---

# TCK-20260824-WOUND-THRESHOLD-DECISION

## Title
Resolve the Wound Threshold Discrepancy (25% Live vs 40% Dead Code)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The live wound-infliction threshold is 25%, but a 40% branch in WoundService.should_inflict_wound() is unreachable dead code, and two Mechanics Bible docs cross-reference the stale value. The author wants a decision made: delete the unreachable branch, or leave it and correct the docs.

## Scope
- Record a single documented decision: delete the unreachable 40% branch in WoundService.should_inflict_wound(), or keep it and correct the docs
- If delete: remove WoundService.should_inflict_wound(), WOUND_THRESHOLD_RATIO, and other zero-caller methods not made live by C3's wiring; remove/rewrite tests/unit/core/test_rpg_depth.py::TestWoundInfliction
- If keep: add an explicit dead/legacy annotation in code, add a docs/guidelines/intentional_divergences.md entry, and update COMB-290's v2_evidence
- Resolve the WOUND_THRESHOLD_RATIO identifier-name collision between docs/mechanics/01_entity_anatomy.md's pseudocode (0.25) and the dead code's 0.40 value so a grep no longer surfaces a contradiction
- Correct docs/parity_ledger/combat_movement.yaml COMB-290's test_path pointer (currently points to test_combat_matrix.py, which contains no wound-related test)

## Out of Scope
- The severity-scaled penalty formula wiring itself (owned by TCK-20260824-WOUND-PENALTY-FORMULA-WIRING)
- The wound-healing trigger decision (owned by TCK-20260824-WOUND-HEALING-DECISION)
- This ticket's final scope should exclude WoundService.create_wound() once C3 makes it live -- narrowing happens after C3 lands, not before

## Acceptance Criteria
- [ ] A single documented delete-vs-keep decision is recorded with rationale
- [ ] docs/mechanics/01_entity_anatomy.md, docs/mechanics/02_combat_laws.md, and COMB-290 stay internally consistent with the decision
- [ ] If delete: should_inflict_wound()/WOUND_THRESHOLD_RATIO removed and TestWoundInfliction updated accordingly
- [ ] If keep: code carries an explicit dead/legacy annotation and intentional_divergences.md gains an entry
- [ ] COMB-290's v2_evidence and test_path are corrected to reflect ground truth regardless of which option is chosen

## Related Tickets
- TCK-20260619-PARITY-P0-BUGS
- TCK-20260613-DOC-MECHANICS-SUBCONTRACTS
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
- TCK-20260824-WOUND-PENALTY-FORMULA-WIRING
- TCK-20260824-WOUND-HEALING-DECISION

## Related Docs
- docs/mechanics/01_entity_anatomy.md
- docs/mechanics/02_combat_laws.md
- docs/parity_ledger/combat_movement.yaml
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/rpg_depth.py
- src/engine/combat.py
- docs/mechanics/01_entity_anatomy.md
- docs/mechanics/02_combat_laws.md
- docs/parity_ledger/combat_movement.yaml

## Assumptions / Open Questions
- This ticket should be sequenced AFTER TCK-20260824-WOUND-PENALTY-FORMULA-WIRING (C3) lands, since C3 wiring create_wound() into live combat narrows this ticket's dead-code scope to should_inflict_wound()/heal_wound() only
- The residual gap is an identifier-name collision in doc pseudocode, not a value error -- both Mechanics Bible docs already state the correct 25% figure
- Whether heal_wound() should be handled here or deferred entirely to TCK-20260824-WOUND-HEALING-DECISION (C4) needs confirming once C4's decision lands

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
