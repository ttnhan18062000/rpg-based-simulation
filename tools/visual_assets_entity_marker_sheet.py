"""Owner review sheets for the entity-marker silhouettes (`TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS`, step 1 of the recognisability process).

    python -m tools.visual_assets_entity_marker_sheet <out_dir>      # writes 01_treatments.png and 02_candidates.png

Reads `visual_assets/icons/entity_marker_silhouettes.yaml` and draws every shape on a 16 x 16 map cell, at x8 and at the real size (x1), each beside the nearest adopted glyph (the collision
map of the investigation) drawn the same way. `01_treatments.png` shows worker, guard and sentinel in the three treatments of the set-wide question: (a) the bare object, (b) the emblem on a
round unit token, (c) a figure silhouette. `02_candidates.png` shows every candidate (A and B) of all 11 kinds as an emblem on the token, a preview of treatment (b). Pure Python, deterministic
(the same file gives byte-identical PNGs), writes only into `<out_dir>`. This is evidence tooling for an owner gate: it adopts nothing and touches no store.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from visual_assets.review import icon_lookalikes as la
from visual_assets.review.review_sheets import DARK, DIM, GREEN, INK, LIGHT, PAGE, Canvas, wrap

REPO = Path(__file__).resolve().parents[1]
SILHOUETTES = REPO / "visual_assets" / "icons" / "entity_marker_silhouettes.yaml"
GRASS = (0x4A, 0x60, 0x30)
OUTLINE = (20, 20, 30)
TOKEN = (0x5A, 0x64, 0x80)
CELL = 16
LIVE = 12
MARGIN = 2
EMBLEM = 8
ZOOM = 8
CHAR_W = 12
CELL_W = 520
COLS = 3
COMPARE = ("worker", "guard", "sentinel")
Rgb = tuple[int, int, int]


def load(path: Path = SILHOUETTES) -> dict:
    data = yaml.safe_load(path.read_text())
    token = data["token"]
    _check_rows(token, LIVE, LIVE, "token")
    for kind, slot in data["kinds"].items():
        for option in ("A", "B"):
            _check_rows(slot[option]["emblem"], EMBLEM, EMBLEM, f"{kind} {option} emblem", exact=False)
        if kind in COMPARE:
            _check_rows(slot["bare"], LIVE, LIVE, f"{kind} bare")
            _check_rows(slot["figure"], LIVE, LIVE, f"{kind} figure")
        elif "bare" in slot or "figure" in slot:
            raise ValueError(f"{kind}: bare and figure belong to {COMPARE} only")
    return data


def _check_rows(rows: list[str], w: int, h: int, what: str, exact: bool = True) -> None:
    widths = {len(r) for r in rows}
    ok = (widths == {w} and len(rows) == h) if exact else (max(widths) <= w and len(rows) <= h and len(widths) == 1)
    if not ok or any(set(r) - {"#", "."} for r in rows):
        raise ValueError(f"{what}: rows must be '#' and '.' and {'exactly' if exact else 'at most'} {w} x {h}")


def grid(live: list[str], emblem: list[str] | None = None) -> list[list[Rgb | None]]:
    """A 16 x 16 cell of colours (None = transparent): the live area at a 2 px margin; with an emblem, the token in its colour and the emblem centred on it in the light ink."""
    cell: list[list[Rgb | None]] = [[None] * CELL for _ in range(CELL)]
    for y, row in enumerate(live):
        for x, ch in enumerate(row):
            if ch == "#":
                cell[MARGIN + y][MARGIN + x] = TOKEN if emblem is not None else OUTLINE
    if emblem is not None:
        top = MARGIN + (LIVE - len(emblem)) // 2
        left = MARGIN + (LIVE - len(emblem[0])) // 2
        for y, row in enumerate(emblem):
            for x, ch in enumerate(row):
                if ch == "#":
                    cell[top + y][left + x] = LIGHT
    return cell


def _paint(c: Canvas, cell: list[list[Rgb | None]], x: int, y: int, zoom: int, bg: Rgb, ink_override: Rgb | None = None) -> None:
    c.rect(x, y, CELL * zoom, CELL * zoom, bg)
    for py, row in enumerate(cell):
        for px, colour in enumerate(row):
            if colour is not None:
                c.rect(x + px * zoom, y + py * zoom, zoom, zoom, ink_override if (ink_override and colour == OUTLINE) else colour)


def _glyph(c: Canvas, key: str, x: int, y: int, zoom: int, bg: Rgb) -> int:
    """Draw the adopted glyph `key` at `zoom` on a `bg` panel (its own size, at least a 16 px cell); return the panel side."""
    sprite = la.all_icon_sprites()[key]
    side = max(sprite.width, CELL) * zoom
    c.rect(x, y, side, side, bg)
    c.sprite(sprite, x + (side - sprite.width * zoom) // 2, y + (side - sprite.height * zoom) // 2, zoom)
    return side


def draw_cell(c: Canvas, x0: int, y0: int, head: str, name: str, cell: list[list[Rgb | None]], nearest: str) -> None:
    c.text(x0, y0, head, GREEN, 2)
    for n, line in enumerate(wrap(name, (CELL_W - 40) // CHAR_W)[:2]):
        c.text(x0, y0 + 26 + 26 * n, line, DIM, 2)
    y1 = y0 + 26 + 26 * 2 + 8
    big = CELL * ZOOM
    one_ink = OUTLINE
    _paint(c, cell, x0, y1, ZOOM, DARK, LIGHT)
    gx = x0 + big + 16
    side = _glyph(c, nearest, gx, y1, ZOOM, DARK)
    c.text(gx, y1 + side + 8, "NEXT TO " + nearest.split(".", 1)[1].upper(), DIM, 2)
    rx = gx + side + 16
    _paint(c, cell, rx, y1, 1, GRASS, one_ink)
    sprite = la.all_icon_sprites()[nearest]
    c.rect(rx + CELL + 8, y1, max(sprite.width, CELL), max(sprite.height, CELL), GRASS)
    c.sprite(sprite, rx + CELL + 8 + (max(sprite.width, CELL) - sprite.width) // 2, y1 + (max(sprite.height, CELL) - sprite.height) // 2, 1)
    c.text(rx, y1 + big // 2, "X1", DIM, 2)


def cell_size() -> tuple[int, int]:
    side = max(max(s.width, CELL) for s in la.all_icon_sprites().values()) * ZOOM
    return CELL_W, 26 + 26 * 2 + 8 + side + 40


def sheet(entries: list[tuple[str, str, list[list[Rgb | None]], str]], title: str, header: str) -> Canvas:
    cw, ch = cell_size()
    width = COLS * cw + 40
    lines = wrap(header, (width - 40) // CHAR_W)
    top = 60 + 26 * len(lines)
    c = Canvas(width, top + -(-len(entries) // COLS) * ch + 20, PAGE)
    c.text(20, 20, title, INK, 2)
    for n, line in enumerate(lines):
        c.text(20, 50 + 26 * n, line, DIM, 2)
    for i, (head, name, cell, nearest) in enumerate(entries):
        draw_cell(c, 20 + (i % COLS) * cw, top + (i // COLS) * ch, head, name, cell, nearest)
    return c


def treatment_entries(data: dict) -> list[tuple[str, str, list[list[Rgb | None]], str]]:
    out = []
    for kind in COMPARE:
        slot = data["kinds"][kind]
        name = slot["A"]["name"]
        out.append((f"{kind.upper()} A (A) BARE OBJECT", name, grid(slot["bare"]), slot["nearest"]))
        out.append((f"{kind.upper()} A (B) EMBLEM ON TOKEN", name, grid(data["token"], slot["A"]["emblem"]), slot["nearest"]))
        out.append((f"{kind.upper()} A (C) FIGURE", name + ", as a figure", grid(slot["figure"]), slot["nearest"]))
    return out


def candidate_entries(data: dict) -> list[tuple[str, str, list[list[Rgb | None]], str]]:
    out = []
    for kind in data["kinds"]:
        slot = data["kinds"][kind]
        for option in ("A", "B"):
            out.append((f"{kind.upper()} {option}", slot[option]["name"], grid(data["token"], slot[option]["emblem"]), slot["nearest"]))
    return out


TREATMENT_HEADER = ("Rows: worker, guard, sentinel. Columns: (A) the bare object, (B) the emblem on a round unit token, (C) a figure silhouette. Every shape is on the real 16 x 16 map cell, "
                    "shown at x8 (dark panel) and at the real size on grass (X1), beside the nearest existing glyph. Shapes are one colour except the token; shading and colour come later.")
CANDIDATE_HEADER = ("Every candidate of all 11 kinds as an emblem on the round token (a preview of treatment B). A and B are the two candidate objects; the owner picks one per kind. "
                    "Each is beside the nearest existing glyph, at x8 and at the real size (X1).")


def build(out_dir: Path, path: Path = SILHOUETTES) -> list[str]:
    data = load(path)
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = {
        "01_treatments.png": sheet(treatment_entries(data), "ENTITY MARKERS: THE THREE TREATMENTS", TREATMENT_HEADER),
        "02_candidates.png": sheet(candidate_entries(data), "ENTITY MARKERS: CANDIDATES A AND B, ALL 11 KINDS", CANDIDATE_HEADER),
    }
    for name, canvas in pages.items():
        (out_dir / name).write_bytes(canvas.png())
    return sorted(pages)


if __name__ == "__main__":
    print("\n".join(build(Path(sys.argv[1]))))
