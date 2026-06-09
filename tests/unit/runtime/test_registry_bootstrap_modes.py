"""
Unit tests for src/runtime/bootstrap.py — mode-governed registry bootstrap pipeline.

Tests verify:
  - CATALOG_STRICT raises HardcodedFallbackError when no catalog is available
  - LEGACY_FALLBACK seeds registries from hardcoded maps and sets fallback_used=True
  - TEST_MANUAL seeds empty registries without requiring a catalog
  - CATALOG_WITH_COMPATIBILITY populates enemy counts via compat projection adapter
  - ContentSourceReport properties total_catalog / total_compat / total_fallback are consistent
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple

import pytest

from src.core.modes import RuntimeContentMode
from src.runtime.bootstrap import (
    ContentSourceReport,
    HardcodedFallbackError,
    bootstrap_registries,
)
from src.core.registries import EnemyRegistry, ItemRegistry, RegionRegistry


# ---------------------------------------------------------------------------
# Minimal mock catalog (empty collections + optional enemy projection)
# ---------------------------------------------------------------------------

@dataclass
class _MockEnemyProjection:
    legacy_enemy_id: str
    archetype_id: str
    danger_hint: str
    loot_table: Dict[str, float] = field(default_factory=dict)
    spawn_regions: Tuple[str, ...] = ("near_forest",)


class _MockCatalog:
    def __init__(self, projections=None):
        self.items: Dict = {}
        self.recipes: Dict = {}
        self.services: Dict = {}
        self.regions: Dict = {}
        self.resources: Dict = {}
        self.legacy_enemy_projections: Dict = projections or {}
        self.fingerprint = "mock-fingerprint"

    def get_entity_archetype(self, archetype_id):
        return None

    def get_stats_profile(self, profile_id):
        return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_strict_mode_raises_hardcoded_fallback_error_when_no_catalog():
    with pytest.raises(HardcodedFallbackError) as exc_info:
        bootstrap_registries(RuntimeContentMode.CATALOG_STRICT, catalog_repo=None)
    assert exc_info.value.mode is RuntimeContentMode.CATALOG_STRICT
    assert "catalog_strict" in str(exc_info.value)


def test_compat_mode_raises_hardcoded_fallback_error_when_no_catalog():
    with pytest.raises(HardcodedFallbackError) as exc_info:
        bootstrap_registries(
            RuntimeContentMode.CATALOG_WITH_COMPATIBILITY, catalog_repo=None
        )
    assert exc_info.value.mode is RuntimeContentMode.CATALOG_WITH_COMPATIBILITY


def test_legacy_fallback_mode_seeds_hardcoded_registries():
    report = bootstrap_registries(RuntimeContentMode.LEGACY_FALLBACK, catalog_repo=None)

    assert report.fallback_used is True
    assert report.mode is RuntimeContentMode.LEGACY_FALLBACK
    assert report.total_fallback > 0
    assert report.total_catalog == 0
    assert report.total_compat == 0

    # Hardcoded registries should have content
    assert EnemyRegistry.contains("wolf")
    assert EnemyRegistry.contains("goblin")
    assert ItemRegistry.contains("rusted_sword")
    assert RegionRegistry.contains("hometown")


def test_test_manual_mode_seeds_empty_registries_without_catalog():
    report = bootstrap_registries(RuntimeContentMode.TEST_MANUAL, catalog_repo=None)

    assert report.fallback_used is False
    assert report.mode is RuntimeContentMode.TEST_MANUAL
    assert report.total_catalog == 0
    assert report.total_compat == 0
    assert report.total_fallback == 0
    assert ItemRegistry.all() == {}
    assert EnemyRegistry.all() == {}


def test_compat_mode_with_catalog_populates_enemies_via_projection():
    proj = _MockEnemyProjection(
        legacy_enemy_id="wolf",
        archetype_id="hungry_wolf",
        danger_hint="MEDIUM",
        loot_table={"wolf_pelt": 0.6},
        spawn_regions=("near_forest",),
    )
    mock_catalog = _MockCatalog(projections={"wolf": proj})

    report = bootstrap_registries(
        RuntimeContentMode.CATALOG_WITH_COMPATIBILITY,
        catalog_repo=mock_catalog,
    )

    assert report.fallback_used is False
    assert report.mode is RuntimeContentMode.CATALOG_WITH_COMPATIBILITY
    # Enemy came through compat projection (ArchetypeToEnemyRegistryAdapter)
    assert dict(report.compat_counts).get("enemy", 0) == 1
    assert EnemyRegistry.contains("wolf")


def test_catalog_path_with_empty_mock_seeds_only_hometown_region():
    report = bootstrap_registries(
        RuntimeContentMode.CATALOG_WITH_COMPATIBILITY,
        catalog_repo=_MockCatalog(),
    )

    assert report.fallback_used is False
    # CatalogToRegionRegistryAdapter always injects hometown
    region_count = dict(report.catalog_counts).get("region", 0)
    assert region_count == 1
    assert RegionRegistry.contains("hometown")


def test_content_source_report_totals_are_consistent():
    report = bootstrap_registries(RuntimeContentMode.LEGACY_FALLBACK, catalog_repo=None)

    item_fallback = dict(report.fallback_counts).get("item", 0)
    enemy_fallback = dict(report.fallback_counts).get("enemy", 0)
    assert item_fallback > 0
    assert enemy_fallback > 0
    assert report.total_fallback == sum(c for _, c in report.fallback_counts)
    assert report.total_catalog == 0
    assert report.total_compat == 0


def test_hardcoded_fallback_error_mode_attribute():
    """HardcodedFallbackError carries the mode that triggered it."""
    err = HardcodedFallbackError(RuntimeContentMode.CATALOG_STRICT, "test detail")
    assert err.mode is RuntimeContentMode.CATALOG_STRICT
    assert "test detail" in str(err)


def test_content_source_report_is_frozen():
    report = ContentSourceReport(
        mode=RuntimeContentMode.TEST_MANUAL,
        catalog_counts=(),
        compat_counts=(),
        fallback_counts=(),
    )
    with pytest.raises((AttributeError, TypeError)):
        report.fallback_used = True  # type: ignore[misc]
