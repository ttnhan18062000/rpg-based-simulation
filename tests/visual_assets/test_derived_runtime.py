"""The derivation helper cannot drift from the store, and a registry-only change no longer breaks the fixture guards (`TCK-20261008-VISUAL-ASSETS-FIXTURE-GUARD-DECOUPLING`).

1. Drift guard: on the hermetic rehearsal catalog, `derived_runtime.derive` equals `export_runtime`'s output byte for byte (the manifest and every PNG).
2. Decoupling proof: after a key is registered (the registry hash moves), `export_runtime` of the old candidate is refused with `registry_mismatch` (the store's refusal, unchanged),
   while `derive` still equals what the export was before the change.
3. Content changes still fail: a PNG whose bytes no longer match the pixel hash the candidate records, and a dropped artifact.
"""

from __future__ import annotations

import filecmp
import json
import shutil

import pytest

from tests.visual_assets import derived_runtime
from tests.visual_assets.store import runtime_fixture as rf
from visual_assets.store import config
from visual_assets.store.errors import BuildError
from visual_assets.store.runtime_export import MANIFEST_NAME, export_runtime


@pytest.fixture(scope="module")
def catalog(tmp_path_factory):
    base = tmp_path_factory.mktemp("derived-runtime")
    with rf.isolated_roots(base):
        rf.build_catalog(base)
        yield base


def _same(left, right) -> bool:
    return rf.same_tree(left, right)


def test_drift_guard_the_derived_manifest_and_files_equal_the_stores_export_byte_for_byte(catalog, tmp_path):
    exported, derived = tmp_path / "exported", tmp_path / "derived"
    export_runtime(rf.CATALOG_ID, rf.RELEASE_ID, exported, allow_fixture_namespace=True)
    derived_runtime.write(derived, rf.CATALOG_ID, rf.RELEASE_ID, allow_fixture_namespace=True)
    assert sorted(p.name for p in exported.iterdir()) == sorted(p.name for p in derived.iterdir()) and len(list(exported.iterdir())) == 4
    assert _same(exported, derived)


def test_a_registry_only_change_is_refused_by_the_store_but_does_not_move_the_derived_export(catalog, tmp_path):
    before = tmp_path / "before"
    export_runtime(rf.CATALOG_ID, rf.RELEASE_ID, before, allow_fixture_namespace=True)
    registry = config.CATALOG_ROOT / "definitions" / "visual_keys.yaml"
    original = registry.read_text()
    try:
        registry.write_text(original.replace("aliases: []", "  - {key: fixture.rehearsal.throwaway, family: terrain, description: a throwaway key, variant_axes: [], optional: true}\naliases: []"))
        with pytest.raises(BuildError) as refused:
            export_runtime(rf.CATALOG_ID, rf.RELEASE_ID, tmp_path / "after", allow_fixture_namespace=True)
        assert refused.value.code == "registry_mismatch"  # the store's refusal stays
        after = tmp_path / "derived-after"
        derived_runtime.write(after, rf.CATALOG_ID, rf.RELEASE_ID, allow_fixture_namespace=True)
        assert _same(before, after)  # the fixture guards compare against this, so they survive the registry change
    finally:
        registry.write_text(original)


def test_an_artifact_that_no_longer_matches_its_recorded_pixel_hash_fails_the_derivation(catalog, tmp_path):
    out = tmp_path / "ok"
    derived_runtime.write(out, rf.CATALOG_ID, rf.RELEASE_ID, allow_fixture_namespace=True)
    victim = next(p for p in sorted((config.CATALOG_ROOT / "generated").rglob("*.png")))
    original = victim.read_bytes()
    try:
        other = next(p for p in sorted((config.CATALOG_ROOT / "generated").rglob("*.png")) if p != victim)
        victim.write_bytes(other.read_bytes())  # a valid PNG, but a different image than the candidate's entry records
        with pytest.raises(AssertionError, match="does not decode to the pixel hash"):
            derived_runtime.derive(rf.CATALOG_ID, rf.RELEASE_ID, allow_fixture_namespace=True)
    finally:
        victim.write_bytes(original)


def test_a_dropped_artifact_fails_the_derivation(catalog):
    victim = next(p for p in sorted((config.CATALOG_ROOT / "generated").rglob("*.png")))
    kept = victim.read_bytes()
    victim.unlink()
    try:
        with pytest.raises(Exception):
            derived_runtime.derive(rf.CATALOG_ID, rf.RELEASE_ID, allow_fixture_namespace=True)
    finally:
        victim.write_bytes(kept)
