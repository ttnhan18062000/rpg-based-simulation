"""The 22 icon set v2 keys in the committed registry (`TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`): registered once, optional, axis-free, each stating size, scale, class and fallback, tied to the
user-approved families, and covered by no artifact, adoption or release candidate yet."""

from __future__ import annotations

import json

from tests.visual_assets import adopted_facts as af
from visual_assets.review import icon_v2_keys as v2
from visual_assets.review.icon_item_families import load_mapping
from visual_assets.store import config, records
from visual_assets.store.catalog.registry import load_registry


def test_the_22_v2_keys_are_registered_optional_axis_free_and_state_size_scale_class_and_fallback():
    registry = load_registry()
    assert sorted(k for k in v2.SIZES if k in registry.keys) == v2.KEYS and len(v2.KEYS) == 22
    for key, size in v2.SIZES.items():
        d = registry.keys[key]
        assert d.family == "icon" and d.optional and d.variant_axes == () and d.detail is None, key  # D17: no variant axis
        assert f"{size}x{size}" in d.description and "scale x1" in d.description, key
        assert "identifying class" in d.description and "fallback" in d.description, key
        assert len(d.description) <= 256, key


def test_the_item_keys_are_exactly_the_users_six_families_and_the_rarity_keys_the_three_badges():
    registry = load_registry()
    families = sorted(set(load_mapping().values()))
    assert sorted(k for k in registry.keys if k.startswith("icon.item.")) == [f"icon.item.{f}" for f in families] and len(families) == 6
    assert sorted(k for k in registry.keys if k.startswith("icon.rarity.")) == [f"icon.rarity.{r}" for r in ("common", "rare", "uncommon")]
    assert not [k for k in registry.keys if k.startswith("icon.rarity.legendary")]  # the one legendary item gets no badge (user, 2026-10-07)


def test_counts_by_family_are_the_approved_5_5_3_3_6():
    registry = load_registry()
    by = {p: sorted(k for k in registry.keys if k.startswith(p) and k in v2.SIZES) for p in ("icon.marker.", "icon.building.", "icon.class.", "icon.rarity.", "icon.item.")}
    assert {p: len(v) for p, v in by.items()} == {"icon.marker.": 5, "icon.building.": 5, "icon.class.": 3, "icon.rarity.": 3, "icon.item.": 6}


def test_the_key_set_keys_are_unchanged_and_no_v2_key_collides_with_them():
    registry = load_registry()
    key_set = sorted(k for k in registry.keys if k.startswith("icon.") and k not in v2.SIZES)
    assert [k.replace(".", "_") for k in key_set] == af.ICON_SOURCES and len(key_set) == 14


def test_every_v2_key_is_adopted_once_by_the_owners_set_adoption_is_built_and_sits_only_in_rc_0008():
    """The owner adopted `icons-v2` on 2026-10-08T00:40:15Z (`TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION`): each key has exactly its own source; `TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE` built one `x1` artifact for each, and only `pilot/rc-0008` lists them (rc-0001 to rc-0007 do not)."""
    registry = load_registry()
    for key in v2.KEYS:
        assert records.slot_holders(registry.keys[key], None) == [key.replace(".", "_")], key
    sources = [p.name for p in (config.CATALOG_ROOT / "sources").iterdir() if p.name != ".gitkeep"]
    assert sorted(s for s in sources if s in {k.replace(".", "_") for k in v2.KEYS}) == af.ICON_V2_SOURCES
    generated = [p.name for p in (config.CATALOG_ROOT / "generated").iterdir() if p.name != ".gitkeep"]
    assert {k.replace(".", "_") + "--x1" for k in v2.KEYS} <= set(generated)
    candidates = config.CATALOG_ROOT / "manifests" / "candidates" / "pilot"
    for path in sorted(candidates.glob("rc-*.json")):
        held = {e["visual_key"] for e in json.loads(path.read_text())["entries"]}
        if path.name == "rc-0008.json":
            assert set(v2.KEYS) <= held, path.name
        else:
            assert not held & set(v2.KEYS), path.name
