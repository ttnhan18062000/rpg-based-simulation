# Plan: TCK-20260619-E-READ-MODEL

## Steps

1. Add `get_entity_timeline_events(entity_id)` to `V2EngineManager`
2. Fix `src/api/ws/stream.py`: remove unused `AuthoritativeState` import; replace `manager._latest_state` with `manager.get_entity_timeline_events()`
3. Create `src/api/read_model_service.py` — `ReadModelService` facade
4. Create `docs/observability/read_model_service_contract.md` — contract doc
5. Create `tests/unit/api/test_read_model_service.py` — unit tests (mocked)
6. Create `tests/architecture/test_api_read_model_guard.py` — architecture guard (static analysis)
7. Append INFRA-210 to `docs/parity_ledger/infrastructure.yaml`

## Scope Guards
- Do NOT change existing route response shapes (behavior-identical)
- Do NOT move routes to import ReadModelService (existing manager call chain already compliant)
- Do NOT add new API endpoints
