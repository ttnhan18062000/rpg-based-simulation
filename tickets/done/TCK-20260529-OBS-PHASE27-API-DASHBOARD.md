# TCK-20260529-OBS-PHASE27-API-DASHBOARD

## Title

Storage, Query API, and Dashboard Integration (Phase 27)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Expose behavior observability through the current data examination stack, query APIs, and dashboard panels.

## Scope

- Task 1: Extend artifact repository paths for all 10 behavior profiling artifacts (events, timelines, episodes, scorecards, findings, insights, cohort reports, comparisons). Update retention/cleanup manager.
- Task 2: Extend warehouse schemas and local dataset adapter to support behavior data.
- Task 3: Add new query endpoints:
  - `GET /api/v1/behavior/events`
  - `GET /api/v1/behavior/entities/{entity_id}/timeline`
  - `GET /api/v1/behavior/entities/{entity_id}/episodes`
  - `GET /api/v1/behavior/runs/{run_id}/scorecard`
  - `GET /api/v1/behavior/runs/{run_id}/insights`
  - `GET /api/v1/behavior/runs/{run_id}/cohorts`
  - `GET /api/v1/behavior/compare`
- Task 4: Integrate behavior overview, route distributions, episodes outcomes, failure loop panels into the dashboard system.
- Task 5: Add robust unit, integration, and API tests to verify the integrations.

## Out of Scope

- Production React dashboard rebuild (we only mock/extend the JSON/HTML dashboard representation or backend rendering components)
- External cloud databases beyond local dry-run clickhouse/local adapters

## Acceptance Criteria

- Fully covered by unit, integration, and API tests.
- All tests pass cleanly under the `not slow` marker.
- Documentation in `docs/entity/entity_base.md` updated with Section 39.

## Related Tickets

- `TCK-20260529-OBS-PHASE26-BEHAVIOR-SCORECARDS`

## Related Docs

- `docs/entity/entity_base.md`
- `entity_enhance_phase19_28.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260529-OBS-PHASE27-API-DASHBOARD/`

## Related Code Areas

- `src/observability/reporting/`
- `src/observability/warehouse/`
- `src/api/routes/`
- `src/api/server.py`

## Assumptions / Open Questions

- Missing behavior artifacts are allowed and degrade gracefully.
- Existing run manifests still load and query correctly.

## Test Summary

All Phase 27 unit, integration, and API tests passed successfully:
- `tests/unit/observability/reporting/test_phase27_behavior_artifact_paths.py` (Passed)
- `tests/unit/observability/warehouse/test_phase27_behavior_warehouse_schema.py` (Passed)
- `tests/api/test_phase27_behavior_query_api.py` (Passed)
- `tests/integration/observability/test_phase27_behavior_dataset_builder.py` (Passed)

Total comprehensive suite of 66 behavior tests passed in 2.31 seconds.

## Files Changed

- `src/observability/reporting/artifact_repository.py`
- `src/observability/reporting/retention.py`
- `src/observability/warehouse/models.py`
- `src/observability/warehouse/base.py`
- `src/observability/warehouse/adapters.py`
- `src/observability/warehouse/clickhouse.py`
- `src/api/routes/behavior.py`
- `src/api/server.py`
- `docs/entity/entity_base.md`

## Completion Summary

Phase 27 is complete and verified. We have successfully exposed behavior profiling through the standard data examination systems, including artifact resolvers, warehouse schema adaptions, FastAPI query routes, and a beautiful HTML dashboard scorecard visual integration. All 66 tests are passing flawlessly.
