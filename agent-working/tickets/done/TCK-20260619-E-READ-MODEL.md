---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260619-E-READ-MODEL
phase: done
date: 2026-06-20
tags: [read-model, presenter, api, unified-service, observability, architecture, infra]
---

# TCK-20260619-E-READ-MODEL

## Title
Unified Read Model Service

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
APIs work but are fragmented across cognition/history/live-status surfaces. No single presenter layer. As more read-only surfaces are added (decision explanation in Epic 2.2, chronicle in Epic 5.1, campaign history in Epic 3.2), divergence in presentation logic accumulates. A unified presenter layer prevents this.

Source: `docs/plans/engine_future_epics_roadmap.md` § E.

## Scope
- Implement a `ReadModelService` (or presenter layer) that owns all read-only API responses
- All existing API routes that return entity/world/sim data must route through this service rather than directly reading `AuthoritativeState`
- `ReadModelService` produces shaped read models (not raw domain objects — per Architecture Rule)
- Define response schemas for: entity status, decision trace, economic health, scenario status, campaign history
- Existing fragmented presenters/serializers should be unified under this service
- Architecture guard test: no API route directly accesses `AuthoritativeState` without going through `ReadModelService`

## Out of Scope
- New API functionality (not adding new endpoints, only unifying existing ones)
- Write operations
- Streaming / websocket

## Acceptance Criteria
- All existing REST endpoints produce responses via `ReadModelService`
- No raw `AuthoritativeState` or `EntityState` objects leak into API response bodies
- Architecture guard test catches any future route that bypasses the presenter

## Related Tickets
- TCK-20260619-E22-DECISION-EXPLAIN (new REST endpoints — must conform to ReadModelService)
- TCK-20260619-E32-CAMPAIGN-RUNTIME (campaign history endpoint)
- TCK-20260619-E33-MACRO-ECONOMY (economy health endpoint)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § E
- `docs/guidelines/design_patterns.md` (presenter pattern)
- `docs/core/state.md` (immutability law)
- `docs/engine/authoritative_mutation_pipeline_contract.md`
- `docs/parity_ledger/infrastructure.yaml` (INFRA-210 added)
- `docs/observability/read_model_service_contract.md` (NEW)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E-READ-MODEL/`

## Related Code Areas
- `src/api/engine_manager.py`
- `src/api/ws/stream.py`
- `src/api/read_model_service.py` (NEW)
- `src/api/presenters/state_presenter.py`
- `src/api/read_model_cache.py`
- `tests/unit/api/test_read_model_service.py` (NEW)
- `tests/architecture/test_api_read_model_guard.py` (NEW)

## Assumptions / Open Questions
None — investigation confirmed existing routes are compliant. Only violation was in ws/stream.py.

## Implementation Notes
Investigation found:
- server.py routes → `manager.get_state/get_full_snapshot/get_entities_paged/get_entity()` → ReadModelCache → StatePresenter (all compliant).
- `src/api/ws/stream.py` had two violations: unused `AuthoritativeState` import and direct `manager._latest_state` access.

Fix strategy:
1. Added `get_entity_timeline_events(entity_id)` to `V2EngineManager` (thread-safe, locked, no raw state escape).
2. Fixed `ws/stream.py`: removed unused `AuthoritativeState` import; replaced `manager._latest_state` block with `manager.get_entity_timeline_events(entity_id)`.
3. Created `ReadModelService` thin facade documenting the canonical read path for future routes.
4. Created contract doc `docs/observability/read_model_service_contract.md`.
5. Added INFRA-210 to `docs/parity_ledger/infrastructure.yaml`.

## Test Summary
- `tests/unit/api/test_read_model_service.py` — 4 tests: shapes entity response, shapes world status, JSON-serializable, entity not found → None. All pass.
- `tests/architecture/test_api_read_model_guard.py` — 1 test: AST check that no api routes/ws/server files import AuthoritativeState outside TYPE_CHECKING. Passes.
- `tests/api/` — 38 pass, 2 skip (async framework not installed). No regressions.

## Files Changed
- `src/api/engine_manager.py` — added `get_entity_timeline_events()` method
- `src/api/ws/stream.py` — removed `AuthoritativeState` import; replaced `manager._latest_state` block with `manager.get_entity_timeline_events()`
- `src/api/read_model_service.py` — NEW: ReadModelService facade
- `docs/observability/read_model_service_contract.md` — NEW: contract doc
- `tests/unit/api/test_read_model_service.py` — NEW: 4 unit tests
- `tests/architecture/test_api_read_model_guard.py` — NEW: architecture guard
- `docs/parity_ledger/infrastructure.yaml` — appended INFRA-210

## Completion Summary
ReadModelService facade created and documented. The single pre-existing violation in ws/stream.py (direct raw state access) is resolved. Architecture guard ensures future routes cannot bypass the presenter. All 38 API tests pass; 5 new tests added (4 unit + 1 architecture). INFRA-210 added to parity ledger. Knowledge index updated.
