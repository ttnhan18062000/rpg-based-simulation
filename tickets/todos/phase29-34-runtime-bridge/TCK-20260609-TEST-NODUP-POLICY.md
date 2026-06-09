# TCK-20260609-TEST-NODUP-POLICY

## Title
Document no-duplication test policy preventing test explosion

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
As phases 29–34 add resolvers, factories, schema models, and integration pipelines, there is risk of test explosion: multiple "basic catalog loads" or "basic world assembly works" tests across different files. This task codifies the no-duplication rules as a doc: 3–6 focused unit tests per new resolver, extend existing schema tests for new authoring forms, one data-driven matrix integration test per new pipeline, no one-test-per-record pattern.

## Scope
- Create `docs/testing/no_duplication_test_policy.md` with rules from Task 33.3: units per resolver type, how to handle new authoring forms, new registry adapters, full pipeline tests, new content records, legacy behavior preservation
- Cross-reference with docs/testing/content_migration_test_ownership.md

## Out of Scope
- Enforcing the policy programmatically
- Modifying existing tests

## Acceptance Criteria
- [ ] docs/testing/no_duplication_test_policy.md exists
- [ ] Rules cover: new resolver, new authoring form, new registry adapter, new full pipeline, new content record, legacy behavior
- [ ] Data-driven coverage is documented as the preferred pattern for content record testing
- [ ] No duplicate "basic catalog loads" or "basic assembly works" rule is explicit

## Related Tickets
- TCK-20260609-TEST-OWNERSHIP-MAP (related)
- TCK-20260609-TEST-DELTA-BUDGET (related — budget complements this policy)

## Related Docs
- docs/testing/v2_test_taxonomy.md
- docs/testing/content_migration_test_ownership.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/testing/no_duplication_test_policy.md (new)

## Assumptions / Open Questions
None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
