"""Tests for the high-level pixel-art layer. Pure-maths tests need nothing; sprite tests need real
Aseprite + bwrap and skip cleanly without them.

Run: .venv/bin/python -m pytest experiments/aseprite_mcp -q
"""

from __future__ import annotations

import colorsys
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapter  # noqa: E402
import highlevel as hl  # noqa: E402
import highlevel_tools as ht  # noqa: E402

needs_aseprite = pytest.mark.skipif(
    not (Path(adapter.ASEPRITE).exists() and shutil.which("bwrap")),
    reason="requires aseprite and bwrap",
)


def hsv(hexcolor):
    r, g, b, _ = hl.hex_to_rgba(hexcolor)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360, s, v


# ============================================================ pure: ramps


def test_ramp_base_in_place_value_monotonic_and_hue_shifts_toward_blue_and_yellow():
    base = "#3ec96b"  # green, hue ~139
    ramp = hl.make_ramp(base, 5)
    assert len(ramp) == 5 and ramp[2] == base
    lumas = [hl.luma(hl.hex_to_rgba(c)) for c in ramp]
    assert lumas == sorted(lumas) and len(set(lumas)) == 5
    h_base = hsv(base)[0]
    assert hsv(ramp[0])[0] > h_base  # shadow drifts toward 250 (blue/purple): hue increases from 139
    assert hsv(ramp[4])[0] < h_base  # highlight drifts toward 55 (yellow): hue decreases
    assert hsv(ramp[4])[1] < hsv(base)[1]  # saturation falls toward the light end


def test_ramp_hue_never_overshoots_target_and_zero_shift_keeps_hue():
    ramp = hl.make_ramp("#3366cc", 9, hue_shift=60.0)  # base hue 220, already near the 250 shadow target
    shadows = [hsv(c)[0] for c in ramp[:4]]
    assert max(shadows) <= 251.0  # clamped at the 250 target, never past it
    assert shadows[0] >= hsv("#3366cc")[0]  # and it did move toward it
    base_h = hsv("#c0392b")[0]
    flat = hl.make_ramp("#c0392b", 5, hue_shift=0.0)
    for c in flat:
        if hsv(c)[1] > 0.05:
            assert abs(hsv(c)[0] - base_h) <= 2.0  # only 8-bit RGB rounding noise


def test_ramp_neutral_base_gets_cool_shadow_warm_light():
    ramp = hl.make_ramp("#808080", 5)
    dr, dg, db, _ = hl.hex_to_rgba(ramp[0])
    lr, lg, lb, _ = hl.hex_to_rgba(ramp[4])
    assert db > dr  # bluish shadow
    assert lr > lb  # yellowish highlight


@pytest.mark.parametrize("kwargs", [
    {"steps": 1}, {"steps": 10}, {"steps": True and "5"}, {"hue_shift": -1.0},
    {"hue_shift": 61.0}, {"base_index": 7},
])
def test_ramp_validation(kwargs):
    with pytest.raises(adapter.AdapterError):
        hl.make_ramp("#336699", **kwargs)


def test_ramp_rejects_bad_colour():
    with pytest.raises(adapter.AdapterError):
        hl.make_ramp("blue")


# ============================================================ pure: dithering


def test_bayer_matrices_are_permutations():
    for n, m in hl._BAYER.items():
        flat = sorted(v for row in m for v in row)
        assert flat == list(range(n * n))


@pytest.mark.parametrize("matrix, level, light_of_total", [
    (2, 0.5, (2, 4)), (4, 0.5, (8, 16)), (4, 0.25, (4, 16)), (8, 0.25, (16, 64)), (8, 0.75, (48, 64)),
])
def test_dither_coverage_over_full_tile_is_exact(matrix, level, light_of_total):
    cells = [(x, y) for y in range(matrix) for x in range(matrix)]
    got = hl.dither_cells(cells, level, matrix=matrix)
    assert sum(got.values()) == light_of_total[0] and len(got) == light_of_total[1]


def test_dither_extremes_and_gradient_monotone():
    cells = [(x, y) for y in range(8) for x in range(8)]
    assert not any(hl.dither_cells(cells, 0.0).values())
    assert all(hl.dither_cells(cells, 1.0).values())
    g = hl.dither_cells(cells, 0.0, 1.0, axis="x", matrix=4)
    per_col = [sum(g[(x, y)] for y in range(8)) for x in range(8)]
    assert per_col[0] == 0 and per_col[-1] == 8 and per_col == sorted(per_col)
    d = hl.dither_cells(cells, 0.0, 1.0, axis="diag", matrix=8)
    assert not d[(0, 0)] and d[(7, 7)]


def test_dither_is_deterministic_and_validates():
    cells = [(x, y) for y in range(6) for x in range(6)]
    assert hl.dither_cells(cells, 0.4, 0.9, "y", 4) == hl.dither_cells(cells, 0.4, 0.9, "y", 4)
    for bad in ({"level": 1.5}, {"level": -0.1}, {"level": 0.5, "matrix": 3},
                {"level": 0.5, "axis": "z"}, {"level": 0.5, "level_to": 2}):
        with pytest.raises(adapter.AdapterError):
            hl.dither_cells(cells, **bad)
    assert hl.dither_cells([], 0.5) == {}


# ============================================================ pure: strokes


def removable_l_corners(path, protected, cyclic=False):
    """Independent check: L-corner pixels of `path` that are not protected."""
    n = len(path)
    idx = range(n) if cyclic else range(1, n - 1)
    out = []
    for i in idx:
        a, b, c = path[i - 1], path[i], path[(i + 1) % n]
        if (abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 and abs(b[0] - c[0]) + abs(b[1] - c[1]) == 1
                and abs(a[0] - c[0]) == 1 and abs(a[1] - c[1]) == 1 and b not in protected):
            out.append(b)
    return out


def test_stroke_freehand_staircase_is_cleaned_only_with_pixel_perfect():
    trace = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]
    assert hl.stroke_pixels(trace, pixel_perfect=True) == [(0, 0), (1, 1), (2, 2)]
    assert hl.stroke_pixels(trace, pixel_perfect=False) == trace


def test_stroke_long_segment_corners_are_intentional_and_kept():
    assert hl.stroke_pixels([(0, 0), (3, 0), (3, 3)]) == [
        (0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3)]


def test_stroke_mixed_long_and_unit_segments():
    # (4,0) borders a long segment: kept. (4,1) and (5,1) are both unit-step trace; the staircase
    # (4,0)-(4,1)-(5,1)-(5,2) loses ONE corner (the first one found, (4,1)), leaving a diagonal step.
    out = hl.stroke_pixels([(0, 0), (4, 0), (4, 1), (5, 1), (5, 2)])
    assert out == [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 1), (5, 2)]
    assert (4, 0) in out and out[0] == (0, 0) and out[-1] == (5, 2)


def test_stroke_closed_box_keeps_all_corners_and_full_perimeter():
    box = hl.stroke_pixels([(1, 1), (5, 1), (5, 4), (1, 4)], closed=True)
    for corner in [(1, 1), (5, 1), (5, 4), (1, 4)]:
        assert corner in box
    assert box[0] == box[-1] and len(box) == len(set(box)) + 1  # closed: start repeated at the end
    perimeter = {(x, 1) for x in range(1, 6)} | {(x, 4) for x in range(1, 6)} | \
                {(1, y) for y in range(1, 5)} | {(5, y) for y in range(1, 5)}
    assert set(box) == perimeter


def test_stroke_closed_first_and_last_vertex_are_judged_by_their_wrap_around_neighbours():
    # (0,0) has a unit step to (1,0) but a long segment arriving from (0,5); (0,5) likewise leaves
    # to a long segment: both are intentional corners only because of the wrap-around neighbour.
    out = hl.stroke_pixels([(0, 0), (1, 0), (1, 5), (0, 5)], closed=True)
    for corner in [(0, 0), (1, 0), (1, 5), (0, 5)]:
        assert corner in out


def test_stroke_closed_unit_step_loop_is_cleaned_all_the_way_round():
    ring = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3), (2, 3), (1, 3), (0, 3), (0, 2), (0, 1)]
    out = hl.stroke_pixels(ring, closed=True)
    body = out[:-1]
    assert out[0] == out[-1] and len(body) == len(set(body)) and len(body) >= 3
    assert not {(0, 0), (3, 0), (3, 3), (0, 3)} & set(body)  # all four square corners rounded off
    assert len(body) == len(ring) - 4
    assert not removable_l_corners(body, set(), cyclic=True)
    assert hl.stroke_pixels(ring, closed=True, pixel_perfect=False)[:-1] == ring


def test_stroke_tiny_unit_loop_never_collapses_below_three_pixels():
    out = hl.stroke_pixels([(0, 0), (1, 0), (1, 1), (0, 1)], closed=True)
    assert len(set(out)) >= 3


def test_stroke_duplicate_consecutive_points_are_ignored():
    assert hl.stroke_pixels([(0, 0), (0, 0), (1, 0), (1, 0), (1, 1), (2, 1), (2, 2)]) == [
        (0, 0), (1, 1), (2, 2)]
    assert hl.stroke_pixels([(2, 2), (2, 2)]) == [(2, 2)]


def test_stroke_property_random_dense_walks():
    import random
    rng = random.Random(20261002)
    for _ in range(300):
        n = rng.randint(3, 40)
        x, y = rng.randint(0, 20), rng.randint(0, 20)
        walk = [(x, y)]
        for _ in range(n):
            dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            x, y = x + dx, y + dy
            walk.append((x, y))
        raw = hl.stroke_pixels(walk, pixel_perfect=False)
        assert raw == walk  # unit steps rasterise to themselves
        out = hl.stroke_pixels(walk, pixel_perfect=True)
        assert out[0] == walk[0] and out[-1] == walk[-1]  # endpoints preserved
        it = iter(walk)
        assert all(p in it for p in out)  # output is a subsequence of the raw path
        # every interior point of a unit-step walk is trace, so no removable L corner may remain
        assert not removable_l_corners(out, {out[0], out[-1]})
        assert out == hl.stroke_pixels(walk, pixel_perfect=True)  # deterministic


def test_stroke_property_mixed_segments_never_remove_a_protected_vertex():
    import random
    rng = random.Random(7)
    for _ in range(300):
        pts = [(rng.randint(0, 15), rng.randint(0, 15)) for _ in range(rng.randint(2, 6))]
        deduped = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        if any(max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 1 for a, b in zip(deduped, deduped[1:])):
            continue  # only vertex lists whose every segment is long: all corners are intentional
        out = hl.stroke_pixels(pts, pixel_perfect=True)
        assert out == hl.stroke_pixels(pts, pixel_perfect=False)  # nothing to clean
        assert out[0] == deduped[0] and out[-1] == deduped[-1]


def test_stroke_straight_and_diagonal_lines_unchanged_by_cleanup():
    for a, b in [((0, 0), (7, 0)), ((0, 0), (0, 5)), ((0, 0), (6, 6)), ((0, 0), (7, 3))]:
        assert hl.stroke_pixels([a, b], pixel_perfect=True) == hl.stroke_pixels([a, b], pixel_perfect=False)


def test_stroke_single_point_and_empty():
    assert hl.stroke_pixels([(2, 3)]) == [(2, 3)]
    with pytest.raises(adapter.AdapterError):
        hl.stroke_pixels([])


# ============================================================ pure: shading


def test_bevel_rect_lights_top_left_edges_and_shades_bottom_right():
    mask = hl.rect_cells(0, 0, 8, 8)
    off = hl.shade_offsets(mask, "tl", 3, "bevel")
    assert off[(3, 0)] == 1 and off[(0, 3)] == 1  # top and left edge: lit
    assert off[(3, 7)] == -1 and off[(7, 3)] == -1  # bottom and right edge: shadow
    assert off[(3, 3)] == 0 and off[(4, 4)] == 0  # interior stays the base colour
    flipped = hl.shade_offsets(mask, "br", 3, "bevel")
    assert flipped[(3, 7)] == 1 and flipped[(3, 0)] == -1  # light moved: edges swap


def test_round_ellipse_has_three_bands_light_side_toward_light():
    mask = hl.ellipse_cells(0, 0, 12, 12)
    off = hl.shade_offsets(mask, "tl", 3, "round")
    assert set(off.values()) == {-1, 0, 1}
    lit = [p for p, o in off.items() if o == 1]
    dark = [p for p, o in off.items() if o == -1]
    assert sum(x + y for x, y in lit) / len(lit) < sum(x + y for x, y in dark) / len(dark)
    br = hl.shade_offsets(mask, "br", 3, "round")
    lit2 = [p for p, o in br.items() if o == 1]
    assert sum(x + y for x, y in lit2) / len(lit2) > sum(x + y for x, y in lit) / len(lit)


def test_five_bands_use_five_levels_on_a_large_form():
    off = hl.shade_offsets(hl.ellipse_cells(0, 0, 24, 24), "tl", 5, "round", contrast=0.08)
    assert set(off.values()) == {-2, -1, 0, 1, 2}


def test_shading_is_deterministic_and_has_no_orphan_bands():
    mask = hl.ellipse_cells(0, 0, 14, 10)
    a = hl.shade_offsets(mask, "tl", 3, "round")
    assert a == hl.shade_offsets(mask, "tl", 3, "round")
    for p, o in a.items():
        nb = [a[(p[0] + dx, p[1] + dy)] for dx, dy in hl._N4 if (p[0] + dx, p[1] + dy) in a]
        if len(nb) >= 2:
            assert o in nb, f"orphan band at {p}"


@pytest.mark.parametrize("kwargs", [
    {"light": "up"}, {"bands": 4}, {"form": "cone"}, {"contrast": 0.0}, {"contrast": 0.9},
])
def test_shading_validation(kwargs):
    with pytest.raises(adapter.AdapterError):
        hl.shade_offsets(hl.rect_cells(0, 0, 4, 4), **kwargs)


def test_shading_empty_mask_is_empty():
    assert hl.shade_offsets(set()) == {}


# ============================================================ pure: ascii + lint


def test_ascii_grid_legend_by_frequency_and_transparent_dot():
    g = [["#ff0000ff", "#ff0000ff", "#00000000"], ["#00ff00ff", "#ff0000ff", "#00000000"]]
    rows, legend = hl.ascii_grid(g)
    assert rows == ["AA.", "BA."] and legend == {"A": "#ff0000ff", "B": "#00ff00ff"}


def make_grid(w, h, painter):
    return [[painter(x, y) or "#00000000" for x in range(w)] for y in range(h)]


def test_lint_clean_sprite_passes():
    grid = make_grid(16, 16, lambda x, y: ("#101010ff" if x in (3, 12) or y in (3, 12) else "#c8c8c8ff")
                     if 3 <= x <= 12 and 3 <= y <= 12 else None)
    r = hl.lint_grid(grid)
    assert r["ok"] and not [f for f in r["findings"] if f["level"] == "warn"]
    assert r["stats"]["colors"] == 2 and r["stats"]["bbox"] == (3, 3, 12, 12)


def test_lint_flags_palette_budget_value_separation_edge_and_orphans():
    base = [(i * 20) % 256 for i in range(12)]
    cols = [f"#{v:02x}{(v * 3) % 256:02x}{(v * 7) % 256:02x}ff" for v in base]
    grid = make_grid(16, 16, lambda x, y: cols[(x // 2 + y // 2) % 12])
    r = hl.lint_grid(grid)
    codes = {f["code"] for f in r["findings"]}
    assert "palette_budget" in codes and "touches_edge" in codes and not r["ok"]

    near = make_grid(8, 8, lambda x, y: "#646464ff" if x < 4 else "#686868ff")
    assert "value_separation" in {f["code"] for f in hl.lint_grid(near)["findings"]}

    dots = make_grid(8, 8, lambda x, y: "#ff0000ff" if (x, y) in {(2, 2), (5, 5)} else
                     ("#222222ff" if (x, y) == (3, 3) else None))
    f = [f for f in hl.lint_grid(dots)["findings"] if f["code"] == "orphan_pixels"][0]
    assert (2, 2) in f["pixels"] and (5, 5) in f["pixels"]


def test_lint_empty_frame_is_a_warning():
    r = hl.lint_grid(make_grid(4, 4, lambda x, y: None))
    assert not r["ok"] and r["findings"][0]["code"] == "empty"


def test_lint_budget_scales_with_canvas():
    assert hl.lint_grid(make_grid(32, 32, lambda x, y: "#ff0000ff"))["stats"]["color_budget"] == 12
    assert hl.lint_grid(make_grid(8, 8, lambda x, y: "#ff0000ff"))["stats"]["color_budget"] == 8
    assert hl.lint_grid(make_grid(64, 64, lambda x, y: "#ff0000ff"))["stats"]["color_budget"] == 16
    assert hl.lint_grid(make_grid(100, 100, lambda x, y: "#ff0000ff"))["stats"]["color_budget"] == 24


# ============================================================ sprite-facing (real Aseprite)


@pytest.fixture
def ws(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "WORKSPACE", tmp_path / "ws")
    return tmp_path / "ws"


def grid_of(name, rev=None, frame=1):
    return ht.read_grid(name, rev, frame)[0]


@needs_aseprite
def test_read_grid_tiles_large_sprites_correctly(ws):
    adapter.new_sprite("big", 70, 40, "#00000000")
    adapter.apply_ops("big", "r0001", [
        {"op": "pixels", "pixels": [{"x": 0, "y": 0, "color": "#ff0000"},
                                    {"x": 69, "y": 39, "color": "#00ff00"},
                                    {"x": 33, "y": 32, "color": "#0000ff"}]}])
    g = grid_of("big")
    assert len(g) == 40 and len(g[0]) == 70
    assert g[0][0] == "#ff0000ff" and g[39][69] == "#00ff00ff" and g[32][33] == "#0000ffff"
    assert sum(c != "#00000000" for row in g for c in row) == 3


@needs_aseprite
def test_shade_ellipse_paints_ramp_bands_and_creates_revision(ws):
    adapter.new_sprite("orb", 16, 16, "#00000000")
    out = ht.shade("orb", "r0001", {"ellipse": {"x": 2, "y": 2, "width": 12, "height": 12}},
                   base="#3ec96b", steps=5, light="tl", bands=3)
    ramp = hl.make_ramp("#3ec96b", 5)
    assert out["revision"] == "r0002" and out["shaded_pixels"] == len(hl.ellipse_cells(2, 2, 12, 12))
    used = {c[:7] for row in grid_of("orb") for c in row if not c.endswith("00")}
    assert used == {ramp[1], ramp[2], ramp[3]}  # 3 bands -> ramp[base-1 .. base+1]
    assert set(out["band_counts"]) == {"-1", "0", "1"} and all(v > 0 for v in out["band_counts"].values())
    g = grid_of("orb")
    assert g[3][5][:7] == ramp[3] and g[12][10][:7] == ramp[1]  # lit top-left, shaded bottom-right


@needs_aseprite
def test_shade_color_target_only_touches_that_colour(ws):
    adapter.new_sprite("c", 12, 12, "#00000000")
    adapter.apply_ops("c", "r0001", [
        {"op": "rect", "x": 1, "y": 1, "width": 6, "height": 6, "color": "#6e7f99"},
        {"op": "rect", "x": 8, "y": 8, "width": 3, "height": 3, "color": "#c0392b"}])
    ht.shade("c", "r0002", {"color": "#6e7f99"}, base="#6e7f99", bands=3, form="bevel")
    g = grid_of("c")
    assert all(g[y][x] == "#c0392bff" for y in range(8, 11) for x in range(8, 11))  # other colour untouched
    assert g[0][0] == "#00000000"
    top_left, bottom_right = g[1][3], g[6][3]
    assert hl.luma(hl.hex_to_rgba(top_left)) > hl.luma(hl.hex_to_rgba(bottom_right))


@needs_aseprite
def test_shade_errors_are_clean(ws):
    adapter.new_sprite("e", 8, 8, "#00000000")
    with pytest.raises(adapter.AdapterError, match="stale"):
        ht.shade("e", "r0009", {"opaque": True}, base="#336699")
    with pytest.raises(adapter.AdapterError, match="selects no pixels"):
        ht.shade("e", "r0001", {"opaque": True}, base="#336699")
    with pytest.raises(adapter.AdapterError, match="exactly one"):
        ht.shade("e", "r0001", {"opaque": True, "color": "#ffffff"}, base="#336699")
    with pytest.raises(adapter.AdapterError, match="either ramp or base"):
        ht.shade("e", "r0001", {"rect": {"x": 0, "y": 0, "width": 2, "height": 2}})
    with pytest.raises(adapter.AdapterError, match="at least 3"):
        ht.shade("e", "r0001", {"rect": {"x": 0, "y": 0, "width": 2, "height": 2}}, ramp_colors=["#000000"])
    assert adapter.inspect_sprite("e")["revision"] == "r0001"  # nothing published by failures


@needs_aseprite
def test_dither_region_half_coverage_and_gradient(ws):
    adapter.new_sprite("d", 8, 8, "#00000000")
    out = ht.dither("d", "r0001", "#102030", "#a0b0c0", 0.5,
                    region={"x": 0, "y": 0, "width": 8, "height": 8})
    assert out["light_pixels"] == 32 and out["dithered_pixels"] == 64
    g = grid_of("d")
    assert sum(c == "#a0b0c0ff" for row in g for c in row) == 32
    out2 = ht.dither("d", "r0002", "#102030", "#a0b0c0", 0.0, level_to=1.0, axis="x",
                     region={"x": 0, "y": 0, "width": 8, "height": 8})
    g = grid_of("d")
    cols = [sum(g[y][x] == "#a0b0c0ff" for y in range(8)) for x in range(8)]
    assert cols[0] == 0 and cols[-1] == 8 and cols == sorted(cols) and out2["revision"] == "r0003"


@needs_aseprite
def test_dither_target_color_mask_and_arg_errors(ws):
    adapter.new_sprite("d", 8, 8, "#00000000")
    adapter.apply_ops("d", "r0001", [{"op": "rect", "x": 2, "y": 2, "width": 4, "height": 4, "color": "#808080"}])
    out = ht.dither("d", "r0002", "#202020", "#e0e0e0", 0.5, target_color="#808080")
    assert out["dithered_pixels"] == 16 and out["light_pixels"] == 8
    with pytest.raises(adapter.AdapterError, match="exactly one"):
        ht.dither("d", "r0003", "#000000", "#ffffff", 0.5)
    with pytest.raises(adapter.AdapterError, match="exactly one"):
        ht.dither("d", "r0003", "#000000", "#ffffff", 0.5, region={"x": 0, "y": 0, "width": 1, "height": 1},
                  target_color="#808080")


@needs_aseprite
def test_stroke_closed_box_and_layer_creation(ws):
    adapter.new_sprite("s", 10, 10, "#00000000")
    out = ht.stroke("s", "r0001", [[1, 1], [6, 1], [6, 5], [1, 5]], "#ff00ff", closed=True, layer="lines")
    assert out["stroke_pixels"] == len(set(hl.stroke_pixels([(1, 1), (6, 1), (6, 5), (1, 5)], True)))
    names = [l["name"] for l in adapter.inspect_sprite("s")["layers"]]
    assert names == ["base", "lines"]
    g = grid_of("s")
    assert g[1][1] == g[1][6] == g[5][6] == g[5][1] == "#ff00ffff" and g[3][3] == "#00000000"
    with pytest.raises(adapter.AdapterError, match="each point"):
        ht.stroke("s", "r0002", [[1, "a"]], "#ffffff")


@needs_aseprite
def test_auto_outline_full_selout_skip_and_clipping(ws):
    for n in ("o1", "o2", "o3", "o4"):
        adapter.new_sprite(n, 10, 10, "#00000000")
        adapter.apply_ops(n, "r0001", [{"op": "rect", "x": 3, "y": 3, "width": 4, "height": 4, "color": "#c9d1dc"}])
    full = ht.auto_outline("o1", "r0002", "full", "#000000")
    assert full["outline_pixels"] == 16 and full["outline_clipped"] == 0  # 4-neighbour ring, no corners
    assert [l["name"] for l in adapter.inspect_sprite("o1")["layers"]] == ["base", "outline"]
    g = grid_of("o1")
    assert g[2][4] == "#000000ff" and g[2][2] == "#00000000"  # ring has no diagonal corner pixels

    se = ht.auto_outline("o2", "r0002", "selout")
    fill = hl.luma(hl.hex_to_rgba("#c9d1dc"))
    out_c = grid_of("o2")[2][4]
    assert out_c != "#000000ff" and hl.luma(hl.hex_to_rgba(out_c)) < fill * 0.6
    assert hsv(out_c)[0] > hsv("#c9d1dc")[0] - 1  # shifted toward blue, not away

    skip = ht.auto_outline("o3", "r0002", "full", lit_edges="skip", light="tl")
    assert skip["outline_pixels"] == 8  # top and left edges left open
    g = grid_of("o3")
    assert g[2][4] == "#00000000" and g[7][4] == "#000000ff"

    adapter.new_sprite("edge", 6, 6, "#00000000")
    adapter.apply_ops("edge", "r0001", [{"op": "rect", "x": 0, "y": 0, "width": 3, "height": 3, "color": "#ffffff"}])
    e = ht.auto_outline("edge", "r0002")
    assert e["outline_clipped"] == 6 and e["outline_pixels"] == 6  # top/left would fall off-canvas
    with pytest.raises(adapter.AdapterError, match="mode"):
        ht.auto_outline("o4", "r0002", "weird")


@needs_aseprite
def test_selout_reuses_existing_dark_colours_instead_of_inventing_new_ones(ws):
    adapter.new_sprite("p", 12, 12, "#00000000")
    adapter.apply_ops("p", "r0001", [
        {"op": "rect", "x": 3, "y": 3, "width": 6, "height": 6, "color": "#8fa9b9"},
        {"op": "rect", "x": 3, "y": 6, "width": 6, "height": 3, "color": "#50546d"},
        {"op": "pixels", "pixels": [{"x": 5, "y": 4, "color": "#252331"}]}])
    before = set(adapter.inspect_sprite("p")["colors"])
    ht.auto_outline("p", "r0002", "selout")
    after = set(adapter.inspect_sprite("p")["colors"])
    assert after == before  # no new colour: every outline pixel reused a darker existing one
    g = grid_of("p")
    assert g[2][5] in before and hl.luma(hl.hex_to_rgba(g[2][5])) < hl.luma(hl.hex_to_rgba("#8fa9b9")) * 0.7


@needs_aseprite
def test_remap_palette_snaps_and_guards_multilayer(ws):
    adapter.new_sprite("r", 6, 6, "#00000000")
    adapter.apply_ops("r", "r0001", [
        {"op": "pixels", "pixels": [{"x": 0, "y": 0, "color": "#fe0101"}, {"x": 1, "y": 0, "color": "#0102fd"},
                                    {"x": 2, "y": 0, "color": "#ff0000cc"}]}])
    out = ht.remap_palette("r", "r0002", ["#ff0000", "#0000ff"])
    g = grid_of("r")
    assert g[0][0] == "#ff0000ff" and g[0][1] == "#0000ffff" and g[0][2] == "#ff0000cc"  # alpha preserved
    assert out["remapped_pixels"] == 2 and out["palette_size"] == 2  # the 3rd was already exact red

    adapter.new_sprite("m", 4, 4)
    adapter.apply_ops("m", "r0001", [
        {"op": "add_layer", "name": "top"},
        {"op": "pixels", "pixels": [{"x": 0, "y": 0, "color": "#ffffff"}], "layer": "base"},
        {"op": "pixels", "pixels": [{"x": 1, "y": 1, "color": "#ffffff"}], "layer": "top"}])
    with pytest.raises(adapter.AdapterError, match="exactly one layer"):
        ht.remap_palette("m", "r0002", ["#000000"])


@needs_aseprite
def test_lint_and_ascii_view_on_a_real_sprite(ws):
    adapter.new_sprite("lint", 16, 16, "#00000000")
    ht.shade("lint", "r0001", {"ellipse": {"x": 3, "y": 3, "width": 10, "height": 10}}, base="#6e7f99")
    ht.auto_outline("lint", "r0002", "full", "#101010")
    rep = ht.lint("lint")
    assert rep["stats"]["colors"] == 4 and rep["ok"] and rep["stats"]["bbox"] == (2, 2, 13, 13)
    view = ht.ascii_view("lint")
    assert view["width"] == 16 and len(view["rows"]) == 16 and all(len(r) == 16 for r in view["rows"])
    assert view["rows"][0] == "." * 16 and len(view["legend"]) == 4
    assert view["rows"][8].count(".") < 16


@needs_aseprite
def test_register_exposes_exactly_the_documented_tools(ws):
    from mcp.server.fastmcp import FastMCP
    srv = FastMCP("t")
    ht.register(srv)
    assert set(srv._tool_manager._tools) == {
        "make_ramp", "shade", "dither", "stroke", "auto_outline", "remap_palette", "lint_sprite", "ascii_view"}
