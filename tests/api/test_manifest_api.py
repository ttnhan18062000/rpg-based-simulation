"""Unit tests for GET /api/v1/manifest endpoint and ManifestPresenter.

Test plan reference: staging_artifacts/TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT/test_plan.md
Ticket: TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.content.repository import CatalogRepository
from src.core.state import AuthoritativeState
from src.api.presenters.manifest_presenter import ManifestPresenter, MANIFEST_PROTOCOL_VERSION


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _catalog() -> CatalogRepository:
    catalog = CatalogRepository()
    catalog.load_all()
    return catalog


def _state(**overrides) -> AuthoritativeState:
    defaults = dict(tick=0, seed=1)
    defaults.update(overrides)
    return AuthoritativeState(**defaults)


def _make_app_with(state: Optional[AuthoritativeState], catalog: Optional[CatalogRepository]):
    """Build a minimal FastAPI app with the manifest route, mocking the DI singletons."""
    from fastapi import FastAPI
    from src.api.routes.manifest import router
    import src.api.dependencies as deps

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    mock_manager = MagicMock()
    mock_manager.latest_state = state
    deps.set_engine_manager(mock_manager)
    deps.set_catalog_repository(catalog)

    return app


# ---------------------------------------------------------------------------
# Route-level tests
# ---------------------------------------------------------------------------

def test_manifest_returns_separate_protocol_and_dictionary_version():
    catalog = _catalog()
    state = _state()
    app = _make_app_with(state, catalog)

    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/v1/manifest")

    assert response.status_code == 200
    body = response.json()
    assert "protocol_version" in body
    assert "dictionary_version" in body
    assert body["protocol_version"] == MANIFEST_PROTOCOL_VERSION
    assert body["dictionary_version"] == catalog.fingerprint
    assert body["protocol_version"] != body["dictionary_version"]


def test_manifest_returns_503_when_catalog_not_ready():
    app = _make_app_with(state=_state(), catalog=None)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/manifest")
    assert response.status_code == 503


def test_manifest_degrades_gracefully_when_state_is_none():
    """No live state yet: terrain_types is empty, but entity_kinds/building_types/versions are still valid."""
    catalog = _catalog()
    app = _make_app_with(state=None, catalog=catalog)
    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/v1/manifest")

    assert response.status_code == 200
    body = response.json()
    assert body["terrain_types"] == {}
    assert body["entity_kinds"]
    assert body["building_types"]


# ---------------------------------------------------------------------------
# Presenter-level tests
# ---------------------------------------------------------------------------

def test_manifest_entity_kinds_and_building_types_from_catalog():
    catalog = _catalog()
    result = ManifestPresenter.present_manifest(_state(), catalog)

    assert result["entity_kinds"] == {
        def_id: (d.display_name or d.id) for def_id, d in catalog.entity_archetypes.items()
    }
    assert result["building_types"] == {
        def_id: (d.display_name or d.id) for def_id, d in catalog.buildings.items()
    }
    assert result["entity_kinds"], "expected non-empty entity_archetypes catalog"
    assert result["building_types"], "expected non-empty buildings catalog"


def test_manifest_dictionary_version_changes_with_catalog_fingerprint():
    catalog_a = _catalog()
    result_a = ManifestPresenter.present_manifest(_state(), catalog_a)
    assert result_a["dictionary_version"] == catalog_a.fingerprint

    # A second, independently-loaded catalog over the same content has the same fingerprint...
    catalog_b = _catalog()
    result_b = ManifestPresenter.present_manifest(_state(), catalog_b)
    assert result_b["dictionary_version"] == catalog_b.fingerprint
    assert result_a["dictionary_version"] == result_b["dictionary_version"]

    # ...but protocol_version stays fixed regardless of catalog content.
    assert result_a["protocol_version"] == result_b["protocol_version"] == MANIFEST_PROTOCOL_VERSION


def test_manifest_location_types_decision_documented_behavior():
    """location_types is dropped entirely (no empty placeholder) -- see manifest_presenter.py comment."""
    catalog = _catalog()
    result = ManifestPresenter.present_manifest(_state(), catalog)
    assert "location_types" not in result


def test_manifest_terrain_types_live_from_catalog_repository():
    catalog = _catalog()
    terrain = {(0, 0): "plain", (1, 0): "forest"}
    result = ManifestPresenter.present_manifest(_state(terrain=terrain), catalog)

    assert result["terrain_types"]["0"] == "Forest"
    assert result["terrain_types"]["1"] == "Plain"


def test_manifest_terrain_types_id_space_matches_present_map_grid():
    """terrain_types must be keyed by the exact same int codes present_map's RLE grid emits."""
    from src.api.presenters.state_presenter import StatePresenter

    catalog = _catalog()
    terrain = {
        (0, 0): "PLAIN", (1, 0): "PLAIN", (2, 0): "GRASS",
        (0, 1): "GRASS", (1, 1): "GRASS", (2, 1): "GRASS",
    }
    state = _state(terrain=terrain)
    code_map = StatePresenter.terrain_code_map(state)
    result = ManifestPresenter.present_manifest(state, catalog)

    # Both codes present_map's grid actually emits must be represented in terrain_types.
    assert set(result["terrain_types"].keys()) == {str(c) for c in code_map.values()}

    # PLAIN has a real lowercase catalog entry ("plain" -> display_name "Plain") -- resolved
    # via the case-insensitive .lower() catalog lookup, NOT the title()-fallback.
    plain_code = str(code_map["PLAIN"])
    assert result["terrain_types"][plain_code] == "Plain"

    # GRASS has no catalog entry at all (no "grass" id in data/content/world/terrain.yaml) --
    # resolved via the title()-cased fallback, a separate code path from PLAIN's above.
    grass_code = str(code_map["GRASS"])
    assert result["terrain_types"][grass_code] == "Grass"


def test_manifest_terrain_types_uncataloged_default_uses_title_fallback():
    catalog = _catalog()
    assert "grass" not in catalog.terrain, "GRASS must remain uncataloged for this test to be meaningful"
    display = ManifestPresenter._terrain_display_name("GRASS", catalog)
    assert display == "Grass"


def test_manifest_terrain_types_cataloged_value_resolves_case_insensitively():
    catalog = _catalog()
    assert "plain" in catalog.terrain, "PLAIN must be cataloged for this test to be meaningful"
    display = ManifestPresenter._terrain_display_name("PLAIN", catalog)
    assert display == "Plain"


def test_manifest_presenter_returns_plain_dicts_not_raw_domain_models():
    catalog = _catalog()
    result = ManifestPresenter.present_manifest(_state(terrain={(0, 0): "plain"}), catalog)

    assert isinstance(result, dict)
    for key in ("terrain_types", "entity_kinds", "building_types"):
        assert isinstance(result[key], dict)
        for value in result[key].values():
            assert isinstance(value, str)
