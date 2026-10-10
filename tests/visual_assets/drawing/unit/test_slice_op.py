"""The `set_slice` op is validated before Aseprite runs (`TCK-20261010-VISUAL-ASSETS-SLICE-DRAWING-TOOL`; ADR D25). No Aseprite needed."""

from __future__ import annotations

import pytest

from visual_assets.drawing import config
from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.schema.ops import validate_ops
from visual_assets.store import config as store_config

GOOD = {"op": "set_slice", "name": "panel", "x": 2, "y": 3, "w": 8, "h": 6}


def test_the_tool_and_the_store_agree_on_the_slice_limit():
    assert config.MAX_SLICES == store_config.MAX_SOURCE_SLICES == 16


def test_a_valid_op_is_passed_to_lua_with_its_geometry_unchanged():
    clean, _ = validate_ops([{**GOOD, "center": {"x": 1, "y": 1, "w": 4, "h": 2}, "pivot": {"x": 8, "y": 6}}])
    assert clean == [{"name": "panel", "x": 2, "y": 3, "w": 8, "h": 6, "center": {"x": 1, "y": 1, "w": 4, "h": 2}, "pivot": {"x": 8, "y": 6}, "op": "set_slice"}]
    assert validate_ops([GOOD])[0] == [{"name": "panel", "x": 2, "y": 3, "w": 8, "h": 6, "op": "set_slice"}]


@pytest.mark.parametrize("over", [
    {"name": ""}, {"name": "x" * 33}, {"name": "bad/name"}, {"name": "‮"}, {"name": 5},
    {"x": -1}, {"y": -1}, {"x": 128}, {"w": 0}, {"h": 0}, {"w": 129}, {"w": True}, {"x": 1.5}, {"x": "1"}, {"w": None},
    {"x": 125, "w": 8}, {"y": 125, "h": 8},
    {"center": {"x": 0, "y": 0, "w": 0, "h": 1}}, {"center": {"x": 0, "y": 0, "w": 9, "h": 1}}, {"center": {"x": 5, "y": 0, "w": 4, "h": 1}},
    {"center": {"x": 0, "y": 5, "w": 1, "h": 2}}, {"center": {"x": -1, "y": 0, "w": 1, "h": 1}}, {"center": {"x": 0, "y": 0, "w": 1}}, {"center": {"x": 0, "y": 0, "w": 1, "h": 1, "z": 1}}, {"center": {"x": 0, "y": 0, "w": 1, "h": 1, "op": "x"}}, {"pivot": {"x": 0, "y": 0, "layer": "x"}}, {"center": 3},
    {"pivot": {"x": 9, "y": 0}}, {"pivot": {"x": 0, "y": 7}}, {"pivot": {"x": -1, "y": 0}}, {"pivot": {"x": 0}}, {"pivot": {"x": 0, "y": 0, "z": 0}}, {"pivot": [1, 2]},
    {"extra": 1}, {"frame": 1},
])
def test_each_bad_request_is_refused_before_aseprite_runs(over):
    with pytest.raises(AdapterError):
        validate_ops([{**GOOD, **over}])


def test_the_pivot_may_sit_on_the_far_edge_and_the_centre_may_fill_the_slice():
    validate_ops([{**GOOD, "pivot": {"x": 8, "y": 6}, "center": {"x": 0, "y": 0, "w": 8, "h": 6}}])


def test_more_slice_ops_than_the_limit_in_one_batch_are_refused():
    validate_ops([{**GOOD, "name": f"s{i}"} for i in range(config.MAX_SLICES)])
    with pytest.raises(AdapterError, match="at most 16 set_slice"):
        validate_ops([{**GOOD, "name": f"s{i}"} for i in range(config.MAX_SLICES + 1)])
