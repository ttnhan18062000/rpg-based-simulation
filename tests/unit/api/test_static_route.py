"""Unit tests for GET /api/v1/static endpoint.

Test plan reference: staging_artifacts/TCK-20260821-REST-MAP-STATIC-STATS/test_plan.md
Ticket: TCK-20260821-REST-MAP-STATIC-STATS
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api.presenters.state_presenter import StatePresenter
from src.core.state import AuthoritativeState, BuildingState


def _make_state(**overrides) -> AuthoritativeState:
    defaults = dict(tick=0, seed=1)
    defaults.update(overrides)
    return AuthoritativeState(**defaults)


def _make_app_with_state(state: Optional[AuthoritativeState]):
    """Build a minimal FastAPI app with the static route, mocking the engine manager."""
    from fastapi import FastAPI
    from src.api.routes.static import router
    import src.api.dependencies as deps

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    mock_manager = MagicMock()
    mock_manager.latest_state = state
    deps.set_engine_manager(mock_manager)

    return app


def test_static_endpoint_returns_200_with_static_data_shape():
    building = BuildingState(id=1, kind="SHOP", position=(2.0, 3.0))
    state = _make_state(buildings={1: building})
    app = _make_app_with_state(state)

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/v1/static")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"buildings", "resource_nodes", "treasure_chests", "regions"}
    assert body == StatePresenter.present_static(state)


def test_static_endpoint_returns_503_when_state_none():
    app = _make_app_with_state(state=None)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/static")
    assert response.status_code == 503
