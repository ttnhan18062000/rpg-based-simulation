"""
Real, in-process `TestClient`-based tests against the fully-wired `create_v2_app()` app,
following `tests/api/test_api_key_auth.py`'s established pattern -- real response status/bodies
asserted, no subprocess.

TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT and
TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION: both subsystems are
fully built and tested but have no real production data source. Gated off by default
(`RuntimeProfile.enable_behavior_analytics_api`/`enable_campaign_chronicle_api`) rather than
removed or wired, per peer-routed decision. This file proves the gate itself, not the underlying
route logic (already covered by test_phase27_behavior_query_api.py, test_campaign_history_api.py,
test_chronicle_api.py, which call the handlers directly and are unaffected by router registration
either way).
"""
from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient

from src.api.server import create_v2_app
from src.config.profiles import RuntimeProfile, HardwareClass

TEST_CLIENT_ID = "gating-test-client"
TEST_RAW_KEY = "gating-test-raw-key-12345"
TEST_KEY_HASH = hashlib.sha256(TEST_RAW_KEY.encode("utf-8")).hexdigest()
AUTH_HEADERS = {"X-API-Key": TEST_RAW_KEY}


def _make_profile(**overrides):
    base = dict(
        name="inert-route-gating-test", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=256, max_cpu_percent=100.0, max_worker_count=0,
        max_queue_depth=100, max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0, max_tick_budget_ms=200.0,
        api_key_hashes=f"{TEST_CLIENT_ID}:{TEST_KEY_HASH}",
    )
    base.update(overrides)
    return RuntimeProfile(**base)


def test_behavior_analytics_api_disabled_by_default():
    profile = _make_profile()
    assert profile.enable_behavior_analytics_api is False
    client = TestClient(create_v2_app(profile))
    resp = client.get("/api/v1/behavior/events", params={"run_id": "run_1"})
    # Route genuinely not mounted -- FastAPI's own generic "no matching route" 404, not the
    # handler's own domain-level response.
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Not Found"}


def test_behavior_analytics_api_reachable_when_enabled():
    profile = _make_profile(enable_behavior_analytics_api=True)
    client = TestClient(create_v2_app(profile))
    resp = client.get("/api/v1/behavior/events", params={"run_id": "run_1"}, headers=AUTH_HEADERS)
    # Real route reached: 200 with an empty list (no data source populated it), not a 404 --
    # proves the gate controls registration, not the handler's own behavior.
    assert resp.status_code == 200
    assert resp.json() == []


def test_campaign_chronicle_api_disabled_by_default():
    profile = _make_profile()
    assert profile.enable_campaign_chronicle_api is False
    client = TestClient(create_v2_app(profile))

    history_resp = client.get("/api/v1/campaigns/camp_1/history")
    assert history_resp.status_code == 404
    assert history_resp.json() == {"detail": "Not Found"}

    chronicle_resp = client.get("/api/v1/chronicle/camp_1")
    assert chronicle_resp.status_code == 404
    assert chronicle_resp.json() == {"detail": "Not Found"}


def test_campaign_chronicle_api_reachable_when_enabled():
    profile = _make_profile(enable_campaign_chronicle_api=True)
    client = TestClient(create_v2_app(profile))

    # Route reached, but the specific campaign_id isn't registered -- the handler's own real
    # domain-level 404, distinguishable from the "route not mounted" 404 above by its message.
    history_resp = client.get("/api/v1/campaigns/camp_1/history", headers=AUTH_HEADERS)
    assert history_resp.status_code == 404
    assert history_resp.json() != {"detail": "Not Found"}

    chronicle_resp = client.get("/api/v1/chronicle/camp_1", headers=AUTH_HEADERS)
    assert chronicle_resp.status_code == 404
    assert chronicle_resp.json() != {"detail": "Not Found"}


def test_gates_are_independent():
    """Enabling one gate does not accidentally enable the other."""
    profile = _make_profile(enable_behavior_analytics_api=True)
    client = TestClient(create_v2_app(profile))

    behavior_resp = client.get("/api/v1/behavior/events", params={"run_id": "run_1"}, headers=AUTH_HEADERS)
    assert behavior_resp.status_code == 200

    chronicle_resp = client.get("/api/v1/chronicle/camp_1", headers=AUTH_HEADERS)
    assert chronicle_resp.status_code == 404
    assert chronicle_resp.json() == {"detail": "Not Found"}


def test_unrelated_route_unaffected_by_default_gating():
    """A real, always-live route (search.py, explicitly left ungated per
    TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE) stays reachable
    regardless of the two gates above."""
    profile = _make_profile()
    client = TestClient(create_v2_app(profile))
    resp = client.get("/api/v1/observability/search/runs", headers=AUTH_HEADERS)
    assert resp.status_code == 200
