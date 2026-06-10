# TCK-20260610-SCENARIO-TEMPLATES

## Title
Add scenario authoring templates with structural validation schema

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Phase 41.1. Define 10 reusable scenario templates for common simulation setups. Templates encode the allowed structure (required world features, perspective types, initial conditions, focus modules) — they do not contain scripted behavior. Phase 30 introduced scenario setup; this ticket expands it so scenarios declare a template and are validated against it.

## Scope
- Add `ScenarioTemplateDefinition(BaseModel)` with fields: `id`, `required_world_features`, `required_perspective_types`, `allowed_initial_conditions`, `allowed_focus_modules`
- Define 10 templates: `territorial_pressure`, `raider_conflict`, `trade_route_risk`, `resource_recovery`, `settlement_defense`, `cult_ritual_pressure`, `undead_containment`, `wildlife_intrusion`, `caravan_escort`, `mine_reopening`
- Register templates in a `ScenarioTemplateRegistry` (dict-backed, loaded once)
- Add `template_id: Optional[str]` to scenario definition schema; validate against registry on load
- Add `tests/unit/scenarios/test_scenario_templates.py`

## Out of Scope
- Scenario-to-world composition validation (that is TCK-20260610-SCENARIO-WORLD-VALIDATION)
- Implementing the scenarios themselves
- Changing scenario resolver or simulation runner

## Acceptance Criteria
- [ ] `ScenarioTemplateDefinition` schema exists and validates with Pydantic
- [ ] All 10 templates are defined and loadable
- [ ] Scenario with matching template ID and valid initial conditions passes validation
- [ ] Scenario with unsupported initial condition key fails with clear error
- [ ] Templates contain no action scripts, only structural constraints
- [ ] Scenario can omit `template_id` without error (templates are opt-in)
- [ ] Tests cover: valid match, unsupported condition, no template, template not found

## Related Tickets
- TCK-20260610-SCENARIO-WORLD-VALIDATION (companion — composition validation)
- TCK-20260610-SCENARIO-CATALOG-MATRIX (downstream — catalog matrix uses templates)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`

## Related Code Areas
- `src/world/scenario/` (existing scenario setup from Phase 30)
- `src/world/scenario/templates.py` — new

## Assumptions / Open Questions
- Where does the existing scenario definition live? Check `src/world/scenario/` before creating new schema.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
