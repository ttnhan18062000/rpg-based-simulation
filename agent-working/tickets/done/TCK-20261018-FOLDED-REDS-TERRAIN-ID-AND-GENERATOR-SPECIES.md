---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261018-FOLDED-REDS-TERRAIN-ID-AND-GENERATOR-SPECIES
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-FOLDED-REDS-TERRAIN-ID-AND-GENERATOR-SPECIES

## Title
Fix two reds on rpg-next b23e78128: a test staging a terrain id the catalog lacks, and the procedural generator emitting populations with no species

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
rpg-planner: two folds (2.129 content-declared terrain lookup, 2.127 declared diet) left three tests red on rpg-next.

## Scope
- `tests/integration/pipeline/test_combat_legality_matrix.py::test_combat_trace_consistency` staged `"HILL"`, `"PLAIN"` and `"FOREST"`. The test's intent is high ground, so `HILL` becomes `mountain` (the only content terrain declaring `high_ground`). The lookup is case-sensitive, so `PLAIN` and `FOREST` become `plain` and `forest` (forest declares cover). No content added, lookup untouched.
- `src/worldgeneration/generator.py`: the `citizens` and `monsters` populations now carry an `archetype_id` (the `PopulationSpec` field exists for this), chosen by new `_archetype_for(faction, role)`: same faction, same role when one exists, else the first of that faction by id. For the shipped catalog: citizens -> `frontier_guard` (species `human`); monsters -> `goblin_raider` (species `goblin`). Species follows the faction the generator already picks, so species, faction and role agree.

## Out of Scope
Content changes; the diet rule; the terrain lookup; gate worlds (none is generated).

## Acceptance Criteria
- The 3 tests green, plus tests/unit/worldgeneration, tests/integration/pipeline, tests/unit/combat (299 passed, `--resource-budget off`).

## Related Tickets
2.127 (declared diet), 2.129 (content-declared cover and high ground).

## Related Docs
docs/guidelines/intentional_divergences.md 2.127, 2.129.

## Related Stored Artifacts
None.

## Related Code Areas
src/worldgeneration/generator.py, src/worldbuilding/diet_declaration.py, src/content/terrain_cost.py.

## Assumptions / Open Questions
Behaviour change in procedurally generated worlds only: their populations now spawn through the archetype path with a declared species. No gate world is generated, so gate output is unchanged. If the catalog holds no archetype of the chosen faction the field is None and the world validator names the population, as before.

## Implementation Notes
See Scope.

## Test Summary
tests/integration/pipeline + tests/unit/worldgeneration + tests/unit/combat: 299 passed.

## Files Changed
src/worldgeneration/generator.py, tests/integration/pipeline/test_combat_legality_matrix.py, this ticket.

## Completion Summary
Both reds fixed at the source named by the planner.
