"""`verify`: a clean store passes; each planted fault gets its own specific finding. Pure Python, so CI runs it without Aseprite."""

from __future__ import annotations

import json
import shutil

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store import builders as b
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config, records
from visual_assets.store.release import assemble_release
from visual_assets.store.revoke import revoke
from visual_assets.store.verify import verify

HERO, ROCK = s.key_for("hero"), s.key_for("rock")


@pytest.fixture
def tree(env):
    s.CALLS.clear()
    env.adoptions, env.built = s.adopted_tree(env)
    s.write_registry(env.catalog, [HERO, ROCK])
    assemble_release("main", allow_fixture_namespace=True)
    return env


def run(env, **kw):
    return verify(env.catalog, allow_fixture_namespace=True, **kw)


def codes(findings, blocking_only=False):
    return sorted(f.code for f in findings if f.blocking or not blocking_only)


def edit(path, **changes):
    data = json.loads(path.read_bytes())
    data.update(changes)
    path.write_bytes(json.dumps(data, sort_keys=True, separators=(",", ":")).encode() + b"\n")


def art(env, artifact="hero--x1"):
    directory = env.catalog / "generated" / artifact
    return next(directory.glob("*.png")), next(directory.glob("*.artifact.json"))


def test_a_clean_synthetic_store_passes(tree):
    assert run(tree) == []


def test_an_empty_store_with_the_layout_files_passes(env):
    s.write_store_format(env.catalog)
    s.write_registry(env.catalog, [])
    assert run(env) == []


def test_verify_is_read_only(tree):
    before = snapshot(tree.catalog)
    run(tree)
    assert snapshot(tree.catalog) == before


def test_an_edited_png_pixel_is_reported(tree):
    png, record = art(tree)
    png.write_bytes(b.png_encode(16, 16, b.sample_pixels(16, 16)))
    found = codes(run(tree))
    assert "ARTIFACT_PIXEL_MISMATCH" in found and "ARTIFACT_PNG_HASH_MISMATCH" in found


def test_a_png_renamed_to_another_hash_is_reported(tree):
    png, record = art(tree)
    png.rename(png.with_name("0" * 64 + ".png"))
    found = codes(run(tree))
    assert "ARTIFACT_PNG_MISSING" in found and "ORPHAN_FILE" in found  # the record has no PNG; the renamed file belongs to no record


def test_a_deleted_artifact_record_is_reported(tree):
    png, record = art(tree)
    record.unlink()
    found = run(tree)
    assert "ORPHAN_FILE" in codes(found) and any(f.path.endswith(".png") for f in found if f.code == "ORPHAN_FILE")
    assert "MANIFEST_DANGLING" in codes(found)  # and the manifest now points at a missing artifact


def test_an_orphan_file_in_generated_is_reported(tree):
    (tree.catalog / "generated" / "hero--x1" / "notes.txt").write_text("stray")
    (tree.catalog / "generated" / "loose.txt").write_text("stray")
    assert codes(run(tree)) == ["ORPHAN_FILE", "ORPHAN_FILE"]


def test_a_manifest_pointing_at_a_missing_artifact_is_reported(tree):
    png, record = art(tree, "rock--x1")
    png.unlink()
    record.unlink()
    assert "MANIFEST_DANGLING" in codes(run(tree))


def test_a_manifest_pointing_at_a_revoked_source_is_reported_as_blocking(tree):
    revoke("hero/r0001", reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    found = run(tree)
    assert "MANIFEST_ENTRY_SOURCE_REVOKED" in codes(found, blocking_only=True)
    assert "ARTIFACT_SOURCE_REVOKED" in codes(found) and "ARTIFACT_SOURCE_REVOKED" not in codes(found, blocking_only=True)  # history, not a fault


def test_an_artifact_of_a_revoked_source_is_visible_history_and_not_blocking_without_a_release(env):
    s.adopted_tree(env)
    s.write_registry(env.catalog, [HERO, ROCK])
    revoke("hero/r0001", reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    found = run(env)
    assert [f.code for f in found] == ["ARTIFACT_SOURCE_REVOKED"] and found[0].blocking is False


def test_a_stray_file_in_sources_is_reported(tree):
    (tree.catalog / "sources" / "hero" / "notes.txt").write_text("stray")
    found = run(tree)
    assert any(f.code == "ORPHAN_FILE" and f.path == "sources/hero/notes.txt" for f in found)


def test_unexpected_files_in_the_tracked_tree_are_reported(tree):
    (tree.catalog / "secrets.txt").write_text("x")
    (tree.catalog / "definitions" / "extra.yaml").write_text("x")
    (tree.catalog / "manifests" / "stray.json").write_text("{}")
    (tree.catalog / "provenance" / "notes.md").write_text("x")
    found = [f for f in run(tree) if f.code == "UNEXPECTED_FILE"]
    assert sorted(f.path for f in found) == ["definitions/extra.yaml", "manifests/stray.json", "provenance/notes.md", "secrets.txt"]


def test_a_manifest_directory_never_names_an_active_release(tree):
    base = tree.catalog / "manifests" / "candidates" / "main"
    shutil.copyfile(base / "rc-0001.json", base / "active.json")
    shutil.copyfile(base / "rc-0001.json", base / "latest-rc.json")
    assert [f.code for f in run(tree)] == ["UNEXPECTED_FILE", "UNEXPECTED_FILE"]


def test_artifact_records_are_checked_against_their_source(tree):
    png, record = art(tree)
    edit(record, source_record_hash="sha256:" + "5" * 64)
    assert codes(run(tree)) == ["ARTIFACT_SOURCE_RECORD_MISMATCH"]
    edit(record, source_hash="sha256:" + "6" * 64, source_record_hash=json.loads(record.read_bytes())["source_record_hash"])
    assert "ARTIFACT_SOURCE_RECORD_MISMATCH" in codes(run(tree))


def test_an_artifact_whose_source_revision_is_gone_is_reported(tree):
    for name in ("r0001.source.json", "r0001.aseprite"):
        (tree.catalog / "sources" / "hero" / name).unlink()
    assert "ARTIFACT_SOURCE_MISSING" in codes(run(tree))


def test_an_artifact_record_that_does_not_match_its_name_is_reported(tree):
    png, record = art(tree)
    edit(record, artifact_id="rock--x1")
    assert "ARTIFACT_NAME_MISMATCH" in codes(run(tree))
    record.write_text("garbage")
    assert "ARTIFACT_RECORD_UNREADABLE" in codes(run(tree))


def test_manifest_problems_are_reported(tree):
    base = tree.catalog / "manifests" / "candidates" / "main"
    manifest = base / "rc-0001.json"
    original = manifest.read_bytes()
    edit(manifest, release_id="rc-0009")
    assert "MANIFEST_MISMATCH" in codes(run(tree))
    manifest.write_bytes(original)
    edit(manifest, entries=[{"visual_key": "fixture.sample.unlisted", "artifact_id": "hero--x1", "pixel_hash": tree.built[0].pixel_hash}])
    assert "MANIFEST_UNKNOWN_KEY" in codes(run(tree))
    manifest.write_text("garbage")
    assert "MANIFEST_UNREADABLE" in codes(run(tree))


def test_store_format_and_registry_problems_are_reported(tree):
    (tree.catalog / "STORE_FORMAT").write_text("store_format_version: 2\n")
    assert "STORE_FORMAT_UNSUPPORTED" in codes(run(tree))
    (tree.catalog / "STORE_FORMAT").unlink()
    assert "STORE_FORMAT_MISSING" in codes(run(tree))
    (tree.catalog / "STORE_FORMAT").write_text("store_format_version: 1\n")
    (tree.catalog / "definitions" / "visual_keys.yaml").write_text("keys: [")
    assert "REGISTRY_INVALID" in codes(run(tree))


def test_build_config_problems_are_reported(tree):
    config_path = tree.catalog / "build-config" / "export.toml"
    config_path.write_text("format = 'gif'\n")
    assert "BUILD_CONFIG_INVALID" in codes(run(tree))
    config_path.unlink()
    assert "BUILD_CONFIG_MISSING" in codes(run(tree))


def test_provenance_chain_breaks_are_part_of_verify(tree):
    (tree.catalog / "provenance" / "adoptions" / f"{tree.adoptions[0].adoption_id}.json").unlink()
    assert "ADOPTION_MISSING" in codes(run(tree))


def test_the_default_root_is_the_configured_catalog(tree):
    assert verify(allow_fixture_namespace=True) == [] and config.CATALOG_ROOT == tree.catalog and records.list_source_ids() == ["hero", "rock"]
