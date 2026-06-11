---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260523-WORLD-VALIDATOR
phase: done
date: 2026-05-23
tags: [world, validator]
---

# TCK-20260523-WORLD-VALIDATOR

## Title

Implementation of World Validation Layer (Milestone 69)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement `WorldValidator` and a pluggable validation rules framework for high-level world specs validation with severity levels (ERROR, WARNING, INFO).

## Scope

- Implement `WorldValidator` and `WorldValidationRule` pluggable system.
- Implement rules checking reference integrity (factions, regions), topology containment, entity density, and empty collections.
- Support deterministic diagnostic output categorized by severity level.
- Support a strict compilation checker mode where warnings can optionally raise failures.
- Implement tests verifying rule correctness, determinism, stability of rule IDs, and non-fixing behavior.

## Out of Scope

- World Compiler to AuthoritativeState (Milestone 70).

## Acceptance Criteria

- Unknown faction reference raises an ERROR issue.
- Region bounds outside topology bounds raises an ERROR issue.
- Duplicate IDs raise ERROR issues.
- Zero resources present in a world generates a WARNING issue.
- Unusually high entity spawn density generates a WARNING issue.
- Pluggable rules are structured using a common `WorldValidationRule` abstract base/class.
- Validation result is deterministic and rule IDs are stable.
- Unknown future sections are flagged according to policy.
- Warnings do not block compilation unless `strict` validation is enabled.

## Related Tickets

- `TCK-20260523-WORLD-REPO-INIT`

## Related Docs

- `world_phase11.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldbuilding/validator.py`
- `tests/unit/worldbuilding/test_world_validator.py`
- `tests/unit/worldbuilding/test_world_validation_rules.py`

## Assumptions / Open Questions

- High entity density threshold will be defined as total population spawns exceeding 50% of the topology tile area.

## Implementation Notes

- Added unexpected top-level section detection by comparing raw input YAML to schema definitions.
- Configured a deterministic sorted diagnostic reporter that aggregates validation issues cleanly.

## Test Summary

- Implemented 7 unit tests under `tests/unit/worldbuilding/test_world_validation_rules.py` validating reference checking, containment, and warning sanity rules.
- Implemented 6 unit tests under `tests/unit/worldbuilding/test_world_validator.py` verifying orchestrator behavior, determinism, strict warnings elevation, unknown sections, and non-fixing traits. All tests passed.

## Files Changed

- `src/worldbuilding/validator.py`
- `src/worldbuilding/__init__.py`
- `tests/unit/worldbuilding/test_world_validation_rules.py`
- `tests/unit/worldbuilding/test_world_validator.py`

## Completion Summary

- Milestone 69 is fully completed. Built a pluggable and extensible validation rules engine that verifies world integrity under `ERROR`, `WARNING`, and `INFO` classifications with 100% test pass rate.
