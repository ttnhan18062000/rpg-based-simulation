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


def test_committed_registry_holds_the_adopted_forest_key_one_optional_key_per_other_terrain_code_and_the_three_border_mask_keys():
    """`terrain.forest` is the one adopted key; the other 22 Live Map terrain codes are registered `optional: true` for the draft set `terrain-v1`
    (`TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET`), and the `border.*` mask family (D19, `TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT`) adds three optional keys
    with a v1-v3 detail axis. The expected terrain keys are read from the page's explicit code-to-key table, the contract both sides share."""
    import re

    table = (Path(__file__).resolve().parents[4] / "frontend" / "src" / "visualAssets" / "terrainDrafts.ts").read_text()
    expected = re.findall(r"'(terrain\.[a-z_]+)'", table[table.index("TERRAIN_DRAFT_KEYS"):table.index("TERRAIN_CODES")])
    assert len(expected) == 23 and len(set(expected)) == 23
    registry = load_registry()
    borders = ["border.edge", "border.inner_corner", "border.outer_corner"]
    assert sorted(registry.keys) == sorted(expected + borders) and dict(registry.aliases) == {}
    for key in borders:
        d = registry.keys[key]
        assert d.optional and d.family == "border" and d.variant_axes == () and d.detail.values == ("v1", "v2", "v3") and d.detail.default == "v1"
    others = [d for k, d in registry.keys.items() if k != "terrain.forest" and k not in borders]
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
    path = write(tmp_path, HEAD + "keys:\n  - {key: real.a.one, family: a, description: d, variant_axes: []}\n"
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
