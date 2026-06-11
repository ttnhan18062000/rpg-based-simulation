---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260523-MUTATION-ENGINE
phase: done
date: 2026-05-23
tags: [mutation, engine]
---

# TCK-20260523-MUTATION-ENGINE

## Title

Milestone 85 — Mutation Engine

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the `MutationEngine` component that safely consumes `WorldSpec`, `ScenarioSpec`, and a `MutationSpec` to generate mutated variants of the world and scenario specifications without in-place side effects. It must generate an execution report (`MutationApplyReport`) detailing old/new values, warnings, and errors, and enforce strict semantic validation on the mutated outputs.

## Scope

- Implement `MutationEngine` in `src/lab/mutation.py`.
- Support 6 polymorphic operations: `set`, `add`, `multiply`, `toggle`, `remove`, `duplicate`.
- Implement non-in-place mutation copies using dict dumps/reconstruction and copy logic.
- Support deep dot-notation path resolution with list-ID matching (e.g. `resources.wood_zone.count` or `resources.nodes.wood_zone.count`).
- Integrate `WorldValidator` and `ScenarioValidator` to ensure all generated variants are structurally and semantically valid.
- Support strict and non-strict error reporting in `MutationApplyReport`.

## Out of Scope

- Variant Matrix Builder (`one_at_a_time`, `combined`, `factorial_limited` sweeps) (Milestone 86).
- Metamorphic expectation checks evaluation (Milestone 87).
- Balance Comparison Engine runs (Milestone 88).

## Acceptance Criteria

- All 6 polymorphic mutation operations function correctly.
- Base World and Scenario specs are never modified in place (strict clone isolation).
- Target path errors (unrecognized path or wrong operands) fail cleanly and gracefully without exposing raw stack tracebacks in non-strict mode, or raise typed exceptions.
- Mutation reports include target paths, operations, old values, new values, status, warnings, and errors.
- Generated mutated specs are validated by both Pydantic schema validation and the full pluggable `WorldValidator` and `ScenarioValidator` rules. Invalid states raise errors and are blocked.
- Clean unit test suite with 100% success coverage for all operations and validation barriers.

## Related Tickets

- TCK-20260523-MUTATION-SCHEMA (Done)

## Related Docs

- `lab_phase13.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/schema.py`
- `src/lab/validator.py`
- `src/worldbuilding/schema.py`
- `src/worldbuilding/validator.py`

## Assumptions / Open Questions

- Path resolution needs to handle nested list search by `id` key/attribute as well as skipping optional dummy segment wrappers (like `nodes` in `resources.nodes.wood_zone.count`).

## Implementation Notes

- We performed mutation operations on a mutable deep-copied dictionary of the specs, mutated it in-place using our safe path traversal functions, and subsequently instantiated and validated using `model_validate()` and both validators in strict mode.

## Test Summary

- Added 12 new, high-quality, comprehensive tests in `tests/unit/lab/test_mutation_engine.py` covering:
  - All 6 operations (`set`, `add`, `multiply`, `toggle`, `remove`, `duplicate`).
  - Base isolation (immutability).
  - Target error resolution (non-existent fields) under strict and non-strict modes.
  - Pydantic schema validation failures.
  - Semantic/topological validation failures via WorldValidator.
  - Option to skip intermediate dummy placeholder segments (`nodes`).
- All 82 lab tests ran and completed with 100% success.

## Files Changed

- `src/lab/mutation.py`
- `src/lab/__init__.py`
- `tests/unit/lab/test_mutation_engine.py`
- `tickets/working_log.csv`

## Completion Summary

- Implemented the safe MutationEngine with strict clone isolation, dot-notation resolution supporting lists ID lookup and layout placeholder skipping, complete polymorphic executors, and rigorous Pydantic/Validator validation barriers. Fully certified with 100% test pass.
