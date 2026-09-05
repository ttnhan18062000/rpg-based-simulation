"""Unit tests for GET /api/v1/metadata/* endpoints and MetadataPresenter.

Ticket: TCK-20260825-METADATA-API-BACKEND-MISSING
Mirrors tests/api/test_manifest_api.py's real-catalog / mocked-DI-singleton pattern.
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.content.repository import CatalogRepository
from src.api.presenters.metadata_presenter import MetadataPresenter


def _catalog() -> CatalogRepository:
    catalog = CatalogRepository()
    catalog.load_all()
    return catalog


def _make_app_with(catalog: Optional[CatalogRepository]):
    from fastapi import FastAPI
    from src.api.routes.metadata import router
    import src.api.dependencies as deps

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    deps.set_catalog_repository(catalog)
    return app


# ---------------------------------------------------------------------------
# Route-level: all 8 routes return 200 with real catalog, 503 without
# ---------------------------------------------------------------------------

_ROUTES = ["/enums", "/items", "/classes", "/traits", "/attributes", "/buildings", "/resources", "/recipes"]


def test_all_8_routes_return_200_with_real_catalog():
    app = _make_app_with(_catalog())
    client = TestClient(app, raise_server_exceptions=True)
    for path in _ROUTES:
        response = client.get(f"/api/v1/metadata{path}")
        assert response.status_code == 200, f"{path} failed: {response.text}"


def test_catalog_backed_routes_return_503_when_catalog_not_ready():
    # /classes has no _catalog() dependency (CLASS_REGISTRY is a static Python dict, not
    # catalog-backed) -- excluded here, covered separately below.
    app = _make_app_with(None)
    client = TestClient(app, raise_server_exceptions=False)
    for path in ["/enums", "/items", "/traits", "/attributes", "/buildings", "/resources", "/recipes"]:
        response = client.get(f"/api/v1/metadata{path}")
        assert response.status_code == 503, f"{path} should 503 without a catalog"


def test_classes_route_does_not_require_catalog():
    app = _make_app_with(None)
    client = TestClient(app, raise_server_exceptions=True)
    response = client.get("/api/v1/metadata/classes")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Response-shape compliance with frontend/src/types/metadata.ts (all 8 top-level keys present)
# ---------------------------------------------------------------------------

def test_enums_response_has_all_11_documented_keys():
    result = MetadataPresenter.present_enums(_catalog())
    assert set(result.keys()) == {
        "materials", "ai_states", "tiers", "rarities", "item_types", "damage_types",
        "elements", "entity_roles", "factions", "faction_relations", "entity_kinds",
    }


def test_classes_response_has_all_6_documented_keys():
    result = MetadataPresenter.present_classes()
    assert set(result.keys()) == {
        "classes", "skills", "race_skills", "scaling_grades", "mastery_tiers", "skill_targets",
    }


# ---------------------------------------------------------------------------
# Real-data domains: prove the response reflects real catalog content, not fabricated data
# ---------------------------------------------------------------------------

def test_materials_ids_come_from_real_catalog_not_fabricated():
    catalog = _catalog()
    result = MetadataPresenter.present_enums(catalog)
    assert len(result["materials"]) == len(catalog.materials)
    real_names = {(m.display_name or m.id) for m in catalog.materials.values()}
    assert {m["name"] for m in result["materials"]} == real_names


def test_materials_walkable_is_defaulted_false_not_fabricated_per_entry():
    result = MetadataPresenter.present_enums(_catalog())
    assert all(m["walkable"] is False for m in result["materials"])


def test_rarities_derived_from_real_items_distinct_values():
    catalog = _catalog()
    result = MetadataPresenter.present_enums(catalog)
    real_rarities = {it.rarity for it in catalog.items.values()}
    assert {r["name"] for r in result["rarities"]} == real_rarities


def test_item_types_derived_from_real_items_first_category():
    catalog = _catalog()
    result = MetadataPresenter.present_enums(catalog)
    real_types = {it.categories[0] for it in catalog.items.values() if it.categories}
    assert {t["name"] for t in result["item_types"]} == real_types


def test_ai_states_tiers_damage_types_are_empty_not_fabricated():
    result = MetadataPresenter.present_enums(_catalog())
    assert result["ai_states"] == []
    assert result["tiers"] == []
    assert result["damage_types"] == []


def test_entity_roles_from_real_enum_not_fabricated():
    from src.core.enums import EntityRole
    result = MetadataPresenter.present_enums(_catalog())
    assert len(result["entity_roles"]) == len(list(EntityRole))
    assert {r["name"] for r in result["entity_roles"]} == {role.name.title() for role in EntityRole}


def test_entity_kinds_matches_real_catalog_entity_archetypes():
    catalog = _catalog()
    result = MetadataPresenter.present_enums(catalog)
    assert len(result["entity_kinds"]) == len(catalog.entity_archetypes)
    real_kinds = {a.id for a in catalog.entity_archetypes.values()}
    assert {k["kind"] for k in result["entity_kinds"]} == real_kinds


def test_faction_relations_reference_valid_faction_indices():
    catalog = _catalog()
    result = MetadataPresenter.present_enums(catalog)
    valid_indices = {f["id"] for f in result["factions"]}
    for rel in result["faction_relations"]:
        assert rel["faction_a"] in valid_indices
        assert rel["faction_b"] in valid_indices


def test_items_real_fields_match_catalog_unbacked_fields_are_zero():
    catalog = _catalog()
    result = MetadataPresenter.present_items(catalog)
    assert len(result["items"]) == len(catalog.items)
    by_id = {it["item_id"]: it for it in result["items"]}
    for real_item in catalog.items.values():
        presented = by_id[real_item.id]
        assert presented["name"] == (real_item.display_name or real_item.id)
        assert presented["rarity"] == real_item.rarity
        assert presented["gold_value"] == real_item.base_value
        assert presented["atk_bonus"] == 0.0
        assert presented["damage_type"] == ""


def test_classes_real_fields_match_registry_unbacked_fields_are_defaulted():
    from src.core.classes import CLASS_REGISTRY
    result = MetadataPresenter.present_classes()
    assert len(result["classes"]) == len(CLASS_REGISTRY)
    by_id = {c["id"]: c for c in result["classes"]}
    for real_class in CLASS_REGISTRY.values():
        presented = by_id[real_class.id]
        assert presented["name"] == real_class.name
        assert presented["breakthrough"] is None
        assert presented["attr_bonuses"] == {"str": 0, "agi": 0, "vit": 0, "int": 0, "spi": 0, "wis": 0, "end": 0, "per": 0, "cha": 0}
    assert result["skills"] == []
    assert result["scaling_grades"] == []


def test_traits_ids_are_stable_across_calls():
    """trait_type is a synthesized index (no real numeric id exists) -- must be deterministic
    across repeated calls against the same catalog content, matching terrain_code_map's own
    stability contract."""
    catalog = _catalog()
    result_a = MetadataPresenter.present_traits(catalog)
    result_b = MetadataPresenter.present_traits(catalog)
    assert result_a == result_b


def test_attributes_real_fields_from_catalog():
    catalog = _catalog()
    result = MetadataPresenter.present_attributes(catalog)
    assert len(result["attributes"]) == len(catalog.attributes)
    real_keys = {a.id for a in catalog.attributes.values()}
    assert {a["key"] for a in result["attributes"]} == real_keys


def test_buildings_real_fields_from_catalog():
    catalog = _catalog()
    result = MetadataPresenter.present_buildings(catalog)
    assert len(result["building_types"]) == len(catalog.buildings)


def test_resources_real_fields_from_catalog():
    catalog = _catalog()
    result = MetadataPresenter.present_resources(catalog)
    assert len(result["resource_types"]) == len(catalog.resources)
    by_type = {r["resource_type"]: r for r in result["resource_types"]}
    for real_resource in catalog.resources.values():
        key = real_resource.resource_type or real_resource.id
        presented = by_type[key]
        assert presented["max_harvests"] == real_resource.default_charges
        assert presented["harvest_ticks"] == real_resource.required_ticks
        assert presented["respawn_cooldown"] == 0


def test_recipes_real_fields_from_catalog_registries_recipe_registry_source():
    catalog = _catalog()
    result = MetadataPresenter.present_recipes(catalog)
    assert len(result["recipes"]) == len(catalog.recipes)
    by_id = {r["recipe_id"]: r for r in result["recipes"]}
    for real_recipe in catalog.recipes.values():
        presented = by_id[real_recipe.id]
        assert presented["gold_cost"] == real_recipe.gold_cost
        assert presented["materials"] == dict(real_recipe.ingredients)
        assert presented["output_item"] in real_recipe.outputs


def test_presenter_returns_plain_dicts_not_raw_domain_models():
    catalog = _catalog()
    for result in (
        MetadataPresenter.present_enums(catalog),
        MetadataPresenter.present_items(catalog),
        MetadataPresenter.present_classes(),
        MetadataPresenter.present_traits(catalog),
        MetadataPresenter.present_attributes(catalog),
        MetadataPresenter.present_buildings(catalog),
        MetadataPresenter.present_resources(catalog),
        MetadataPresenter.present_recipes(catalog),
    ):
        assert isinstance(result, dict)
