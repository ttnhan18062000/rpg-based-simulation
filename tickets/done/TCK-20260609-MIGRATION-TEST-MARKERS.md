---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260609-MIGRATION-TEST-MARKERS
phase: done
date: 2026-06-09
tags: [migration, test, markers]
---

# TCK-20260609-MIGRATION-TEST-MARKERS

## Title
Add migration pytest markers enabling targeted CI test lane execution

## Status
DONE

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
Added 8 new markers to pyproject.toml. Applied per-file pytestmark to new phase 29-34 test files. For arena/certification (many existing files), used conftest.py with pytest_collection_modifyitems hook. strict_world_matrix updated to list [worldassembly, strict_matrix].

## Test Summary
All 7 marker selections verified via --collect-only. 51 affected tests pass.

## Files Changed
- pyproject.toml (8 new markers)
- tests/unit/content/test_migration_map_schema.py (catalog)
- tests/integration/content/test_active_data_consumer.py (content_graph)
- tests/integration/content/test_strict_world_matrix.py (+ strict_matrix)
- tests/unit/scenarios/test_scenario_schema.py (scenario_setup)
- tests/unit/scenarios/test_scenario_modifier_apply.py (scenario_setup)
- tests/integration/scenarios/test_scenario_setup_resolver.py (scenario_setup)
- tests/unit/runtime/test_registry_bootstrap_modes.py (registry_projection)
- tests/architecture/test_no_new_hardcoded_gameplay_truth.py (architecture)
- tests/arena/conftest.py (new — legacy_compat hook)
- tests/certification/conftest.py (new — legacy_compat hook)

## Completion Summary
All acceptance criteria met. All new markers declared in pyproject.toml. Marker selections verified. Slow tests not in fast unit groups.
