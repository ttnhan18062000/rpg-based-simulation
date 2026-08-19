"""
Integration test for `/health`'s liveness-aware route wiring
(TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC).

Uses an in-process TestClient (no subprocess) to verify the route actually calls
V2EngineManager.get_health_status() and maps the healthy case to HTTP 200.
"""
from fastapi.testclient import TestClient

from src.api.server import create_v2_app
from src.config.profiles import PROD_DEFAULT


def test_health_route_wiring_returns_ok_for_healthy_engine():
    app = create_v2_app(PROD_DEFAULT)
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "v2"
        assert "engine" in data
        assert data["engine"]["thread_alive"] is True
