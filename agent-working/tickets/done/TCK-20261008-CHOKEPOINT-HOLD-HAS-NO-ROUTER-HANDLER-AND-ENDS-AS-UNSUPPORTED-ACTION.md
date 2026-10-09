---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261008-CHOKEPOINT-HOLD-HAS-NO-ROUTER-HANDLER-AND-ENDS-AS-UNSUPPORTED-ACTION
phase: done
date: 2026-10-08
tags: [combat]
---

# TCK-20261008-CHOKEPOINT-HOLD-HAS-NO-ROUTER-HANDLER-AND-ENDS-AS-UNSUPPORTED-ACTION

## Title
A VANGUARD holding a chokepoint emits an ENTITY_ACT HOLD that no router handler recognised, so every hold ended as UNSUPPORTED_ACTION

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`tactical.py` HOLD_CHOKEPOINT emitted `ENTITY_ACT` `HOLD`; the router fell through to `UNSUPPORTED_ACTION`. The tile was still held by movement mode `HOLD` (speed multiplier 0) and the brain re-decided on its cadence, so the only defect was a reported failure. 0 decisions in 30 pinned runs (needs WALL tiles with a one-tile gap).

## Scope
Router: HOLD is a typed no-op success. actions.py: a HOLD success ends its task like a survival action. Constructed test; COMB-015 test_path; divergence 2.90.

## Out of Scope
- When a VANGUARD chooses to hold (`identify_chokepoints`, the 5-tile trigger). - Any ReasonCode or state field.

## Acceptance Criteria
- [x] Zero UNSUPPORTED_ACTION reports for the hold. - [x] The holder stays on its tile and its brain re-decides. - [x] COMB-015 has a test_path.

## Related Tickets
- TCK-20261008-A-FIGHTER-HOLDS-BETWEEN-BLOWS-CONFLICT-04. - The batch's free-hit ticket (same PR).

## Related Docs
- `docs/world_rules/capability-progression/conflict-combat.md` (CONFLICT-04, decision 32), `docs/mechanics/02_combat_laws.md` section 7, `docs/engine/contracts/tactical_contract.md`, `docs/guidelines/intentional_divergences.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-CHOKEPOINT-HOLD-HAS-NO-ROUTER-HANDLER-AND-ENDS-AS-UNSUPPORTED-ACTION/` (investigation.md, plan.md, test_plan.md, probes/)

## Related Code Areas
- `src/engine/candidate_selector.py`, `src/engine/hostility.py`, `src/engine/executor.py`, `src/engine/worker_logic.py`, `src/engine/domain/action_router.py`, `src/engine/pipeline_phases/actions.py`

## Assumptions / Open Questions
- The shape rpg-planner first ruled (keep the task) was built and rejected: the holder reported HOLD SUCCESS for all 60 ticks and its brain never re-decided. The bounded variant was accepted.

## Implementation Notes
See the investigation and plan in the stored artifacts.

## Test Summary
`tests/unit/combat/test_chokepoint_hold.py` (decision; typed success ending its task with no UNSUPPORTED_ACTION; kernel stays on the tile and re-decides). Part of the 797-test sweeps above.

## Files Changed
src/engine/domain/action_router.py, src/engine/pipeline_phases/actions.py, tests/unit/combat/test_chokepoint_hold.py, docs (tactical_contract chokepoint line, divergences 2.90, parity COMB-015).

## Completion Summary
A chokepoint hold is a typed success; trajectory identical to main; zero UNSUPPORTED_ACTION.
