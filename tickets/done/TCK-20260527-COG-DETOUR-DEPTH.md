# TCK-20260527-COG-DETOUR-DEPTH

## Title

Rename detour_depth to reserved_detour_depth to Resolve Config Overpromise

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

The strategic configuration parameter `detour_depth` was misleading as it was not actively used by any recursive detour planning mechanisms. Rename it to `reserved_detour_depth` and document/comment it clearly as a reserved configuration parameter for future multi-step planning to align architectural design and prevent user confusion.

## Scope

- Rename field `detour_depth` to `reserved_detour_depth` in `CognitionProfile` within `src/core/strategic.py`.
- Rename `detour_depth` parameter and keys in `V2EntityBuilder.cognition` method within `src/core/builder.py`.
- Rename `detour_depth` local and parameter fields in `CapacityService.derive_profile` within `src/strategy/cognition_capacity.py`.
- Update tests referencing the config key in `tests/unit/strategic/test_cognition_capacity.py`.

## Out of Scope

- Implementing recursive multi-step planning.

## Acceptance Criteria

- All occurrences of `detour_depth` are renamed to `reserved_detour_depth`.
- Cognitive profile and capacity derivation works seamlessly with the renamed parameter.
- All 143 strategic tests pass.

## Related Tickets

- None

## Related Docs

- `entity_cognition_fix_phase0.md` (Task 10)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/strategic.py`
- `src/core/builder.py`
- `src/strategy/cognition_capacity.py`
- `tests/unit/strategic/test_cognition_capacity.py`

## Assumptions / Open Questions

- We mark it as reserved to preserve capacity calculation formulas while removing misleading structural expectations.

## Implementation Notes

- None

## Test Summary

- Strategic unit tests pass: `pytest tests/unit/strategic/test_cognition_capacity.py` successfully completed.

## Files Changed

- `src/core/strategic.py`
- `src/core/builder.py`
- `src/strategy/cognition_capacity.py`
- `tests/unit/strategic/test_cognition_capacity.py`

## Completion Summary

- Renamed `detour_depth` to `reserved_detour_depth` in strategic profile definition, builder, capacity derivation service, and unit tests. Verified correct operation under capacity scaling test bounds. All tests pass successfully.
