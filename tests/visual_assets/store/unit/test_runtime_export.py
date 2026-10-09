"""`export_runtime`: a runtime manifest and its PNGs from one release candidate; every refusal leaves no output and the catalog unchanged."""

from __future__ import annotations

import json
import os

import pytest

from tests.visual_assets.store import runtime_fixture as fx
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config, runtime_export, verify
from visual_assets.store import cli
from visual_assets.store.contracts import RuntimeManifest, parse_record
from visual_assets.store.errors import BuildError
from visual_assets.store.runtime_export import export_runtime

PROVENANCE_WORDS = ("approver", "Approver", "licence", "adoption", "revocation", "source_path", "reviewer", "artifact_id", "intake")


@pytest.fixture
def released(env):
    fx.build_catalog(env.tmp)
    env.out = env.tmp / "out" / "runtime"
    env.out.parent.mkdir()
    return env


def export(env, out=None, **kw):
    return export_runtime(fx.CATALOG_ID, kw.pop("release_id", fx.RELEASE_ID), out or env.out, allow_fixture_namespace=True, **kw)


def refused(env, code, out=None, **kw):
    before_catalog, before_out = snapshot(env.catalog), snapshot(env.out.parent)
    with pytest.raises(BuildError) as err:
        export(env, out, **kw)
    assert err.value.code == code, err.value
    assert snapshot(env.catalog) == before_catalog
    assert snapshot(env.out.parent) == before_out  # no output directory, no .tmp-* leftover


def test_the_export_writes_the_manifest_and_one_png_per_distinct_image(released):
    runtime = export(released)
    names = sorted(p.name for p in released.out.iterdir())
    assert names == sorted(["runtime_manifest.json", *(e.file for e in runtime.entries)])
    assert parse_record(RuntimeManifest, (released.out / "runtime_manifest.json").read_bytes()) == runtime
    assert [e.visual_key for e in runtime.entries] == ["fixture.rehearsal.frame", "fixture.rehearsal.gem", "fixture.rehearsal.rock"]
    assert {e.visual_key: e.family for e in runtime.entries} == {"fixture.rehearsal.gem": "item", "fixture.rehearsal.rock": "terrain", "fixture.rehearsal.frame": "ui"}
    assert all((e.width, e.height) == (16, 16) for e in runtime.entries)


def test_the_manifest_carries_nothing_from_the_protected_provenance(released):
    export(released)
    text = (released.out / "runtime_manifest.json").read_text()
    assert set(json.loads(text)) == {"record_type", "schema_version", "catalog_id", "release_id", "candidate_manifest_hash", "registry_hash",
                                    "fallback_contract_version", "entries"}
    assert not [word for word in PROVENANCE_WORDS if word in text], text
    assert str(released.catalog) not in text and "Pat" not in text


def test_the_candidate_manifest_hash_names_the_exact_candidate_bytes(released):
    import hashlib

    runtime = export(released)
    path = released.catalog / "manifests" / "candidates" / fx.CATALOG_ID / f"{fx.RELEASE_ID}.json"
    assert runtime.candidate_manifest_hash == "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_two_exports_of_the_same_release_are_byte_identical(released):
    export(released, released.tmp / "out" / "a")
    export(released, released.tmp / "out" / "b")
    assert snapshot(released.tmp / "out" / "a") == snapshot(released.tmp / "out" / "b")


def test_the_export_does_not_change_the_catalog(released):
    before = snapshot(released.catalog)
    export(released)
    assert snapshot(released.catalog) == before


def _verify_must_not_run(monkeypatch):
    """Output problems are refused up front, before the (slow) whole-store verify and before anything is read."""
    def boom(*a, **k):
        raise AssertionError("verify ran before the output was checked")

    monkeypatch.setattr(verify, "verify", boom)


def test_an_existing_output_is_refused_even_a_dangling_symlink(released, monkeypatch):
    _verify_must_not_run(monkeypatch)
    released.out.mkdir()
    refused(released, "out_exists")
    other = released.tmp / "out" / "link"
    other.symlink_to(released.tmp / "nowhere")
    refused(released, "out_exists", out=other)


def test_an_output_inside_the_catalog_is_refused(released, monkeypatch):
    _verify_must_not_run(monkeypatch)
    refused(released, "out_inside_catalog", out=released.catalog / "runtime")
    refused(released, "out_inside_catalog", out=released.catalog / "generated" / "runtime")


def test_an_output_whose_parent_is_a_symlink_into_the_catalog_is_refused(released, monkeypatch):
    _verify_must_not_run(monkeypatch)
    link = released.tmp / "out" / "into-catalog"
    link.symlink_to(released.catalog)
    refused(released, "out_inside_catalog", out=link / "runtime")


def test_an_unknown_release_is_refused(released):
    refused(released, "unknown_release", release_id="rc-0099")


def test_invalid_ids_are_refused(released):
    with pytest.raises(BuildError) as err:
        export_runtime("Bad Id", fx.RELEASE_ID, released.out, allow_fixture_namespace=True)
    assert err.value.code == "invalid_catalog_id"
    with pytest.raises(BuildError) as err:
        export_runtime(fx.CATALOG_ID, "latest", released.out, allow_fixture_namespace=True)
    assert err.value.code == "invalid_release_id"


def _first_png(env):
    return next((env.catalog / "generated").rglob("*.png"))


def test_a_store_that_fails_verify_is_refused(released):
    _first_png(released).write_bytes(b"not a png")
    refused(released, "verify_failed")


def test_an_artifact_that_does_not_match_its_pixel_hash_is_refused(released, monkeypatch):
    monkeypatch.setattr(verify, "verify", lambda *a, **k: [])  # verify would catch this first; here the export's own check is what is under test
    png = _first_png(released)
    png.write_bytes(fx.shape_png("disc", (1, 2, 3)))  # a valid PNG of the right size but other pixels
    refused(released, "artifact_mismatch")


def test_a_missing_artifact_is_refused_as_a_mismatch(released, monkeypatch):
    monkeypatch.setattr(verify, "verify", lambda *a, **k: [])
    _first_png(released).unlink()
    refused(released, "artifact_mismatch")


def test_a_key_left_without_an_alternative_is_refused_at_export_time(released, monkeypatch):
    """`AM1-W06.3` at activation: the same check as at release time, run again when the client's manifest is written."""
    monkeypatch.setattr(verify, "verify", lambda *a, **k: [])
    seen = {}

    def problems(registry, present):
        seen["present"] = set(present)
        return ["real.x.y: identifying key has no image in this release and no alternative that carries its fact"]

    monkeypatch.setattr(runtime_export, "fallback_problems", problems)
    real_load = runtime_export.load_registry

    def with_an_extra_key_without_an_image(*args, **kwargs):  # same file hash, so the registry-mismatch refusal stays quiet; one more optional key that has no artifact
        from visual_assets.store.catalog.registry import Registry
        from visual_assets.store.contracts.definitions import Fallback, VisualKeyDefinition

        registry = real_load(*args, **kwargs)
        extra = VisualKeyDefinition(key="fixture.rehearsal.noimage", family="terrain", description="d", variant_axes=(), optional=True, safety_class="identifying", fallback=Fallback(kind="text", text="t"))
        return Registry({**registry.keys, extra.key: extra}, dict(registry.aliases), registry.file_hash)

    monkeypatch.setattr(runtime_export, "load_registry", with_an_extra_key_without_an_image)
    refused(released, "fallback_missing")
    assert seen["present"] == {key for _, key, *_ in fx.ASSETS}  # it is asked about exactly the keys the release has images for, not every registry key


def test_a_registry_changed_since_the_candidate_was_assembled_is_refused(released, monkeypatch):
    monkeypatch.setattr(verify, "verify", lambda *a, **k: [])
    path = released.catalog / "definitions" / "visual_keys.yaml"
    path.write_text(path.read_text().replace("synthetic rehearsal image", "a changed description"))
    refused(released, "registry_mismatch")


def test_a_failure_while_writing_leaves_no_output_and_no_temp_directory(released, monkeypatch):
    calls = {"n": 0}
    real = runtime_export._write_new

    def failing(path, data):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk full")
        real(path, data)

    monkeypatch.setattr(runtime_export, "_write_new", failing)
    before = snapshot(released.out.parent)
    with pytest.raises(OSError):
        export(released)
    assert calls["n"] == 2 and snapshot(released.out.parent) == before


def test_an_output_that_appears_during_the_export_is_not_replaced(released, monkeypatch):
    real = os.rename

    def racing(src, dst):
        os.mkdir(dst)
        (os.path.join(dst, "keep.txt") and open(os.path.join(dst, "keep.txt"), "w")).close()
        real(src, dst)

    monkeypatch.setattr(runtime_export.os, "rename", racing)
    with pytest.raises(BuildError) as err:
        export(released)
    assert err.value.code == "out_exists" and [p.name for p in released.out.iterdir()] == ["keep.txt"]
    assert not [p for p in released.out.parent.iterdir() if p.name.startswith(".tmp-")]


def test_the_cli_exports_and_refuses_with_exit_code_2(released, capsys, monkeypatch):
    monkeypatch.setattr(runtime_export, "export_runtime", lambda c, r, o, **kw: export_runtime(c, r, o, allow_fixture_namespace=True))
    assert cli.main(["export-runtime", "--catalog-id", fx.CATALOG_ID, "--release-id", fx.RELEASE_ID, "--out", str(released.out)]) == 0
    assert "3 entries exported" in capsys.readouterr().out
    assert cli.main(["export-runtime", "--catalog-id", fx.CATALOG_ID, "--release-id", fx.RELEASE_ID, "--out", str(released.out)]) == 2
    assert "out_exists" in capsys.readouterr().err
