# TCK-20260515-PIPELINE-ALIGNMENT

## Title

Reconcile Authoritative Pipeline with Staggered Cadence Regressions

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Resolve 29 test failures introduced by performance hardening (staggered cadence). Ensure that biological decay, strategic intelligence, and shop enforcement remain functionally correct while maintaining performance benefits.

## Scope

- Align `src/engine/apply.py` (passive phase) with 100% semantic parity for biological laws.
- Align `src/engine/pipeline.py` (refine phases) with system-level cadence constraints.
- Fix unit tests that are too sensitive to staggered cadence or update them to be cadence-aware.

## Out of Scope

- Major refactoring of the biological component (e.g. lazy evaluation) unless absolutely necessary.
- Changing the core Kernel loop structure.

## Acceptance Criteria

- 100% pass rate for `tests/unit/strategic/test_biological_needs.py`.
- 100% pass rate for `tests/unit/social/test_town_contract.py`.
- 100% pass rate for `tests/integration/pipeline/`.
- No significant performance regression in 5000-entity stress tests.

## Related Tickets

- None

## Related Docs

- `docs/mechanics/04_strategic_cognition.md`
- `docs/engine/authoritative_pipeline.md`

## Related Stored Artifacts

- `performance_hardening_review.md`

## Related Code Areas

- `src/engine/apply.py`
- `src/engine/pipeline.py`
- `src/engine/cadence.py`

## Assumptions / Open Questions

- We assume that the 100% semantic parity requirement takes precedence over raw performance numbers.
- We assume that "staggered cadence" is acceptable for long-term world simulation but must be bypassable for unit testing.

## Implementation Notes

- We will explore using a "High Precision" flag or per-tick overrides for testing.
- We will consolidate dirty tracking to ensure that cadence-skipped entities don't leave stale state.

## Test Summary

- `pytest tests/unit/strategic/test_biological_needs.py tests/unit/social/test_town_contract.py tests/integration/pipeline/` passed with 100% success rate (96/96 tests passed).
- Verified flawless execution across the full unit (730/730) and integration (186/186) test suites under staggered cadence optimizations.

## Files Changed

- `src/engine/apply.py`
- `src/engine/pipeline.py`
- `src/engine/cadence.py`

## Completion Summary

Successfully reconciled the authoritative 17-phase pipeline with staggered cadence performance hardening. Biological decay, town contract enforcement, and strategic intelligence correctly maintain 100% semantic parity and deterministic behavior while preserving memory pooling and latency benefits.
