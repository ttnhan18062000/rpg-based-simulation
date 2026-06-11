---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-SCENARIO-CATALOG-MATRIX
phase: done
date: 2026-06-10
tags: [scenario, catalog, matrix]
---

# TCK-20260610-SCENARIO-CATALOG-MATRIX

## Title
Add scenario catalog matrix integration test covering 8 scenario setups

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Phase 41.3. Create a data-driven integration test proving the scenario authoring model works across 8 different world setups. Each scenario must load, validate against its template, resolve its composition and perspectives, normalise initial conditions, and produce setup modifiers — without embedding behavior scripts.

## Scope
- Add `tests/integration/scenarios/test_scenario_catalog_matrix.py`
- Define 8 scenario definitions in the test (or as fixture YAML): `wolf_territory_pressure`, `goblin_camp_pressure`, `merchant_trade_route_risk`, `old_mine_recovery`, `undead_battlefield_containment`, `moon_cult_ruins_pressure`, `settlement_defense`, `forest_warden_patrol`
- Each scenario assertion proves: loads, template validates, composition resolves, perspective resolves, initial conditions normalise, setup modifiers produced, no simulation script embedded
- Test is data-driven (parametrize over scenario list)
- Add `tests/integration/scenarios/__init__.py` if missing

## Out of Scope
- Running simulation ticks (setup validation only)
- Adding new world composition types or modules beyond what existing system supports

## Acceptance Criteria
- [ ] All 8 scenarios load without error
- [ ] All 8 scenarios reference valid compositions
- [ ] All 8 scenarios reference valid perspectives
- [ ] All 8 scenarios pass feature validation
- [ ] All 8 scenarios produce setup modifiers
- [ ] No scenario embeds direct behavior scripts
- [ ] Test is parametrized (data-driven)
- [ ] Test passes with base content only (no pack required)

## Related Tickets
- TCK-20260610-SCENARIO-TEMPLATES (prerequisite)
- TCK-20260610-SCENARIO-WORLD-VALIDATION (prerequisite)

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md`

## Related Code Areas
- `tests/integration/scenarios/` — new test directory
- `src/world/scenario/` — resolver under test

## Assumptions / Open Questions
- Are any of the 8 scenario types already defined in `data/content/`? Check before authoring fixtures.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
