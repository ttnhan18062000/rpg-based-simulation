"""
Per-client HTTP admission control (TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL).

Real, in-process `TestClient`-based tests against the fully-wired `create_v2_app()`
app for integration coverage, plus direct unit-level tests against
`src.api.admission_control`'s private helpers for the hysteresis/eviction logic
that would otherwise require hundreds of real requests to exercise. Follows
`tests/api/test_api_key_auth.py`'s established conventions (real TestClient,
real response status/headers, hashlib.sha256-derived test keys, `dependant.dependencies`
introspection for architecture guards). See
docs/architecture/http_admission_control.md for the mechanism this file guards.
"""
from __future__ import annotations

import ast
import hashlib
import time

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

import src.api.admission_control as admission_control
from src.api.admission_control import (
    ObservabilityMode,
    _ClientAdmissionState,
    _check_admission,
    _evaluate,
    _prune_idle_clients,
    _recovery_limit_for,
    admission_status,
    reset_admission_mode,
)
from src.api.server import create_v2_app
from src.config.profiles import RuntimeProfile, HardwareClass

TEST_CLIENT_ID = "test-client"
TEST_RAW_KEY = "test-raw-key-12345"
TEST_KEY_HASH = hashlib.sha256(TEST_RAW_KEY.encode("utf-8")).hexdigest()

CLIENT_A_ID = "clientA"
CLIENT_A_RAW_KEY = "client-a-raw-key"
CLIENT_A_KEY_HASH = hashlib.sha256(CLIENT_A_RAW_KEY.encode("utf-8")).hexdigest()

CLIENT_B_ID = "clientB"
CLIENT_B_RAW_KEY = "client-b-raw-key"
CLIENT_B_KEY_HASH = hashlib.sha256(CLIENT_B_RAW_KEY.encode("utf-8")).hexdigest()


def _make_profile(**overrides):
    base = dict(
        name="admission-test", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=256, max_cpu_percent=100.0, max_worker_count=0,
        max_queue_depth=100, max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0, max_tick_budget_ms=200.0,
        api_key_hashes=f"{TEST_CLIENT_ID}:{TEST_KEY_HASH}",
    )
    base.update(overrides)
    return RuntimeProfile(**base)


@pytest.fixture(autouse=True)
def _reset_state():
    """Every test starts with a clean admission_control module-level singleton
    state -- mirrors test_api_key_auth.py's implicit per-test isolation (that
    module's _client_keys is reconfigured by every _make_profile()/
    create_v2_app() call; this module's _client_state additionally needs an
    explicit clear since it accumulates across calls within one test run)."""
    reset_admission_mode()
    yield
    reset_admission_mode()


def test_admission_control_mode_vocabulary_matches_observability():
    import src.observability.event_recorder as event_recorder_mod

    assert {m.value for m in ObservabilityMode} == {"NORMAL", "PRESSURE", "DEGRADED", "SURVIVAL"}
    assert admission_control.ObservabilityMode is event_recorder_mod.ObservabilityMode


def test_first_request_from_new_client_is_admitted():
    app = create_v2_app(_make_profile())
    with TestClient(app) as client:
        resp = client.get("/api/v1/state", headers={"X-API-Key": TEST_RAW_KEY})
        assert resp.status_code == 200


def test_escalation_is_immediate_on_pressure_signal():
    state = _ClientAdmissionState()
    current_time = 1000.0

    # Drain the token bucket without further wall-clock advance so fill_ratio
    # climbs monotonically: fill_ratio = 1.0 - tokens/capacity, tokens decrease
    # by 1 per call once the bucket's initial (capped) refill settles.
    mode = ObservabilityMode.NORMAL
    for _ in range(int(admission_control._BUCKET_CAPACITY) + 5):
        mode = _evaluate(state, admission_control._consume_token(state, current_time))
        if mode is ObservabilityMode.PRESSURE:
            break

    assert mode is ObservabilityMode.PRESSURE
    # Escalation is immediate -- no dwell delay on the very evaluation that crosses.
    assert state.dwell_count == 0


def test_recovery_is_gated_by_dwell_and_confidence():
    admission_control._dwell_time_ticks = 2
    admission_control._confidence_window_ticks = 2
    try:
        state = _ClientAdmissionState()
        state.mode = ObservabilityMode.SURVIVAL

        limit = _recovery_limit_for(ObservabilityMode.SURVIVAL)
        low_fill_ratio = max(0.0, limit - 0.1)

        modes = [_evaluate(state, low_fill_ratio) for _ in range(6)]

        # Stays SURVIVAL while dwell_count is still below dwell_time_ticks,
        # even though every fill_ratio sample is already low.
        assert modes[0] is ObservabilityMode.SURVIVAL
        assert modes[1] is ObservabilityMode.SURVIVAL

        # Eventually recovers, but never straight past DEGRADED to NORMAL --
        # exactly one level at a time -- and never before dwell_time_ticks
        # evaluation calls have elapsed.
        assert ObservabilityMode.NORMAL not in modes
        assert ObservabilityMode.DEGRADED in modes
        first_degraded_index = modes.index(ObservabilityMode.DEGRADED)
        assert first_degraded_index >= admission_control._dwell_time_ticks
    finally:
        admission_control._dwell_time_ticks = 10
        admission_control._confidence_window_ticks = 5


def test_per_client_state_is_isolated():
    profile = _make_profile(
        api_key_hashes=f"{CLIENT_A_ID}:{CLIENT_A_KEY_HASH},{CLIENT_B_ID}:{CLIENT_B_KEY_HASH}",
    )
    app = create_v2_app(profile)
    with TestClient(app) as client:
        state = _ClientAdmissionState(last_active_time=time.time())
        state.mode = ObservabilityMode.SURVIVAL
        admission_control._client_state[CLIENT_A_ID] = state
        admission_control._client_order.append(CLIENT_A_ID)

        resp_a = client.get("/api/v1/state", headers={"X-API-Key": CLIENT_A_RAW_KEY})
        assert resp_a.status_code == 429

        resp_b = client.get("/api/v1/state", headers={"X-API-Key": CLIENT_B_RAW_KEY})
        assert resp_b.status_code == 200


def test_survival_mode_sheds_or_rejects_requests():
    app = create_v2_app(_make_profile())
    with TestClient(app) as client:
        state = _ClientAdmissionState(last_active_time=time.time())
        state.mode = ObservabilityMode.SURVIVAL
        admission_control._client_state[TEST_CLIENT_ID] = state
        admission_control._client_order.append(TEST_CLIENT_ID)

        resp = client.get("/api/v1/state", headers={"X-API-Key": TEST_RAW_KEY})
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers


def test_idle_client_entry_is_evicted_after_ttl():
    _check_admission("c1", current_time=1000.0)
    assert "c1" in admission_control._client_state

    _prune_idle_clients(1000.0 + admission_control._IDLE_TTL_SECONDS + 1)
    assert "c1" not in admission_control._client_state


def test_max_entries_cap_evicts_least_recently_active(monkeypatch):
    monkeypatch.setattr(admission_control, "_MAX_CLIENT_ENTRIES", 3)

    for i in range(3):
        _check_admission(f"c{i}", current_time=float(i))
    assert set(admission_control._client_state.keys()) == {"c0", "c1", "c2"}

    _check_admission("c3", current_time=3.0)
    assert "c0" not in admission_control._client_state
    assert set(admission_control._client_state.keys()) == {"c1", "c2", "c3"}


def test_eviction_does_not_lose_active_clients(monkeypatch):
    monkeypatch.setattr(admission_control, "_MAX_CLIENT_ENTRIES", 3)

    _check_admission("active", current_time=0.0)
    for i in range(10):
        _check_admission("active", current_time=float(i) + 0.5)
        _check_admission(f"idle{i}", current_time=float(i) + 0.6)

    assert "active" in admission_control._client_state


def test_admission_status_accessor_shape():
    _check_admission("statusclient", current_time=1.0)
    status = admission_status("statusclient")
    assert set(status.keys()) == {"client_id", "mode", "fill_ratio", "tokens_remaining", "dwell_count"}


def test_reset_admission_mode_clears_state():
    _check_admission("clientX", current_time=1.0)
    reset_admission_mode("clientX")
    assert admission_status("clientX")["mode"] == "NORMAL"
    assert "clientX" not in admission_control._client_state

    _check_admission("clientY", current_time=1.0)
    _check_admission("clientZ", current_time=1.0)
    reset_admission_mode()
    assert admission_control._client_state == {}


def test_admission_dependency_requires_resolved_client_identity():
    """Architecture guard for Decision 2: every require_admission* dependency's
    own dependant sub-graph must contain the matching require_api_key* by name,
    confirming the parameter-chain composition rather than a standalone
    reimplementation of identity resolution."""
    app = create_v2_app(_make_profile())

    admission_to_auth = {
        "require_admission": "require_api_key",
        "require_admission_header_or_query": "require_api_key_header_or_query",
        "require_admission_ws": "require_api_key_ws",
    }

    checked_any = False
    for route in app.routes:
        dependant = getattr(route, "dependant", None)
        if dependant is None:
            continue
        for dep in dependant.dependencies:
            dep_name = getattr(dep.call, "__name__", None)
            if dep_name not in admission_to_auth:
                continue
            checked_any = True
            nested_names = {
                getattr(sub.call, "__name__", None)
                for sub in dep.dependencies
                if sub.call is not None
            }
            assert admission_to_auth[dep_name] in nested_names, (
                f"{dep_name} on {route.path} does not chain "
                f"{admission_to_auth[dep_name]} as a parameter dependency"
            )

    assert checked_any


def test_admission_control_covers_every_authenticated_route():
    """Architecture guard: every route carrying a require_api_key* dependency
    name anywhere in its dependant graph must also carry the matching
    require_admission* name; /health is the sole route carrying neither."""
    app = create_v2_app(_make_profile())

    auth_names = {"require_api_key", "require_api_key_header_or_query", "require_api_key_ws"}
    admission_names = {"require_admission", "require_admission_header_or_query", "require_admission_ws"}

    neither_paths = set()
    for route in app.routes:
        dependant = getattr(route, "dependant", None)
        if dependant is None:
            continue

        all_names = set()

        def _collect(d):
            for sub in d.dependencies:
                name = getattr(sub.call, "__name__", None)
                if name is not None:
                    all_names.add(name)
                _collect(sub)

        _collect(dependant)

        path = getattr(route, "path", None)
        has_auth = bool(all_names & auth_names)
        has_admission = bool(all_names & admission_names)

        if has_auth:
            assert has_admission, f"{path} carries auth but no admission-control dependency"
        if not has_auth and not has_admission:
            neither_paths.add(path)

    assert neither_paths == {"/health"}


def test_admission_control_does_not_reach_into_governor_internals():
    """Static guard: src/api/admission_control.py must never import from
    src.engine.governor or src.engine.phase_governor -- the hysteresis logic is
    pattern-mirrored, never imported, per the ticket's Out of Scope."""
    with open("src/api/admission_control.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename="src/api/admission_control.py")

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert not module.startswith("src.engine.governor")
            assert not module.startswith("src.engine.phase_governor")
