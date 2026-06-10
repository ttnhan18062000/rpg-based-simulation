# TCK-20260610-FALLBACK-RETIREMENT-CRITERIA

## Title
Document and gate explicit fallback retirement criteria with CI mappings

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Phase 44.1. Define 9 retirement gate conditions, map each to a test or CI job, and create a retirement gate check.

## Scope
- `docs/guidelines/fallback_retirement_criteria.md` with all 9 criteria
- `tests/architecture/test_fallback_retirement_gate.py` CI-runnable gate

## Out of Scope
- Deleting fallback code (TCK-20260610-FALLBACK-RECORDS-REMOVAL)
- Restricting fallback modes (TCK-20260610-FALLBACK-RESTRICT-MODES)

## Acceptance Criteria
- [x] Retirement criteria documented in `docs/guidelines/fallback_retirement_criteria.md`
- [x] Each criterion maps to a named test or CI job
- [x] Criteria distinguish compatibility projection from hardcoded fallback
- [x] Architecture test verifies each mapped test exists
- [x] Missing criterion blocks further retirement steps
- [x] Current status field per criterion (all MET)

## Related Tickets
- TCK-20260610-FALLBACK-RESTRICT-MODES (downstream)
- TCK-20260610-FALLBACK-RECORDS-REMOVAL (downstream)

## Related Docs
- `docs/guidelines/fallback_retirement_criteria.md` (new)

## Related Code Areas
- `tests/architecture/test_fallback_retirement_gate.py` (new)

## Assumptions / Open Questions
N/A — all 9 criteria are MET with Phase 43 complete (swamp_border_pack done).

## Implementation Notes
All 9 criteria currently MET. Architecture test is parametrized: 9 file-existence checks, 9 status checks, 1 top-level gate, 1 not-checked guard, 2 doc checks = 22 tests. Gate will fail immediately if a mapped test file is deleted or renamed, or if a criterion status changes to UNMET.

## Test Summary
22 tests in `tests/architecture/test_fallback_retirement_gate.py`. All pass.

## Files Changed
- `docs/guidelines/fallback_retirement_criteria.md` (new)
- `tests/architecture/test_fallback_retirement_gate.py` (new)

## Completion Summary
All 9 retirement gate conditions documented and mapped to existing tests. Gate architecture test passes. Retirement may proceed to TCK-20260610-FALLBACK-RESTRICT-MODES.
