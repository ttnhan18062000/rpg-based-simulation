"""Tests for AdapterHeuristicUsage emission from adapter classes."""
from __future__ import annotations

import os
import tempfile
import yaml
import pytest

from src.core.modes import RuntimeContentMode, AdapterHeuristicUsage
from src.core.registries import (
    AdapterError,
    AdapterProjectionResult,
    CatalogToItemRegistryAdapter,
    CatalogToServiceRegistryAdapter,
    CatalogToResourceRegistryAdapter,
    seed_phase1_content,
)


# ── minimal catalog repo helpers ────────────────────────────────────────────

def _make_item(item_id: str, categories: list, **extra) -> dict:
    return {
        "id": item_id,
        "schema_version": "itemdefinition.v1",
        "categories": categories,
        "rarity": "COMMON",
        "base_value": 5.0,
        **extra,
    }


def _make_service(s_id: str, **extra) -> dict:
    return {
        "id": s_id,
        "schema_version": "servicedefinition.v1",
        "provided_items": [],
        **extra,
    }


def _make_resource(res_id: str, resource_type: str = "wood", **extra) -> dict:
    return {
        "id": res_id,
        "schema_version": "resourcedefinition.v1",
        "resource_type": resource_type,
        **extra,
    }


def _build_repo(tmp_dir: str, items=(), services=(), resources=()):
    from src.content.repository import CatalogRepository
    os.makedirs(os.path.join(tmp_dir, "world"), exist_ok=True)
    os.makedirs(os.path.join(tmp_dir, "compatibility"), exist_ok=True)
    os.makedirs(os.path.join(tmp_dir, "entities"), exist_ok=True)
    with open(os.path.join(tmp_dir, "world", "items.yaml"), "w") as f:
        yaml.dump(list(items), f)
    with open(os.path.join(tmp_dir, "world", "services.yaml"), "w") as f:
        yaml.dump(list(services), f)
    with open(os.path.join(tmp_dir, "world", "resources.yaml"), "w") as f:
        yaml.dump(list(resources), f)
    for fname in ["recipes.yaml"]:
        with open(os.path.join(tmp_dir, "world", fname), "w") as f:
            yaml.dump([], f)
    with open(os.path.join(tmp_dir, "world", "runtime_regions.yaml"), "w") as f:
        yaml.dump([{"id": "hometown", "schema_version": "runtimeregiondefinition.v1", "danger_level": 0, "tags": ["safe"]}], f)
    with open(os.path.join(tmp_dir, "compatibility", "legacy_enemy_projection.yaml"), "w") as f:
        yaml.dump([], f)
    with open(os.path.join(tmp_dir, "entities", "entity_archetypes.yaml"), "w") as f:
        yaml.dump([], f)
    with open(os.path.join(tmp_dir, "entities", "stat_profiles.yaml"), "w") as f:
        yaml.dump([], f)
    repo = CatalogRepository(tmp_dir)
    repo.load_all()
    return repo


# ── item adapter ────────────────────────────────────────────────────────────

class TestItemAdapterHeuristics:
    def test_use_kind_heuristic_emitted_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _build_repo(tmp, items=[_make_item("sword_x", ["weapon"])])
            adapter = CatalogToItemRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
            _, usages = adapter.adapt()
            use_kind_usages = [u for u in usages if u.heuristic_type == "use_kind"]
            assert len(use_kind_usages) == 1
            u = use_kind_usages[0]
            assert u.record_id == "sword_x"
            assert u.family == "item"
            assert u.adapter == "CatalogToItemRegistryAdapter"
            assert u.mode == RuntimeContentMode.CATALOG_WITH_COMPATIBILITY

    def test_class_fit_heuristic_emitted_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _build_repo(tmp, items=[_make_item("rusted_sword", ["weapon", "melee"])])
            adapter = CatalogToItemRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
            _, usages = adapter.adapt()
            class_fit_usages = [u for u in usages if u.heuristic_type == "class_fit"]
            assert len(class_fit_usages) == 1
            assert class_fit_usages[0].record_id == "rusted_sword"

    def test_no_heuristics_when_fields_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            item = _make_item("magic_wand", ["weapon"], use_kind="weapon",
                              class_fit=["mage"], metadata={"class_fit": ["mage"]})
            repo = _build_repo(tmp, items=[item])
            adapter = CatalogToItemRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
            _, usages = adapter.adapt()
            assert usages == ()

    def test_catalog_strict_raises_on_missing_use_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _build_repo(tmp, items=[_make_item("item_no_use_kind", ["weapon"])])
            adapter = CatalogToItemRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_STRICT)
            with pytest.raises(AdapterError):
                adapter.adapt()

    def test_heuristic_usages_is_tuple(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _build_repo(tmp, items=[_make_item("sword_x", ["weapon"])])
            adapter = CatalogToItemRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
            _, usages = adapter.adapt()
            assert isinstance(usages, tuple)
            assert all(isinstance(u, AdapterHeuristicUsage) for u in usages)


# ── service adapter ──────────────────────────────────────────────────────────

class TestServiceAdapterHeuristics:
    def test_affordances_heuristic_emitted_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _build_repo(tmp, services=[_make_service("blacksmith_village")])
            adapter = CatalogToServiceRegistryAdapter(repo, catalog_mode=True, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
            _, usages = adapter.adapt()
            aff_usages = [u for u in usages if u.heuristic_type == "affordances"]
            assert len(aff_usages) == 1
            u = aff_usages[0]
            assert u.record_id == "blacksmith_village"
            assert u.family == "service"
            assert u.adapter == "CatalogToServiceRegistryAdapter"

    def test_catalog_strict_raises_on_missing_affordances(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _build_repo(tmp, services=[_make_service("shop_no_affordances")])
            adapter = CatalogToServiceRegistryAdapter(repo, catalog_mode=True, mode=RuntimeContentMode.CATALOG_STRICT)
            with pytest.raises(AdapterError):
                adapter.adapt()

    def test_no_heuristics_when_affordances_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            svc = _make_service("inn_village", affordances=["rest"])
            repo = _build_repo(tmp, services=[svc])
            adapter = CatalogToServiceRegistryAdapter(repo, catalog_mode=True, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
            _, usages = adapter.adapt()
            assert usages == ()


# ── resource adapter ─────────────────────────────────────────────────────────

class TestResourceAdapterHeuristics:
    def _make_res_repo(self, tmp, resources):
        return _build_repo(tmp, resources=resources)

    def test_required_tool_heuristic_emitted_for_iron_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = _make_resource("iron_vein", resource_type="iron_ore", legacy_id="node_iron",
                                 metadata={"source_region_tags": ["old_mine"]})
            repo = self._make_res_repo(tmp, [res])
            adapter = CatalogToResourceRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
            _, usages = adapter.adapt()
            tool_usages = [u for u in usages if u.heuristic_type == "required_tool"]
            assert len(tool_usages) == 1
            assert tool_usages[0].record_id == "iron_vein"

    def test_base_difficulty_heuristic_emitted_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = _make_resource("wood_node", resource_type="wood", legacy_id="node_wood",
                                 metadata={"source_region_tags": ["near_forest"]})
            repo = self._make_res_repo(tmp, [res])
            adapter = CatalogToResourceRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
            _, usages = adapter.adapt()
            diff_usages = [u for u in usages if u.heuristic_type == "base_difficulty"]
            assert len(diff_usages) == 1
            assert diff_usages[0].family == "resource"

    def test_legacy_id_heuristic_emitted_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = _make_resource("wood_node", resource_type="wood",
                                 metadata={"source_region_tags": ["near_forest"]})
            repo = self._make_res_repo(tmp, [res])
            adapter = CatalogToResourceRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
            _, usages = adapter.adapt()
            legacy_usages = [u for u in usages if u.heuristic_type == "legacy_id"]
            assert len(legacy_usages) == 1
            assert legacy_usages[0].record_id == "wood_node"

    def test_catalog_strict_raises_on_missing_legacy_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = _make_resource("wood_node", resource_type="wood",
                                 metadata={"source_region_tags": ["near_forest"]})
            repo = self._make_res_repo(tmp, [res])
            adapter = CatalogToResourceRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_STRICT)
            with pytest.raises(AdapterError):
                adapter.adapt()


# ── AdapterProjectionResult ──────────────────────────────────────────────────

class TestAdapterProjectionResult:
    def test_heuristic_count_property_returns_len(self):
        h = AdapterHeuristicUsage(
            record_id="x", family="item", adapter="A",
            heuristic_type="use_kind", reason="test",
            mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY,
        )
        result = AdapterProjectionResult(
            mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY,
            item_count=1, service_count=0, resource_count=0,
            heuristic_usages=(h,),
        )
        assert result.heuristic_count == 1

    def test_empty_heuristic_usages_count_is_zero(self):
        result = AdapterProjectionResult(
            mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY,
            item_count=0, service_count=0, resource_count=0,
            heuristic_usages=(),
        )
        assert result.heuristic_count == 0

    def test_compatibility_mode_returns_populated_heuristic_usages(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _build_repo(tmp, items=[_make_item("sword_x", ["weapon"])])
            result = seed_phase1_content(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
            assert isinstance(result, AdapterProjectionResult)
            assert isinstance(result.heuristic_usages, tuple)
            assert result.heuristic_count > 0
            assert all(isinstance(u, AdapterHeuristicUsage) for u in result.heuristic_usages)

    def test_catalog_strict_raises_when_heuristics_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _build_repo(tmp, items=[_make_item("sword_x", ["weapon"])])
            with pytest.raises(AdapterError):
                seed_phase1_content(repo, mode=RuntimeContentMode.CATALOG_STRICT)
