# TCK-20260610-FALLBACK-RETIREMENT-CRITERIA

## Title
Document and gate explicit fallback retirement criteria with CI mappings

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Phase 44.1. Legacy fallback retirement requires explicit, documented criteria — not implicit drift. This ticket defines the 9 retirement gate conditions, maps each to a specific test or CI job, and creates a retirement gate check that can block further retirement steps if any criterion is unmet. This is a gate definition ticket, not an implementation change.

## Scope
- Document retirement criteria in `docs/guidelines/fallback_retirement_criteria.md`:
  1. Catalog-backed mode is default
  2. Strict mode passes
  3. Core scenario matrix passes
  4. First content pack passes (`frontier_extended_pack`)
  5. Second content pack passes (`swamp_border_pack`)
  6. Legacy mapping is complete
  7. Arena smoke has clean catalog equivalent
  8. Relation projection used in high-impact systems
  9. Hardcoded gameplay guard passes
- For each criterion: description, mapped test or CI job, current status (MET / UNMET / NOT_CHECKED), notes
- Add architecture test `tests/architecture/test_fallback_retirement_gate.py` that reads the criteria doc and asserts each mapped test exists (CI-runnable gate)
- Distinguish: compatibility projection (allowed to remain) vs hardcoded fallback (target for retirement)

## Out of Scope
- Deleting any fallback code (that is TCK-20260610-FALLBACK-RECORDS-REMOVAL)
- Restricting fallback modes (that is TCK-20260610-FALLBACK-RESTRICT-MODES)

## Acceptance Criteria
- [ ] Retirement criteria documented in `docs/guidelines/fallback_retirement_criteria.md`
- [ ] Each criterion maps to a named test or CI job
- [ ] Criteria distinguish compatibility projection from hardcoded fallback
- [ ] Architecture test verifies each mapped test exists
- [ ] Missing criterion blocks further retirement steps
- [ ] Current status field per criterion (reflects state at time of writing)

## Related Tickets
- TCK-20260610-FALLBACK-RESTRICT-MODES (downstream — uses criteria)
- TCK-20260610-FALLBACK-RECORDS-REMOVAL (downstream — follows criteria)

## Related Docs
- `docs/guidelines/v2_intentional_divergences.md`
- `docs/guidelines/` — new file created here

## Related Code Areas
- `tests/architecture/test_fallback_retirement_gate.py` — new
- `src/content/repository.py` — catalog mode selection

## Assumptions / Open Questions
- Are all 9 gate conditions already achievable with current system? Some (e.g., second content pack) will be UNMET until Phase 43 is done — that is acceptable.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
