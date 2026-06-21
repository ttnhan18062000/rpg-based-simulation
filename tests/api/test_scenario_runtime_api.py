from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from src.engine.scenario_runtime import ScenarioObjectiveState
import src.engine.scenario_registry as registry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_scenario_svc():
    svc = MagicMock()
    svc.tick = 42
    svc.objective_state = ScenarioObjectiveState.RUNNING
    svc.alive_entity_count = 5
    return svc


@pytest.fixture
def client(mock_scenario_svc):
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.api.server import create_v2_app

    registry.register("test-scenario", mock_scenario_svc)

    profile = RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=256,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=100,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=200.0,
    )
    app = create_v2_app(profile=profile)
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    registry.unregister("test-scenario")


# ---------------------------------------------------------------------------
# T-01: status happy path
# ---------------------------------------------------------------------------

def test_status_endpoint_returns_live_state(client, mock_scenario_svc):
    response = client.get("/api/v1/scenarios/test-scenario/status")
    assert response.status_code == 200
    data = response.json()
    assert data["tick"] == 42
    assert data["objective_state"] == "RUNNING"
    assert data["alive_entity_count"] == 5
    assert "key_metrics" in data


# ---------------------------------------------------------------------------
# T-02: status 404 for unknown scenario
# ---------------------------------------------------------------------------

def test_status_endpoint_returns_404_for_unknown_scenario(client):
    response = client.get("/api/v1/scenarios/no-such-scenario/status")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# T-03: status is read-only (tick unchanged, no step/start called)
# ---------------------------------------------------------------------------

def test_status_does_not_advance_tick(client, mock_scenario_svc):
    r1 = client.get("/api/v1/scenarios/test-scenario/status")
    r2 = client.get("/api/v1/scenarios/test-scenario/status")
    assert r1.json()["tick"] == r2.json()["tick"]
    assert mock_scenario_svc.step.call_count == 0
    assert mock_scenario_svc.start.call_count == 0


# ---------------------------------------------------------------------------
# T-04: checkpoint happy path
# ---------------------------------------------------------------------------

def test_checkpoint_endpoint_returns_path_and_tick(client, mock_scenario_svc, monkeypatch):
    monkeypatch.setattr("src.api.routes.scenarios.ScenarioCheckpointer.save", lambda svc, p: None)
    response = client.post(
        "/api/v1/scenarios/test-scenario/checkpoint",
        json={"name": "my-save"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "my-save" in data["path"]
    assert data["tick"] == mock_scenario_svc.tick


# ---------------------------------------------------------------------------
# T-05: checkpoint 400 when kernel not started
# ---------------------------------------------------------------------------

def test_checkpoint_endpoint_400_when_kernel_not_started(client, mock_scenario_svc, monkeypatch):
    def _raise(svc, p):
        raise RuntimeError("kernel not started")

    monkeypatch.setattr("src.api.routes.scenarios.ScenarioCheckpointer.save", _raise)
    response = client.post(
        "/api/v1/scenarios/test-scenario/checkpoint",
        json={"name": "bad"},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# T-06: restore happy path
# ---------------------------------------------------------------------------

def test_restore_endpoint_returns_tick_and_state(client, mock_scenario_svc, monkeypatch):
    restored_svc = MagicMock()
    restored_svc.tick = 25
    restored_svc.objective_state.value = "RUNNING"

    monkeypatch.setattr(
        "src.api.routes.scenarios.ScenarioCheckpointer.restore",
        lambda path, spec: restored_svc,
    )
    response = client.post("/api/v1/scenarios/test-scenario/restore/my-save")
    assert response.status_code == 200
    data = response.json()
    assert data["tick"] == 25
    assert data["objective_state"] == "RUNNING"


# ---------------------------------------------------------------------------
# T-07: restore 404 when checkpoint file not found
# ---------------------------------------------------------------------------

def test_restore_endpoint_404_when_file_not_found(client, mock_scenario_svc, monkeypatch):
    def _raise(path, spec):
        raise FileNotFoundError("not found")

    monkeypatch.setattr("src.api.routes.scenarios.ScenarioCheckpointer.restore", _raise)
    response = client.post("/api/v1/scenarios/test-scenario/restore/ghost-save")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# T-08: restore 400 on spec_id mismatch
# ---------------------------------------------------------------------------

def test_restore_endpoint_400_on_spec_id_mismatch(client, mock_scenario_svc, monkeypatch):
    def _raise(path, spec):
        raise ValueError("spec_id mismatch")

    monkeypatch.setattr("src.api.routes.scenarios.ScenarioCheckpointer.restore", _raise)
    response = client.post("/api/v1/scenarios/test-scenario/restore/wrong-save")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# T-09: presenter does not expose raw domain objects
# ---------------------------------------------------------------------------

def test_presenter_does_not_expose_raw_domain_objects():
    from src.api.presenters.scenarios import ScenarioPresenter

    svc = MagicMock()
    svc.tick = 10
    svc.objective_state = ScenarioObjectiveState.RUNNING
    svc.alive_entity_count = 3

    result = ScenarioPresenter.present_status(svc)
    assert isinstance(result["tick"], int)
    assert isinstance(result["objective_state"], str)
    assert isinstance(result["alive_entity_count"], int)
    assert isinstance(result.get("key_metrics", {}), dict)


# ---------------------------------------------------------------------------
# T-10: checkpoint presenter returns correct shape
# ---------------------------------------------------------------------------

def test_checkpoint_presenter_returns_path_and_tick():
    from src.api.presenters.scenarios import ScenarioPresenter

    result = ScenarioPresenter.present_checkpoint("checkpoints/abc/save1.ckpt", tick=33)
    assert result["path"] == "checkpoints/abc/save1.ckpt"
    assert result["tick"] == 33


# ---------------------------------------------------------------------------
# T-11: scenarios router is registered in the app
# ---------------------------------------------------------------------------

def test_route_registered_in_server():
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.api.server import create_v2_app

    profile = RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=256,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=100,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=200.0,
    )
    app = create_v2_app(profile=profile)
    routes = [r.path for r in app.routes]
    assert any("/scenarios" in r for r in routes)
