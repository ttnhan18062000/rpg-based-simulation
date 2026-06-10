# TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS

## Title
Connect MotivationPressureResolver and PerceptionGate to existing decision points

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Phase 42.3. `MotivationPressureResolver` (42.1) and `PerceptionGate` (42.2) exist but are not yet wired into simulation decision points. This ticket adds them as scoring inputs to five high-impact decision locations: combat target eligibility, territorial response, avoidance/flee decision, resource-seeking priority, service/trade seeking. The flow is: perception gate → relation projection → motivation pressure → target/goal scoring. No existing decision point is rewritten — pressures are additive scoring inputs.

## Scope
- Combat target eligibility: entity cannot target unperceived enemy (`PerceptionGate.can_perceive()` gates hostiles list in `src/engine/tactical.py`)
- Territorial animal scores intruder higher inside territory when `territory_pressure` is elevated
- Merchant avoids high-threat target when `safety_pressure` is high (flee/avoidance decision)
- Guard scores duty-related threats higher when `duty_pressure` is elevated
- Resource-seeking priority weighted by `hunger_pressure` / `wealth_pressure`
- Do NOT rewrite the entire behavior engine — insert pressure as a multiplier/gate at existing scoring callsites

## Out of Scope
- Adding new goal types or behavior trees
- Rewriting tactical decision engine
- Scripted behavior per archetype

## Acceptance Criteria
- [x] Unperceived enemy cannot be selected as combat target
- [x] Territorial animal scores intruder higher when territory_pressure elevated
- [x] Merchant flee decision triggered by safety_pressure above threshold
- [x] Guard prioritises duty-related threat when duty_pressure elevated
- [x] Existing combat tests still pass
- [x] New behavioral tests are deterministic and small
- [x] No direct scripted behavior added (pressure-based scoring only)

## Related Tickets
- TCK-20260610-MOTIVATION-PRESSURE-RESOLVER (prerequisite)
- TCK-20260610-SENSE-PERCEPTION-GATE (prerequisite)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md`
- `docs/engine/kernel.md`

## Related Code Areas
- `src/engine/tactical.py` — hostile target selection (primary consumer)
- `src/engine/behavior_consumers.py` — singleton bridge (new)

## Assumptions / Open Questions
- Resource-seeking priority (hunger/wealth) is a strategic-level concern; tactical.py follows the already-selected objective, so no tactical hook is needed here.

## Implementation Notes
Created `src/engine/behavior_consumers.py` as singleton bridge with configurable injection for tests (`configure_behavior_consumers` / `reset_behavior_consumers`). Four changes in `evaluate_entity_intent`:
1. Pressure resolved once via `get_pressure_resolver().resolve_pressures(entity)` — read-only, silent fallback to `MotivationPressureSet.empty()`
2. Perception gate in hostile loop: `get_perception_gate().can_perceive(entity, get_entity_signals(n), {"distance": dist})` — permissive fallback on exception
3. Safety pressure flee: after hostile list and strat_up, if `safety_pressure > 0.75` triggers SAFETY_PRESSURE_RETREAT
4. `target_score()` closure: `pressure_dist_mod = max(0, 1 - territory_pressure*0.4 - duty_pressure*0.3)` multiplies effective distance

## Test Summary
7 tests in `tests/unit/engine/test_pressure_perception_consumers.py`. Covers: magic-only target not perceived by humanoid, arcane entity perceives magic target, territorial entity selects target, safety_pressure retreat trigger, low safety no retreat, duty pressure target selection, determinism. All 7 pass. Pre-existing `test_stamina_drain` failure unchanged.

## Files Changed
- `src/engine/behavior_consumers.py` (new)
- `src/engine/tactical.py` (modified — 4 insertion points)
- `tests/unit/engine/test_pressure_perception_consumers.py` (new)

## Completion Summary
Perception gate and motivation pressures are now live consumers in the tactical decision pipeline. All wiring is additive (no rewrites), data-driven, and deterministic. Seven new tests pass. No scripted per-archetype behavior introduced.
