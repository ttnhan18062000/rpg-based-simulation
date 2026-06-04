# TCK-20260604-PHASE20-CONTRACT-AND-TESTMAP

## Title
Phase 20 — Content usage contract and test map

## Status
DONE

## Request Summary
Investigate and implement Phase 20 requirements, defining exactly how every `data/content/` component is used via a concrete implementation contract (`ContentUsageMatrix`) and implementation states.

## Scope
- Create `ContentUsageMatrix` as a python specification and generated markdown document covering all content families.
- Standardize and validate implementation states (`LOADED_ONLY`, `VALIDATED_ONLY`, `RESOLVED_PARTIALLY`, `PROJECTED_TO_LEGACY`, `RUNTIME_AUTHORITATIVE`, `DESIGN_ONLY`).
- Add tests in `tests/unit/content/test_content_usage_matrix.py` to enforce completeness and constraints.

## Out of Scope
- Implementing Phase 21+ resolvers or schemas (only defining their target state/contract in the matrix).

## Acceptance Criteria
- Matrix includes every current `data/content/` family, `world_modules`, `world_compositions`, and `simulation_scenarios`.
- Each family has a declared schema, validator responsibility, resolver or design-only mark, and runtime/compile consumer.
- Every content family has exactly one implementation state.
- Compatibility data is clearly marked as adapter-only / `PROJECTED_TO_LEGACY`.
- Missing state classification or unregistered family fails the test.
- All tests pass cleanly.

## Related Tickets
- None

## Related Docs
- `world_phase_20_28.md`
- `docs/mechanics/06_worldbuilding_foundation.md`
- `docs/mechanics/content_usage_matrix.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/content/repository.py`
- `src/content/schema.py`
- `src/content/matrix.py`
- `tests/unit/content/test_content_usage_matrix.py`

## Assumptions / Open Questions
- Where should the generated markdown report be written (e.g., `docs/mechanics/content_usage_matrix.md`)?
  - Resolved: `docs/mechanics/content_usage_matrix.md`.
- Should the `ContentUsageMatrix` python definition be in `src/content/matrix.py`?
  - Resolved: Yes.

## Implementation Notes
- Created `src/content/matrix.py` defining all content families and matrix structure.
- Created `tests/unit/content/test_content_usage_matrix.py` to assert contract constraints and generate matrix report.

## Test Summary
- Verified `test_content_usage_matrix.py` test suite passes.
- Verified all regression tests in `tests/unit/content/test_catalog.py`, `tests/unit/content/test_runtime_catalog.py`, `tests/unit/content/test_layered_catalog.py`, and `tests/unit/worldassembly/test_assembly.py` pass.

## Files Changed
- `src/content/matrix.py`
- `tests/unit/content/test_content_usage_matrix.py`
- `docs/mechanics/content_usage_matrix.md`

## Completion Summary
- Defined component family contracts for all 35+ families and validated implementation states via strict test map verification. Matrix report generated successfully.
