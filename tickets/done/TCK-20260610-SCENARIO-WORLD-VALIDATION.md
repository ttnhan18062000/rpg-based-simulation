---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260610-SCENARIO-WORLD-VALIDATION
phase: done
date: 2026-06-10
tags: [scenario, world, validation]
---

# TCK-20260610-SCENARIO-WORLD-VALIDATION

## Title
Add scenario-to-world-composition feature validator

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Phase 41.2. Scenarios reference world features (ecology types, trade route modules, etc.). This ticket adds `ScenarioWorldFeatureValidator.validate(scenario, resolved_world_composition)` so scenarios fail at load time if they reference features not provided by their selected world composition. Prevents silent mis-configuration.

## Scope
- Add `ScenarioWorldFeatureValidator` class with `validate(scenario, resolved_world_composition)` method
- Validation checks: each `required_world_features` entry exists in composition outputs; each `allowed_focus_modules` reference is present; each `required_perspective_types` is provided
- Return type: `ValidationResult(ok: bool, errors: list[str])` where each error names scenario ID and missing feature
- Integrate validation into scenario load / scenario setup resolver
- Add unit tests for: feature present, feature missing, focus module missing, perspective missing, deterministic output

## Out of Scope
- Runtime validation during simulation (this is load-time only)
- Changing scenario template schema (that is TCK-20260610-SCENARIO-TEMPLATES)
- Building the world composition resolver itself

## Acceptance Criteria
- [ ] `ScenarioWorldFeatureValidator.validate()` exists
- [ ] Missing required world feature returns `ok=False` with error naming scenario ID and feature
- [ ] Missing focus module returns `ok=False`
- [ ] Missing required perspective returns `ok=False`
- [ ] All features present returns `ok=True`
- [ ] Validation result is deterministic for same inputs
- [ ] Error message includes scenario ID and missing feature name

## Related Tickets
- TCK-20260610-SCENARIO-TEMPLATES (prerequisite schema)
- TCK-20260610-SCENARIO-CATALOG-MATRIX (downstream — matrix validates via this)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`

## Related Code Areas
- `src/world/scenario/` — existing resolver
- `src/world/scenario/feature_validator.py` — new
- `src/world/composition/` — resolved world composition

## Assumptions / Open Questions
- Does `resolved_world_composition` have a typed contract? Read existing composition code before designing validator interface.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
