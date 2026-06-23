"""Tests for FeaturePackManifest, RuntimeProfile, CompatibilityResolver (E63B)."""

import pytest

from src.domains.feature_packs.manifest import (
    CompatibilityResolver,
    ExtensionPoint,
    FeaturePackManifest,
    PackConflictError,
    PackDependencyError,
)
from src.domains.feature_packs.profile import RuntimeProfile
from src.scenarios.schema import SimulationScenarioDefinition


def _manifest(name: str, requires: list[str] | None = None, eps: list[dict] | None = None) -> FeaturePackManifest:
    return FeaturePackManifest(
        name=name,
        version="1.0.0",
        requires=requires or [],
        extension_points=[ExtensionPoint(**ep) for ep in (eps or [])],
    )


# ── FeaturePackManifest ───────────────────────────────────────────────────────

def test_manifest_defaults():
    m = FeaturePackManifest(name="base", version="1.0.0")
    assert m.requires == []
    assert m.extension_points == []
    assert m.balance_specs == []


def test_manifest_round_trip():
    m = FeaturePackManifest(
        name="demo_escort_pack",
        version="1.2.3",
        requires=["base"],
        extension_points=[
            ExtensionPoint(
                domain="adventure_routing",
                class_path="demo_escort_pack.routes:EscortGenerator",
                registry_key="ESCORT_DIGNITARY",
            )
        ],
        balance_specs=["escort_caution_check"],
    )
    restored = FeaturePackManifest.from_yaml_dict(m.to_yaml_dict())
    assert restored == m


def test_manifest_frozen():
    m = _manifest("base")
    with pytest.raises(Exception):
        m.name = "changed"  # type: ignore[misc]


# ── RuntimeProfile ────────────────────────────────────────────────────────────

def test_runtime_profile_defaults():
    rp = RuntimeProfile()
    assert rp.active_pack_names == []


def test_runtime_profile_with_packs():
    rp = RuntimeProfile(active_pack_names=["base", "faction_pack"])
    assert "faction_pack" in rp.active_pack_names


# ── SimulationScenarioDefinition.runtime_profile ─────────────────────────────

def test_scenario_runtime_profile_optional():
    ssd = SimulationScenarioDefinition(
        id="test",
        world_composition="urban_political",
        perspective="entity",
    )
    assert ssd.runtime_profile is None


def test_scenario_runtime_profile_set():
    rp = RuntimeProfile(active_pack_names=["base", "demo_escort_pack"])
    ssd = SimulationScenarioDefinition(
        id="test",
        world_composition="urban_political",
        perspective="entity",
        runtime_profile=rp,
    )
    assert ssd.runtime_profile is not None
    assert "demo_escort_pack" in ssd.runtime_profile.active_pack_names


# ── CompatibilityResolver ─────────────────────────────────────────────────────

def test_resolver_single_pack():
    m = _manifest("base")
    result = CompatibilityResolver.resolve([m])
    assert [x.name for x in result] == ["base"]


def test_resolver_linear_chain():
    base = _manifest("base")
    a = _manifest("pack_a", requires=["base"])
    b = _manifest("pack_b", requires=["pack_a"])
    result = CompatibilityResolver.resolve([b, a, base])
    names = [x.name for x in result]
    assert names.index("base") < names.index("pack_a") < names.index("pack_b")


def test_resolver_deterministic_within_level():
    base = _manifest("base")
    a = _manifest("aaa", requires=["base"])
    b = _manifest("bbb", requires=["base"])
    result = CompatibilityResolver.resolve([b, a, base])
    names = [x.name for x in result]
    # base first, then aaa before bbb (lexicographic within same level)
    assert names[0] == "base"
    assert names.index("aaa") < names.index("bbb")


def test_resolver_circular_dependency_raises():
    a = _manifest("pack_a", requires=["pack_b"])
    b = _manifest("pack_b", requires=["pack_a"])
    with pytest.raises(PackDependencyError, match="Circular"):
        CompatibilityResolver.resolve([a, b])


def test_resolver_missing_dependency_raises():
    a = _manifest("pack_a", requires=["nonexistent"])
    with pytest.raises(PackDependencyError, match="nonexistent"):
        CompatibilityResolver.resolve([a])


def test_resolver_conflict_detection():
    a = _manifest("pack_a", eps=[{"domain": "adventure_routing", "class_path": "a:Gen", "registry_key": "ESCORT"}])
    b = _manifest("pack_b", eps=[{"domain": "adventure_routing", "class_path": "b:Gen", "registry_key": "ESCORT"}])
    with pytest.raises(PackConflictError):
        CompatibilityResolver.resolve([a, b])


def test_resolver_same_key_different_domains_ok():
    a = _manifest("pack_a", eps=[{"domain": "adventure_routing", "class_path": "a:Gen", "registry_key": "ESCORT"}])
    b = _manifest("pack_b", eps=[{"domain": "world_emergence", "class_path": "b:Gen", "registry_key": "ESCORT"}])
    result = CompatibilityResolver.resolve([a, b])
    assert len(result) == 2
