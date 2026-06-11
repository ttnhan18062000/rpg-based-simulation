---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260609-SCENARIO-MODIFIER-APPLY
phase: done
date: 2026-06-09
tags: [scenario, modifier, apply]
---

# TCK-20260609-SCENARIO-MODIFIER-APPLY

## Title
Apply scenario setup modifiers safely as deterministic state/context effects

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
ScenarioSetupResolver produces a list of StateSetupModifier records. This task converts those records into actual deterministic effects on the initial world/runtime state: territorial_intrusion marks a faction inside claimed territory context, resource_scarcity reduces resource counts or adds pressure tags, faction_activity changes initial alertness level, population_alertness sets readiness hints. Scenarios remain setup data, not behavior scripts — no modifier should force direct entity actions like "wolf attacks hero."

## Scope
- Implement modifier application logic in `src/scenarios/modifier_applicator.py`
- Support modifier types: territorial_intrusion, resource_scarcity, faction_activity, population_alertness (and any others listed in allowed categories from Task 30.1)
- Unsupported modifier types must fail explicitly (not silently skip)
- Modifier application must be testable without running a full simulation tick
- Add unit tests: initial_condition → setup modifier, modifier → deterministic state/context effect, unsupported modifier fails

## Out of Scope
- Adding new modifier types not in the allowed category set
- Simulating entity behavioral responses to modifiers
- Directly forcing entity actions

## Acceptance Criteria
- [ ] Setup modifiers are applied deterministically (same modifiers → same state)
- [ ] Modifiers do not bypass entity behavior systems
- [ ] Modifiers do not embed direct action scripts
- [ ] Unsupported modifier types raise a clear error
- [ ] Modifier application can be tested without running a full simulation tick
- [ ] All supported modifier types have at least one test covering the state/context effect

## Related Tickets
- TCK-20260609-SCENARIO-SETUP-RESOLVER (dependency)

## Related Docs
- docs/mechanics/05_world_evolution.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/scenarios/modifier_applicator.py (new)
- src/scenarios/resolver.py
- tests/unit/scenarios/test_scenario_modifier_apply.py (new)

## Assumptions / Open Questions
- Initial world/runtime state object is accessible at setup time before the first tick

## Implementation Notes
- `ModifierApplicator.apply()` processes modifiers sorted by type for determinism, builds
  `ScenarioSetupContext` fields per type, raises `UnsupportedModifierError` for unknown types
- `ScenarioSetupContext` is a frozen Pydantic model; no catalog/repo/tick access required
- Modifiers do not embed entity actions — all effects are typed overlay fields

## Test Summary
16 passed — all 8 modifier types covered, empty list, unsupported type error, determinism, frozen context, no catalog imports

## Files Changed
- `src/scenarios/modifier_applicator.py` (new)
- `tests/unit/scenarios/test_scenario_modifier_apply.py` (new)

## Completion Summary
ModifierApplicator converts StateSetupModifier list into ScenarioSetupContext deterministically.
All acceptance criteria met: deterministic, no entity actions, unsupported types fail explicitly,
testable without tick.
