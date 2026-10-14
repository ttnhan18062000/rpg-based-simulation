"""Palettes as data (TCK-20261010-VISUAL-ASSETS-PALETTE-AS-DATA): generated files are drift-guarded, lint reports off-palette pixels as advice, and the colour budgets keep their values."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from visual_assets.drawing import compose, palettes
from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.technique import lint
from visual_assets.review import palette_data
from visual_assets.store import pixels

REPO = Path(__file__).resolve().parents[2]
PALETTES = REPO / "visual_assets" / "palettes"


# ---- drift guards ----

@pytest.mark.parametrize("path", sorted(palette_data.expected_files(), key=str), ids=lambda p: p.name)
def test_every_generated_palette_file_equals_its_generator(path):
    assert path.read_text(encoding="utf-8") == palette_data.expected_files()[path], f"{path.name} drifted: run `python -m visual_assets.review.palette_data --write`"


def test_terrain_palette_is_the_live_map_terrain_fills():
    ts = (REPO / "frontend" / "src" / "constants" / "colors.ts").read_text()
    fills = set(re.findall(r"#[0-9a-fA-F]{6}", ts))
    colors = json.loads((PALETTES / "terrain-v1.json").read_text())["colors"]
    assert len(colors) == 23 and set(colors) <= {c.lower() for c in fills}


def test_gpl_files_are_valid_gimp_palettes_with_one_line_per_entry():
    for pid in ("icons-v1", "terrain-v1"):
        lines = (PALETTES / f"{pid}.gpl").read_text().splitlines()
        assert lines[:4] == ["GIMP Palette", f"Name: {pid}", "Columns: 8", "#"]
        entries = json.loads((PALETTES / f"{pid}.json").read_text())["entries"]
        assert len(lines) == 4 + len(entries)
        for line, entry in zip(lines[4:], entries):
            m = re.fullmatch(r"\s*(\d+)\s+(\d+)\s+(\d+)\t([0-9a-f]{6}) .+", line)
            assert m and "#" + m.group(4) == entry["color"] and "{:02x}{:02x}{:02x}".format(*map(int, m.groups()[:3])) == m.group(4)


def test_a_drifted_generated_file_would_be_caught(tmp_path):
    text = palette_data.expected_files()[palette_data.TERRAIN_FILE]
    assert text.replace("#4a6050", "#4a6051") != text  # the guard compares exact text, so a one-digit edit differs


# ---- lint: advisory off-palette report ----

def grid_of(colours, w=4, h=4):
    return [[colours[(x + y) % len(colours)] for x in range(w)] for y in range(h)]


def test_lint_without_a_palette_is_unchanged():
    grid = grid_of(["#112233ff", "#445566ff"])
    report = lint.lint_grid(grid)
    assert "off_palette_pixels" not in report["stats"] and not [f for f in report["findings"] if f["code"] == "off_palette"]
    assert report == lint.lint_grid(grid, palette=None)


def test_a_planted_off_palette_pixel_is_reported_with_its_coordinates_and_never_rules():
    grid = grid_of(["#112233ff", "#445566ff"])
    grid[2][3] = "#ff00ffff"
    report = lint.lint_grid(grid, palette=["#112233", "#445566"])
    finding = next(f for f in report["findings"] if f["code"] == "off_palette")
    assert finding["level"] == "info" and finding["count"] == 1 and finding["pixels"] == [(3, 2)] and finding["colors"] == ["#ff00ff"]
    assert report["stats"]["off_palette_pixels"] == 1
    assert report["ok"] == lint.lint_grid(grid)["ok"]  # advice only: ok does not change


def test_transparent_pixels_and_alpha_do_not_count_as_off_palette():
    grid = grid_of(["#112233ff", "#44556680", "#ff00ff00"])
    assert lint.lint_grid(grid, palette=["#112233", "#445566"])["stats"]["off_palette_pixels"] == 0


def test_off_palette_coordinates_are_capped_and_ordered_row_major():
    grid = [["#ff0000ff"] * 8 for _ in range(8)]
    finding = next(f for f in lint.lint_grid(grid, palette=["#000000"])["findings"] if f["code"] == "off_palette")
    assert finding["count"] == 64 and len(finding["pixels"]) == 20 and finding["pixels"][:3] == [(0, 0), (1, 0), (2, 0)]


def adopted_icon_grids():
    out = {}
    for png in sorted((REPO / "visual_assets" / "catalog" / "generated").glob("icon_*/*.png")):
        image = pixels.decode_png(png.read_bytes(), max_dim=1024)
        out[png.parent.name] = [[f"#{image.rgba[i]:02x}{image.rgba[i+1]:02x}{image.rgba[i+2]:02x}{image.rgba[i+3]:02x}" for i in range((y * image.width) * 4, ((y + 1) * image.width) * 4, 4)] for y in range(image.height)]
    return out


def test_adopted_icons_pass_the_icon_palette():
    grids = adopted_icon_grids()
    assert len(grids) >= 36
    colours = palettes.load_palette("icons-v1")
    off = {k: lint.lint_grid(g, palette=colours)["stats"]["off_palette_pixels"] for k, g in grids.items()}
    assert {k: v for k, v in off.items() if v} == {}


def test_a_planted_pixel_in_an_adopted_icon_is_flagged():
    name, grid = next(iter(adopted_icon_grids().items()))
    y, x = next((y, x) for y, row in enumerate(grid) for x, c in enumerate(row) if c.endswith("ff"))
    grid[y][x] = "#fe01fdff"
    assert lint.lint_grid(grid, palette=palettes.load_palette("icons-v1"))["stats"]["off_palette_pixels"] == 1


# ---- the palette loader and the compose entry ----

def test_palette_ids_load_and_bad_ids_are_refused():
    assert palettes.palette_ids() == ["icons-v1", "terrain-v1"]
    assert len(palettes.load_palette("terrain-v1")) == 23 and all(re.fullmatch(r"#[0-9a-f]{6}", c) for c in palettes.load_palette("icons-v1"))
    for bad in ("../icons-v1", "icons-v1.json", "nope-v1", "", "ICONS-V1", "icons-v1/../../x", 5):
        with pytest.raises(AdapterError):
            palettes.load_palette(bad)  # type: ignore[arg-type]


def test_compose_lint_takes_a_palette_or_a_palette_id_not_both(monkeypatch):
    grid = grid_of(["#4a6050ff"])
    monkeypatch.setattr(compose, "read_grid", lambda name, revision, frame: (grid, {}))
    assert compose.lint("s", palette_id="terrain-v1")["stats"]["off_palette_pixels"] == 0
    assert compose.lint("s", palette=["#000000"])["stats"]["off_palette_pixels"] == 16
    assert compose.lint("s")["stats"].get("off_palette_pixels") is None
    with pytest.raises(AdapterError):
        compose.lint("s", palette=["#000000"], palette_id="terrain-v1")


# ---- colour budgets keep their values ----

def test_the_colour_budgets_moved_to_data_with_the_same_values():
    assert lint._BUDGETS == ((16, 8), (32, 12), (64, 16)) and lint._BUDGET_ABOVE == 24
    for side, budget in ((8, 8), (16, 8), (17, 12), (32, 12), (33, 16), (64, 16), (65, 24), (128, 24)):
        grid = [["#000000ff"] * side for _ in range(side)]
        assert lint.lint_grid(grid)["stats"]["color_budget"] == budget, side
