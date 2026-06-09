# TCK-20260609-MIGRATION-CI-LANES

## Title
Define migration CI lanes for targeted test execution by content domain

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
As migration test markers are applied, CI needs corresponding lane definitions that run targeted subsets of the test suite. This task creates CI lane configuration (or a Makefile/script) defining six lanes: catalog-fast, worldassembly-fast, runtime-projection, strict-matrix, legacy-regression, and architecture. Each lane maps to specific pytest markers and keeps slow tests out of fast feedback loops.

## Scope
- Define six CI test lanes as pytest commands or Makefile targets:
  - catalog-fast: content schema, catalog loader, reference graph, no-dead-active-data tests
  - worldassembly-fast: normalizers, module/composition assembly, provenance
  - runtime-projection: registry adapters, entity construction, runtime content mode
  - strict-matrix: representative end-to-end content builds
  - legacy-regression: arena, certification, legacy compat tests
  - architecture: import boundaries, enum usage boundaries, hardcoded gameplay guard
- Lane definitions use pytest -m markers from TCK-20260609-MIGRATION-TEST-MARKERS
- Document in docs/testing/migration_ci_lanes.md

## Out of Scope
- Setting up actual CI pipeline YAML files (GitHub Actions, etc.) — this ticket defines the lane commands only
- Modifying any test code

## Acceptance Criteria
- [ ] Six lane commands or Makefile targets are defined and executable locally
- [ ] Each lane selects only the appropriate tests via -m markers
- [ ] Strict matrix can be run separately from fast lanes
- [ ] Legacy regression remains visible and runnable
- [ ] Architecture guards run in normal CI
- [ ] Slow tests are isolated from fast feedback lanes
- [ ] docs/testing/migration_ci_lanes.md documents the lanes

## Related Tickets
- TCK-20260609-MIGRATION-TEST-MARKERS (dependency — markers must exist before lanes can use them)

## Related Docs
- docs/testing/migration_ci_lanes.md (new)

## Related Stored Artifacts
None.

## Related Code Areas
- Makefile or scripts/ci/ (new or updated)
- docs/testing/migration_ci_lanes.md (new)
- pyproject.toml

## Assumptions / Open Questions
- Project uses a Makefile or equivalent for local test commands

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
