# TCK-20260523-METAMORPHIC-VALIDATION

## Title

Milestone 87 — Metamorphic Validation Rules

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Define and implement a metamorphic rule validation system for the RPG simulation balance lab. Traditional testing asserts exact values; metamorphic testing asserts that when configuration inputs change in known ways, performance/balance outputs change in expected relative directions.

## Scope

- Define core domain classes/models for metamorphic validation:
  - `MetamorphicRule`
  - `MetamorphicRuleEngine`
  - `MetamorphicComparisonResult`
- Support six essential rule comparison types:
  - `monotonic_non_decreasing`: metric should stay same or increase
  - `monotonic_non_increasing`: metric should stay same or decrease
  - `within_tolerance`: metric should remain near baseline (within a provided tolerance band)
  - `expected_worse`: mutation intentionally worsens condition (e.g. increase stuck_entity_ratio or reduce resource_production_rate)
  - `expected_better`: mutation intentionally improves condition (e.g. reduce stuck_entity_ratio or increase resource_production_rate)
  - `no_new_hard_law_violation`: mutation must not introduce any new hard law violations
- Support robust fallback for missing telemetry, yielding `INSUFFICIENT_DATA` rather than false positives or crashes.
- Design comprehensive unit and integration test coverage.

## Out of Scope

- Balance Comparison Engine sweep orchestration (Milestone 88).

## Acceptance Criteria

- `monotonic_non_decreasing` passes when metric increases or stays same, and fails when metric decreases.
- `monotonic_non_increasing` passes when metric decreases or stays same, and fails when metric increases.
- `within_tolerance` handles small differences correctly according to the specified tolerance.
- `expected_worse` correctly maps and passes when target metrics worsen (e.g., stuck entities ratio increases, resource rate decreases).
- `no_new_hard_law_violation` evaluates correctly and fails when compared variant introduces new hard law violations.
- Missing metrics yield `INSUFFICIENT_DATA` cleanly.
- Baseline or compared variants with insufficient evidence (e.g. too few seed runs) are flagged as `WEAK_EVIDENCE`.

## Related Tickets

- TCK-20260523-MUTATION-MATRIX (Done)

## Related Docs

- `lab_phase13.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260523-METAMORPHIC-VALIDATION/`

## Related Code Areas

- `src/lab/metamorphic.py`
- `src/lab/schema.py`
- `tests/unit/lab/test_metamorphic_rules.py`
- `tests/integration/lab/test_metamorphic_validation_flow.py`

## Assumptions / Open Questions

- None. Evaluated successfully under all metric states and telemetry configurations.

## Implementation Notes

- Added `src/lab/metamorphic.py` defining `MetamorphicComparisonResult`, `MetamorphicRule`, and `MetamorphicRuleEngine`.
- Evaluates six rule types securely.
- Missing metrics and non-numeric metrics yield `INSUFFICIENT_DATA` cleanly.
- Baseline or compared variant run counts < 3 flag `weak_evidence=True`.
- No circular imports by importing `ExpectedRelationshipSpec` only where needed.

## Test Summary

- Evaluated 11 unit test scenarios covering all metamorphic types, missing telemetry fallbacks, and weak evidence flags.
- Evaluated integration test representing a real-world multi-variant sweep validation scorecard.
- **100% Pass Rate** across 99 unit/integration tests in the `lab` package.

## Files Changed

- `src/lab/__init__.py`
- `src/lab/schema.py`
- `src/lab/metamorphic.py` (New)
- `tests/unit/lab/test_metamorphic_rules.py` (New)
- `tests/integration/lab/test_metamorphic_validation_flow.py` (New)

## Completion Summary

- Milestone 87 is fully implemented, verified, and integrated with the lab framework.
