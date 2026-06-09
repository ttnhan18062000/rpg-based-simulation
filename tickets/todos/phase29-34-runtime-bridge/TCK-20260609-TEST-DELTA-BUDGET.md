# TCK-20260609-TEST-DELTA-BUDGET

## Title
Document test delta budget per task type to control test volume

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Without a hard budget for how many tests each phase or task type should add, the test suite grows unbounded. This task codifies a test delta budget: 3–6 tests per small resolver/task, 1–2 integration tests per medium integration feature, 1 data-driven matrix test per strict matrix scenario, 1 manifest + 1 validation + 1 strict matrix test per content pack, and 1 architecture test per guard. Any task exceeding the budget must justify it.

## Scope
- Create `docs/testing/test_delta_budget.md` with budget rules from Task 33.4
- Document the justification requirements for exceeding the budget: why existing tests cannot be extended, what unique behavior is being protected, whether the test can be data-driven instead
- Cross-reference with docs/testing/no_duplication_test_policy.md

## Out of Scope
- Enforcing programmatically
- Modifying existing tests

## Acceptance Criteria
- [ ] docs/testing/test_delta_budget.md exists
- [ ] Budget covers: small resolver, medium integration feature, strict matrix, content pack, architecture guard
- [ ] Justification process for budget overruns is documented
- [ ] Document references no_duplication_test_policy.md for related rules

## Related Tickets
- TCK-20260609-TEST-NODUP-POLICY (related)

## Related Docs
- docs/testing/no_duplication_test_policy.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/testing/test_delta_budget.md (new)

## Assumptions / Open Questions
None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
