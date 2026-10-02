"""ASCII view and advisory lint maths (pure; no Aseprite)."""

from __future__ import annotations

import pytest

from visual_assets.drawing.technique.ascii import ascii_grid
from visual_assets.drawing.technique.lint import lint_grid

# ============================================================ pure: ascii + lint


def test_ascii_grid_legend_by_frequency_and_transparent_dot():
    g = [["#ff0000ff", "#ff0000ff", "#00000000"], ["#00ff00ff", "#ff0000ff", "#00000000"]]
    rows, legend = ascii_grid(g)
    assert rows == ["AA.", "BA."] and legend == {"A": "#ff0000ff", "B": "#00ff00ff"}


def make_grid(w, h, painter):
    return [[painter(x, y) or "#00000000" for x in range(w)] for y in range(h)]


def test_lint_clean_sprite_passes():
    grid = make_grid(16, 16, lambda x, y: ("#101010ff" if x in (3, 12) or y in (3, 12) else "#c8c8c8ff")
                     if 3 <= x <= 12 and 3 <= y <= 12 else None)
    r = lint_grid(grid)
    assert r["ok"] and not [f for f in r["findings"] if f["level"] == "warn"]
    assert r["stats"]["colors"] == 2 and r["stats"]["bbox"] == (3, 3, 12, 12)


def test_lint_flags_palette_budget_value_separation_edge_and_orphans():
    base = [(i * 20) % 256 for i in range(12)]
    cols = [f"#{v:02x}{(v * 3) % 256:02x}{(v * 7) % 256:02x}ff" for v in base]
    grid = make_grid(16, 16, lambda x, y: cols[(x // 2 + y // 2) % 12])
    r = lint_grid(grid)
    codes = {f["code"] for f in r["findings"]}
    assert "palette_budget" in codes and "touches_edge" in codes and not r["ok"]

    near = make_grid(8, 8, lambda x, y: "#646464ff" if x < 4 else "#686868ff")
    assert "value_separation" in {f["code"] for f in lint_grid(near)["findings"]}

    dots = make_grid(8, 8, lambda x, y: "#ff0000ff" if (x, y) in {(2, 2), (5, 5)} else
                     ("#222222ff" if (x, y) == (3, 3) else None))
    f = [f for f in lint_grid(dots)["findings"] if f["code"] == "orphan_pixels"][0]
    assert (2, 2) in f["pixels"] and (5, 5) in f["pixels"]


def test_lint_empty_frame_is_a_warning():
    r = lint_grid(make_grid(4, 4, lambda x, y: None))
    assert not r["ok"] and r["findings"][0]["code"] == "empty"


def test_lint_budget_scales_with_canvas():
    assert lint_grid(make_grid(32, 32, lambda x, y: "#ff0000ff"))["stats"]["color_budget"] == 12
    assert lint_grid(make_grid(8, 8, lambda x, y: "#ff0000ff"))["stats"]["color_budget"] == 8
    assert lint_grid(make_grid(64, 64, lambda x, y: "#ff0000ff"))["stats"]["color_budget"] == 16
    assert lint_grid(make_grid(100, 100, lambda x, y: "#ff0000ff"))["stats"]["color_budget"] == 24


