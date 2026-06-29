---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-E5-API
phase: done
date: 2026-06-28
tags: [simulation-quality, scoring, api, rest]
---

# TCK-20260628-SIMQ-E5-API

## Title
Simulation Quality Scoring — REST API & Post-Run Artifact Generation

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement the REST API endpoints for live and post-run quality data, and wire the
post-run `quality_report.json` artifact generation into the existing run lifecycle
(run-end hook or engine manager shutdown path).

## Scope
- `src/simulation_quality/api/routes.py` — FastAPI router with endpoints:
  - `GET /api/v1/quality/status` — enabled flag, run_id, tick_count, overall_grade
  - `GET /api/v1/quality/pillars` — all 10 pillar summaries (normalized_score, grade)
  - `GET /api/v1/quality/pillars/{pillar_id}` — full pillar state + top-10 worst_events
  - `GET /api/v1/quality/alerts` — pillars graded D or F + active loop_flags
  - `GET /api/v1/quality/report` — full QualityReport snapshot
- Registration in `src/api/server.py` (or equivalent router include)
- Post-run artifact: wire `QualityPersistence.write_report()` to run-end lifecycle
  (the same hook or callback used by replay `manifest.json` finalization)
- Disabled-state response: all endpoints return `{"enabled": false}` when
  `QUALITY_SCORING_DISABLED=1`

## Out of Scope
- WebSocket push endpoints
- Cross-run historical comparison endpoints
- Authentication/authorization (consistent with existing API pattern)

## Acceptance Criteria
- [ ] All 5 endpoints return correct data for a live run in progress
- [ ] All 5 endpoints return correct data post-run (after `quality_report.json` written)
- [ ] `GET /api/v1/quality/pillars/{pillar_id}` returns 404 for unknown pillar_id
- [ ] All endpoints return `{"enabled": false}` when `QUALITY_SCORING_DISABLED=1`
- [ ] `quality_report.json` is written to `data/runs/{run_id}/` at run end
- [ ] API routes have no return type annotations gap (add `response_model=` per §13 of architecture_reference, consistent with D13 F2 finding: 18 routes lack response_model)
- [ ] Integration tests: all 5 endpoints with live accumulator data
- [ ] Integration tests: disabled state responses

## Related Tickets
- Parent: TCK-20260628-SIMQ-EPIC
- Requires: TCK-20260628-SIMQ-E3-SCORERS-A, TCK-20260628-SIMQ-E4-SCORERS-B
- Next: TCK-20260628-SIMQ-E6-TESTS

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §10 (REST API Surface)
- `docs/engine/contracts/observability_artifact_contract.md` §3 (Replay artifact pattern — use same lifecycle hook for quality_report.json)
- `docs/audits/D13_type_safety.md` F2 — existing API response_model gap (do not repeat this pattern)

## Implementation Notes
Follow the existing FastAPI router pattern in `src/api/`. Do not create a new server
or port. Add the quality router to the existing `api/server.py` include list.

The `response_model=` parameter must be set on all 5 route handlers — this is explicitly
required by the acceptance criteria and addresses the D13 F2 finding proactively.

For post-run artifact timing: locate where `manifest.json` is written for replay
(observability_artifact_contract.md §3) and add `QualityPersistence.write_report()`
immediately after. This ensures both artifacts are written at the same lifecycle point.

## Implementation Notes
Created src/simulation_quality/api/routes.py with 5 endpoints; response_model= on all handlers per D13 F2. Added set/get_quality_hub and set/get_quality_persistence to src/api/dependencies.py. Router included in server.py. quality_report.json written at lifespan teardown via write_report(). Coupling rule preserved: simulation_quality only imports from fastapi and api.dependencies.

## Test Summary
14 integration tests covering all 5 endpoints: enabled responses, disabled state, 404 for unknown pillar, alert detection for D/F grade and loop_detected, full report shape.

## Files Changed
- `src/simulation_quality/api/__init__.py` (new)
- `src/simulation_quality/api/routes.py` (new)
- `src/api/dependencies.py` (set/get_quality_hub, set/get_quality_persistence added)
- `src/api/server.py` (router include + write_report at shutdown)
- `tests/simulation_quality/test_api_routes.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-248 through INFRA-249)

## Completion Summary
5 REST endpoints live at /api/v1/quality/{status,pillars,pillars/{id},alerts,report}. All endpoints have response_model= per D13 F2 requirement. quality_report.json written at shutdown. All 14 tests pass.
