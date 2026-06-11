---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260523-MUTATION-SCHEMA
phase: done
date: 2026-05-23
tags: [mutation, schema]
---

# TCK-20260523-MUTATION-SCHEMA

## Title

Implement Phase 13 MutationSpec Schema and Validation Framework

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the schema, parser, safe loader, and pluggable verification rules for MutationSpec to support controlled world and scenario mutations.

## Scope

- Define Pydantic models for polymorphic mutation operations, MatrixSpec, ExpectedRelationshipSpec, and MutationSpec.
- Implement YAML loaders and safe custom exceptions to prevent traceback leaks.
- Implement pluggable `MutationValidationRule` instances and the `MutationValidator` engine to verify references and metamorphic relationship sanity.
- Write unit tests for schema parsing, edge-case rejection, and validator checks.

## Out of Scope

- Implementing the Mutation Engine itself (Milestone 85).
- Metamorphic runner execution and balance reporting (Milestone 86/87).

## Acceptance Criteria

- All MutationSpec fields (`schema_version`, `mutation_id`, `name`, `base_world_id`, `base_scenario_id`, `mutations`, `matrix`, `expected_relationships`, `budgets`) are validated with Pydantic.
- All operations (`set`, `add`, `multiply`, `toggle`, `remove`, `duplicate`) are parsed using strongly typed polymorphic models.
- Safe YAML loading is implemented under `load_mutation_spec_from_yaml`.
- Pluggable validator rules verify base world/scenario existence, metamorphic reference sanity, and unrecognized metrics (warnings).
- Comprehensive unit tests cover valid parse, invalid parse, incorrect mode, unknown operation, reference checking, metamorphic variant checking, unrecognized metrics warnings, strict mode warnings-to-errors elevation, and preserving unknown future fields.

## Related Tickets

- None

## Related Docs

- `docs/superpowers/specs/2026-05-23-mutationspec-schema-design.md`
- `lab_phase13.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260523-MUTATION-SCHEMA/plan.md`
- `stored_artifacts/TCK-20260523-MUTATION-SCHEMA/investigation.md`
- `stored_artifacts/TCK-20260523-MUTATION-SCHEMA/test_plan.md`

## Related Code Areas

- `src/lab/schema.py`
- `src/lab/validator.py`
- `tests/unit/lab/test_mutationspec_schema.py`
- `tests/unit/lab/test_mutationspec_validator.py`

## Assumptions / Open Questions

- None (all clarified and approved during brainstorming).

## Implementation Notes

- Leveraged Pydantic v2 discriminated unions (`operation` literal field) to achieve parse-time type safety for polymorphic operation types.
- Integrated validations cleanly into `src/lab/validator.py` without coupling schema classes to repository/disk lookups, respecting the boundary between structure and reference mapping.

## Test Summary

- Scoped schema unit tests: `tests/unit/lab/test_mutationspec_schema.py` (6 tests)
- Scoped validator unit tests: `tests/unit/lab/test_mutationspec_validator.py` (7 tests)
- Original lab unit test suite ran for regressions: 70 tests passed cleanly in 1.56s.

## Files Changed

- `src/lab/schema.py`
- `src/lab/validator.py`
- `tests/unit/lab/test_mutationspec_schema.py`
- `tests/unit/lab/test_mutationspec_validator.py`

## Completion Summary

- Milestone 84 is fully completed. All Pydantic model definitions, error handling exceptions, YAML safe loading functions, pluggable validation rule classes, and test suites are fully implemented, verified, and integrated into the repository.
