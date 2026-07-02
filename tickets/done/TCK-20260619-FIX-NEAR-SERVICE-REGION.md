---
status: historical
layer: engine
authority: P0
audience: agent
ticket_id: TCK-20260619-FIX-NEAR-SERVICE-REGION
phase: done
date: 2026-06-19
tags: [requirements, near_service, region, sandbox, audit-blocker]
---

# TCK-20260619-FIX-NEAR-SERVICE-REGION

## Title
Fix `near_service` requirement: replace `"hometown"` hardcode with actual building lookup

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
`RequirementEvaluator.evaluate()` for `kind="near_service"` passes only if `entity.navigation.region_id == "hometown"` (hardcoded Phase 1 stub, `requirements.py:154`). No world other than the Phase 1 test scaffold uses `"hometown"` as a region ID. `sandbox_world` uses `"town_center"` and `"woods"`. This means every `near_service` requirement fails for every entity in every real world, blocking all resource and service opportunities from passing their requirement checks. The correct implementation is to query `TownNavigation.get_nearest_service()` (already exists at `src/town/town_navigation.py:13`) and check the result against a distance threshold.

## Scope
- Replace the `if current_region == "hometown"` stub in `RequirementEvaluator.evaluate()` for `kind="near_service"` with a call to `TownNavigation.get_nearest_service(entity, subject, state)`.
- A service is "near" if the returned `BuildingState` is not `None` and the entity's position is within a configurable distance threshold (use the existing `manhattan ≤ 2.0` rule from `docs/simulation/town_contract.md` as the default, or the building's own proximity rule if available).
- Remove the `or "hometown"` fallback on `current_region` (line 152) — it silently masks missing `region_id` data.

## Out of Scope
- Changes to `TownNavigation.get_nearest_service()`.
- Changes to `ResourceOpportunityProvider` or the opportunity kind produced.
- Fixing RC1 or RC3.

## Acceptance Criteria
1. `RequirementEvaluator.evaluate()` for `kind="near_service"` calls `TownNavigation.get_nearest_service(entity, subject, state)` when `state` is not `None`.
2. Result is `True` (passed) if a functional building of the requested `service_kind` is found within distance ≤ 5.0 (Euclidean, matching `town_contract.md` proximity rules) of the entity's position.
3. When `state` is `None` (unit test context), the evaluator returns `passed=False` with `blocker_kind="too_far_from_service"` — it does not raise.
4. The `"hometown"` string no longer appears in the `near_service` branch of `requirements.py`.
5. `pytest tests/unit/strategic/test_requirements.py -x` passes.
6. A new test in `test_requirements.py` verifies: given an entity at position (0,0) and a functional `blacksmith` building at (2,2), `near_service` with `subject="blacksmith"` returns `passed=True`.

## Related Tickets
- TCK-20260527-COG-PHASE1-EVALUATOR (original implementation — stub comment says "Phase 1 mock")
- TCK-20260527-COG-PHASE1-OPPORTUNITIES (attaches `near_service` requirement to resource opportunities)
- TCK-20260619-FIX-ADVENTURE-OPPORTUNITY-WIRING (RC1 — must be fixed first for opportunities to reach this evaluator)
- TCK-20260619-FIX-PERF-BUDGETS-RESET (RC3)

## Related Docs
- `docs/audits/D03_behavioral_emergence.md` — RC2, Finding F2
- `docs/simulation/town_contract.md` — `TownNavigation.get_nearest_service()` contract and proximity rules
- `docs/mechanics/adventure_routing_contract.md` — §Blocker detection

## Related Stored Artifacts
- `stored_artifacts/TCK-20260527-COG-PHASE1-EVALUATOR/`

## Related Code Areas
- `src/world/providers/requirements.py:144-166` — `near_service` branch
- `src/town/town_navigation.py:13-29` — `TownNavigation.get_nearest_service()`
- `tests/unit/strategic/test_requirements.py` — add new test case

## Assumptions / Open Questions
- Distance threshold 5.0 Euclidean chosen (matches sabotage proximity rule in `town_contract.md`). Sufficient for sandbox_world where entities spawn within ~10 units of buildings.

## Implementation Notes
Replaced the `"hometown"` hardcode stub in `RequirementEvaluator.evaluate()` for `kind="near_service"` with a real `TownNavigation.get_nearest_service(entity, subject, state)` call. Distance threshold is 5.0 Euclidean. When `state is None`, `near` stays `False` → returns `passed=False` with `blocker_kind="too_far_from_service"` without raising. The `or "hometown"` fallback on `current_region` was removed (it was only used by the stub, no longer needed). Added three new tests: within-range pass, out-of-range fail, and `state=None` safety.

## Test Summary
`pytest tests/unit/strategic/test_requirements.py -x` — 5/5 passed (2 existing + 3 new).

## Files Changed
- `src/world/providers/requirements.py`
- `tests/unit/strategic/test_requirements.py`

## Completion Summary
Replaced Phase 1 `"hometown"` stub in `RequirementEvaluator.near_service` branch with a real `TownNavigation.get_nearest_service()` call using 5.0 Euclidean threshold. Added parity entry TOWN-171. Three new tests cover pass, fail, and state=None safety cases.
