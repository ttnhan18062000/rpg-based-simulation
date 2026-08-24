"""Unit tests for GET /api/v1/stats endpoint and StatePresenter.present_stats.

Test plan reference: staging_artifacts/TCK-20260821-REST-MAP-STATIC-STATS/test_plan.md
Ticket: TCK-20260821-REST-MAP-STATIC-STATS
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState


def _make_entity(eid: int, alive: bool = True):
    return (
        V2EntityBuilder(eid)
        .kind("goblin")
        .location(0.0, 0.0)
        .combat(hp=10, max_hp=10, atk=1, def_stat=1, attack_range=1, alive=alive, readiness=100.0)
        .inventory(gold=0)
        .build()
    )


def _make_state(entities: Optional[dict] = None, tick: int = 0) -> AuthoritativeState:
    return AuthoritativeState(tick=tick, seed=1, entities=entities or {})


def _make_app_with_manager(mock_manager):
    from fastapi import FastAPI
    from src.api.routes.stats import router
    import src.api.dependencies as deps

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    deps.set_engine_manager(mock_manager)
    return app


def _make_mock_manager(state, total_spawned=0, total_deaths=0, is_running=True, is_paused=False):
    mock_manager = MagicMock()
    mock_manager.latest_state = state
    mock_manager.total_spawned = total_spawned
    mock_manager.total_deaths = total_deaths
    mock_manager.is_running = is_running
    mock_manager.is_paused = is_paused
    return mock_manager


def test_stats_endpoint_returns_200_with_expected_fields():
    entity = _make_entity(1)
    state = _make_state({1: entity}, tick=100)
    manager = _make_mock_manager(state, total_spawned=5, total_deaths=2, is_running=True, is_paused=False)
    app = _make_app_with_manager(manager)

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/v1/stats")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "tick", "world_day", "alive_count", "total_spawned", "total_deaths", "running", "paused",
    }
    assert isinstance(body["tick"], int)
    assert isinstance(body["world_day"], int)
    assert isinstance(body["alive_count"], int)
    assert isinstance(body["total_spawned"], int)
    assert isinstance(body["total_deaths"], int)
    assert isinstance(body["running"], bool)
    assert isinstance(body["paused"], bool)
    assert body["tick"] == 100
    assert body["total_spawned"] == 5
    assert body["total_deaths"] == 2
    assert body["running"] is True
    assert body["paused"] is False


def test_stats_endpoint_returns_503_when_state_none():
    manager = _make_mock_manager(state=None)
    app = _make_app_with_manager(manager)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/stats")
    assert response.status_code == 503


def test_stats_alive_count_excludes_dead_entities():
    alive = _make_entity(1, alive=True)
    dead = _make_entity(2, alive=False)
    state = _make_state({1: alive, 2: dead}, tick=10)
    manager = _make_mock_manager(state)
    app = _make_app_with_manager(manager)

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/v1/stats")

    assert response.status_code == 200
    assert response.json()["alive_count"] == 1


def test_stats_world_day_derivation():
    # tick=4800 distinguishes //2400 (=2, correct) from //100 (=48, wrong).
    state = _make_state(tick=4800)
    manager = _make_mock_manager(state)
    app = _make_app_with_manager(manager)

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/v1/stats")

    assert response.status_code == 200
    assert response.json()["world_day"] == 2
