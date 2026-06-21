---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E31D-REST-API
phase: test_plan
date: 2026-06-21
---

# Test Plan — TCK-20260619-E31D-REST-API

## Regression Surface (existing tests that must still pass)

These tests exercise code paths that E31D will touch or is adjacent to. Run before and after implementation.

| Test file | What it protects |
|-----------|-----------------|
| `tests/unit/engine/test_scenario_runtime_service.py` | `ScenarioRuntimeService` lifecycle, tick, objective_state, alive_entity_count — read by status endpoint |
| `tests/unit/engine/test_scenario_checkpointer.py` | `ScenarioCheckpointer.save()/restore()` — called by checkpoint + restore endpoints |
| `tests/integration/scenarios/test_scenario_runtime_service.py` | E31C determinism (checkpoint/restore identity); must not regress |
| `tests/api/test_rest_parity.py` | `/health`, `/api/v1/state`, `/api/v1/control/pause|resume` — server.py router registration must not break these |
| `tests/api/test_live_observability_status.py` | `/api/v1/observability/live/status` — server.py lifespan and existing route chain |
| `tests/api/test_phase27_behavior_query_api.py` | `/api/v1/behavior/*` — ensures no router registration collision |
| `tests/api/test_decision_api.py` | `/api/v1/observability/entities/{id}/decisions` — route collision guard |

Scoped regression run:
```bash
pytest tests/unit/engine/test_scenario_runtime_service.py \
       tests/unit/engine/test_scenario_checkpointer.py \
       tests/api/ \
       -x -v -m "not slow"
```


## New Tests Required (per AC)

All new tests go in `tests/api/test_scenario_runtime_api.py`.

Use FastAPI `TestClient` (synchronous, no subprocess) and inject a mock or minimal `ScenarioRuntimeService` via dependency override — do NOT spin up a real kernel for unit-level API tests.

---

### T-01 — `test_status_endpoint_returns_live_state` (required by AC)

**What it proves**: `GET /api/v1/scenarios/{id}/status` returns `{tick, objective_state, alive_entity_count}` from a live service.

```python
def test_status_endpoint_returns_live_state(client, mock_scenario_svc):
    # mock_svc.tick = 42, .objective_state = "RUNNING", .alive_entity_count = 5
    response = client.get("/api/v1/scenarios/test-scenario/status")
    assert response.status_code == 200
    data = response.json()
    assert data["tick"] == 42
    assert data["objective_state"] == "RUNNING"
    assert data["alive_entity_count"] == 5
    assert "key_metrics" in data  # can be {}
```

---

### T-02 — `test_status_endpoint_returns_404_for_unknown_scenario`

**What it proves**: Unknown scenario ID returns 404, not 500.

```python
def test_status_endpoint_returns_404_for_unknown_scenario(client):
    response = client.get("/api/v1/scenarios/no-such-scenario/status")
    assert response.status_code == 404
```

---

### T-03 — `test_status_does_not_advance_tick`

**What it proves**: GET /status is read-only — `tick` does not change between two consecutive calls.

```python
def test_status_does_not_advance_tick(client, mock_scenario_svc):
    r1 = client.get("/api/v1/scenarios/test-scenario/status")
    r2 = client.get("/api/v1/scenarios/test-scenario/status")
    assert r1.json()["tick"] == r2.json()["tick"]
    # verify svc.step() was never called
```

---

### T-04 — `test_checkpoint_endpoint_returns_path_and_tick`

**What it proves**: `POST /api/v1/scenarios/{id}/checkpoint` calls `ScenarioCheckpointer.save()` and returns `{path, tick}`.

```python
def test_checkpoint_endpoint_returns_path_and_tick(client, mock_scenario_svc, tmp_path, monkeypatch):
    # Patch ScenarioCheckpointer.save to avoid real I/O
    monkeypatch.setattr("src.api.routes.scenarios.ScenarioCheckpointer.save", lambda svc, p: None)
    response = client.post(
        "/api/v1/scenarios/test-scenario/checkpoint",
        json={"name": "my-save"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "my-save" in data["path"]
    assert data["tick"] == mock_scenario_svc.tick
```

---

### T-05 — `test_checkpoint_endpoint_400_when_kernel_not_started`

**What it proves**: If `ScenarioCheckpointer.save()` raises `RuntimeError` (kernel not started), route returns 400 not 500.

```python
def test_checkpoint_endpoint_400_when_kernel_not_started(client, mock_scenario_svc, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.scenarios.ScenarioCheckpointer.save",
        lambda svc, p: (_ for _ in ()).throw(RuntimeError("kernel not started"))
    )
    response = client.post(
        "/api/v1/scenarios/test-scenario/checkpoint",
        json={"name": "bad"}
    )
    assert response.status_code == 400
```

---

### T-06 — `test_restore_endpoint_returns_tick_and_state`

**What it proves**: `POST /api/v1/scenarios/{id}/restore/{checkpoint_name}` calls `ScenarioCheckpointer.restore()` and returns `{tick, objective_state}`.

```python
def test_restore_endpoint_returns_tick_and_state(client, mock_scenario_svc, monkeypatch):
    restored_svc = MagicMock()
    restored_svc.tick = 25
    restored_svc.objective_state.value = "RUNNING"
    monkeypatch.setattr(
        "src.api.routes.scenarios.ScenarioCheckpointer.restore",
        lambda path, spec: restored_svc
    )
    response = client.post("/api/v1/scenarios/test-scenario/restore/my-save")
    assert response.status_code == 200
    data = response.json()
    assert data["tick"] == 25
    assert data["objective_state"] == "RUNNING"
```

---

### T-07 — `test_restore_endpoint_404_when_file_not_found`

**What it proves**: `FileNotFoundError` from `restore()` maps to 404.

```python
def test_restore_endpoint_404_when_file_not_found(client, mock_scenario_svc, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.scenarios.ScenarioCheckpointer.restore",
        lambda path, spec: (_ for _ in ()).throw(FileNotFoundError("not found"))
    )
    response = client.post("/api/v1/scenarios/test-scenario/restore/ghost-save")
    assert response.status_code == 404
```

---

### T-08 — `test_restore_endpoint_400_on_spec_id_mismatch`

**What it proves**: `ValueError` (spec_id mismatch from `restore()`) maps to 400.

```python
def test_restore_endpoint_400_on_spec_id_mismatch(client, mock_scenario_svc, monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.scenarios.ScenarioCheckpointer.restore",
        lambda path, spec: (_ for _ in ()).throw(ValueError("spec_id mismatch"))
    )
    response = client.post("/api/v1/scenarios/test-scenario/restore/wrong-save")
    assert response.status_code == 400
```

---

### T-09 — `test_presenter_does_not_expose_raw_domain_objects`

**What it proves**: Presenter returns only plain Python dict values (no enum instances, no domain model objects).

```python
def test_presenter_does_not_expose_raw_domain_objects():
    from src.api.presenters.scenarios import ScenarioPresenter
    from src.engine.scenario_runtime import ScenarioObjectiveState
    from unittest.mock import MagicMock

    svc = MagicMock()
    svc.tick = 10
    svc.objective_state = ScenarioObjectiveState.RUNNING
    svc.alive_entity_count = 3

    result = ScenarioPresenter.present_status(svc)
    assert isinstance(result["tick"], int)
    assert isinstance(result["objective_state"], str)
    assert isinstance(result["alive_entity_count"], int)
    assert isinstance(result.get("key_metrics", {}), dict)
```

---

### T-10 — `test_checkpoint_presenter_returns_path_and_tick`

**What it proves**: `ScenarioPresenter.present_checkpoint()` returns correct shape.

```python
def test_checkpoint_presenter_returns_path_and_tick():
    from src.api.presenters.scenarios import ScenarioPresenter
    result = ScenarioPresenter.present_checkpoint("checkpoints/abc/save1.ckpt", tick=33)
    assert result["path"] == "checkpoints/abc/save1.ckpt"
    assert result["tick"] == 33
```

---

### T-11 — `test_route_registered_in_server`

**What it proves**: The scenarios router is reachable (prevents silent registration omission).

```python
def test_route_registered_in_server():
    from src.api.server import create_v2_app
    from src.config.profiles import RuntimeProfile
    # Use a test profile
    app = create_v2_app(profile=...)
    routes = [r.path for r in app.routes]
    assert any("/scenarios" in r for r in routes)
```


## Scoped Pytest Commands

### New API tests only (primary AC check)
```bash
pytest tests/api/test_scenario_runtime_api.py -x -v
```

### Required AC test only
```bash
pytest tests/api/test_scenario_runtime_api.py::test_status_endpoint_returns_live_state -x -v
```

### Presenter unit tests only (no server needed)
```bash
pytest tests/api/test_scenario_runtime_api.py -x -v -k "presenter"
```

### Full regression scope (before + after)
```bash
pytest tests/unit/engine/test_scenario_runtime_service.py \
       tests/unit/engine/test_scenario_checkpointer.py \
       tests/api/ \
       -x -v -m "not slow"
```

### E31 integration tests (determinism guard)
```bash
pytest tests/integration/scenarios/test_scenario_runtime_service.py -x -v -m "not slow"
```


## Anti-Drift Test Guards

1. **Presenter isolation test (T-09)** must verify no enum instances or domain objects leak through. The `ScenarioObjectiveState` enum's `.value` must be extracted before returning — the presenter must call `svc.objective_state.value` or equivalent, not return the enum directly.

2. **Read-only guard (T-03)** must assert that `tick` does not change across repeated GET calls. This guards against accidental `svc.step()` or `svc.start()` calls inside a GET handler.

3. **Route registration test (T-11)** prevents the common failure mode where `src/api/routes/scenarios.py` is created but the `app.include_router(...)` line is forgotten in `server.py`.

4. **Error mapping tests (T-05, T-07, T-08)** guard against exception bleed-through (500s) for client-recoverable error conditions. These are the highest-risk drift surface because FastAPI defaults to 500 for unhandled exceptions.

5. **Parity ledger update test path**: `docs/parity_ledger/infrastructure.yaml` entry INFRA-215 must have its `test_path` updated to include `tests/api/test_scenario_runtime_api.py`. A new INFRA-216 entry must be added. These are verified manually at finalize time against the ledger — no automated test guard, but must be confirmed before moving to done.
