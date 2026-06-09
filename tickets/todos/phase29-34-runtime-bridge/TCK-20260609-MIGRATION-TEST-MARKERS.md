# TCK-20260609-MIGRATION-TEST-MARKERS

## Title
Add migration pytest markers enabling targeted CI test lane execution

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
CI currently cannot run targeted migration-related test jobs because no pytest markers distinguish catalog, worldassembly, registry_projection, entity_construction, scenario_setup, strict_matrix, architecture, and legacy_compat tests. This task declares the markers in pyproject.toml and applies them to the most relevant existing and new test files so CI lanes can run only the relevant suite without running the full test suite.

## Scope
- Declare new markers in pyproject.toml: catalog, content_graph, worldassembly, registry_projection, entity_construction, scenario_setup, perspective, legacy_compat, content_pack, strict_matrix, architecture
- Apply markers to existing relevant test files that are not yet marked
- Apply markers to new test files from phases 29–34 once they exist
- Verify `pytest -m worldassembly` and `pytest -m strict_matrix` select the correct tests without false positives

## Out of Scope
- Creating CI pipeline configuration files (see TCK-20260609-MIGRATION-CI-LANES)
- Adding markers to tests not related to this migration

## Acceptance Criteria
- [ ] All new markers are declared in pyproject.toml with descriptions
- [ ] Existing relevant tests are tagged where useful (not exhaustive — focus on meaningful separation)
- [ ] pytest -m catalog selects catalog tests only
- [ ] pytest -m worldassembly selects worldassembly tests only
- [ ] pytest -m strict_matrix selects strict matrix tests only
- [ ] pytest -m legacy_compat selects arena/certification tests
- [ ] Slow tests are not accidentally added to fast unit marker groups

## Related Tickets
- TCK-20260609-TEST-OWNERSHIP-MAP (dependency — defines which tests belong to which suite)
- TCK-20260609-MIGRATION-CI-LANES (successor — uses these markers to define CI lanes)

## Related Docs
- docs/testing/v2_test_taxonomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- pyproject.toml
- tests/unit/content/
- tests/integration/content/
- tests/arena/
- tests/architecture/

## Assumptions / Open Questions
- pytest is configured via pyproject.toml (confirmed by existing project structure)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
