"""
Per-client API-key authentication (TCK-20260823-HTTP-API-KEY-AUTH).

Real, in-process `TestClient`-based tests against the fully-wired `create_v2_app()`
app, following `tests/api/test_cors_config.py`'s established pattern -- real response
status/headers asserted, no subprocess. See
docs/architecture/http_api_key_authentication.md for the mechanism this file guards.
"""
from __future__ import annotations

import hashlib
import hmac
from unittest.mock import patch

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import src.api.auth as auth_mod
from src.api.auth import ClientIdentity, configure_api_keys
from src.api.server import create_v2_app
from src.config.profiles import RuntimeProfile, HardwareClass

TEST_CLIENT_ID = "test-client"
TEST_RAW_KEY = "test-raw-key-12345"
TEST_KEY_HASH = hashlib.sha256(TEST_RAW_KEY.encode("utf-8")).hexdigest()

# Routes deliberately allowed to use the weaker header-or-query-param channel
# (Decision 3/4) -- see the Anti-Drift Notes in plan.md: this set must never grow
# without a documented reason, so the guard test below pins it exactly.
_DASHBOARD_AND_WS_PATHS = {
    "/api/v1/observability/ui",
    "/observability/ui",
    "/api/v1/observability/live/ui",
    "/api/v1/ws",
    "/api/v1/ws/observe",
    "/api/v1/ws/observability/events",
}


def _make_profile(**overrides):
    base = dict(
        name="auth-test", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=256, max_cpu_percent=100.0, max_worker_count=0,
        max_queue_depth=100, max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0, max_tick_budget_ms=200.0,
        api_key_hashes=f"{TEST_CLIENT_ID}:{TEST_KEY_HASH}",
    )
    base.update(overrides)
    return RuntimeProfile(**base)


def test_missing_api_key_returns_401_on_protected_route():
    client = TestClient(create_v2_app(_make_profile()))
    resp = client.get("/api/v1/state")
    assert resp.status_code == 401


def test_invalid_api_key_returns_401_on_protected_route():
    client = TestClient(create_v2_app(_make_profile()))
    resp = client.get("/api/v1/state", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


def test_malformed_api_key_header_returns_401_not_500():
    client = TestClient(create_v2_app(_make_profile()))
    # str.encode("utf-8") cannot raise for any Python str, so _hash_key never
    # throws regardless of header content -- these edge cases are safe by
    # construction, not by a special-cased guard clause. Header value is passed
    # as raw bytes (not str) because httpx's TestClient itself rejects a
    # non-ASCII str header value client-side (UnicodeEncodeError) before the
    # request ever reaches our dependency -- that is an httpx-level restriction
    # on this test transport, not something the route/dependency needs to guard
    # against; bytes bypass httpx's client-side ASCII check the same way a real
    # non-ASCII header would arrive over the wire.
    resp_empty = client.get("/api/v1/state", headers={"X-API-Key": ""})
    assert resp_empty.status_code == 401

    resp_control_chars = client.get(
        "/api/v1/state", headers={"X-API-Key": b"\x00\xff invalid e"}
    )
    assert resp_control_chars.status_code == 401


def test_valid_api_key_allows_request_through():
    app = create_v2_app(_make_profile())
    with TestClient(app) as client:
        resp = client.get("/api/v1/state", headers={"X-API-Key": TEST_RAW_KEY})
        assert resp.status_code == 200


def test_health_exempt_from_auth():
    app = create_v2_app(_make_profile())
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code in (200, 503)


def test_metrics_requires_auth():
    client = TestClient(create_v2_app(_make_profile()))
    resp = client.get("/metrics")
    assert resp.status_code == 401


def test_control_mutation_routes_require_auth():
    client = TestClient(create_v2_app(_make_profile()))
    resp_pause = client.post("/api/v1/control/pause")
    resp_resume = client.post("/api/v1/control/resume")
    assert resp_pause.status_code == 401
    assert resp_resume.status_code == 401


def test_key_comparison_is_constant_time():
    with patch("src.api.auth.hmac.compare_digest", wraps=hmac.compare_digest) as spy:
        app = create_v2_app(_make_profile())
        with TestClient(app) as client:
            resp = client.get("/api/v1/state", headers={"X-API-Key": TEST_RAW_KEY})
            assert resp.status_code == 200
    assert spy.called


def test_keys_never_stored_or_compared_as_plaintext():
    profile = _make_profile()
    configure_api_keys(profile)
    assert TEST_RAW_KEY not in auth_mod._client_keys
    assert TEST_KEY_HASH in auth_mod._client_keys
    for stored_hash in auth_mod._client_keys:
        assert len(stored_hash) == 64
        assert stored_hash == stored_hash.lower()
        int(stored_hash, 16)  # raises ValueError if not valid hex


def test_config_loader_env_var_seeds_api_keys(monkeypatch):
    from src.config.loader import ConfigLoader

    monkeypatch.setenv("RPG_API_KEY_HASHES", f"{TEST_CLIENT_ID}:{TEST_KEY_HASH}")
    profile = ConfigLoader.load_profile(profile_name="cli_default")
    assert profile.api_key_hashes == f"{TEST_CLIENT_ID}:{TEST_KEY_HASH}"

    app = create_v2_app(profile)
    with TestClient(app) as client:
        resp = client.get("/api/v1/state", headers={"X-API-Key": TEST_RAW_KEY})
        assert resp.status_code == 200


def test_client_identity_exposes_client_id():
    ci = ClientIdentity(client_id="abc")
    assert ci.client_id == "abc"
    assert {ci: 1}[ci] == 1


def test_websocket_route_requires_valid_key_and_closes_cleanly():
    app = create_v2_app(_make_profile())
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/ws"):
                pass


def test_websocket_route_accepts_valid_key_via_query_param():
    app = create_v2_app(_make_profile())
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/ws?key={TEST_RAW_KEY}"):
            pass


def test_only_dashboard_and_websocket_routes_use_weaker_auth_channel():
    """Anti-drift guard for Decision 3/4 (plan.md): require_api_key_header_or_query
    and require_api_key_ws must be scoped to exactly the 3 dashboard routes and the
    3 WebSocket routes -- never silently reused on an ordinary protected route.
    Inspects the real route table via FastAPI's own dependant introspection rather
    than trusting source-reading, so a future accidental broadening of the weaker
    auth channel fails this test."""
    app = create_v2_app(_make_profile())

    weak_dependency_names = {"require_api_key_header_or_query", "require_api_key_ws"}
    found_weak_paths = set()
    found_strict_paths = set()

    for route in app.routes:
        dependant = getattr(route, "dependant", None)
        if dependant is None:
            continue
        dep_names = {
            getattr(dep.call, "__name__", None)
            for dep in dependant.dependencies
            if dep.call is not None
        }
        path = getattr(route, "path", None)
        if dep_names & weak_dependency_names:
            found_weak_paths.add(path)
        elif "require_api_key" in dep_names:
            found_strict_paths.add(path)

    assert found_weak_paths == _DASHBOARD_AND_WS_PATHS
    assert found_weak_paths.isdisjoint(found_strict_paths)
