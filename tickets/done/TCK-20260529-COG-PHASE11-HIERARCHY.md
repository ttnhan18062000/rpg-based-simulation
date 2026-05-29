# TCK-20260529-COG-PHASE11-HIERARCHY

## Title

Entity Cognition Hierarchy Restructure

## Status

DONE

## Request Summary

Restructure the flat entity self-model and knowledge fields into a clean nested cognition hierarchy model under EntityState.cognition, providing backward compatibility, deterministic hashing, and updated tests.

## Scope

- Define `CognitionModel` as the single unified container.
- Nested sub-models under `SubjectiveModel`, `MemoryModel`, `MotivationModel`, `CommitmentModel`, and `RelationshipModel`.
- Embed `SelfModel` wrapping existing self-awareness, needs, and capabilities under `cognition.subjective.self`.
- Provide deprecation-safe accessors in `EntityState` and `SelfModelBundle` compatibility layer.
- Integrate into canonical hashing and state serialization.
- Establish unit and scenario verification tests.

## Out of Scope

- Implementing functional cognition behaviors for Phase 12-18 (e.g., active perception cones, causal learning steps, moral bias logic).

## Acceptance Criteria

- `EntityState` contains a `cognition` attribute of type `CognitionModel`.
- Access to older flat fields (e.g., `.self_model`) resolves transparently through accessors.
- Serialization and canonical state hashing include cognition fields safely.
- No raw flat cognition properties are added directly to the top-level of `EntityState`.
- Unit test suite is successfully completed and passes.

## Related Tickets

- None

## Related Docs

- `docs/entity/entity_base.md`
- `docs/entity/phase11_investigation.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/state.py`
- `src/core/cognition.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Initial schemas are structured under `src/core/cognition.py`.
- EntityState to_readonly handles cognition nested structures cleanly.

## Test Summary

- Unit tests written under `tests/unit/entity/test_phase11_cognition_model_schema.py` covering EntityState cognition initialization, empty defaults, deterministic canonical serialization, and compatibility accessors.
- Test suite passed successfully in 0.13 seconds.

## Files Changed

- `src/core/cognition.py` (created)
- `src/core/state.py`
- `src/core/cognition_accessors.py` (created)
- `tests/unit/entity/test_phase11_cognition_model_schema.py` (created)
- `docs/entity/entity_base.md`
