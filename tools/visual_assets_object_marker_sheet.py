"""Owner review sheets for the object-marker silhouettes (`TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS`, step 1 of the recognisability process).

    python -m tools.visual_assets_object_marker_sheet <out_dir>      # writes 01_nodes_and_nest.png and 02_buildings.png

Reads `visual_assets/icons/object_marker_silhouettes.yaml` (one-colour rows of `#`, the live area only) and draws each option at x4 (light on dark and dark on light) and at the
real size (x1 and x2) over a grass-coloured cell. Pure Python, deterministic (the same file gives byte-identical PNGs), writes only into `<out_dir>`. This is evidence tooling for an
owner gate: it adopts nothing and touches no store.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from visual_assets.review.review_sheets import DARK, DIM, GREEN, INK, LIGHT, PAGE, Canvas, wrap

REPO = Path(__file__).resolve().parents[1]
SILHOUETTES = REPO / "visual_assets" / "icons" / "object_marker_silhouettes.yaml"
GRASS = (0x4A, 0x60, 0x30)
OUTLINE = (20, 20, 30)
MARGIN = 2
LIVE = {16: 12, 24: 20}


def load(path: Path = SILHOUETTES) -> dict:
    slots = yaml.safe_load(path.read_text())["slots"]
    for key, slot in slots.items():
        live = LIVE[slot["size"]]
        for option, rows in slot["options"].items():
            if len(rows) != live or any(len(r) != live or set(r) - {"#", "."} for r in rows):
                raise ValueError(f"{key} option {option}: rows must be {live} x {live} of '#' and '.'")
    return slots


def _draw(c: Canvas, rows: list[str], x: int, y: int, canvas: int, zoom: int, bg: tuple, ink: tuple) -> None:
    c.rect(x, y, canvas * zoom, canvas * zoom, bg)
    for ry, row in enumerate(rows):
        for rx, ch in enumerate(row):
            if ch == "#":
                c.rect(x + (MARGIN + rx) * zoom, y + (MARGIN + ry) * zoom, zoom, zoom, ink)


CHAR_W = 12  # the review font at scale 2: 6 columns of 2 px per character
HEADER = "One colour, outline included. Left: x4 light on dark. Middle: x4 dark on light. Right: x1 and x2 on grass (the real size)."


def layout(entries: list[tuple[str, list[str]]], canvas: int, cols: int = 2) -> dict:
    """Cell and page sizes; a cell is as wide as its longest label needs (plus a gutter), so no label can run into its neighbour or off the page."""
    picture = canvas * 4 * 2 + 10 + 10 + canvas + 8 + canvas * 2
    cell_w = max(picture, max(len(label) for label, _ in entries) * CHAR_W) + 40
    width = cols * cell_w + 40
    header = wrap(HEADER, (width - 40) // CHAR_W)
    return {"cell_w": cell_w, "width": width, "header": header, "row_h": canvas * 4 + 60, "top": 60 + 26 * len(header), "cols": cols}


def sheet(entries: list[tuple[str, list[str]]], canvas: int, title: str) -> Canvas:
    g = layout(entries, canvas)
    cols, cell_w, row_h = g["cols"], g["cell_w"], g["row_h"]
    c = Canvas(g["width"], g["top"] + -(-len(entries) // cols) * row_h + 20, PAGE)
    c.text(20, 20, title, INK, 2)
    for n, line in enumerate(g["header"]):
        c.text(20, 50 + 26 * n, line, DIM, 2)
    for i, (label, rows) in enumerate(entries):
        x0, y0 = 20 + (i % cols) * cell_w, g["top"] + (i // cols) * row_h
        c.text(x0, y0, label, GREEN, 2)
        y1 = y0 + 24
        _draw(c, rows, x0, y1, canvas, 4, DARK, LIGHT)
        _draw(c, rows, x0 + canvas * 4 + 10, y1, canvas, 4, LIGHT, DARK)
        xr = x0 + 2 * (canvas * 4 + 10) + 10
        _draw(c, rows, xr, y1, canvas, 1, GRASS, OUTLINE)
        _draw(c, rows, xr + canvas + 8, y1, canvas, 2, GRASS, OUTLINE)
    return c


def entries_for(slots: dict, size: int) -> list[tuple[str, list[str]]]:
    """Labels carry no family prefix (it is in the sheet title), only the option letter where a slot has two."""
    out = []
    for key in sorted(slots):
        if slots[key]["size"] != size:
            continue
        options = slots[key]["options"]
        for option in sorted(options):
            suffix = f" OPTION {option}" if len(options) > 1 else ""
            out.append((key.split(".", 2)[2].upper() + suffix, options[option]))
    return out


def build(out_dir: Path, path: Path = SILHOUETTES) -> list[str]:
    slots = load(path)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = {16: "01_nodes_and_nest.png", 24: "02_buildings.png"}
    titles = {16: "OBJECT MARKERS 16X16: RESOURCE NODES AND NEST", 24: "OBJECT MARKERS 24X24: BUILDINGS"}
    for size in (16, 24):
        (out_dir / names[size]).write_bytes(sheet(entries_for(slots, size), size, titles[size]).png())
    return sorted(names.values())


if __name__ == "__main__":
    print("\n".join(build(Path(sys.argv[1]))))
