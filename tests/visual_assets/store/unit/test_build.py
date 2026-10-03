"""`build`: adopted sources -> PNG artifacts identified by decoded pixels. The real build code with an injected deterministic renderer."""

from __future__ import annotations

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config, pixels, records
from visual_assets.store.build import exporter
from visual_assets.store.contracts import ArtifactRecord, parse_record
from visual_assets.store.errors import BuildError
from visual_assets.store.intake.validator import file_hash
from visual_assets.store.revoke import revoke


@pytest.fixture(autouse=True)
def _reset():
    s.CALLS.clear()


def artifact_files(env, artifact_id):
    return sorted(p.name for p in (env.catalog / "generated" / artifact_id).iterdir())


def revoke_rev(target):
    revoke(target, reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)


def test_build_writes_a_png_named_by_its_pixel_hash_and_a_record(env):
    adoptions, built = s.adopted_tree(env)
    assert [(b.artifact_id, b.source_revision, b.created) for b in built] == [("hero--x1", "r0001", True), ("rock--x1", "r0001", True)]
    hero = built[0]
    digest = hero.pixel_hash[len("pixels-v1:"):]
    assert artifact_files(env, "hero--x1") == [f"{digest}.png", f"{digest}.r0001.artifact.json"]
    png = (env.catalog / "generated" / "hero--x1" / f"{digest}.png").read_bytes()
    record = parse_record(ArtifactRecord, (env.catalog / "generated" / "hero--x1" / f"{digest}.r0001.artifact.json").read_bytes())
    assert pixels.pixel_hash(png) == record.pixel_hash == hero.pixel_hash and record.png_hash == file_hash(png)
    source = records.load_source("hero", "r0001")
    assert (record.source_asset_id, record.source_revision, record.source_hash) == ("hero", "r0001", source.source_hash)
    assert record.source_record_hash == file_hash((env.catalog / "sources" / "hero" / "r0001.source.json").read_bytes())  # chain anchoring
    assert record.scale_class == "x1" and (record.width, record.height) == (16, 16)
    assert (record.build.tool_name, record.build.tool_version) == ("Aseprite", "1.3.test")
    assert record.build.export_config_hash == file_hash((env.catalog / "build-config" / "export.toml").read_bytes())
    assert record.build.lua_pin_hash == "sha256:" + exporter.sandbox.config.LUA_SHA256


def test_building_twice_gives_the_same_hash_and_one_artifact_file(env):
    _, first = s.adopted_tree(env)
    before = snapshot(env.catalog)
    again = exporter.build(renderer=s.HashRenderer())
    assert [(b.pixel_hash, b.created) for b in again] == [(b.pixel_hash, False) for b in first]
    assert snapshot(env.catalog) == before
    assert len(artifact_files(env, "hero--x1")) == 2  # one PNG, one record


def test_a_new_revision_adds_history_and_keeps_the_old_artifact(env):
    s.adopted_tree(env)
    old = exporter.build("hero", renderer=s.HashRenderer())[0]
    new_intake = s.make_intake(env.tmp, 18)
    s.do_adopt(new_intake.intake_id, new=False, parent="r0001")
    built = exporter.build("hero", renderer=s.HashRenderer())
    assert built[0].source_revision == "r0002" and built[0].created and built[0].pixel_hash != old.pixel_hash
    names = artifact_files(env, "hero--x1")
    assert len(names) == 4 and any(".r0001." in n for n in names) and any(".r0002." in n for n in names)  # history is kept


def test_identical_pixels_from_a_newer_revision_share_the_png_and_get_their_own_record(env):
    same = s.ConstantRenderer()  # every revision renders the same image
    s.adopted_tree(env, renderer=same)
    s.do_adopt(s.make_intake(env.tmp, 18).intake_id, new=False, parent="r0001")
    built = exporter.build("hero", renderer=same)
    assert built[0].created and built[0].source_revision == "r0002"
    names = artifact_files(env, "hero--x1")
    assert sum(n.endswith(".png") for n in names) == 1 and sum(n.endswith(".artifact.json") for n in names) == 2
    new = next(n for n in names if ".r0002." in n)
    record = parse_record(ArtifactRecord, (env.catalog / "generated" / "hero--x1" / new).read_bytes())
    png = (env.catalog / "generated" / "hero--x1" / names[0 if names[0].endswith(".png") else -1]).read_bytes()
    assert record.png_hash == file_hash(png) and pixels.pixel_hash(png) == record.pixel_hash


def test_only_the_latest_eligible_revision_of_each_asset_is_exported(env):
    s.adopted_tree(env, widths=(16,), build=False)  # nothing built yet
    s.do_adopt(s.make_intake(env.tmp, 18).intake_id, new=False, parent="r0001")
    built = exporter.build(renderer=s.HashRenderer())
    assert [(b.artifact_id, b.source_revision) for b in built] == [("hero--x1", "r0002")]
    assert not any(".r0001." in n for n in artifact_files(env, "hero--x1"))  # r0001 was never built (nor needs to be)


def test_a_revoked_revision_is_skipped_and_the_previous_live_one_is_built(env):
    s.adopted_tree(env, widths=(16,))
    s.do_adopt(s.make_intake(env.tmp, 18).intake_id, new=False, parent="r0001")
    revoke_rev("hero/r0002")
    assert [(b.source_revision) for b in exporter.build("hero", renderer=s.HashRenderer())] == ["r0001"]


def test_an_asset_with_every_revision_revoked_is_refused_by_name_and_skipped_in_a_full_build(env):
    s.adopted_tree(env)
    revoke_rev("rock/r0001")
    before = snapshot(env.catalog)
    with pytest.raises(BuildError) as err:
        exporter.build("rock", renderer=s.HashRenderer())
    assert err.value.code == "source_revoked" and snapshot(env.catalog) == before
    assert [b.artifact_id for b in exporter.build(renderer=s.HashRenderer())] == ["hero--x1"]


def test_unknown_assets_and_a_missing_renderer_are_refused_before_writing(env, monkeypatch):
    s.adopted_tree(env)
    before = snapshot(env.catalog)
    with pytest.raises(BuildError) as err:
        exporter.build("ghost", renderer=s.HashRenderer())
    assert err.value.code == "unknown_source_asset"
    monkeypatch.setattr(exporter, "default_renderer", lambda: None)
    with pytest.raises(BuildError) as err:
        exporter.build()
    assert err.value.code == "renderer_unavailable" and snapshot(env.catalog) == before


def test_a_render_that_is_not_reproducible_is_refused(env):
    s.adopted_tree(env, widths=(16,))

    class Flaky(s.HashRenderer):
        def render(self, source, *, scale):
            return s.FakeRenderer().render(source, scale=scale)  # different pixels than the first build

    before = snapshot(env.catalog)
    with pytest.raises(BuildError) as err:
        exporter.build("hero", renderer=Flaky())
    assert err.value.code == "nondeterministic_render" and snapshot(env.catalog) == before


def test_a_changed_source_is_refused_not_exported(env):
    s.adopted_tree(env, widths=(16,))
    (env.catalog / "sources" / "hero" / "r0001.aseprite").write_bytes(b"tampered")
    with pytest.raises(BuildError) as err:
        exporter.build("hero", renderer=s.HashRenderer())
    assert err.value.code == "source_bytes_changed"


def test_renderer_and_decoder_problems_are_coded_and_write_nothing(env):
    from visual_assets.store.errors import RenderError

    s.write_export_config(env.catalog)
    s.do_adopt(s.make_intake(env.tmp, 16).intake_id)
    before = snapshot(env.catalog)

    class Broken(s.HashRenderer):
        def render(self, source, *, scale):
            raise RenderError("render_failed", "boom")

    class NotPng(s.HashRenderer):
        def render(self, source, *, scale):
            return b"nope"

    for renderer, code in ((Broken(), "render_failed"), (NotPng(), "render_undecodable")):
        with pytest.raises(BuildError) as err:
            exporter.build(renderer=renderer)
        assert err.value.code == code and snapshot(env.catalog) == before


def test_a_stored_png_that_does_not_match_its_name_is_refused(env):
    same = s.ConstantRenderer()
    s.adopted_tree(env, widths=(16,), renderer=same)
    s.do_adopt(s.make_intake(env.tmp, 18).intake_id, new=False, parent="r0001")
    png = next((env.catalog / "generated" / "hero--x1").glob("*.png"))
    png.write_bytes(s.FakeRenderer().render(records.read_file(env.catalog / "sources" / "hero" / "r0001.aseprite", 10**6), scale=2))
    with pytest.raises(BuildError) as err:
        exporter.build("hero", renderer=same)
    assert err.value.code == "artifact_corrupt"


def test_a_missing_or_invalid_export_config_stops_the_build(env):
    s.adopted_tree(env, widths=(16,))
    (env.catalog / "build-config" / "export.toml").write_text("format = 'gif'\n")
    with pytest.raises(BuildError) as err:
        exporter.build(renderer=s.HashRenderer())
    assert err.value.code == "export_config_invalid"
    assert config.CATALOG_ROOT == env.catalog
