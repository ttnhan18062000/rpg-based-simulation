# TCK-20260517-STATIC-DIRTYSET-GUARD

## Title

Static Guard Against Direct DirtySet Usage

## Status

DONE

## Request Summary

Implement Milestone 3 of the Performance Optimization Hardening Plan: a static analysis test suite (`tests/static/test_no_direct_dirtyset_candidate_selection.py`) that strictly prohibits simulation phases, systems, and AI modules from directly accessing `update.dirty_set` properties (e.g. `update.dirty_set.movement_entities`). This guarantees that all candidate selection remains centralized inside `CandidateSelector` and prevents optimization inconsistencies or silent bypasses in future feature additions.

## Scope

- Create static verification test suite in `tests/static/test_no_direct_dirtyset_candidate_selection.py`
- Scan all Python files in:
  - `src/engine/pipeline_phases/`
  - `src/systems/`
  - `src/ai/`
- Enforce that no files in these directories contain direct `.dirty_set` property accesses.
- Guarantee 100% pass rate across the test suite and zero regressions in existing tests.

## Out of Scope

- Modifying existing centralized dirty set logic in `src/core/dirty.py` or `src/engine/pipeline.py`.

## Acceptance Criteria

- `tests/static/test_no_direct_dirtyset_candidate_selection.py` successfully runs and passes.
- Direct accesses to `dirty_set` properties are statically forbidden in gameplay and simulation phase directories.

## Related Tickets

- Milestone 1: CandidateSelector (`TCK-20260517-CANDIDATE-SELECTOR.md`)
- Milestone 2: Full-Scan Compliance (`TCK-20260517-FULL-SCAN-COMPLIANCE.md`)

## Related Docs

- `perf_test_plan.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260517-STATIC-DIRTYSET-GUARD/`

## Related Code Areas

- `tests/static/test_no_direct_dirtyset_candidate_selection.py`

## Assumptions / Open Questions

- Assumes standard AST or regex scanning of Python source files is sufficient for static verification.

## Implementation Notes

- Static verification implemented via recursive file traversal across restricted directories, checking against exact forbidden property string patterns.

## Test Summary

- `pytest tests/static/test_no_direct_dirtyset_candidate_selection.py -v` passed 1/1 test in 0.08s.
- `pytest tests/unit/ -m "not slow" -v` passed 737/737 tests in 13.49s.

## Files Changed

- `tests/static/__init__.py`
- `tests/static/test_no_direct_dirtyset_candidate_selection.py`
- `perf_test_plan.md`

## Completion Summary

- Implemented centralized static architectural guard preventing direct `dirty_set` property access across all simulation phase, gameplay, and AI directories, confirming complete adherence to centralized `CandidateSelector` patterns.
