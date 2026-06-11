---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260523-WORLD-TEMPLATES
phase: done
date: 2026-05-23
tags: [world, templates]
---

# TCK-20260523-WORLD-TEMPLATES

## Title

Milestone 71 — World Template and Recipe System

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement a pluggable World Template and Recipe System that allows worlds to be created dynamically using population, resource, building, and region recipes instead of tedious manual lists. The system must support deterministic recipe expansion to standard `WorldSpec` specifications, strictly validate topological containment, ensure stable ID generation, and guarantee that expanded specs pass all existing validation checks without bypassing them.

## Scope

- Create a `WorldTemplateSpec` Pydantic model representing the template and recipes schema.
- Implement population, resource, building, and region recipe structures inside `src/worldbuilding/recipe.py` (or schema module).
- Implement a deterministic recipe expander `WorldTemplateExpander` to expand `WorldTemplateSpec` into `WorldSpec`.
- Enforce strict topological containment during expansion (no recipes placing elements outside maps).
- Ensure stable, traceable generated identifiers (e.g. `<type>_<region>_<index>`).
- Implement comprehensive unit tests in `tests/unit/worldbuilding/test_world_recipes.py`.
- Guarantee that expanded specs do not bypass validation.

## Out of Scope

- Procedural terrain generation (heightmaps, simplex noise).
- Complex road networks or river networks.
- Visual editor interface or JSON-canvas layout.

## Acceptance Criteria

- `WorldTemplateSpec` successfully loads from template YAML files.
- Population recipes expand to the expected number of population groups / counts.
- Resource recipes expand to the expected number of resource node specifications.
- Building recipes expand to the expected number of building specifications.
- Expansion is completely deterministic (same spec + seed = same expanded `WorldSpec`).
- The expansion raises clear containment errors if any recipe places structures/entities outside the topology bounds.
- All expanded `WorldSpec` outputs are successfully run through `WorldValidator` and pass without bypassing rules.
- 100% of tests in `tests/unit/worldbuilding/test_world_recipes.py` pass.

## Related Tickets

- `TCK-20260523-WORLD-COMPILER`

## Related Docs

- `world_phase11.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldbuilding/recipe.py`
- `src/worldbuilding/schema.py`
- `src/worldbuilding/__init__.py`
- `tests/unit/worldbuilding/test_world_recipes.py`

## Assumptions / Open Questions

- We assume recipe expansion is a pre-compile step: a template is expanded to a `WorldSpec`, which is then compiled to an `AuthoritativeState`.

## Implementation Notes

- None.

## Test Summary

- **Unit Tests (`tests/unit/worldbuilding/test_world_recipes.py`)**: Verified that population, resource, and building recipes expand to the expected specs and counts, confirmed deterministic expansion, verified that containment checks fail when out of bounds, confirmed stable suffixes for traceable ID generation, and certified that Pydantic and `WorldValidator` rules are not bypassed during expansion.
- **Results**: 100% of the 7 new unit tests passed cleanly, and all 50 tests in the package pass successfully.

## Files Changed

- `src/worldbuilding/recipe.py`
- `src/worldbuilding/schema.py`
- `src/worldbuilding/__init__.py`
- `tests/unit/worldbuilding/test_world_recipes.py`

## Completion Summary

- Designed and implemented full procedural `WorldTemplateSpec` representing regions, factions, populations, resource, and building recipes.
- Created `WorldTemplateExpander` to deterministically expand template specs into full `WorldSpec` models.
- Upgraded `RegionSpec` in `src/worldbuilding/schema.py` to support `terrain` and `hazard_level` fields directly.
- Guaranteed complete safety by integrating containment boundary checks and running `WorldValidator` on all expanded specs.
