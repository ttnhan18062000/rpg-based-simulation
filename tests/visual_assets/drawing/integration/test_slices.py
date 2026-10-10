"""Slices made by the drawing tool, through the real Aseprite (`TCK-20261010-VISUAL-ASSETS-SLICE-DRAWING-TOOL`; ADR D25). Needs Aseprite + bwrap."""

from __future__ import annotations

import json

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import env, snapshot  # noqa: F401  (`env` isolates the catalog, quarantine and review roots)
from visual_assets.drawing import api, config, handoff
from visual_assets.drawing.errors import AdapterError
from visual_assets.store import records, slices
from visual_assets.store.build import exporter
from visual_assets.store.contracts import CandidateHandoffPackage, parse_record
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.contracts.intake import IntakeFindingCode as Code
from visual_assets.store.contracts.slices import SlicePivot, SliceRect
from visual_assets.store.intake import aseprite, intake
from visual_assets.store import review as review_api

pytestmark = pytest.mark.needs_aseprite

KW = dict(licence_state="CLEARED", licence_evidence_ref="note-1", brief_id="brief-7", review_evidence_ref="NOT_APPLICABLE")
NINE = {"op": "set_slice", "name": "panel", "x": 2, "y": 3, "w": 8, "h": 6, "center": {"x": 1, "y": 1, "w": 4, "h": 2}}
PIVOT = {"op": "set_slice", "name": "hand", "x": 4, "y": 5, "w": 6, "h": 4, "pivot": {"x": 3, "y": 2}}


def sprite(name="hero", w=16, h=16, ops=()):
    api.new_sprite(name, w, h, "#102030")
    rev = "r0001"
    for batch in ops:
        rev = api.apply_ops(name, rev, batch)["revision"]
    return rev


def bytes_of(name, rev):
    return (config.WORKSPACE / "sprites" / name / f"{rev}.aseprite").read_bytes()


def test_the_tool_makes_a_nine_slice_and_a_pivot_slice_that_inspect_and_the_parser_both_report():
    rev = sprite(ops=[[NINE, PIVOT]])
    info = api.inspect_sprite("hero", rev)
    by_name = {x["name"]: x for x in info["slices"]}
    assert by_name["panel"] == {"name": "panel", "x": 2, "y": 3, "w": 8, "h": 6, "center": {"x": 1, "y": 1, "w": 4, "h": 2}}
    assert by_name["hand"] == {"name": "hand", "x": 4, "y": 5, "w": 6, "h": 4, "pivot": {"x": 3, "y": 2}}
    facts, problems = aseprite.read_facts(bytes_of("hero", rev))
    assert not [p for p in problems if p[0].value.startswith(("SLICE_", "SOURCE_"))], problems
    parsed = {x.name: x for x in slices.slices_from_source(bytes_of("hero", rev))}
    assert parsed["panel"].keys[0].center == SliceRect(x=1, y=1, w=4, h=2) and parsed["hand"].keys[0].pivot == SlicePivot(x=3, y=2)
    assert all(len(x.keys) == 1 and x.keys[0].frame == 0 for x in parsed.values())


def test_a_slice_made_on_a_sprite_with_frames_holds_for_every_frame_as_one_key():
    rev = sprite(ops=[[{"op": "add_frame"}, {"op": "add_frame"}], [NINE]])
    assert [(x.name, [k.frame for k in x.keys]) for x in slices.slices_from_source(bytes_of("hero", rev))] == [("panel", [0])]


def test_set_slice_replaces_the_whole_slice_of_that_name():
    rev = sprite(ops=[[NINE]])
    rev = api.apply_ops("hero", rev, [{"op": "set_slice", "name": "panel", "x": 0, "y": 0, "w": 4, "h": 4}])["revision"]
    info = api.inspect_sprite("hero", rev)
    assert info["slices"] == [{"name": "panel", "x": 0, "y": 0, "w": 4, "h": 4}]  # one slice, and the old centre is gone


def test_the_slice_limit_is_enforced_across_batches():
    rev = sprite(ops=[[{"op": "set_slice", "name": f"s{i}", "x": 0, "y": 0, "w": 1, "h": 1} for i in range(config.MAX_SLICES)]])
    assert len(api.inspect_sprite("hero", rev)["slices"]) == config.MAX_SLICES
    with pytest.raises(AdapterError, match="slice limit"):
        api.apply_ops("hero", rev, [{"op": "set_slice", "name": "one-too-many", "x": 0, "y": 0, "w": 1, "h": 1}])
    api.apply_ops("hero", rev, [{"op": "set_slice", "name": "s0", "x": 1, "y": 1, "w": 1, "h": 1}])  # replacing one is fine at the limit


def test_a_slice_outside_the_current_canvas_is_refused_and_no_revision_is_saved():
    rev = sprite(w=8, h=8)
    before = snapshot(config.WORKSPACE / "sprites" / "hero")
    with pytest.raises(AdapterError, match="outside the canvas"):
        api.apply_ops("hero", rev, [{"op": "set_slice", "name": "wide", "x": 4, "y": 0, "w": 6, "h": 2}])
    assert snapshot(config.WORKSPACE / "sprites" / "hero") == before


def test_shrinking_the_canvas_under_a_slice_fails_the_batch_atomically():
    rev = sprite(ops=[[NINE]])
    before = snapshot(config.WORKSPACE / "sprites" / "hero")
    with pytest.raises(AdapterError, match="final canvas"):  # set earlier in the same batch
        api.apply_ops("hero", rev, [{"op": "set_slice", "name": "late", "x": 10, "y": 10, "w": 4, "h": 4}, {"op": "resize_canvas", "width": 8, "height": 8}])
    with pytest.raises(AdapterError, match="final canvas"):  # a slice the sprite already had
        api.apply_ops("hero", rev, [{"op": "resize_canvas", "width": 6, "height": 6}])
    assert snapshot(config.WORKSPACE / "sprites" / "hero") == before
    api.apply_ops("hero", rev, [{"op": "resize_canvas", "width": 12, "height": 12}])  # a shrink that still fits is fine


def test_the_handoff_always_declares_the_slice_count_when_there_are_slices_and_omits_it_otherwise():
    with_slices = handoff.build_handoff("hero", sprite(ops=[[NINE, PIVOT]]), **KW)
    package = (config.WORKSPACE / "handoffs" / with_slices["handoff_id"] / "package.json").read_bytes()
    assert parse_record(CandidateHandoffPackage, package).slice_count == 2 and b'"slice_count":2' in package.replace(b" ", b"")
    without = handoff.build_handoff("plain", sprite("plain"), **KW)
    plain_bytes = (config.WORKSPACE / "handoffs" / without["handoff_id"] / "package.json").read_bytes()
    assert b"slice_count" not in plain_bytes and parse_record(CandidateHandoffPackage, plain_bytes).slice_count is None


def test_an_agent_drawn_sprite_with_a_nine_slice_and_a_pivot_passes_handoff_intake_and_adoption(env):
    """The whole path: drawn -> exported -> intake (declared count checked) -> adopted; the stored SourceRecord matches what was asked for."""
    s.write_export_config(env.catalog)
    s.write_store_format(env.catalog)
    rev = sprite(ops=[[NINE, PIVOT]])
    result = handoff.build_handoff("hero", rev, **KW)
    outcome = intake(result["directory"], created_at="2026-01-01T00:00:00Z")
    assert outcome.verdict is IntakeVerdict.PASSED, [f.code for f in outcome.findings]
    renderer = exporter.default_renderer()
    review_api.review(outcome.intake_id, created_at="2026-01-01T00:30:00Z", renderer=renderer)
    s.do_adopt(outcome.intake_id, source_asset_id="hero", renderer=renderer)
    got = {x.name: x for x in records.load_source("hero", "r0001").slices}
    assert got["panel"].keys[0].bounds == SliceRect(x=2, y=3, w=8, h=6) and got["panel"].keys[0].center == SliceRect(x=1, y=1, w=4, h=2)
    assert got["hand"].keys[0].pivot == SlicePivot(x=3, y=2) and got["hand"].keys[0].bounds == SliceRect(x=4, y=5, w=6, h=4)


def test_a_declared_count_that_differs_from_the_file_quarantines_the_handoff(env):
    tmp_path = env.tmp
    result = handoff.build_handoff("hero", sprite(ops=[[NINE, PIVOT]]), **KW)
    directory = config.WORKSPACE / "handoffs" / result["handoff_id"]
    for number, declared in enumerate((1, 3)):
        changed = tmp_path / f"changed-{number}"
        changed.mkdir()
        for name in handoff.FILES:
            (changed / name).write_bytes((directory / name).read_bytes())
        package = json.loads((changed / "package.json").read_bytes())
        package["slice_count"] = declared
        (changed / "package.json").write_text(json.dumps(package))
        outcome = intake(changed, created_at="2026-01-01T00:00:00Z")
        assert outcome.verdict is IntakeVerdict.QUARANTINED and Code.SLICE_COUNT_MISMATCH in {f.code for f in outcome.findings}, declared
