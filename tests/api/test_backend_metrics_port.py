"""The real API app and the internal metrics port (issue #622, R1).

The registry the manager holds is served on the internal port without auth, while `/metrics` on the API port stays behind the API key
(401 without one). The internal port belongs to the lifespan: the app mounts no route for it and the port is released at shutdown.
"""
from __future__ import annotations

import hashlib
import urllib.request

from fastapi.testclient import TestClient

from src.api.dependencies import get_engine_manager
from src.api.metrics_port import METRICS_PORT_ENV
from src.api.server import create_v2_app
from src.config.profiles import PROD_SMALL

KEY = "metrics-port-probe"


def _app():
    profile = PROD_SMALL.model_copy(update={"api_key_hashes": "probe:" + hashlib.sha256(KEY.encode()).hexdigest()})
    return create_v2_app(profile, seed=42, world_id="sandbox_world")


def test_the_internal_port_serves_the_engine_registry_while_the_api_metrics_route_stays_authenticated(monkeypatch):
    monkeypatch.setenv(METRICS_PORT_ENV, "0")  # a free port; the default 9109 may be taken on a developer machine
    app = _app()
    with TestClient(app) as client:
        assert client.get("/metrics").status_code == 401  # the API port is unchanged: no key, no metrics
        assert client.get("/metrics", headers={"X-API-Key": KEY}).status_code == 200
        handle = get_engine_manager().metrics_port
        assert handle is not None
        with urllib.request.urlopen(f"http://127.0.0.1:{handle.port}/metrics", timeout=5) as response:  # no credential
            internal = response.read().decode()
    assert "sim_" in internal


def test_the_api_app_mounts_no_route_for_the_internal_port_and_it_is_released_at_shutdown(monkeypatch):
    monkeypatch.setenv(METRICS_PORT_ENV, "0")
    app = _app()
    paths_before = sorted(getattr(r, "path", "") for r in app.routes)
    with TestClient(app):
        port = get_engine_manager().metrics_port.port
        assert sorted(getattr(r, "path", "") for r in app.routes) == paths_before
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=2)
    except OSError:
        released = True
    else:
        released = False
    assert released, "the internal metrics port is still serving after the app shut down"
