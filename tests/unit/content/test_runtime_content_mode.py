"""Tests for RuntimeContentMode — four explicit catalog modes."""
import os
import tempfile

import pytest
import yaml

from src.core.modes import RuntimeContentMode
from src.core.registries import (
    AdapterError,
    CatalogToItemRegistryAdapter,
    CatalogToServiceRegistryAdapter,
    CatalogToResourceRegistryAdapter,
    seed_phase1_content,
    ItemRegistry,
)


def _make_minimal_catalog_dir(tmp_dir: str) -> None:
    """Create a minimal content catalog with one item that requires heuristic projection."""
    os.makedirs(os.path.join(tmp_dir, "world"), exist_ok=True)
    items_data = [
        {
            "id": "mystery_item",
            "display_name": "Mystery Item",
            "schema_version": "itemdefinition.v1",
            "categories": ["weapon"],
            "rarity": "COMMON",
            "base_value": 10.0,
        }
    ]
    with open(os.path.join(tmp_dir, "world", "items.yaml"), "w") as f:
        yaml.dump(items_data, f)


def test_exactly_four_modes():
    """RuntimeContentMode must have exactly four values."""
    assert len(RuntimeContentMode) == 4


def test_all_four_mode_names_exist():
    """All four required mode names are present."""
    names = {m.name for m in RuntimeContentMode}
    assert names == {"CATALOG_STRICT", "CATALOG_WITH_COMPATIBILITY", "LEGACY_FALLBACK", "TEST_MANUAL"}


def test_migration_and_v2_removed():
    """Deprecated MIGRATION and V2 values must not exist."""
    names = {m.name for m in RuntimeContentMode}
    assert "MIGRATION" not in names
    assert "V2" not in names


def test_catalog_strict_rejects_heuristic_use_kind():
    """CATALOG_STRICT raises AdapterError when use_kind must be inferred heuristically."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        _make_minimal_catalog_dir(tmp_dir)
        from src.content.repository import CatalogRepository
        repo = CatalogRepository(tmp_dir)
        repo.load_all()
        adapter = CatalogToItemRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_STRICT)
        with pytest.raises(AdapterError):
            adapter.adapt()


def test_catalog_with_compatibility_allows_heuristic():
    """CATALOG_WITH_COMPATIBILITY mode allows heuristic inference and returns items."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        _make_minimal_catalog_dir(tmp_dir)
        from src.content.repository import CatalogRepository
        repo = CatalogRepository(tmp_dir)
        repo.load_all()
        adapter = CatalogToItemRegistryAdapter(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
        items, heuristic_usages = adapter.adapt()
        assert "mystery_item" in items
        assert len(heuristic_usages) > 0


def test_legacy_fallback_seeds_hardcoded_records():
    """LEGACY_FALLBACK mode (no catalog) falls back to hardcoded records."""
    result = seed_phase1_content(catalog_repo=None, mode=RuntimeContentMode.LEGACY_FALLBACK)
    assert result is None
    assert ItemRegistry.contains("rusted_sword")
    assert ItemRegistry.contains("small_potion")


def test_test_manual_mode_does_not_require_catalog():
    """TEST_MANUAL mode can be passed to adapters without a catalog present."""
    result = seed_phase1_content(catalog_repo=None, mode=RuntimeContentMode.TEST_MANUAL)
    assert result is None
