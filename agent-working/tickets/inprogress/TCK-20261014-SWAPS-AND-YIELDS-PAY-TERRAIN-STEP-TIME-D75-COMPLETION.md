---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261014-SWAPS-AND-YIELDS-PAY-TERRAIN-STEP-TIME-D75-COMPLETION
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-SWAPS-AND-YIELDS-PAY-TERRAIN-STEP-TIME-D75-COMPLETION

## Title
A position swap and a yield displacement pay the step time of the tile the entity is moved onto, and an entity still taking its previous step is neither swapped nor displaced (D75 completion; closes the 2.126 disclosure).

## Status
INPROGRESS

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
The D75 attribution (rpg-implementer-3, 2026-10-14) found that terrain step time (`NavigationComponent.step_ready_tick`, divergence 2.126) is paid only on an entity's own step in `MovementSystem.resolve_move`. Over five frontier seeds (ON, 247544 steps): 921 steps (0.37%) were untimed (swaps, yields, 45 unclassified) and 26 were taken while the entity was still held. Per rpg-planner and the designer (D75/D76): make swaps and yields pay step time and respect the hold, measure alone under audit_mode with a base-vs-base check.

## Scope
- `MovementPhase._build_position_swap_entity_update` sets `step_ready_tick`; a held entity is not swapped (`_can_attempt_position_swap_pair`).
- The yield displacement (`MovementSystem._yield_update`) sets the occupant's `step_ready_tick`; a held occupant is not displaced.
- Classify the 45 untimed "other" steps first; fix any that are a stepping path.
- Divergence update (closes the 2.126 "not timed" disclosure), parity, Bible note, measurement.

## Out of Scope
- Route choice weighted by cost (its own ticket). Teleports and displacement to a safe region (not a step). The typed death cause (own ticket).

## Acceptance Criteria
- A swap onto a tile of cost N sets `step_ready_tick` to tick + N for both; a held participant does not swap; a yielded occupant pays the cost of its new tile and a held occupant is not displaced. Pinned by tests.
- Re-count of untimed steps and steps that broke the hold is 0 on the paths fixed.
- Paired measurement under audit_mode with base-vs-base, reported as drift.

## Related Tickets
TCK-20261014-TERRAIN-COST-BECOMES-TIME-A-STEP-COSTING-N-TAKES-N-TIMES-AS-LONG-D75.

## Related Docs
docs/guidelines/intentional_divergences.md 2.126; docs/mechanics/02_combat_laws.md section 8.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/movement.py (_yield_update, _step_ready_tick); src/engine/pipeline_phases/movement.py (swap phase).

## Assumptions / Open Questions
- The 45 unclassified untimed steps may be a non-stepping path (teleport, spawn); classified in the Investigation.

## Implementation Notes
TBD

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
