from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from src.engine.scenario_runtime import ScenarioObjectiveState
import src.engine.scenario_registry as registry

_TEST_CLIENT_ID = "scenario-runtime-test-client"
_TEST_RAW_KEY = "scenario-runtime-test-key"
_TEST_KEY_HASH = hashlib.sha256(_TEST_RAW_KEY.encode("utf-8")).hexdigest()


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
        api_key_hashes=f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}",
    )
    app = create_v2_app(profile=profile)
    with TestClient(app, raise_server_exceptions=True, headers={"X-API-Key": _TEST_RAW_KEY}) as c:
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


# ---------------------------------------------------------------------------
# TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE: spec_path containment
# ---------------------------------------------------------------------------

@pytest.fixture
def allowed_spec_dir(tmp_path, monkeypatch):
    spec_dir = tmp_path / "scenario_specs"
    spec_dir.mkdir()
    monkeypatch.setattr("src.api.routes.scenarios.ALLOWED_SPEC_BASE_DIR", spec_dir)
    return spec_dir


def test_restore_endpoint_accepts_in_bounds_spec_path(client, mock_scenario_svc, monkeypatch, allowed_spec_dir):
    spec_file = allowed_spec_dir / "valid_spec.yaml"
    spec_file.write_text(
        "id: test-scenario\nworld_composition: default\nperspective: default\n"
    )

    restored_svc = MagicMock()
    restored_svc.tick = 25
    restored_svc.objective_state.value = "RUNNING"
    monkeypatch.setattr(
        "src.api.routes.scenarios.ScenarioCheckpointer.restore",
        lambda path, spec: restored_svc,
    )

    response = client.post(
        "/api/v1/scenarios/test-scenario/restore/my-save",
        json={"spec_path": "valid_spec.yaml"},
    )
    assert response.status_code == 200
    assert response.json()["tick"] == 25


def test_restore_endpoint_rejects_traversal_spec_path(client, mock_scenario_svc, allowed_spec_dir):
    response = client.post(
        "/api/v1/scenarios/test-scenario/restore/my-save",
        json={"spec_path": "../../etc/passwd"},
    )
    assert response.status_code == 400
    assert "allowed" in response.json()["detail"].lower()


def test_restore_endpoint_rejects_absolute_spec_path_outside_base(client, mock_scenario_svc, allowed_spec_dir, tmp_path):
    outside_file = tmp_path / "outside_secret.yaml"
    outside_file.write_text("id: leaked\nworld_composition: default\nperspective: default\n")

    response = client.post(
        "/api/v1/scenarios/test-scenario/restore/my-save",
        json={"spec_path": str(outside_file)},
    )
    assert response.status_code == 400


def test_restore_endpoint_containment_rejection_closes_existence_oracle(client, mock_scenario_svc, allowed_spec_dir, tmp_path):
    """Both an existing-but-out-of-bounds and a nonexistent-and-out-of-bounds
    spec_path must fail identically (400, before any open()), so the response
    cannot be used to probe the filesystem for file existence."""
    existing_outside = tmp_path / "exists.yaml"
    existing_outside.write_text("id: x\nworld_composition: default\nperspective: default\n")

    resp_exists = client.post(
        "/api/v1/scenarios/test-scenario/restore/my-save",
        json={"spec_path": str(existing_outside)},
    )
    resp_missing = client.post(
        "/api/v1/scenarios/test-scenario/restore/my-save",
        json={"spec_path": str(tmp_path / "does_not_exist.yaml")},
    )

    assert resp_exists.status_code == 400
    assert resp_missing.status_code == 400
    assert resp_exists.json()["detail"] == resp_missing.json()["detail"]


def test_restore_endpoint_default_spec_branch_unaffected_by_containment(client, mock_scenario_svc, monkeypatch, allowed_spec_dir):
    restored_svc = MagicMock()
    restored_svc.tick = 7
    restored_svc.objective_state.value = "RUNNING"
    monkeypatch.setattr(
        "src.api.routes.scenarios.ScenarioCheckpointer.restore",
        lambda path, spec: restored_svc,
    )

    response = client.post("/api/v1/scenarios/test-scenario/restore/my-save")
    assert response.status_code == 200
    assert response.json()["tick"] == 7
