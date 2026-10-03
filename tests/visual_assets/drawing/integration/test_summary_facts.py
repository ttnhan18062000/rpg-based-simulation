"""`cels` and `aseprite_version` in every sprite summary (read-only facts used by candidate handoff)."""

from __future__ import annotations

import subprocess

import pytest

from visual_assets.drawing import api, config
from visual_assets.store.intake import aseprite

pytestmark = pytest.mark.needs_aseprite


def source_bytes(name: str, rev: str) -> bytes:
    return (config.WORKSPACE / "sprites" / name / f"{rev}.aseprite").read_bytes()


def test_every_summary_carries_cels_and_the_binary_version():
    version = subprocess.run([config.ASEPRITE, "--version"], capture_output=True, text=True).stdout.split()[1]
    made = api.new_sprite("s", 8, 8)
    edited = api.apply_ops("s", "r0001", [{"op": "add_layer", "name": "top"}])
    branched = api.branch_sprite("s", "t")
    inspected = api.inspect_sprite("s")
    for info in (made, edited, branched, inspected):
        assert isinstance(info["cels"], int) and info["cels"] >= 1
        assert version.startswith(info["aseprite_version"]) and info["aseprite_version"].count(".") == 3  # e.g. 1.3.18.6


def test_cel_count_equals_the_store_readers_count_with_an_empty_cel_and_a_multi_frame_layer():
    """The planner's hard case: a layer with no pixels, and a layer that spans several frames."""
    api.new_sprite("hard", 12, 12, "#203040")
    rev = "r0001"
    steps = [
        [{"op": "add_layer", "name": "empty"}, {"op": "add_layer", "name": "wide"}],
        [{"op": "add_frame"}, {"op": "add_frame", "copy_from": 1}, {"op": "add_frame"}],
        [{"op": "pixels", "pixels": [{"x": 2, "y": 2, "color": "#ff0000"}], "layer": "wide", "frame": 1},
         {"op": "pixels", "pixels": [{"x": 3, "y": 3, "color": "#00ff00"}], "layer": "wide", "frame": 3}],
        [{"op": "delete_frame", "frame": 2}],
    ]
    for ops in steps:
        info = api.apply_ops("hard", rev, ops)
        rev = info["revision"]
        facts, problems = aseprite.read_facts(source_bytes("hard", rev))
        assert problems == [], (rev, problems)
        assert info["cels"] == facts.cels, (rev, info["cels"], facts.cels)
        assert api.inspect_sprite("hard", rev)["cels"] == facts.cels
    assert facts.layers == 3 and facts.frames == 3  # 1 frame + 3 added - 1 deleted
    # Aseprite stores no cel for a layer/frame without content, so the count is NOT layers x frames: this is the empty-cel case
    assert 0 < facts.cels < facts.layers * facts.frames
