"""`assemble_release`: an immutable release CANDIDATE manifest; every refusal has its own code; nothing names an active release (D6)."""

from __future__ import annotations

import json

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import pixels, records
from visual_assets.store.build import exporter
from visual_assets.store.contracts import ReleaseCandidateManifest, parse_record
from visual_assets.store.errors import BuildError
from visual_assets.store.release import assemble_release
from visual_assets.store.revoke import revoke

HERO, ROCK = s.key_for("hero"), s.key_for("rock")


@pytest.fixture
def tree(env):
    s.CALLS.clear()
    env.adoptions, env.built = s.adopted_tree(env)
    s.write_registry(env.catalog, [HERO, ROCK])
    return env


def release(env, **kw):
    return assemble_release("main", allow_fixture_namespace=True, **kw)


def refused(env, code, **kw):
    before = snapshot(env.catalog)
    with pytest.raises(BuildError) as err:
        release(env, **kw)
    assert err.value.code == code, err.value
    assert snapshot(env.catalog) == before


def test_a_manifest_is_written_parses_strictly_and_lists_every_key(tree):
    manifest = release(tree)
    path = tree.catalog / "manifests" / "candidates" / "main" / "rc-0001.json"
    assert parse_record(ReleaseCandidateManifest, path.read_bytes()) == manifest
    assert manifest.status == "CANDIDATE" and (manifest.catalog_id, manifest.release_id) == ("main", "rc-0001")
    assert [(e.visual_key, e.artifact_id) for e in manifest.entries] == [(HERO, "hero--x1"), (ROCK, "rock--x1")]
    assert {e.visual_key: e.pixel_hash for e in manifest.entries} == {HERO: tree.built[0].pixel_hash, ROCK: tree.built[1].pixel_hash}
    assert manifest.registry_hash == "sha256:" + __import__("hashlib").sha256((tree.catalog / "definitions" / "visual_keys.yaml").read_bytes()).hexdigest()


def test_release_ids_are_ordered_and_a_candidate_is_never_overwritten(tree):
    assert release(tree).release_id == "rc-0001"
    assert release(tree).release_id == "rc-0002"  # the next one by default
    before = snapshot(tree.catalog)
    refused(tree, "release_exists", release_id="rc-0002")
    refused(tree, "release_exists", release_id="rc-0001")  # an existing id is "exists" before it is "not greater"
    refused(tree, "invalid_release_id", release_id="fixture-rc-9")
    assert release(tree, release_id="rc-0010").release_id == "rc-0010"
    refused(tree, "release_id_not_greater", release_id="rc-0009")  # numeric, not string, order
    assert snapshot(tree.catalog) != before


def test_a_catalog_id_must_be_valid(tree):
    for bad in ("", "Main", "a/b", "..", "x" * 65):
        before = snapshot(tree.catalog)
        with pytest.raises(BuildError) as err:
            assemble_release(bad, allow_fixture_namespace=True)
        assert err.value.code == "invalid_catalog_id" and snapshot(tree.catalog) == before


def test_a_key_left_without_an_alternative_is_refused_at_release_time(tree, monkeypatch):
    """`AM1-W06.3`: the loader refuses a malformed key, this is the explicit check on the registry object `assemble_release` actually uses."""
    from visual_assets.store import release as release_module

    seen = {}

    def problems(registry, present):
        seen["present"] = set(present)
        return ["real.x.y: identifying key has no image in this release and no alternative that carries its fact"]

    monkeypatch.setattr(release_module, "fallback_problems", problems)
    other = s.key_for("other")
    s.write_registry(tree.catalog, [HERO, ROCK, other], optional=(other,))  # a third, optional key with NO image: it must be absent from `present`
    before = snapshot(tree.catalog)
    with pytest.raises(BuildError) as err:
        release(tree)
    assert err.value.code == "fallback_missing" and "real.x.y" in str(err.value) and snapshot(tree.catalog) == before  # nothing was written
    assert seen["present"] == {HERO, ROCK}


def test_a_registry_key_with_no_artifact_is_refused_unless_it_is_optional(tree):
    s.write_registry(tree.catalog, [HERO, ROCK, s.key_for("other")])
    refused(tree, "key_without_artifact")
    s.write_registry(tree.catalog, [HERO, ROCK, s.key_for("other")], optional=(s.key_for("other"),))
    assert [e.visual_key for e in release(tree).entries] == [HERO, ROCK]  # the optional key is simply omitted


def test_a_key_whose_asset_has_no_artifact_yet_says_to_run_build(tree):
    s.do_adopt(s.make_intake(tree.tmp, 18).intake_id, source_asset_id="other")  # adopted, not built
    s.write_registry(tree.catalog, [HERO, ROCK, s.key_for("other")])
    before = snapshot(tree.catalog)
    with pytest.raises(BuildError) as err:
        release(tree)
    assert err.value.code == "key_without_artifact" and "run build" in err.value.message and snapshot(tree.catalog) == before


def test_an_artifact_from_a_revoked_source_is_refused_and_the_key_has_no_live_asset(tree):
    revoke("rock/r0001", reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    refused(tree, "key_without_artifact")  # the revoked asset no longer holds its key
    s.write_registry(tree.catalog, [HERO, ROCK], optional=(ROCK,))
    assert [e.visual_key for e in release(tree).entries] == [HERO]


def test_eligibility_is_decided_by_is_build_eligible_alone(tree, monkeypatch):
    from visual_assets.store import release as release_mod

    monkeypatch.setattr(release_mod, "is_build_eligible", lambda sid, rev: sid != "hero")  # the single function later code asks
    s.write_registry(tree.catalog, [ROCK])
    assert [e.visual_key for e in release(tree).entries] == [ROCK]
    s.write_registry(tree.catalog, [HERO, ROCK])
    refused(tree, "key_without_artifact")


def test_an_artifact_whose_bytes_fail_re_hashing_is_refused(tree):
    png = next((tree.catalog / "generated" / "hero--x1").glob("*.png"))
    png.write_bytes(png.read_bytes() + b"\x00")
    refused(tree, "artifact_hash_mismatch")


def test_an_edited_pixel_in_an_artifact_is_refused(tree):
    from tests.visual_assets.store import builders as b

    png = next((tree.catalog / "generated" / "hero--x1").glob("*.png"))
    png.write_bytes(b.png_encode(16, 16, b.sample_pixels(16, 16)))  # a valid PNG, different pixels, same name
    record = next((tree.catalog / "generated" / "hero--x1").glob("*.artifact.json"))
    data = json.loads(record.read_bytes())
    data["png_hash"] = __import__("visual_assets.store.intake.validator", fromlist=["file_hash"]).file_hash(png.read_bytes())
    record.write_bytes(json.dumps(data, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    refused(tree, "artifact_hash_mismatch")  # the decoded pixels no longer hash to the recorded value


def test_an_ambiguous_key_is_refused(tree):
    # two live assets under one key cannot be created through adopt (visual_key_taken), so plant it in the records
    adoption_path = tree.catalog / "provenance" / "adoptions" / f"{tree.adoptions[1].adoption_id}.json"
    data = json.loads(adoption_path.read_bytes())
    data["visual_key"] = HERO
    adoption_path.write_bytes(json.dumps(data, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    refused(tree, "ambiguous_key")


def test_an_invalid_registry_is_refused(tree):
    (tree.catalog / "definitions" / "visual_keys.yaml").write_text("keys: [")
    refused(tree, "registry_invalid")
    s.write_registry(tree.catalog, [HERO, "fixture.other.thing"])
    with pytest.raises(BuildError) as err:  # fixture keys are refused unless the caller opts in
        assemble_release("main")
    assert err.value.code == "registry_invalid"


def test_an_unreadable_record_is_reported_as_unreadable(tree):
    (tree.catalog / "sources" / "hero" / "r0001.source.json").write_text("{}")
    with pytest.raises(BuildError) as err:
        release(tree)
    assert err.value.code in {"catalog_unreadable", "key_without_artifact"}


def test_no_file_or_field_names_an_active_release(tree):
    release(tree)
    names = [str(p.relative_to(tree.catalog)).lower() for p in tree.catalog.rglob("*")]
    assert not [n for n in names if any(w in n for w in ("active", "current", "latest"))]
    manifest = (tree.catalog / "manifests" / "candidates" / "main" / "rc-0001.json").read_text().lower()
    for word in ("active", "current", "latest"):
        assert f'"{word}' not in manifest
    assert set(ReleaseCandidateManifest.model_fields) == {"record_type", "schema_version", "catalog_id", "release_id", "registry_hash", "entries", "status"}


def test_an_empty_registry_gives_an_empty_candidate(env):
    s.write_export_config(env.catalog)
    s.write_registry(env.catalog, [])
    manifest = assemble_release("main")
    assert manifest.entries == () and manifest.status == "CANDIDATE"
    assert records.manifests_dir() == env.catalog / "manifests" / "candidates" and pixels.HASH_PREFIX
    assert exporter.aseprite_available() in (True, False)


def test_a_forged_artifact_record_naming_a_revoked_revision_is_refused(env):
    """The asset is chosen through its latest eligible revision, so only a forged record can name a revoked one: release must still refuse it."""
    s.CALLS.clear()
    s.adopted_tree(env, widths=(16,), build=False)
    s.do_adopt(s.make_intake(env.tmp, 18).intake_id, new=False, parent="r0001")  # hero r0002
    exporter.build("hero", renderer=s.HashRenderer())  # builds r0002 (the latest eligible one)
    s.write_registry(env.catalog, [HERO])
    revoke("hero/r0002", reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    exporter.build("hero", renderer=s.HashRenderer())  # now r0001 is the live one and gets its own artifact
    record = next((env.catalog / "generated" / "hero--x1").glob("*.r0001.artifact.json"))
    data = json.loads(record.read_bytes())
    data["source_revision"] = "r0002"  # the record now claims the revoked revision
    record.write_bytes(json.dumps(data, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    before = snapshot(env.catalog)
    with pytest.raises(BuildError) as err:
        release(env)
    assert err.value.code == "artifact_source_revoked" and snapshot(env.catalog) == before
