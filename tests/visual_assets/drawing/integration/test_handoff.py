"""`build_handoff` / `export_handoff`: a real revision packaged for intake. Needs Aseprite."""

from __future__ import annotations

import hashlib
import json

import pytest

from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.drawing import __version__, api, config, handoff
from visual_assets.drawing.errors import AdapterError
from visual_assets.store import config as store_config
from visual_assets.store.contracts import CandidateHandoffPackage, parse_record
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.intake import intake

pytestmark = pytest.mark.needs_aseprite

KW = dict(licence_state="CLEARED", licence_evidence_ref="note-1", brief_id="brief-7", review_evidence_ref="NOT_APPLICABLE")


def drawn() -> str:
    api.new_sprite("hero", 16, 16, "#102030")
    rev = api.apply_ops("hero", "r0001", [{"op": "add_layer", "name": "top"}, {"op": "add_frame"}])["revision"]
    return api.apply_ops("hero", rev, [{"op": "pixels", "pixels": [{"x": 3, "y": 3, "color": "#ff0000"}], "layer": "top", "frame": 2},
                                       {"op": "add_tag", "name": "idle", "from_frame": 1, "to_frame": 2}])["revision"]


def test_a_handoff_is_three_files_built_from_the_exact_revision():
    rev = drawn()
    result = handoff.build_handoff("hero", rev, **KW)
    directory = config.WORKSPACE / "handoffs" / result["candidate_id"]
    assert str(directory) == result["directory"] and sorted(p.name for p in directory.iterdir()) == sorted(handoff.FILES)
    source = (config.WORKSPACE / "sprites" / "hero" / f"{rev}.aseprite").read_bytes()
    assert (directory / "source.aseprite").read_bytes() == source
    assert result["candidate_id"] == "cand-" + hashlib.sha256(source).hexdigest()[:16]
    package = parse_record(CandidateHandoffPackage, (directory / "package.json").read_bytes())
    assert package.source_revision == rev and package.expected_parent == f"r{int(rev[1:]) - 1:04d}"
    assert package.producer_class.value == "CAP_A" and package.producer_state.value == "ACTIVE"
    assert package.source_hash == result["source_hash"] and package.preview_hash == result["preview_hash"]
    info = api.inspect_sprite("hero", rev)
    assert (package.width, package.height, package.frame_count, package.layer_count, package.cel_count, package.tag_count,
            package.palette_size) == (16, 16, len(info["frames"]), len(info["layers"]), info["cels"], len(info["tags"]), info["palette_size"])


def test_provenance_comes_from_what_the_tools_know_and_markers_otherwise():
    rev = drawn()
    result = handoff.build_handoff("hero", rev, **KW)
    package = parse_record(CandidateHandoffPackage, (config.WORKSPACE / "handoffs" / result["candidate_id"] / "package.json").read_bytes())
    info = api.inspect_sprite("hero", rev)
    assert package.tool_version == info["aseprite_version"] and package.tool == "Aseprite" == package.editor
    assert __version__ in package.adapter and config.LUA_SHA256[:12] in package.adapter
    assert package.creator.value == "UNAVAILABLE"  # the tools do not know who drew it: never invented
    assert package.producer_validation.value == "NOT_RUN"
    assert (package.brief_id, package.licence_state.value, package.licence_evidence_ref) == ("brief-7", "CLEARED", "note-1")
    assert package.human_review_ref.value == "NOT_APPLICABLE"
    first = parse_record(CandidateHandoffPackage, json.dumps({**json.loads((config.WORKSPACE / "handoffs" / result["candidate_id"] / "package.json").read_bytes()), "source_revision": "r0001", "expected_parent": "NOT_APPLICABLE"}).encode())
    assert first.expected_parent == "NOT_APPLICABLE"


def test_rebuilding_the_same_revision_is_idempotent_and_never_overwrites():
    rev = drawn()
    first = handoff.build_handoff("hero", rev, **KW)
    directory = config.WORKSPACE / "handoffs" / first["candidate_id"]
    before = snapshot(directory)
    mtimes = {p.name: p.stat().st_mtime_ns for p in directory.iterdir()}
    assert handoff.build_handoff("hero", rev, **KW) == first
    assert snapshot(directory) == before and {p.name: p.stat().st_mtime_ns for p in directory.iterdir()} == mtimes
    with pytest.raises(AdapterError, match="different handoff already exists"):
        handoff.build_handoff("hero", rev, **{**KW, "licence_state": "RESTRICTED"})
    assert snapshot(directory) == before
    assert [p.name for p in (config.WORKSPACE / "handoffs").iterdir()] == [first["candidate_id"]]  # no temp dir left


def test_a_handoff_writes_only_inside_its_own_workspace_directory(tmp_path):
    rev = drawn()
    catalog = snapshot(store_config.CATALOG_ROOT)
    sprites = snapshot(config.WORKSPACE / "sprites")
    handoff.build_handoff("hero", rev, **KW)
    assert snapshot(store_config.CATALOG_ROOT) == catalog and snapshot(config.WORKSPACE / "sprites") == sprites
    assert sorted(p.name for p in config.WORKSPACE.iterdir() if p.name != ".jobs") == ["handoffs", "sprites"]


@pytest.mark.parametrize("kw,match", [
    (dict(name="ghost", revision="r0001"), "no such sprite"),
    (dict(name="../evil", revision="r0001"), "name must match"),
    (dict(name="hero", revision="r9999"), "no such revision"),
    (dict(name="hero", revision="latest"), "revision must look like"),
    (dict(name="hero", revision=None), "revision is required"),
    (dict(name="hero", revision="r0002", licence_state="MAYBE"), "handoff rejected"),
    (dict(name="hero", revision="r0002", brief_id="line\nbreak"), "handoff rejected"),
    (dict(name="hero", revision="r0002", limitations=["x" * 300]), "handoff rejected"),
])
def test_bad_requests_are_rejected_and_write_nothing(kw, match):
    drawn()
    args = {**KW, **kw}
    with pytest.raises(AdapterError, match=match):
        handoff.build_handoff(args.pop("name"), args.pop("revision"), **args)
    assert not (config.WORKSPACE / "handoffs").exists()


def test_a_real_handoff_passes_intake_end_to_end(tmp_path, monkeypatch):
    rev = drawn()
    result = handoff.build_handoff("hero", rev, **KW)
    monkeypatch.setattr(store_config, "QUARANTINE_ROOT", tmp_path / "q")
    monkeypatch.setattr(store_config, "REVIEW_ROOT", tmp_path / "r")
    outcome = intake(result["directory"], created_at="2026-01-01T00:00:00Z")
    assert outcome.verdict is IntakeVerdict.PASSED and outcome.findings == () and outcome.candidate_id == result["candidate_id"]


def test_an_untouched_first_revision_is_quarantined_as_palette_unverifiable(tmp_path, monkeypatch):
    api.new_sprite("blank", 8, 8, "#336699")
    result = handoff.build_handoff("blank", "r0001", **KW)
    monkeypatch.setattr(store_config, "QUARANTINE_ROOT", tmp_path / "q")
    monkeypatch.setattr(store_config, "REVIEW_ROOT", tmp_path / "r")
    outcome = intake(result["directory"], created_at="2026-01-01T00:00:00Z")
    assert outcome.verdict is IntakeVerdict.QUARANTINED
    assert [f.code.value for f in outcome.findings] == ["PALETTE_UNVERIFIABLE"]  # and nothing else is wrong with it


def test_a_withdrawn_licence_is_packaged_but_quarantined_by_intake(tmp_path, monkeypatch):
    rev = drawn()
    result = handoff.build_handoff("hero", rev, **{**KW, "licence_state": "WITHDRAWN"})
    monkeypatch.setattr(store_config, "QUARANTINE_ROOT", tmp_path / "q")
    monkeypatch.setattr(store_config, "REVIEW_ROOT", tmp_path / "r")
    outcome = intake(result["directory"], created_at="2026-01-01T00:00:00Z")
    assert [f.code.value for f in outcome.findings] == ["LICENCE_WITHDRAWN"]


def test_the_handoff_layer_never_imports_the_store_beyond_contracts():
    import ast
    from pathlib import Path

    tree = ast.parse(Path(handoff.__file__).read_text())
    mods = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
    assert [m for m in mods if m.startswith("visual_assets.store")] == ["visual_assets.store.contracts", "visual_assets.store.contracts.handoff"]
