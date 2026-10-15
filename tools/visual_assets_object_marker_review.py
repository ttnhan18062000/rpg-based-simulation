"""Owner review sheets 01 to 03 of the object-marker drafts (`TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS`): every marker, nodes over terrain, buildings beside the adopted ones.

Pure functions over `rule.Sprite` dicts, so the layout can be tested without the Aseprite workspace. The driver that reads the drafts and the sample-map data (sheet 04) is the scratch script
in the ticket's staging artifacts. Deterministic, writes nothing itself. Evidence tooling for an owner gate: adopts nothing.
"""

from __future__ import annotations

from visual_assets.review import icon_sheet_rule as rule
from visual_assets.review.review_sheets import DARK, DIM, GREEN, INK, LIGHT, PAGE, Canvas, wrap

CH = 12  # the review font at scale 2: 6 columns of 2 px per character
GRASS = (0x4A, 0x60, 0x30)
TITLE_01 = "OBJECT MARKERS V1: EVERY MARKER AT THE REAL SIZE (X1) AND X4"
HEADER_01 = "Each marker is shown x4 on a dark and a light panel, then at x1 and x2 on a grass cell. Nodes and the nest are 16 x 16; buildings are 24 x 24 panel icons."
ROW_H = 24 * 4 + 60


def label(key: str) -> str:
    return key.split(".", 2)[2].upper()


def layout_01(names: list[str], cols: int = 2) -> dict:
    """Cell width from the longest label and the widest picture; the title and header wrap to the page width and the first row starts below them (no overlap, no clipping)."""
    picture = 24 * 4 * 2 + 10 + 10 + 24 * 2 + 10
    cell = max(picture, max(len(label(k)) for k in names) * CH + 20) + 40
    width = cols * cell + 40
    chars = (width - 40) // CH
    title = wrap(TITLE_01, chars)
    header = wrap(HEADER_01, chars)
    top = 20 + 26 * len(title) + 26 * len(header) + 30
    rows = -(-len(names) // cols)
    return {"cell": cell, "width": width, "height": top + rows * ROW_H + 20, "title": title, "header": header, "top": top, "cols": cols}


def draw(c: Canvas, sp: rule.Sprite, x: int, y: int, z: int, bg=None) -> None:
    if bg is not None:
        c.rect(x, y, sp.width * z, sp.height * z, bg)
    for i, (r, g, b, a) in enumerate(sp.rgba):
        if a:
            c.rect(x + (i % sp.width) * z, y + (i // sp.width) * z, z, z, (r, g, b))


def sheet_01(sprites: dict[str, rule.Sprite], names: list[str]) -> Canvas:
    g = layout_01(names)
    c = Canvas(g["width"], g["height"], PAGE)
    y = 20
    for line in g["title"]:
        c.text(20, y, line, INK, 2)
        y += 26
    for line in g["header"]:
        c.text(20, y, line, DIM, 2)
        y += 26
    for i, k in enumerate(names):
        sp = sprites[k]
        x0, y0 = 20 + (i % g["cols"]) * g["cell"], g["top"] + (i // g["cols"]) * ROW_H
        c.text(x0, y0, label(k), GREEN, 2)
        draw(c, sp, x0, y0 + 24, 4, DARK)
        draw(c, sp, x0 + sp.width * 4 + 10, y0 + 24, 4, LIGHT)
        xr = x0 + 2 * (sp.width * 4 + 10) + 10
        draw(c, sp, xr, y0 + 24, 1, GRASS)
        draw(c, sp, xr + sp.width + 8, y0 + 24, 2, GRASS)
    return c
