"""High-level sprite tools against real Aseprite + bwrap (compose + MCP registration)."""

from __future__ import annotations

import colorsys

import pytest

from visual_assets.drawing import api
from visual_assets.drawing import compose
from visual_assets.drawing.colors import hex_to_rgba, luma
from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.server.highlevel_tools import register
from visual_assets.drawing.technique.masks import ellipse_cells
from visual_assets.drawing.technique.ramps import make_ramp
from visual_assets.drawing.technique.stroke import stroke_pixels

def hsv(hexcolor):
    r, g, b, _ = hex_to_rgba(hexcolor)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360, s, v


# ============================================================ sprite-facing (real Aseprite)




def grid_of(name, rev=None, frame=1):
    return compose.read_grid(name, rev, frame)[0]


@pytest.mark.needs_aseprite
def test_read_grid_tiles_large_sprites_correctly(ws):
    api.new_sprite("big", 70, 40, "#00000000")
    api.apply_ops("big", "r0001", [
        {"op": "pixels", "pixels": [{"x": 0, "y": 0, "color": "#ff0000"},
                                    {"x": 69, "y": 39, "color": "#00ff00"},
                                    {"x": 33, "y": 32, "color": "#0000ff"}]}])
    g = grid_of("big")
    assert len(g) == 40 and len(g[0]) == 70
    assert g[0][0] == "#ff0000ff" and g[39][69] == "#00ff00ff" and g[32][33] == "#0000ffff"
    assert sum(c != "#00000000" for row in g for c in row) == 3


@pytest.mark.needs_aseprite
def test_shade_ellipse_paints_ramp_bands_and_creates_revision(ws):
    api.new_sprite("orb", 16, 16, "#00000000")
    out = compose.shade("orb", "r0001", {"ellipse": {"x": 2, "y": 2, "width": 12, "height": 12}},
                   base="#3ec96b", steps=5, light="tl", bands=3)
    ramp = make_ramp("#3ec96b", 5)
    assert out["revision"] == "r0002" and out["shaded_pixels"] == len(ellipse_cells(2, 2, 12, 12))
    used = {c[:7] for row in grid_of("orb") for c in row if not c.endswith("00")}
    assert used == {ramp[1], ramp[2], ramp[3]}  # 3 bands -> ramp[base-1 .. base+1]
    assert set(out["band_counts"]) == {"-1", "0", "1"} and all(v > 0 for v in out["band_counts"].values())
    g = grid_of("orb")
    assert g[3][5][:7] == ramp[3] and g[12][10][:7] == ramp[1]  # lit top-left, shaded bottom-right


@pytest.mark.needs_aseprite
def test_shade_color_target_only_touches_that_colour(ws):
    api.new_sprite("c", 12, 12, "#00000000")
    api.apply_ops("c", "r0001", [
        {"op": "rect", "x": 1, "y": 1, "width": 6, "height": 6, "color": "#6e7f99"},
        {"op": "rect", "x": 8, "y": 8, "width": 3, "height": 3, "color": "#c0392b"}])
    compose.shade("c", "r0002", {"color": "#6e7f99"}, base="#6e7f99", bands=3, form="bevel")
    g = grid_of("c")
    assert all(g[y][x] == "#c0392bff" for y in range(8, 11) for x in range(8, 11))  # other colour untouched
    assert g[0][0] == "#00000000"
    top_left, bottom_right = g[1][3], g[6][3]
    assert luma(hex_to_rgba(top_left)) > luma(hex_to_rgba(bottom_right))


@pytest.mark.needs_aseprite
def test_shade_errors_are_clean(ws):
    api.new_sprite("e", 8, 8, "#00000000")
    with pytest.raises(AdapterError, match="stale"):
        compose.shade("e", "r0009", {"opaque": True}, base="#336699")
    with pytest.raises(AdapterError, match="selects no pixels"):
        compose.shade("e", "r0001", {"opaque": True}, base="#336699")
    with pytest.raises(AdapterError, match="exactly one"):
        compose.shade("e", "r0001", {"opaque": True, "color": "#ffffff"}, base="#336699")
    with pytest.raises(AdapterError, match="either ramp or base"):
        compose.shade("e", "r0001", {"rect": {"x": 0, "y": 0, "width": 2, "height": 2}})
    with pytest.raises(AdapterError, match="at least 3"):
        compose.shade("e", "r0001", {"rect": {"x": 0, "y": 0, "width": 2, "height": 2}}, ramp_colors=["#000000"])
    assert api.inspect_sprite("e")["revision"] == "r0001"  # nothing published by failures


@pytest.mark.needs_aseprite
def test_dither_region_half_coverage_and_gradient(ws):
    api.new_sprite("d", 8, 8, "#00000000")
    out = compose.dither("d", "r0001", "#102030", "#a0b0c0", 0.5,
                    region={"x": 0, "y": 0, "width": 8, "height": 8})
    assert out["light_pixels"] == 32 and out["dithered_pixels"] == 64
    g = grid_of("d")
    assert sum(c == "#a0b0c0ff" for row in g for c in row) == 32
    out2 = compose.dither("d", "r0002", "#102030", "#a0b0c0", 0.0, level_to=1.0, axis="x",
                     region={"x": 0, "y": 0, "width": 8, "height": 8})
    g = grid_of("d")
    cols = [sum(g[y][x] == "#a0b0c0ff" for y in range(8)) for x in range(8)]
    assert cols[0] == 0 and cols[-1] == 8 and cols == sorted(cols) and out2["revision"] == "r0003"


@pytest.mark.needs_aseprite
def test_dither_target_color_mask_and_arg_errors(ws):
    api.new_sprite("d", 8, 8, "#00000000")
    api.apply_ops("d", "r0001", [{"op": "rect", "x": 2, "y": 2, "width": 4, "height": 4, "color": "#808080"}])
    out = compose.dither("d", "r0002", "#202020", "#e0e0e0", 0.5, target_color="#808080")
    assert out["dithered_pixels"] == 16 and out["light_pixels"] == 8
    with pytest.raises(AdapterError, match="exactly one"):
        compose.dither("d", "r0003", "#000000", "#ffffff", 0.5)
    with pytest.raises(AdapterError, match="exactly one"):
        compose.dither("d", "r0003", "#000000", "#ffffff", 0.5, region={"x": 0, "y": 0, "width": 1, "height": 1},
                  target_color="#808080")


@pytest.mark.needs_aseprite
def test_stroke_closed_box_and_layer_creation(ws):
    api.new_sprite("s", 10, 10, "#00000000")
    out = compose.stroke("s", "r0001", [[1, 1], [6, 1], [6, 5], [1, 5]], "#ff00ff", closed=True, layer="lines")
    assert out["stroke_pixels"] == len(set(stroke_pixels([(1, 1), (6, 1), (6, 5), (1, 5)], True)))
    names = [l["name"] for l in api.inspect_sprite("s")["layers"]]
    assert names == ["base", "lines"]
    g = grid_of("s")
    assert g[1][1] == g[1][6] == g[5][6] == g[5][1] == "#ff00ffff" and g[3][3] == "#00000000"
    with pytest.raises(AdapterError, match="each point"):
        compose.stroke("s", "r0002", [[1, "a"]], "#ffffff")


@pytest.mark.needs_aseprite
def test_auto_outline_full_selout_skip_and_clipping(ws):
    for n in ("o1", "o2", "o3", "o4"):
        api.new_sprite(n, 10, 10, "#00000000")
        api.apply_ops(n, "r0001", [{"op": "rect", "x": 3, "y": 3, "width": 4, "height": 4, "color": "#c9d1dc"}])
    full = compose.auto_outline("o1", "r0002", "full", "#000000")
    assert full["outline_pixels"] == 16 and full["outline_clipped"] == 0  # 4-neighbour ring, no corners
    assert [l["name"] for l in api.inspect_sprite("o1")["layers"]] == ["base", "outline"]
    g = grid_of("o1")
    assert g[2][4] == "#000000ff" and g[2][2] == "#00000000"  # ring has no diagonal corner pixels

    se = compose.auto_outline("o2", "r0002", "selout")
    fill = luma(hex_to_rgba("#c9d1dc"))
    out_c = grid_of("o2")[2][4]
    assert out_c != "#000000ff" and luma(hex_to_rgba(out_c)) < fill * 0.6
    assert hsv(out_c)[0] > hsv("#c9d1dc")[0] - 1  # shifted toward blue, not away

    skip = compose.auto_outline("o3", "r0002", "full", lit_edges="skip", light="tl")
    assert skip["outline_pixels"] == 8  # top and left edges left open
    g = grid_of("o3")
    assert g[2][4] == "#00000000" and g[7][4] == "#000000ff"

    api.new_sprite("edge", 6, 6, "#00000000")
    api.apply_ops("edge", "r0001", [{"op": "rect", "x": 0, "y": 0, "width": 3, "height": 3, "color": "#ffffff"}])
    e = compose.auto_outline("edge", "r0002")
    assert e["outline_clipped"] == 6 and e["outline_pixels"] == 6  # top/left would fall off-canvas
    with pytest.raises(AdapterError, match="mode"):
        compose.auto_outline("o4", "r0002", "weird")


@pytest.mark.needs_aseprite
def test_selout_reuses_existing_dark_colours_instead_of_inventing_new_ones(ws):
    api.new_sprite("p", 12, 12, "#00000000")
    api.apply_ops("p", "r0001", [
        {"op": "rect", "x": 3, "y": 3, "width": 6, "height": 6, "color": "#8fa9b9"},
        {"op": "rect", "x": 3, "y": 6, "width": 6, "height": 3, "color": "#50546d"},
        {"op": "pixels", "pixels": [{"x": 5, "y": 4, "color": "#252331"}]}])
    before = set(api.inspect_sprite("p")["colors"])
    compose.auto_outline("p", "r0002", "selout")
    after = set(api.inspect_sprite("p")["colors"])
    assert after == before  # no new colour: every outline pixel reused a darker existing one
    g = grid_of("p")
    assert g[2][5] in before and luma(hex_to_rgba(g[2][5])) < luma(hex_to_rgba("#8fa9b9")) * 0.7


@pytest.mark.needs_aseprite
def test_remap_palette_snaps_and_guards_multilayer(ws):
    api.new_sprite("r", 6, 6, "#00000000")
    api.apply_ops("r", "r0001", [
        {"op": "pixels", "pixels": [{"x": 0, "y": 0, "color": "#fe0101"}, {"x": 1, "y": 0, "color": "#0102fd"},
                                    {"x": 2, "y": 0, "color": "#ff0000cc"}]}])
    out = compose.remap_palette("r", "r0002", ["#ff0000", "#0000ff"])
    g = grid_of("r")
    assert g[0][0] == "#ff0000ff" and g[0][1] == "#0000ffff" and g[0][2] == "#ff0000cc"  # alpha preserved
    assert out["remapped_pixels"] == 2 and out["palette_size"] == 2  # the 3rd was already exact red

    api.new_sprite("m", 4, 4)
    api.apply_ops("m", "r0001", [
        {"op": "add_layer", "name": "top"},
        {"op": "pixels", "pixels": [{"x": 0, "y": 0, "color": "#ffffff"}], "layer": "base"},
        {"op": "pixels", "pixels": [{"x": 1, "y": 1, "color": "#ffffff"}], "layer": "top"}])
    with pytest.raises(AdapterError, match="exactly one layer"):
        compose.remap_palette("m", "r0002", ["#000000"])


@pytest.mark.needs_aseprite
def test_lint_and_ascii_view_on_a_real_sprite(ws):
    api.new_sprite("lint", 16, 16, "#00000000")
    compose.shade("lint", "r0001", {"ellipse": {"x": 3, "y": 3, "width": 10, "height": 10}}, base="#6e7f99")
    compose.auto_outline("lint", "r0002", "full", "#101010")
    rep = compose.lint("lint")
    assert rep["stats"]["colors"] == 4 and rep["ok"] and rep["stats"]["bbox"] == (2, 2, 13, 13)
    view = compose.ascii_view("lint")
    assert view["width"] == 16 and len(view["rows"]) == 16 and all(len(r) == 16 for r in view["rows"])
    assert view["rows"][0] == "." * 16 and len(view["legend"]) == 4
    assert view["rows"][8].count(".") < 16


@pytest.mark.needs_aseprite
def test_register_exposes_exactly_the_documented_tools(ws):
    from mcp.server.fastmcp import FastMCP
    srv = FastMCP("t")
    register(srv)
    assert set(srv._tool_manager._tools) == {
        "make_ramp", "shade", "dither", "stroke", "auto_outline", "remap_palette", "lint_sprite", "ascii_view"}
