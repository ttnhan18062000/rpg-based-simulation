---
status: open
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260619-E-READ-MODEL
phase: open
date: 2026-06-19
tags: [read-model, presenter, api, unified-service, observability, architecture, infra]
---

# TCK-20260619-E-READ-MODEL

## Title
Unified Read Model Service

## Status
OPEN

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
- `docs/guidelines/design_patterns.md` (presenter pattern — update with ReadModelService as the canonical presenter implementation)
- `docs/core/state.md` (immutability law — read models must not expose raw state; this doc defines what counts as a raw domain object)
- `docs/engine/authoritative_mutation_pipeline_contract.md` (defines the read/write boundary — read models must only read state after the authoritative apply path, never bypass it)
- `docs/parity_ledger/infrastructure.yaml` (add ReadModelService presenter contract as verified entry)
- New doc: `docs/observability/read_model_service_contract.md` (ReadModelService schema, presenter rules, response shape definitions, API surface contract)

## Related Code Areas
- `src/` (find existing REST API layer / FastAPI/Flask routes)
- `src/core/state.py:L981` (AuthoritativeState — must not be directly serialized)
- `tests/api/` (existing API tests pattern)

## Assumptions / Open Questions
- Where is the existing REST API layer? Find it before designing the presenter — the unification must fit the existing framework
- Are there existing presenter/schema classes? Check for `src/*/presenters/` or `src/*/schemas/`

## Implementation Notes
Start by auditing all existing API routes to find where raw `AuthoritativeState` or `EntityState` is leaked directly into responses. Then introduce `ReadModelService` and redirect routes one by one. Run existing API tests after each redirect to verify no regression.

After implementation: create `docs/observability/read_model_service_contract.md` (presenter rules, response shape definitions, schema registry). Update `docs/parity_ledger/infrastructure.yaml` (add ReadModelService presenter contract as verified entry). Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/unit/api/test_read_model_service.py`:
  - `test_read_model_shapes_entity_response()` — assert ReadModelService.entity_status() returns shaped dict, not raw EntityState
  - `test_read_model_shapes_scenario_status_response()` — assert scenario status response schema has expected keys
  - `test_read_model_does_not_expose_raw_state()` — assert response is JSON-serializable without accessing internal state attributes
- New file `tests/architecture/test_api_read_model_guard.py`:
  - `test_no_api_route_directly_accesses_authoritative_state()` — static analysis: grep/AST check that no FastAPI/Flask route handler imports or directly reads `AuthoritativeState` without going through ReadModelService
- Regression: all existing `tests/api/` tests continue to pass after unification

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
