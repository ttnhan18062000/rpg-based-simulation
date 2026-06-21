"""Unit tests for GET /api/v1/economy/health endpoint and EconomyPresenter.

Test plan reference: staging_artifacts/TCK-20260619-E33B-ALERTS-REST/test_plan.md
Ticket: TCK-20260619-E33B-ALERTS-REST
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.api.presenters.economy import EconomyPresenter
from src.economy.health_monitor import EconomyHealthMonitor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entity(eid: int, gold: int, alive: bool = True, region_id: Optional[str] = None):
    from dataclasses import replace as dc_replace
    builder = (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(hp=100, max_hp=100, atk=5, def_stat=5,
                attack_range=1, alive=alive, readiness=100.0)
        .inventory(gold=gold)
    )
    entity = builder.build()
    # region_id lives on NavigationComponent — replace navigation to set it
    if region_id is not None:
        new_nav = dc_replace(entity.navigation, region_id=region_id)
        object.__setattr__(entity, "navigation", new_nav)
    return entity


def _make_state(entities: dict, tick: int = 100) -> AuthoritativeState:
    return AuthoritativeState(tick=tick, seed=42, entities=entities)


def _make_app_with_state(state: Optional[AuthoritativeState]):
    """Build a minimal FastAPI app with economy route, mocking the engine manager."""
    from fastapi import FastAPI
    from src.api.routes.economy import router
    import src.api.dependencies as deps

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    mock_manager = MagicMock()
    mock_manager.latest_state = state
    deps.set_engine_manager(mock_manager)

    return app


# ---------------------------------------------------------------------------
# TC-B06: GET /api/v1/economy/health returns 200 with correct shape
# ---------------------------------------------------------------------------

def test_economy_health_endpoint_returns_200():
    """GET /api/v1/economy/health returns 200 with tick and regions keys."""
    entity = _make_entity(1, gold=100)
    state = _make_state({1: entity}, tick=200)
    app = _make_app_with_state(state)

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/v1/economy/health")

    assert response.status_code == 200
    body = response.json()
    assert "tick" in body
    assert "regions" in body
    assert body["tick"] == 200


# ---------------------------------------------------------------------------
# TC-B07: Response schema has expected per-region structure
# ---------------------------------------------------------------------------

def test_economy_health_response_schema():
    """Response has tick: int, regions: dict with per-region gini/velocity/alert."""
    entity_a = _make_entity(1, gold=50)
    entity_b = _make_entity(2, gold=200)
    state = _make_state({1: entity_a, 2: entity_b}, tick=300)
    app = _make_app_with_state(state)

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/v1/economy/health")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["tick"], int)
    assert isinstance(body["regions"], dict)
    # Both entities have no region_id set → grouped under "global"
    assert "global" in body["regions"]
    region = body["regions"]["global"]
    assert "gini" in region
    assert "transaction_velocity" in region
    assert "alert" in region
    assert isinstance(region["gini"], float)
    assert isinstance(region["transaction_velocity"], float)
    # alert is null or a string
    assert region["alert"] is None or isinstance(region["alert"], str)


# ---------------------------------------------------------------------------
# TC-B08: EconomyPresenter shapes correctly — plain dict, no raw state
# ---------------------------------------------------------------------------

def test_economy_presenter_shapes_correctly():
    """EconomyPresenter.present_health() returns a plain dict, no raw domain objects."""
    entity = _make_entity(1, gold=100)
    state = _make_state({1: entity})

    result = EconomyPresenter.present_health(state)

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "tick" in result
    assert "regions" in result
    # Verify no Pydantic models or AuthoritativeState objects leak through
    for key, val in result.items():
        assert not hasattr(val, "model_dump"), f"Field '{key}' is a Pydantic model — presenter must return plain dicts"
    for region_key, region_val in result["regions"].items():
        assert isinstance(region_val, dict)


# ---------------------------------------------------------------------------
# TC-B09: Presenter correctly propagates INFLATION_SPIRAL alert for high Gini
# ---------------------------------------------------------------------------

def test_presenter_sets_inflation_spiral_for_high_gini():
    """When Gini > 0.7, presenter includes INFLATION_SPIRAL alert in region."""
    # Unequal gold: one rich entity vs many poor → high gini
    entities = {
        1: _make_entity(1, gold=10000),
        2: _make_entity(2, gold=1),
        3: _make_entity(3, gold=1),
        4: _make_entity(4, gold=1),
    }
    state = _make_state(entities, tick=100)
    result = EconomyPresenter.present_health(state)

    assert "global" in result["regions"]
    region = result["regions"]["global"]
    assert region["gini"] > EconomyHealthMonitor.INFLATION_SPIRAL_GINI_THRESHOLD
    assert region["alert"] in ("INFLATION_SPIRAL", "GOLD_HOARDING")


# ---------------------------------------------------------------------------
# TC-B10: 503 when engine state is None
# ---------------------------------------------------------------------------

def test_economy_health_returns_503_when_no_state():
    """GET /api/v1/economy/health returns 503 when engine has no state yet."""
    app = _make_app_with_state(state=None)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/economy/health")
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# TC-B11: Dead entities excluded from region Gini
# ---------------------------------------------------------------------------

def test_presenter_excludes_dead_entities():
    """Dead entities must not contribute to per-region Gini computation."""
    alive = _make_entity(1, gold=100, alive=True)
    dead  = _make_entity(2, gold=99999, alive=False)
    state = _make_state({1: alive, 2: dead}, tick=100)

    result = EconomyPresenter.present_health(state)
    # Only one alive entity → Gini of single entity = 0.0
    assert result["regions"]["global"]["gini"] == pytest.approx(0.0, abs=1e-9)
