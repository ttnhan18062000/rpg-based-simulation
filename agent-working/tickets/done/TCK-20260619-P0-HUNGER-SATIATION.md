---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-P0-HUNGER-SATIATION
phase: done
date: 2026-06-19
tags: [hunger, satiation, world-content, balance, phase-0, p0-foundation]
---

# TCK-20260619-P0-HUNGER-SATIATION

## Title
P0-3 · Hunger Satiation Gap — Add food resource node and verify need resolution

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
No food-kind resource node exists in any tested world. Entities generate `proj_hunger_N` every ~30 ticks but hunger urgency never resolves because there is nothing in the opportunity pipeline that provides food. Hunger permanently outscores all economic goals, making economic balance measurement, crafting validation, quest execution, and personality-driven route diversity unobservable.

Source: `docs/audits/D06_economic_cycle.md` F1; `docs/audits/D04_balance_tuning.md` § Hunger Calibration.

## Scope
- Add a `food_provision` resource node type to `sandbox_world` and `urban_political` world definitions (likely in `data/` world content files)
- Verify the hunger `need` reduction: completing a food-provision project must reduce `BiologicalComponent.hunger` durably (inspect `src/core/state.py:BiologicalComponent`)
- If hunger urgency does not drop after food consumption due to threshold calibration, adjust the urgency threshold so that a satisfied hunger scores below a typical economic goal
- Run a 400-tick `urban_political` simulation and verify ≥10% of active ticks per entity produce non-hunger project kinds

## Out of Scope
- Crafting recipes involving food (Epic 1.3)
- Faction food supply chains (Phase 5)
- Nutritional variation / food quality mechanics

## Acceptance Criteria
- In a 400-tick `urban_political` run, at least 10% of active ticks per entity produce non-hunger project kinds (verified in metric windows or event count)
- At least one `proj_hunger_N` project reaches COMPLETED (not SUSPENDED/REPLACED) in the run
- Hunger urgency drops measurably after food-provision completion (inspect scoring trace)

## Related Tickets
- TCK-20260618-AUDIT-EPIC (source: D06 F1 finding)
- TCK-20260619-P0-ENTITY-INIT (prerequisite: personality seeding; entity differentiation cannot be measured until both are fixed)
- TCK-20260619-E12-BALANCE-BASELINE (blocked by this ticket)

## Related Docs
- `docs/audits/D06_economic_cycle.md`
- `docs/audits/D04_balance_tuning.md`
- `docs/mechanics/01_entity_anatomy.md` § Biological Pressures (hunger trigger threshold — verify against values being fixed in P0-5 before changing)
- `docs/mechanics/03_economic_laws.md` § 3 (Resource Harvesting — update if satiation mechanic changes)
- `docs/plans/long_term_development_roadmap.md` § P0-3
- `docs/parity_ledger/town_resource.yaml` (resource node / harvesting entries — update status)
- `docs/parity_ledger/strategic_cognition.yaml` (need urgency entries — update if threshold changes)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-EPIC/`

## Related Code Areas
- `src/core/state.py:L114` (BiologicalComponent — hunger field)
- `src/engine/scheduler.py` (readiness gate for brain vs action work)
- `src/engine/tactical.py` (reach_location distance check and movement dispatch)
- `src/engine/domain/action_router.py` (EAT/REST/SLEEP survival bypass)
- `src/engine/pipeline_phases/actions.py` (ActionRoutingPhase survival bypass and task reset)
- `src/engine/phase_graph.py` (strategic_intelligence must_run_every_tick)
- `src/systems/strategic_systems/intelligence.py` (hunger project completion on satiation)

## Assumptions / Open Questions
- Root cause was NOT a missing content node but broken mechanics: entity brain was blocked by combat readiness drain from movement (no recharge mechanism), and EAT action was gated behind the same readiness check. The governor also escalated to DEGRADED mode due to small test tick budget, further delaying brain fires.

## Implementation Notes
Five interrelated bugs identified and fixed:

1. **Scheduler readiness gate** (`scheduler.py`): Brain tasks (ENTITY_BRAIN, idle ENTITY_ACT) were gated on readiness >= 100.0 same as combat actions. Fixed: brain bypasses readiness gate; only ENTITY_ACT-with-payload and ENTITY_MOVE require full readiness (COMB-266).

2. **Tactical movement dispatch** (`tactical.py`): `reach_location` objective dispatched ENTITY_MOVE when dist > 1.0, making entity non-idle and preventing future brain fires. Distance check was also `< 1.0` excluding entities adjacent at exactly 1.0 Manhattan tiles. Fixed: `dist <= 1.0` for adjacency; only set nav target when en-route (no task change — locomotion phase handles movement each tick).

3. **EAT readiness gate in action router** (`action_router.py`): EAT/REST/SLEEP survival actions were blocked by `verify_readiness` check (requires 100.0 readiness). Fixed: survival actions bypass readiness before the check.

4. **EAT readiness gate in pipeline phase** (`pipeline_phases/actions.py`): ActionRoutingPhase also blocked survival actions via readiness. Fixed: `is_survival` flag skips readiness gate. On successful survival action, task resets to empty payload so entity returns to idle and brain fires next cadence.

5. **Test tick budget** (`test_hunger_satiation.py`): `max_tick_budget_ms=1.0` caused governor to enter DEGRADED mode at tick 6, raising brain cadence from 10 to 50. Fixed: `max_tick_budget_ms=500.0` + `no_frame_pacing=True` to avoid both governor escalation and frame-pacing sleep overhead.

6. **Hunger project completion** (`intelligence.py`): HUNGER project had no completion path — the `_resolve_active_objective` function only handled "detour" kind, and the blocker-resolution path skipped projects with no blockers. Fixed: added explicit completion check when `hunger < 20.0`.

## Test Summary
- `tests/integration/scenarios/test_hunger_satiation.py::test_hunger_satiation_resolves_in_food_world` — PASSES (2.1s)
- `tests/unit/kernel/test_scheduler_contract.py` — all 8 pass including new `test_action_readiness_gate`
- `tests/integration/worldassembly/` — both affected tests pass after reverting frontier_village_core.yaml change
- Pre-existing failures confirmed pre-existing (unchanged by this ticket): `test_tactical_trust_obedience`, `test_hardening_e5`, content/registry tests

## Files Changed
- `src/engine/scheduler.py` — readiness gate bypass for brain tasks
- `src/engine/tactical.py` — dist <= 1.0, no ENTITY_MOVE dispatch for en-route
- `src/engine/domain/action_router.py` — EAT/REST/SLEEP bypass before readiness check
- `src/engine/pipeline_phases/actions.py` — survival bypass + task reset on success
- `src/engine/phase_graph.py` — strategic_intelligence must_run_every_tick=True
- `src/systems/strategic_systems/intelligence.py` — hunger/fatigue project completion on satiation
- `tests/integration/scenarios/test_hunger_satiation.py` — new integration test (max_tick_budget_ms=500, no_frame_pacing=True)
- `tests/unit/kernel/test_scheduler_contract.py` — updated test + new test_action_readiness_gate

## Completion Summary
Root cause was broken satiation mechanics, not missing content. The entity brain was starved of execution opportunities by: (1) readiness drain from movement with no recharge, (2) brain gated behind combat readiness, (3) EAT gated behind combat readiness, (4) task not reset after eating preventing future brain fires, (5) test tick budget causing governor escalation. All five fixed. Integration test passes in 2.1s with 87.5% non-hunger tick ratio and 1 completed HUNGER project.
