"""Unit tests for GET /api/v1/map endpoint.

Test plan reference: staging_artifacts/TCK-20260821-REST-MAP-STATIC-STATS/test_plan.md
Ticket: TCK-20260821-REST-MAP-STATIC-STATS
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.core.state import AuthoritativeState


def _make_state(terrain: Optional[dict] = None, tick: int = 0) -> AuthoritativeState:
    return AuthoritativeState(tick=tick, seed=1, terrain=terrain or {})


def _make_app_with_state(state: Optional[AuthoritativeState]):
    """Build a minimal FastAPI app with the map route, mocking the engine manager."""
    from fastapi import FastAPI
    from src.api.routes.map import router
    import src.api.dependencies as deps

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    mock_manager = MagicMock()
    mock_manager.latest_state = state
    deps.set_engine_manager(mock_manager)

    return app


def test_map_endpoint_returns_200_with_rle_shape():
    terrain = {(0, 0): "PLAIN", (1, 0): "GRASS"}
    state = _make_state(terrain=terrain)
    app = _make_app_with_state(state)

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/v1/map")

    assert response.status_code == 200
    body = response.json()
    assert body["width"] == 2
    assert body["height"] == 1
    assert isinstance(body["grid"], list)
    assert all(isinstance(v, int) for v in body["grid"])


def test_map_endpoint_returns_503_when_state_none():
    app = _make_app_with_state(state=None)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/map")
    assert response.status_code == 503
