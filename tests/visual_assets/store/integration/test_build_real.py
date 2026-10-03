"""The real sandboxed exporter end to end with real files: draw, hand off, intake, store-render review, adopt (re-render), build. Needs Aseprite + bwrap."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.drawing import api, handoff
from visual_assets.drawing import config as drawing_config
from visual_assets.store import config, pixels
from visual_assets.store import review as review_mod
from visual_assets.store.build import exporter
from visual_assets.store.contracts import ArtifactRecord, parse_record
from visual_assets.store.contracts.review import RenderVerdict
from visual_assets.store.errors import BuildError, GateError
from visual_assets.store.intake import intake
from visual_assets.store.revoke import revoke

pytestmark = pytest.mark.needs_aseprite


@pytest.fixture
def world(tmp_path, monkeypatch):
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    monkeypatch.setattr(config, "CATALOG_ROOT", catalog)
    monkeypatch.setattr(config, "QUARANTINE_ROOT", tmp_path / "quarantine")
    monkeypatch.setattr(config, "REVIEW_ROOT", tmp_path / "review")
    monkeypatch.setattr(drawing_config, "WORKSPACE", tmp_path / "ws")
    s.write_export_config(catalog)
    s.write_store_format(catalog)
    return SimpleNamespace(catalog=catalog, tmp=tmp_path, quarantine=tmp_path / "quarantine", review=tmp_path / "review")


def drawn(name="hero", colour="#ff0000"):
    api.new_sprite(name, 16, 12, "#102030")
    rev = api.apply_ops(name, "r0001", [{"op": "add_layer", "name": "top"}])["revision"]  # past r0001: a verifiable palette
    return api.apply_ops(name, rev, [{"op": "pixels", "pixels": [{"x": 3, "y": 3, "color": colour}, {"x": 4, "y": 3, "color": "#00ff00"}], "layer": "top"}])["revision"]


def real_intake(world, name="hero", colour="#ff0000"):
    rev = drawn(name, colour)
    package = handoff.build_handoff(name, rev, licence_state="CLEARED", licence_evidence_ref="note", brief_id="brief", review_evidence_ref="NOT_APPLICABLE")
    return intake(package["directory"], created_at="2026-01-01T00:00:00Z"), rev


def test_the_real_renderer_matches_what_the_drawing_tools_preview(world):
    rev = drawn()
    renderer = exporter.default_renderer()
    assert renderer is not None
    source = api.read_revision("hero", rev)[1]
    for scale in (1, 8):
        store_png = renderer.render(source, scale=scale)
        drawing_png = api.render_preview("hero", rev, scale=scale)
        assert pixels.pixel_hash(store_png, max_dim=2048) == pixels.pixel_hash(drawing_png, max_dim=2048), scale
    version = subprocess.run([drawing_config.ASEPRITE, "--version"], capture_output=True, text=True).stdout
    assert renderer.tool_version in version and renderer.tool_name == "Aseprite"


def test_a_real_candidate_goes_review_adopt_build_with_real_renders(world):
    result, rev = real_intake(world)
    assert result.verdict.value == "PASSED", result.findings
    renderer = exporter.default_renderer()
    outcome = review_mod.review(result.intake_id, created_at="2026-01-01T00:30:00Z", renderer=renderer)
    assert outcome.verdict is RenderVerdict.MATCH  # the drawing tools' preview and the store's own render show the same pixels
    adoption = s.do_adopt(result.intake_id, renderer=renderer)
    first = exporter.build(renderer=renderer)
    second = exporter.build(renderer=renderer)
    assert [(b.artifact_id, b.created) for b in first] == [("hero--x1", True)] and [b.created for b in second] == [False]
    assert first[0].pixel_hash == second[0].pixel_hash
    directory = world.catalog / "generated" / "hero--x1"
    assert len(list(directory.glob("*.png"))) == 1 and len(list(directory.glob("*.artifact.json"))) == 1  # one artifact file
    record = parse_record(ArtifactRecord, next(directory.glob("*.artifact.json")).read_bytes())
    assert record.source_revision == "r0001" and record.build.tool_version == renderer.tool_version
    assert (record.width, record.height) == (16, 12) and adoption.source_revision == "r0001"
    # the artifact shows the drawn pixels: the PNG decodes to the same image the drawing tools render at scale 1
    drawing_png = api.render_preview("hero", rev, scale=1)
    assert record.pixel_hash == pixels.pixel_hash(drawing_png, max_dim=2048)


def test_a_revoked_real_source_is_refused_by_build(world):
    result, _ = real_intake(world)
    renderer = exporter.default_renderer()
    review_mod.review(result.intake_id, created_at="2026-01-01T00:30:00Z", renderer=renderer)
    s.do_adopt(result.intake_id, renderer=renderer)
    revoke("hero/r0001", reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    before = snapshot(world.catalog)
    with pytest.raises(BuildError) as err:
        exporter.build("hero", renderer=renderer)
    assert err.value.code == "source_revoked" and snapshot(world.catalog) == before


def test_a_producer_preview_of_a_different_picture_is_caught_with_the_real_renderer(world):
    """The producer hands off a good-looking preview of ANOTHER sprite with this source: review shows MISMATCH and adopt refuses."""
    from tests.visual_assets.store import builders as b

    rev = drawn("hero", "#ff0000")
    other_rev = drawn("villain", "#0000ff")
    package = handoff.build_handoff("hero", rev, licence_state="CLEARED", licence_evidence_ref="note", brief_id="brief", review_evidence_ref="NOT_APPLICABLE")
    swapped = api.render_preview("villain", other_rev, scale=8)  # same size, different picture
    directory = b.write_dir(world.tmp / "swapped", b.package_bytes(api.read_revision("hero", rev)[1], swapped), api.read_revision("hero", rev)[1], swapped)
    result = intake(directory, created_at="2026-01-01T00:00:00Z")
    assert result.verdict.value == "PASSED"  # intake alone cannot tell: structure, hashes and scale are all fine
    renderer = exporter.default_renderer()
    assert review_mod.review(result.intake_id, created_at="2026-01-01T00:30:00Z", renderer=renderer).verdict is RenderVerdict.MISMATCH
    before = snapshot(world.catalog)
    with pytest.raises(GateError) as err:
        s.do_adopt(result.intake_id, renderer=renderer)
    assert err.value.code == "preview_mismatch" and snapshot(world.catalog) == before  # nothing was adopted
    assert package["candidate_id"].startswith("cand-")


def test_the_store_renders_exactly_one_frame_with_all_visible_layers(world):
    api.new_sprite("anim", 8, 8, "#102030")
    rev = api.apply_ops("anim", "r0001", [{"op": "add_frame"}, {"op": "add_layer", "name": "top"}])["revision"]
    rev = api.apply_ops("anim", rev, [{"op": "pixels", "pixels": [{"x": 1, "y": 1, "color": "#ffffff"}], "layer": "top", "frame": 1}])["revision"]
    source = api.read_revision("anim", rev)[1]
    png = exporter.default_renderer().render(source, scale=2)
    assert pixels.decode_png(png, max_dim=2048).width == 16  # one frame, not a sheet
    assert pixels.pixel_hash(png, max_dim=2048) == pixels.pixel_hash(api.render_preview("anim", rev, scale=2, frame=1), max_dim=2048)
