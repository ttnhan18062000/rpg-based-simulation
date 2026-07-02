# Test Plan: TCK-20260619-E-READ-MODEL

## Regression Surface
- `tests/api/` — all existing API tests must pass after fixing ws/stream.py

## New Tests
### `tests/unit/api/test_read_model_service.py`
- `test_read_model_shapes_entity_response` — ReadModelService.entity_status() returns shaped dict, not raw EntityState
- `test_read_model_shapes_world_status` — world_status() has expected keys
- `test_read_model_does_not_expose_raw_state` — response is JSON-serializable, no internal state attrs
- `test_read_model_entity_not_found` — entity_status() returns None for unknown id

### `tests/architecture/test_api_read_model_guard.py`
- `test_no_api_route_directly_imports_authoritative_state` — no route/ws/server file imports AuthoritativeState outside TYPE_CHECKING

## Scoped Pytest Commands
```bash
pytest tests/unit/api/test_read_model_service.py tests/architecture/test_api_read_model_guard.py -v
pytest tests/api/ -v --tb=short -m "not slow"
```
