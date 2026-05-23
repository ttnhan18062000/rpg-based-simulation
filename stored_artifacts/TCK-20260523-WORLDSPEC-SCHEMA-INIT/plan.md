# Plan - WorldSpec Schema Initialization

## Goal
Implement Milestone 67 of Phase 11, defining the core WorldSpec file schema and its parsing/validation logic.

## Scope
- Define Pydantic/dataclass models for WorldSpec.
- Write loading utility to load YAML files safely into the WorldSpec models.
- Set up unit tests to verify the schema validation.

## Steps
1. Brainstorm with the user on WorldSpec schema details.
2. Present a detailed design spec and get approval.
3. Implement `src/worldbuilding/schema.py` containing Pydantic models.
4. Implement `tests/unit/worldbuilding/test_worldspec_schema.py`.
5. Run the new tests and verify all pass.
