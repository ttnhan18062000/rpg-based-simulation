# TCK-20260523-COGNITION-REPORTS-API

## Title

Cognition Evidence Reports Integration and CLI/API Inspection

## Status

DONE

## Request Summary

Enrich Phase 9 Observatory reports and evidence packs with strategic cognition summaries, and implement a robust, read-only Click CLI and API layer to allow developers to inspect cognition logs without opening raw artifact files.

## Scope

- Add "Strategic Cognition Evidence" sections to Observatory reports, summarizing current project, active blockers, leads, concerns, and recent updates.
- Enrich evidence packs with files (`cognition_snapshot_before.json`, `cognition_snapshot_after.json`, `cognition_diff.json`).
- Implement safe, read-only API endpoints for snapshots, diffs, features, and patterns.
- Implement pagination, graph size caps, and parameter validation on the API layer.
- Add CLI commands:
  - `rpg-observe cognition snapshot <run_id> <entity_id> --tick <tick>`
  - `rpg-observe cognition diff <run_id> <entity_id> --from <tick1> --to <tick2>`
  - `rpg-observe cognition features <run_id> <entity_id>`
  - `rpg-observe cognition patterns <run_id>`
- Write unit tests for API pagination and CLI path-traversal safety.

## Out of Scope

- Core feature extraction or pattern mining algorithms.
- Validation checks for state-hash drift.

## Acceptance Criteria

- [x] Evidence packs compress graphs to simple summaries by default to avoid huge payloads.
- [x] API endpoints are strictly read-only and prevent path traversal attacks.
- [x] CLI commands parse parameters, validate existence of runs/ticks, and output clean formatted lists/tables.
- [x] Missing cognition data reports a clear user-facing error message (no stack traces).

## Related Tickets

- TCK-20260523-COGNITION-FEATURE-MINING
- TCK-20260523-COGNITION-SAFETY-VERIFICATION

## Related Docs

- `obs_sim_phase10.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/reporting/`
- `src/api/routes/`
- `src/cli/`

## Assumptions / Open Questions

- None

## Implementation Notes

- Seamlessly integrated all routes, repository methods, CLI options, and formatting tables/JSON in accordance with architecture constraints.

## Test Summary

- Added `tests/api/test_cognition_history_api.py` verifying paginated retrievals, full graph flags, traversal prevention, and missing metadata.
- Added `tests/cli/test_cognition_cli.py` verifying parameter sanitization and graceful error outputs.
- Added `tests/unit/observability/cognition/test_cognition_query_service.py` to ensure core artifact retrieval logic works correctly.
- Added `tests/unit/observability/cognition/test_cognition_evidence_pack_builder.py` validating that the EvidencePackBuilder correctly structures raw JSONL lines and aggregates properties.
- Added `tests/integration/observability/test_cognition_report_section.py` verifying that report generators successfully render the strategic cognition details in markdown and JSON, handling missing data cleanly.

## Files Changed

- `src/observability/reporting/history_query.py`
- `src/api/routes/history.py`
- `src/cli/entry.py`
- `src/observability/reporting/run_report.py`
- `src/observability/mining/evidence.py`
- `tests/api/test_cognition_history_api.py`
- `tests/cli/test_cognition_cli.py`
- `tests/unit/observability/cognition/test_cognition_query_service.py`
- `tests/unit/observability/cognition/test_cognition_evidence_pack_builder.py`
- `tests/integration/observability/test_cognition_report_section.py`

## Completion Summary

- Implemented comprehensive API routes, service methods, CLI tools, and automated test coverage. Completed full report and evidence integration, securing the API/CLI against path traversals. All tests pass successfully.
