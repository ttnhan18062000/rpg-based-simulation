# TCK-20260609-TEST-OWNERSHIP-MAP

## Title
Create test ownership map documenting which suites own which behavior

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
The test base has grown to cover API, arena, architecture, runtime, catalog, worldassembly, movement, and certification behaviors. Without a documented ownership map, new tests get added to the wrong suite, behaviors get duplicated, and reviewers cannot quickly tell where a new test belongs. This task creates docs/testing/content_migration_test_ownership.md listing each existing test file, what behavior it owns, and which new Phase 29–34 tests belong to which suite.

## Scope
- Create `docs/testing/content_migration_test_ownership.md`
- Document ownership for: tests/unit/content/, tests/unit/worldassembly/, tests/unit/content_semantics/, tests/arena/, tests/certification/, tests/architecture/, and new test suites from phases 29–34
- For each new planned test file (entities/, scenarios/, strict matrix, consumer gate), name the owner suite
- Identify any existing duplicate test coverage areas

## Out of Scope
- Modifying any existing tests
- Enforcing ownership programmatically (that is TCK-20260609-MIGRATION-TEST-MARKERS)

## Acceptance Criteria
- [ ] docs/testing/content_migration_test_ownership.md exists
- [ ] Each existing major test suite has an ownership entry
- [ ] Each new planned test file from phases 29–34 is pointed to an owner suite
- [ ] Existing regression suites (arena, certification) are explicitly preserved
- [ ] Duplicate test coverage areas are identified

## Related Tickets
- TCK-20260609-MIGRATION-TEST-MARKERS (successor — applies markers based on this map)

## Related Docs
- docs/testing/v2_test_taxonomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/testing/content_migration_test_ownership.md (new)
- docs/testing/v2_test_taxonomy.md

## Assumptions / Open Questions
None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
