from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tests.visual_assets.store.unit.conftest import FIXTURES
from visual_assets.store import config
from visual_assets.store.catalog.registry import Registry, load_registry
from visual_assets.store.errors import RegistryError

HEAD = "record_type: visual_key_registry\nschema_version: 1\n"
KEY_A = "  - {key: fixture.a.one, family: a, description: d, variant_axes: []}\n"
KEY_B = "  - {key: fixture.a.two, family: a, description: d, variant_axes: []}\n"


def write(tmp_path: Path, body: str, name: str = "reg.yaml") -> Path:
    path = tmp_path / name
    path.write_text(body)
    return path


def load(tmp_path: Path, body: str, **kw) -> Registry:
    return load_registry(write(tmp_path, body), allow_fixture_namespace=True, **kw)


def rejects(tmp_path: Path, body: str, match: str | None = None, **kw) -> None:
    with pytest.raises(RegistryError, match=match):
        load(tmp_path, body, **kw)


def test_committed_registry_holds_the_adopted_forest_key_one_optional_key_per_other_terrain_code_the_three_border_mask_keys_and_the_36_icon_keys():
    """`terrain.forest` is the one adopted key; the other 22 Live Map terrain codes are registered `optional: true` for the draft set `terrain-v1`
    (`TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET`), and the `border.*` mask family (D19, `TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT`) adds three optional keys
    with a v1-v3 detail axis; the `icon.*` key set (D20, `TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES`) adds 14 optional keys with no axis, and icon set v2 (`TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`) 22 more. The expected terrain keys are read from the page's explicit code-to-key table, the contract both sides share."""
    import re

    table = (Path(__file__).resolve().parents[4] / "frontend" / "src" / "visualAssets" / "terrainDrafts.ts").read_text()
    expected = re.findall(r"'(terrain\.[a-z_]+)'", table[table.index("TERRAIN_DRAFT_KEYS"):table.index("TERRAIN_CODES")])
    assert len(expected) == 23 and len(set(expected)) == 23
    registry = load_registry()
    borders = ["border.edge", "border.inner_corner", "border.outer_corner"]
    tiers = [f"icon.tier.{g}" for g in ("e", "d", "c", "b", "a", "s", "ss", "sss")]
    icons = ["icon.plate.location", "icon.marker.enemy_camp", "icon.building.blacksmith", "icon.class.warrior", *tiers, "icon.status.frame_buff", "icon.status.frame_debuff"]
    from visual_assets.review import icon_v2_keys as v2

    assert sorted(registry.keys) == sorted(expected + borders + icons + v2.KEYS) and dict(registry.aliases) == {}
    sizes = {"icon.plate.location": 16, "icon.marker.enemy_camp": 16, "icon.building.blacksmith": 24, "icon.class.warrior": 24, "icon.status.frame_buff": 16, "icon.status.frame_debuff": 16, **dict.fromkeys(tiers, 8)}
    for key, size in {**sizes, **v2.SIZES}.items():
        d = registry.keys[key]
        assert d.optional and d.family == "icon" and d.variant_axes == () and d.detail is None  # D17: tier and marker state are separate keys, never axes
        assert f"{size}x{size}" in d.description and "scale x1" in d.description and "fallback" in d.description and " class" in d.description
    for key in borders:
        d = registry.keys[key]
        assert d.optional and d.family == "border" and d.variant_axes == () and d.detail.values == ("v1", "v2", "v3") and d.detail.default == "v1"
    others = [d for k, d in registry.keys.items() if k != "terrain.forest" and k not in borders and k not in icons and k not in v2.KEYS]
    assert len(others) == 22 and all(d.optional and d.family == "terrain" and d.detail is None and d.variant_axes == () for d in others)
    forest = registry.keys["terrain.forest"]
    assert forest.family == "terrain" and forest.variant_axes == () and not forest.optional
    # the declared order is what the client picks over: the spread the user approved (64 x 64: plain 1354, bush 1397, tree 1345) was computed for it
    assert forest.detail.values == ("plain", "bush", "tree") and forest.detail.default == "plain"
    data = (config.CATALOG_ROOT / "definitions" / "visual_keys.yaml").read_bytes()
    assert registry.file_hash == "sha256:" + hashlib.sha256(data).hexdigest()


def test_committed_catalog_holds_the_pilot_forest_and_the_adopted_terrain_v1_sources():
    # the forest's three slot sources and what was derived from them (artifacts and release candidates: forest only) plus the 31 sources of the owner's adoption of terrain-v1 on 2026-10-05T18:17:03Z;
    # exact contents: tests/visual_assets/adopted_facts.py and test_catalog_integrity.py
    from tests.visual_assets import adopted_facts as af

    expected = {"sources": af.ADOPTED_SOURCES, "generated": af.GENERATED, "manifests/candidates": ["pilot"]}
    for sub, names in expected.items():
        assert sorted(p.name for p in (config.CATALOG_ROOT / sub).iterdir() if p.name != ".gitkeep") == names, sub
    for sub in ("provenance/adoptions", "provenance/intake"):
        assert len([p for p in (config.CATALOG_ROOT / sub).iterdir() if p.name != ".gitkeep"]) == (af.ADOPTION_COUNT if sub.endswith("adoptions") else af.INTAKE_FILE_COUNT), sub
    assert [p.name for p in (config.CATALOG_ROOT / "build-config").iterdir() if p.name != ".gitkeep"] == ["export.toml"]  # rules, not an asset
    assert {p.name for p in (config.CATALOG_ROOT / "fixtures").iterdir()} == {"contracts"}
    assert "fixture" not in [p.name for p in (config.CATALOG_ROOT / "definitions").iterdir()]


def test_fixture_registry_loads_with_the_flag_and_only_with_it():
    path = FIXTURES / "visual_keys.fixture.yaml"
    registry = load_registry(path, allow_fixture_namespace=True)
    assert set(registry.keys) == {"fixture.sample.icon", "fixture.sample.tile"}
    with pytest.raises(RegistryError, match="fixture"):
        load_registry(path)


def test_resolve_returns_definition_and_follows_one_alias():
    registry = load_registry(FIXTURES / "visual_keys.fixture.yaml", allow_fixture_namespace=True)
    direct = registry.resolve("fixture.sample.icon")
    assert direct.key == "fixture.sample.icon"
    assert registry.resolve("fixture.sample.old_icon") is direct


def test_resolve_unknown_raises_and_registers_nothing():
    registry = load_registry(FIXTURES / "visual_keys.fixture.yaml", allow_fixture_namespace=True)
    before = (dict(registry.keys), dict(registry.aliases))
    for unknown in ("nope.nope", "", "fixture.sample.missing", "FIXTURE.SAMPLE.ICON", "fixture.sample.icon "):
        with pytest.raises(RegistryError, match="unknown visual key"):
            registry.resolve(unknown)
    assert (dict(registry.keys), dict(registry.aliases)) == before
    with pytest.raises(TypeError):
        registry.keys["x.y"] = None  # type: ignore[index]
    with pytest.raises(TypeError):
        registry.aliases["x.y"] = "z.z"  # type: ignore[index]


def test_resolve_on_the_empty_committed_registry_raises():
    with pytest.raises(RegistryError):
        load_registry().resolve("terrain.grass.tile")


def test_duplicate_yaml_mapping_key_is_rejected(tmp_path):
    rejects(tmp_path, HEAD + "keys: []\naliases: []\naliases: []\n", "duplicate YAML key")
    rejects(tmp_path, HEAD + "keys:\n  - {key: fixture.a.one, key: fixture.a.two, family: a, description: d, variant_axes: []}\naliases: []\n",
            "duplicate YAML key")


def test_duplicate_key_and_duplicate_alias_are_rejected(tmp_path):
    rejects(tmp_path, HEAD + "keys:\n" + KEY_A + KEY_A + "aliases: []\n", "duplicate key")
    rejects(tmp_path, HEAD + "keys:\n" + KEY_A + "aliases:\n  - {alias: fixture.a.old, target: fixture.a.one}\n"
            "  - {alias: fixture.a.old, target: fixture.a.one}\n", "duplicate alias")


def test_alias_problems_are_rejected(tmp_path):
    base = HEAD + "keys:\n" + KEY_A + KEY_B
    rejects(tmp_path, base + "aliases:\n  - {alias: fixture.a.old, target: fixture.a.nope}\n", "missing key")
    rejects(tmp_path, base + "aliases:\n  - {alias: fixture.a.two, target: fixture.a.one}\n", "also a key")
    rejects(tmp_path, base + "aliases:\n  - {alias: fixture.a.one, target: fixture.a.one}\n", "also a key")
    rejects(tmp_path, base + "aliases:\n  - {alias: fixture.a.x, target: fixture.a.y}\n"
            "  - {alias: fixture.a.y, target: fixture.a.one}\n", "chains")
    rejects(tmp_path, base + "aliases:\n  - {alias: fixture.a.x, target: fixture.a.x}\n", "chains")
    ok = load(tmp_path, base + "aliases:\n  - {alias: fixture.a.old, target: fixture.a.one}\n")
    assert ok.resolve("fixture.a.old").key == "fixture.a.one"


def test_fixture_namespace_is_rejected_without_the_flag(tmp_path):
    path = write(tmp_path, HEAD + "keys:\n" + KEY_A + "aliases: []\n")
    with pytest.raises(RegistryError, match="fixture"):
        load_registry(path)
    assert load_registry(path, allow_fixture_namespace=True).resolve("fixture.a.one")
    path = write(tmp_path, HEAD + "keys:\n  - {key: real.a.one, family: a, description: d, variant_axes: [], safety_class: decorative, fallback: {kind: none}}\n"
                 "aliases:\n  - {alias: fixture.a.old, target: real.a.one}\n", "alias.yaml")
    with pytest.raises(RegistryError, match="fixture alias"):
        load_registry(path)


def test_count_bounds(tmp_path, monkeypatch):
    body = HEAD + "keys:\n" + KEY_A + KEY_B + "aliases:\n  - {alias: fixture.a.old, target: fixture.a.one}\n"
    load(tmp_path, body)
    monkeypatch.setattr(config, "MAX_VISUAL_KEYS", 1)
    rejects(tmp_path, body, "more than 1 keys")
    monkeypatch.setattr(config, "MAX_VISUAL_KEYS", 4096)
    monkeypatch.setattr(config, "MAX_ALIASES", 0)
    rejects(tmp_path, body, "more than 0 aliases")


def test_size_bound(tmp_path, monkeypatch):
    # padded with a comment: the bound applies to the file and, as compact JSON, to the parsed body, which must not exceed it
    path = write(tmp_path, HEAD + "keys: []\naliases: []\n# " + "x" * 200 + "\n")
    size = path.stat().st_size
    monkeypatch.setattr(config, "MAX_REGISTRY_BYTES", size)
    load_registry(path)
    monkeypatch.setattr(config, "MAX_REGISTRY_BYTES", size - 1)
    with pytest.raises(RegistryError, match="exceeds"):
        load_registry(path)


def test_yaml_anchors_and_aliases_are_rejected(tmp_path):
    rejects(tmp_path, HEAD + "keys: []\naliases: &a []\nextra: *a\n", "aliases are not allowed")


def test_unsafe_or_odd_yaml_is_rejected_not_executed(tmp_path):
    for body in ("!!python/object/apply:os.system ['true']\n", "- not a mapping\n", "", "just text\n",
                 HEAD + "keys: []\naliases: []\nwhen: 2026-01-01\n", HEAD + "keys: []\naliases: []\n? [a]\n: b\n",
                 HEAD + "keys: []\naliases: []\n1: 2\n", "\x00\n", "{", HEAD + "keys: [\n"):
        rejects(tmp_path, body)


def test_schema_problems_in_yaml_are_registry_errors(tmp_path):
    for body in (HEAD.replace("version: 1", "version: 2") + "keys: []\naliases: []\n",
                 "record_type: other\nschema_version: 1\nkeys: []\naliases: []\n",
                 HEAD + "keys: []\n",
                 HEAD + "keys: []\naliases: []\nsurprise: 1\n",
                 HEAD + "keys:\n  - {key: Bad.Key, family: a, description: d, variant_axes: []}\naliases: []\n",
                 HEAD + "keys:\n  - {key: fixture.a.one, family: a, description: '', variant_axes: []}\naliases: []\n"):
        rejects(tmp_path, body)


def test_missing_file_and_directory_are_registry_errors(tmp_path):
    with pytest.raises(RegistryError):
        load_registry(tmp_path / "absent.yaml")
    with pytest.raises(RegistryError):
        load_registry(tmp_path)


def test_invalid_utf8_is_a_registry_error(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_bytes(b"\xff\xfe" + (HEAD + "keys: []\naliases: []\n").encode())
    with pytest.raises(RegistryError):
        load_registry(path)


def test_default_path_is_read_at_call_time(tmp_path, monkeypatch):
    (tmp_path / "definitions").mkdir()
    (tmp_path / "definitions" / "visual_keys.yaml").write_text(HEAD + "keys:\n" + KEY_A + "aliases: []\n")
    monkeypatch.setattr(config, "CATALOG_ROOT", tmp_path)
    assert set(load_registry(allow_fixture_namespace=True).keys) == {"fixture.a.one"}
    with pytest.raises(RegistryError, match="fixture"):
        load_registry()


REAL = "  - {{key: real.{fam}.one, family: {fam}, description: d, variant_axes: [], {extra}}}\n"


def real(fam="b", extra="safety_class: identifying, fallback: {kind: text, text: the name as text}"):
    return HEAD + "keys:\n" + REAL.format(fam=fam, extra=extra) + "aliases: []\n"


def test_a_real_key_needs_a_safety_class_and_a_fallback_but_a_fixture_key_does_not(tmp_path):
    """`AM1-W02.7`."""
    rejects(tmp_path, HEAD + "keys:\n  - {key: real.b.one, family: b, description: d, variant_axes: []}\naliases: []\n", "safety_class and fallback are required")
    rejects(tmp_path, real(extra="safety_class: identifying"), "safety_class and fallback are required")
    rejects(tmp_path, real(extra="fallback: {kind: text, text: x}"), "safety_class and fallback are required")
    assert load(tmp_path, real()).resolve("real.b.one").safety_class == "identifying"
    assert load(tmp_path, HEAD + "keys:\n" + KEY_A + "aliases: []\n").resolve("fixture.a.one").safety_class is None  # synthetic fixture keys are exempt


def test_the_fallback_must_fit_the_class_and_its_own_kind(tmp_path):
    for extra, message in (
        ("safety_class: identifying, fallback: {kind: none}", "identifying key needs a fallback"),
        ("safety_class: critical, fallback: {kind: flat_fill, text: x}", "critical key needs a text alternative"),
        ("safety_class: critical, fallback: {kind: none}", "critical key needs a text alternative"),
        ("safety_class: decorative, fallback: {kind: none, text: x}", "needs no text and no glyph"),
        ("safety_class: identifying, fallback: {kind: text}", "needs text and no glyph"),
        ("safety_class: identifying, fallback: {kind: text, text: x, glyph: g}", "needs text and no glyph"),
        ("safety_class: identifying, fallback: {kind: glyph_and_text, text: x}", "text and a glyph"),
        ("safety_class: identifying, fallback: {kind: flat_fill, text: '  '}", "registry rejected"),  # whitespace-only text is refused by the record's own text rule
    ):
        rejects(tmp_path, real(extra=extra), message)
    for ok in ("safety_class: decorative, fallback: {kind: none}", "safety_class: critical, fallback: {kind: text, text: the warning as text}",
               "safety_class: critical, fallback: {kind: glyph_and_text, text: t, glyph: g}", "safety_class: identifying, fallback: {kind: flat_fill, text: the fill}"):
        load(tmp_path, real(extra=ok))


def test_an_icon_that_is_not_decorative_needs_its_derived_label_key_and_a_label_and_a_decorative_one_has_none(tmp_path):
    base = "fallback: {kind: text, text: t}"
    rejects(tmp_path, real("icon", f"safety_class: identifying, {base}"), "needs label_key 'label.real.icon.one'")
    rejects(tmp_path, real("icon", f"safety_class: identifying, {base}, label_key: label.other, label: X"), "needs label_key 'label.real.icon.one'")
    rejects(tmp_path, real("icon", f"safety_class: identifying, {base}, label_key: label.real.icon.one, label: ''"), "registry rejected")
    rejects(tmp_path, real("icon", "safety_class: decorative, fallback: {kind: none}, label_key: label.real.icon.one, label: X"), "decorative key carries no label")
    load(tmp_path, real("icon", f"safety_class: identifying, {base}, label_key: label.real.icon.one, label: A name"))
    load(tmp_path, real("icon", "safety_class: decorative, fallback: {kind: none}"))
    load(tmp_path, real("terrain"))  # labels are an icon-family rule only


def test_a_non_empty_variant_axes_is_rejected_even_for_a_fixture_key(tmp_path):
    """`AM1-W03.1` (D17): only the detail axis exists, so a variant axis would promise a precedence nothing implements."""
    rejects(tmp_path, HEAD + "keys:\n  - {key: fixture.a.one, family: a, description: d, variant_axes: [{name: scale, values: [x1, x2]}]}\naliases: []\n", "variant_axes must be empty")
    rejects(tmp_path, real(extra="safety_class: identifying, fallback: {kind: text, text: t}").replace("variant_axes: []", "variant_axes: [{name: scale, values: [x1]}]"), "variant_axes must be empty")


def test_fallback_problems_name_every_identifying_or_critical_key_left_without_an_alternative(tmp_path):
    """`AM1-W06.3`, on a registry object built by hand (the loader would refuse it): the release check stands on its own."""
    from visual_assets.store.catalog.registry import fallback_problems
    from visual_assets.store.contracts.definitions import Fallback, VisualKeyDefinition

    def key(name, cls, fb):
        return VisualKeyDefinition(key=name, family="b", description="d", variant_axes=(), optional=True, safety_class=cls, fallback=fb)

    good = key("real.b.good", "identifying", Fallback(kind="text", text="t"))
    bad = key("real.b.bad", "identifying", Fallback(kind="none"))
    crit = key("real.b.crit", "critical", Fallback(kind="flat_fill"))  # a flat fill with no text carries nothing
    deco = key("real.b.deco", "decorative", Fallback(kind="none"))
    registry = Registry({k.key: k for k in (good, bad, crit, deco)}, {}, "sha256:x")
    assert fallback_problems(registry, set()) == [
        "real.b.bad: identifying key has no image in this release and no alternative that carries its fact",
        "real.b.crit: critical key has no image in this release and no alternative that carries its fact",
    ]
    assert fallback_problems(registry, {"real.b.bad", "real.b.crit"}) == []  # an image present: nothing to fall back to
    assert fallback_problems(Registry({good.key: good}, {}, "sha256:x"), set()) == []


def test_the_committed_registry_carries_a_class_a_structured_fallback_and_35_labels_for_every_key():
    registry = load_registry()  # the real read path: every rule above applies to the committed file
    keys = registry.keys
    assert len(keys) == 62 and all(d.safety_class and d.fallback for d in keys.values())
    from collections import Counter

    assert Counter((d.family, d.safety_class) for d in keys.values()) == Counter({("terrain", "identifying"): 23, ("border", "decorative"): 3, ("icon", "identifying"): 35, ("icon", "decorative"): 1})
    labelled = {k: d.label for k, d in keys.items() if d.label is not None}
    assert len(labelled) == 35 and all(keys[k].label_key == f"label.{k}" for k in labelled) and "icon.plate.location" not in labelled
    assert labelled["icon.tier.sss"] == "Tier SSS" and labelled["icon.status.frame_debuff"] == "Harmful effect" and labelled["icon.item.consumable"] == "Consumable item"
