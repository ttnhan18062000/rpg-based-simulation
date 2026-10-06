"""The detail axis (`TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT`): a key may carry one adopted artifact per declared detail value.

A slot is `(visual key, effective detail value)`; an adoption without `detail_value` fills the key's declared default, which is what
keeps an adoption made before the axis existed valid. Everything here is pure Python (no Aseprite).
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config, records, runtime_export
from visual_assets.store.build import exporter
from visual_assets.store.contracts import AdoptionRecord, ReleaseCandidateManifest, RuntimeManifest, canonical_json, parse_record
from visual_assets.store.contracts.definitions import MAX_DETAIL_VALUES, DetailAxis, VisualKeyDefinition
from visual_assets.store.contracts.release import ReleaseEntry
from visual_assets.store.contracts.runtime import RuntimeDetail, RuntimeEntry
from visual_assets.store.errors import BuildError, ContractError, GateError, RegistryError
from visual_assets.store.catalog.registry import load_registry
from visual_assets.store.release import assemble_release
from visual_assets.store.verify import verify

HERO, ROCK = s.key_for("hero"), s.key_for("rock")
AXIS = {HERO: (("plain", "bush", "tree"), "plain")}
HASH_A, HASH_B = "pixels-v1:" + "a" * 64, "pixels-v1:" + "b" * 64


def definition(**over) -> VisualKeyDefinition:
    return VisualKeyDefinition(key=HERO, family="sample", description="d", variant_axes=(), detail=DetailAxis(values=("plain", "bush"), default="plain"), **over)


# ---- the registry declaration ----------------------------------------------------------------------------------------------------

def test_a_detail_axis_needs_unique_values_and_a_default_among_them():
    with pytest.raises(ValidationError):
        DetailAxis(values=("plain", "plain"), default="plain")
    with pytest.raises(ValidationError):
        DetailAxis(values=("plain", "bush"), default="tree")
    with pytest.raises(ValidationError):
        DetailAxis(values=(), default="plain")
    with pytest.raises(ValidationError):
        DetailAxis(values=tuple(f"v{i}" for i in range(MAX_DETAIL_VALUES + 1)), default="v0")
    assert DetailAxis(values=tuple(f"v{i}" for i in range(MAX_DETAIL_VALUES)), default="v0").default == "v0"


def test_the_effective_detail_is_the_declared_default_for_none_and_nothing_for_a_key_without_an_axis():
    assert definition().effective_detail(None) == "plain" and definition().effective_detail("bush") == "bush"
    plain_key = VisualKeyDefinition(key=ROCK, family="sample", description="d", variant_axes=())
    assert plain_key.effective_detail(None) is None


def test_the_registry_loader_bounds_the_keys_that_declare_an_axis(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MAX_DETAIL_KEYS", 1)
    keys = [s.key_for("hero"), s.key_for("rock")]
    path = s.write_registry(tmp_path, keys, detail={k: (("plain", "bush"), "plain") for k in keys[:1]})
    assert load_registry(path, allow_fixture_namespace=True).keys[keys[0]].detail.default == "plain"
    path = s.write_registry(tmp_path, keys, detail={k: (("plain", "bush"), "plain") for k in keys})
    with pytest.raises(RegistryError, match="declare a detail axis"):
        load_registry(path, allow_fixture_namespace=True)


# ---- adoption ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def adopting(env):
    s.CALLS.clear()
    s.write_export_config(env.catalog)
    s.write_store_format(env.catalog)
    env.registry = s.detail_registry(HERO)
    return env


def adopt(env, intake_id, sid, **over):
    return s.do_adopt(intake_id, source_asset_id=sid, registry=env.registry, **over)


def test_an_adoption_without_a_detail_value_stays_byte_identical_and_fills_the_default_slot(adopting):
    record = adopt(adopting, s.make_intake(adopting.tmp, 16).intake_id, "hero", visual_key=HERO)
    assert record.detail_value is None
    path = adopting.catalog / "provenance" / "adoptions" / f"{record.adoption_id}.json"
    assert b"detail_value" not in path.read_bytes()  # a record written before the field existed round-trips unchanged
    assert canonical_json(parse_record(AdoptionRecord, path.read_bytes())) == path.read_bytes()
    assert records.slot_holders(adopting.registry.keys[HERO], "plain") == ["hero"]
    assert records.slot_holders(adopting.registry.keys[HERO], "bush") == []


def test_a_declared_detail_value_is_recorded_and_fills_its_own_slot(adopting):
    record = adopt(adopting, s.make_intake(adopting.tmp, 16).intake_id, "hero", visual_key=HERO, detail_value="bush")
    assert record.detail_value == "bush"
    assert json.loads((adopting.catalog / "provenance" / "adoptions" / f"{record.adoption_id}.json").read_bytes())["detail_value"] == "bush"
    assert records.slot_holders(adopting.registry.keys[HERO], "bush") == ["hero"]
    assert records.slot_holders(adopting.registry.keys[HERO], "plain") == []
    text = "\n".join(s.CALLS[-1][1])
    assert f"visual key {HERO} [bush]; licence recorded as CLEARED, evidence 'licence-note-7'" in text  # the slot AND the real evidence ref
    assert "default detail value" not in text


def test_the_notice_says_when_the_slot_is_the_keys_default(adopting):
    adopt(adopting, s.make_intake(adopting.tmp, 16).intake_id, "hero", visual_key=HERO)
    assert f"visual key {HERO} [plain] (the key's default detail value); licence" in "\n".join(s.CALLS[-1][1])


def refuse(env, code, intake_id, sid, **over):
    before = snapshot(env.catalog)
    with pytest.raises(GateError) as err:
        adopt(env, intake_id, sid, **over)
    assert err.value.code == code, err.value
    assert snapshot(env.catalog) == before


def test_an_undeclared_detail_value_and_a_value_on_a_key_without_an_axis_are_refused(adopting):
    intake_id = s.make_intake(adopting.tmp, 16).intake_id
    refuse(adopting, "unknown_detail_value", intake_id, "hero", visual_key=HERO, detail_value="shrub")
    refuse(adopting, "detail_not_declared", intake_id, "rock", visual_key=ROCK, detail_value="plain")


def test_the_second_holder_of_a_slot_is_refused_and_a_different_slot_is_accepted(adopting):
    adopt(adopting, s.make_intake(adopting.tmp, 16).intake_id, "hero", visual_key=HERO)
    second = s.make_intake(adopting.tmp, 17).intake_id
    refuse(adopting, "visual_key_taken", second, "rock", visual_key=HERO)  # None = the default slot, already held
    refuse(adopting, "visual_key_taken", second, "rock", visual_key=HERO, detail_value="plain")  # the explicit default is the SAME slot
    assert adopt(adopting, second, "rock", visual_key=HERO, detail_value="bush").detail_value == "bush"
    third = s.make_intake(adopting.tmp, 18).intake_id
    refuse(adopting, "visual_key_taken", third, "other", visual_key=HERO, detail_value="bush")


def test_changing_the_declared_default_rebinds_the_adoptions_that_name_none(adopting):
    adopt(adopting, s.make_intake(adopting.tmp, 16).intake_id, "hero", visual_key=HERO)
    moved = s.detail_registry(HERO, default="tree").keys[HERO]
    assert records.slot_holders(moved, "tree") == ["hero"] and records.slot_holders(moved, "plain") == []


# ---- the release candidate ---------------------------------------------------------------------------------------------------------

@pytest.fixture
def tree(env):
    """hero fills HERO [plain] (named explicitly, so a later change of the declared default does not move it), rock fills HERO [bush]; both built."""
    s.CALLS.clear()
    s.write_export_config(env.catalog)
    s.write_store_format(env.catalog)
    env.registry = s.detail_registry(HERO)
    env.hero = adopt(env, s.make_intake(env.tmp, 16).intake_id, "hero", visual_key=HERO, detail_value="plain")
    env.rock = adopt(env, s.make_intake(env.tmp, 17).intake_id, "rock", visual_key=HERO, detail_value="bush")
    env.built = exporter.build(renderer=s.HashRenderer())
    s.write_registry(env.catalog, [HERO], detail=AXIS)
    return env


def release(env, **kw):
    return assemble_release("main", allow_fixture_namespace=True, **kw)


def test_a_release_lists_one_entry_per_slot_sorted_by_key_then_detail(tree):
    manifest = release(tree)
    assert [(e.visual_key, e.detail, e.artifact_id) for e in manifest.entries] == [(HERO, "bush", "rock--x1"), (HERO, "plain", "hero--x1")]
    path = tree.catalog / "manifests" / "candidates" / "main" / "rc-0001.json"
    assert parse_record(ReleaseCandidateManifest, path.read_bytes()) == manifest


def test_a_release_needs_the_default_slot_but_not_the_other_values(tree):
    assert [e.detail for e in release(tree).entries] == ["bush", "plain"]  # tree has no art: fine, it is not the default
    s.write_registry(tree.catalog, [HERO], detail={HERO: (("plain", "bush", "tree"), "tree")})  # now the default slot has no asset
    before = snapshot(tree.catalog)
    with pytest.raises(BuildError) as err:
        release(tree)
    assert err.value.code == "key_without_artifact" and "[tree]" in err.value.message and snapshot(tree.catalog) == before


def test_an_adopted_slot_without_an_artifact_is_refused_not_dropped(env):
    s.CALLS.clear()
    s.write_export_config(env.catalog)
    s.write_store_format(env.catalog)
    env.registry = s.detail_registry(HERO)
    adopt(env, s.make_intake(env.tmp, 16).intake_id, "hero", visual_key=HERO, detail_value="plain")
    exporter.build(renderer=s.HashRenderer())  # plain is built; bush is adopted AFTERWARDS and never built
    adopt(env, s.make_intake(env.tmp, 17).intake_id, "rock", visual_key=HERO, detail_value="bush")
    s.write_registry(env.catalog, [HERO], detail=AXIS)
    before = snapshot(env.catalog)
    with pytest.raises(BuildError) as err:
        release(env)
    assert err.value.code == "key_without_artifact" and "[bush]" in err.value.message and "run build" in err.value.message
    assert snapshot(env.catalog) == before
    s.write_registry(env.catalog, [HERO], optional=(HERO,), detail=AXIS)  # an OPTIONAL key keeps the old skip behaviour
    assert [e.detail for e in release(env).entries] == ["plain"]


def test_an_unadopted_non_default_slot_is_simply_absent(tree):
    s.write_registry(tree.catalog, [HERO], detail={HERO: (("plain", "bush", "tree", "shrub"), "plain")})  # tree and shrub: declared, never adopted
    assert [e.detail for e in release(tree).entries] == ["bush", "plain"]


def test_an_optional_key_may_omit_its_default_slot(tree):
    s.write_registry(tree.catalog, [HERO], optional=(HERO,), detail={HERO: (("plain", "bush", "tree"), "tree")})
    assert [e.detail for e in release(tree).entries] == ["bush", "plain"]  # nothing is required, what exists is listed


def test_an_adoption_naming_a_value_the_registry_no_longer_declares_is_refused(tree):
    s.write_registry(tree.catalog, [HERO], detail={HERO: (("plain", "tree"), "plain")})
    before = snapshot(tree.catalog)
    with pytest.raises(BuildError) as err:
        release(tree)
    assert err.value.code == "undeclared_detail" and snapshot(tree.catalog) == before


def test_two_assets_in_one_slot_are_ambiguous(tree):
    path = tree.catalog / "provenance" / "adoptions" / f"{tree.rock.adoption_id}.json"
    data = json.loads(path.read_bytes())
    data["detail_value"] = "plain"  # planted: adopt itself would refuse this
    path.write_bytes(json.dumps(data, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    with pytest.raises(BuildError) as err:
        release(tree)
    assert err.value.code == "ambiguous_key" and "[plain]" in err.value.message


def test_a_key_without_an_axis_is_still_one_slot(env):
    s.CALLS.clear()
    env.adoptions, env.built = s.adopted_tree(env)
    s.write_registry(env.catalog, [HERO, ROCK])
    manifest = release(env)
    assert [(e.visual_key, e.detail) for e in manifest.entries] == [(HERO, None), (ROCK, None)]
    assert b'"detail"' not in (env.catalog / "manifests" / "candidates" / "main" / "rc-0001.json").read_bytes()


# ---- the manifest contracts --------------------------------------------------------------------------------------------------------

def candidate(*entries):
    return dict(record_type="release_candidate_manifest", schema_version=1, catalog_id="main", release_id="rc-0001",
                registry_hash="sha256:" + "0" * 64, entries=entries, status="CANDIDATE")


def entry(key, detail, hash_=HASH_A):
    return ReleaseEntry(visual_key=key, detail=detail, artifact_id="hero--x1", pixel_hash=hash_)


def test_candidate_entries_are_unique_and_sorted_per_slot():
    ReleaseCandidateManifest(**candidate(entry(HERO, "bush"), entry(HERO, "plain"), entry(ROCK, None)))
    with pytest.raises(ValidationError, match="unique"):
        ReleaseCandidateManifest(**candidate(entry(HERO, "bush"), entry(HERO, "bush", HASH_B)))
    with pytest.raises(ValidationError, match="sorted"):
        ReleaseCandidateManifest(**candidate(entry(HERO, "plain"), entry(HERO, "bush")))


def test_a_candidate_has_at_most_max_visual_keys_entries_across_all_slots(monkeypatch):
    monkeypatch.setattr(config, "MAX_VISUAL_KEYS", 3)
    ReleaseCandidateManifest(**candidate(*(entry(HERO, d) for d in ("a", "b", "c"))))
    with pytest.raises(ValidationError, match="more than 3"):
        ReleaseCandidateManifest(**candidate(*(entry(HERO, d) for d in ("a", "b", "c", "d"))))


def runtime_entry(key, detail, hash_=HASH_A):
    return RuntimeEntry(visual_key=key, family="sample", pixel_hash=hash_, file=hash_.split(":")[1] + ".png", width=16, height=16, detail=detail)


def runtime(entries, details):
    return dict(record_type="runtime_manifest", schema_version=1, catalog_id="main", release_id="rc-0001", candidate_manifest_hash="sha256:" + "1" * 64,
                registry_hash="sha256:" + "0" * 64, fallback_contract_version=1, entries=entries, details=details)


def axis(key=HERO, values=("bush", "plain"), default="plain"):
    return RuntimeDetail(visual_key=key, values=values, default=default)


def test_a_runtime_manifest_ties_an_entrys_detail_to_its_keys_declared_values():
    good = RuntimeManifest(**runtime((runtime_entry(HERO, "bush"), runtime_entry(HERO, "plain", HASH_B), runtime_entry(ROCK, None)), (axis(),)))
    assert parse_record(RuntimeManifest, canonical_json(good)) == good
    for entries, details in (
        ((runtime_entry(HERO, "tree"),), (axis(),)),  # a value the key does not declare
        ((runtime_entry(HERO, None),), (axis(),)),  # a key with an axis needs a value
        ((runtime_entry(HERO, "bush"),), ()),  # a value on a key with no declared axis
        ((runtime_entry(HERO, "plain"), runtime_entry(HERO, "bush", HASH_B)), (axis(),)),  # unsorted slots
        ((runtime_entry(HERO, "bush"), runtime_entry(HERO, "bush", HASH_B)), (axis(),)),  # duplicate slot
        ((runtime_entry(HERO, "bush"),), (axis(), axis())),  # duplicate details
        ((runtime_entry(HERO, "bush"),), (axis(key=ROCK), axis())),  # unsorted details
    ):
        with pytest.raises(ValidationError):
            RuntimeManifest(**runtime(entries, details))


def test_a_runtime_manifest_with_no_axes_omits_the_details_block_so_old_bytes_stay_identical():
    plain = RuntimeManifest(**runtime((runtime_entry(ROCK, None),), ()))
    assert b"details" not in canonical_json(plain) and b"detail" not in canonical_json(plain)


def test_a_manifest_has_at_most_max_detail_keys_details(monkeypatch):
    monkeypatch.setattr(config, "MAX_DETAIL_KEYS", 1)
    keys = [s.key_for("hero"), s.key_for("rock")]
    with pytest.raises(ValidationError, match="more than 1 details"):
        RuntimeManifest(**runtime(tuple(runtime_entry(k, "plain", h) for k, h in zip(keys, (HASH_A, HASH_B))), tuple(axis(k, ("plain",)) for k in sorted(keys))))


# ---- export and verify -------------------------------------------------------------------------------------------------------------

def test_the_export_copies_the_declared_axis_and_each_slots_value(tree, tmp_path):
    release(tree)
    out = tmp_path / "out"
    manifest = runtime_export.export_runtime("main", "rc-0001", out, allow_fixture_namespace=True)
    assert [(e.visual_key, e.detail) for e in manifest.entries] == [(HERO, "bush"), (HERO, "plain")]
    assert [(d.visual_key, d.values, d.default) for d in manifest.details] == [(HERO, ("plain", "bush", "tree"), "plain")]  # declared order, tree has no art
    assert parse_record(RuntimeManifest, (out / "runtime_manifest.json").read_bytes()) == manifest


def codes(env):
    return sorted(f.code for f in verify(env.catalog, allow_fixture_namespace=True) if f.blocking)


def test_verify_is_clean_and_flags_an_undeclared_detail_in_an_adoption_and_in_a_manifest(tree):
    release(tree)
    assert codes(tree) == []
    s.write_registry(tree.catalog, [HERO], detail={HERO: (("plain", "tree"), "plain")})
    assert codes(tree) == ["ADOPTION_UNKNOWN_DETAIL", "MANIFEST_UNKNOWN_DETAIL"]


def test_a_manifest_that_predates_the_declaration_is_tolerated(env):
    s.CALLS.clear()
    env.adoptions, env.built = s.adopted_tree(env)
    s.write_registry(env.catalog, [HERO, ROCK])
    release(env)
    s.write_registry(env.catalog, [HERO, ROCK], detail={HERO: (("plain", "bush"), "plain")})  # the axis is declared AFTER rc-0001
    assert codes(env) == []


def test_verify_reports_a_manifest_with_a_duplicate_slot_as_unreadable(tree):
    release(tree)
    path = tree.catalog / "manifests" / "candidates" / "main" / "rc-0001.json"
    data = json.loads(path.read_bytes())
    data["entries"][1]["detail"] = "bush"
    path.write_bytes(json.dumps(data, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    assert "MANIFEST_UNREADABLE" in codes(tree)


def test_the_committed_catalog_fills_each_declared_slot_of_terrain_forest_once_and_the_pilot_adoption_still_names_none():
    from tests.visual_assets import adopted_facts as af

    forest = load_registry().keys["terrain.forest"]
    assert [(detail, records.slot_holders(forest, detail)) for detail in forest.detail.values] == [
        ("plain", ["terrain_forest"]), ("bush", ["terrain_forest_bush"]), ("tree", ["terrain_forest_tree"]),
    ]
    # the pilot adoption was made before the axis existed: it names no detail value and fills the default, with no re-adoption
    assert records.load_adoption("ad-caf09a15bd89d2af").detail_value is None
    # the owner's adoption of terrain-v1 (2026-10-05T18:17:03Z) added 22 terrain tiles (no detail axis: None) and 9 border masks, each naming its v1-v3 value
    expected = {"terrain_forest": None, "terrain_forest_bush": "bush", "terrain_forest_tree": "tree"}
    expected.update({source: None for source in af.TERRAIN_SOURCES})
    expected.update({source: source.rsplit("_", 1)[1] for source in af.BORDER_SOURCES})
    assert {a.source_asset_id: a.detail_value for a in (records.load_adoption(p.stem) for p in sorted(records.adoptions_dir().glob("*.json")))} == expected


# ---- the client parser accepts and rejects the same manifests -----------------------------------------------------------------------

CASES = json.loads((config.CATALOG_ROOT.parent.parent / "frontend" / "src" / "visualAssets" / "__fixtures__" / "detail_cases.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_the_shared_detail_cases_are_decided_as_the_client_parser_decides_them(case):
    """`frontend/src/visualAssets/__tests__/manifest.test.ts` runs the SAME file through `parseManifest`; the two must agree on every case."""
    data = json.dumps(case["manifest"]).encode()
    if case["accept"]:
        parse_record(RuntimeManifest, data)
    else:
        with pytest.raises(ContractError):
            parse_record(RuntimeManifest, data)
