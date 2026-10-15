"""The V2 terrain aliases (`TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES`, owner answer on #523, 2026-10-12): registry-only, resolved by name, carried by nothing at runtime."""

from __future__ import annotations

import pytest

from tests.visual_assets import adopted_facts as af
from visual_assets.store import identities
from visual_assets.store.catalog.registry import load_registry
from visual_assets.store.contracts import ReleaseCandidateManifest
from visual_assets.store.contracts.runtime import RuntimeManifest
from visual_assets.store.errors import RegistryError


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def test_the_eight_aliases_load_and_resolve_to_the_art_that_exists(registry):  # three terrain (V2 names) + five object aliases
    assert dict(registry.aliases) == af.REGISTRY_ALIASES and len(registry.aliases) == 8
    assert [registry.resolve(a).key for a in af.TERRAIN_ALIASES] == ["terrain.grassland", "terrain.ruins", "terrain.shallow_water"]
    assert [registry.resolve(a).key for a in af.OBJECT_ALIASES] == list(af.OBJECT_ALIASES.values())


def test_no_alias_is_a_key_and_no_alias_points_at_an_alias(registry):
    assert not set(registry.aliases) & set(registry.keys)  # the loader's own rule, on the real file
    assert not set(registry.aliases.values()) & set(registry.aliases)  # no chain
    assert set(registry.aliases.values()) <= set(registry.keys)


def test_resolve_follows_exactly_one_alias_and_refuses_an_unknown_name(registry):
    assert registry.resolve("terrain.grassland").key == "terrain.grassland"  # a key resolves to itself
    with pytest.raises(RegistryError):
        registry.resolve("terrain.plains")


def test_an_upper_case_name_cannot_be_a_key_so_the_name_rule_lowercases():
    """`terrain.PLAIN` cannot exist (`identities.py` VISUAL_KEY_PATTERN is lower case): `PLAIN` and `plain` both resolve through `terrain.plain`."""
    with pytest.raises(identities.IdentityError):
        identities.check(identities.VisualKey, "terrain.PLAIN")
    assert identities.check(identities.VisualKey, "terrain.plain") == "terrain.plain"
    from tools import visual_assets_sample_map as sm

    assert {f"terrain.{sm._snake(n)}" for n in ("PLAIN", "plain")} == {"terrain.plain"}


def test_each_alias_has_a_v2_name_with_no_key_of_its_own_and_its_target_exists(registry):
    for alias, target in af.REGISTRY_ALIASES.items():
        assert alias not in registry.keys and target in registry.keys


def test_aliases_are_registry_only_nothing_at_release_or_runtime_carries_them():
    """The finding of `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN`: the release and runtime records have no alias field, so a client asking for `terrain.plain` finds no entry; a runtime consumer is needed at activation."""
    for model in (ReleaseCandidateManifest, RuntimeManifest):
        assert not [name for name in model.model_fields if "alias" in name], model.__name__


def test_key_usage_counts_a_reference_through_an_alias_for_its_target():
    from visual_assets.review import key_usage

    source = key_usage.__file__
    text = open(source).read()
    assert "known = set(registry.keys) | set(registry.aliases)" in text and "registry.aliases.get(key, key)" in text  # the one consumer
