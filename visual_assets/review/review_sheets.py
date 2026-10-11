"""Owner review sheets: one command writes a folder of large labelled PNG canvases plus a README for a draft set (`TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER`).

The owner finds the live preview page slow (start Vite, scroll a long page) and asked for review material as large images in ONE folder per review, outside every repository:

    python -m visual_assets.review review-sheets --set icons-owner-fixes-v1 [--out DIR]       # default DIR = ~/Work/asset-review/<set>/

It writes, deterministically (no timestamps; the same drafts give the same bytes):
  01_overview.png      every proposed draft at its true size and at a whole-number zoom, on a dark and a light panel, beside its fallback
  02_before_after.png  the adopted drawing (r0001) next to the draft that would revise it
  03_groups.png        every must-differ group the drafts belong to, side by side
  04_colour_vision.png those groups in colour, greyscale and three simulated visions (an approximation, never a verdict)
  05_map_markers.png   location glyphs on the plate over the darkest and the brightest terrain fill, and a small map scene
  06_silhouettes.png   one-colour silhouettes (the owner-approval sheet of the recognisability process)
  README.txt           what each image shows, the recorded results, the findings and the exact owner commands

Pure Python: the images are encoded with `zlib` and `struct` (the same primitives as the store's PNG helpers) and the labels use a small built-in 5x7 bitmap font (letters are drawn in capitals), so no
dependency is added. Reads the committed drafts and records only; never writes into a repository.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zlib
from pathlib import Path

import yaml

from visual_assets.review import icon_draft_set as keyset
from visual_assets.review import icon_lookalikes as la
from visual_assets.review import icon_owner_fixes_draft_set as fixes
from visual_assets.review import icon_sheet_rule as rule
from visual_assets.review import icon_silhouette_sheet as silsheet
from visual_assets.review import icon_v2_groups as v2groups
from visual_assets.review.pilot_colour_vision import REPO, simulate
from visual_assets.store import pixels

DEFAULT_ROOT = Path.home() / "Work" / "asset-review"
FILES = ("01_overview.png", "02_before_after.png", "03_groups.png", "04_colour_vision.png", "05_map_markers.png", "06_silhouettes.png", "README.txt")
SCALE = 8  # `export_handoff` makes 8x previews
Rgb = tuple[int, int, int]
PAGE, DARK, LIGHT, INK, DIM, GREEN = (36, 38, 46), (17, 24, 39), (229, 231, 235), (240, 240, 245), (150, 155, 170), (52, 211, 153)
FLOOR, SNOW = (0x1A, 0x1D, 0x27), (0xC8, 0xD8, 0xE8)  # terrain-v1's darkest and brightest flat fills (a copy of the Live Map's TILE_COLORS)
SCENE = ["....ssss....", "..mmsssss.ww", ".mmm.sss.www", "..ff..gg.ww.", ".fff.ggggg..", "..dd.gaaa...", ".dddd.aaaa.."]
SCENE_FILLS = {".": FLOOR, "s": SNOW, "g": (0x4A, 0x60, 0x30), "w": (0x1E, 0x3A, 0x5F), "f": (0x1B, 0x3A, 0x1B), "m": (0x3A, 0x3A, 0x3A), "d": (0x3A, 0x34, 0x20), "a": (0x6A, 0x7A, 0x40)}
SCENE_MARKERS = [(1, 0), (6, 0), (7, 4), (10, 2)]
VISIONS = (("colour", None), ("greyscale", "grey"), ("protanopia (approximation)", "protan"), ("deuteranopia (approximation)", "deutan"), ("tritanopia (approximation)", "tritan"))

# ---- a 5x7 bitmap font (capitals, digits and the punctuation the labels use) ------------------------------------------------------------------------------------------------------------------
_G = {
    "A": ".###. #...# #...# ##### #...# #...# #...#", "B": "####. #...# #...# ####. #...# #...# ####.", "C": ".###. #...# #.... #.... #.... #...# .###.",
    "D": "####. #...# #...# #...# #...# #...# ####.", "E": "##### #.... #.... ####. #.... #.... #####", "F": "##### #.... #.... ####. #.... #.... #....",
    "G": ".###. #...# #.... #.### #...# #...# .###.", "H": "#...# #...# #...# ##### #...# #...# #...#", "I": ".###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.",
    "J": "..### ...#. ...#. ...#. ...#. #..#. .##..", "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#", "L": "#.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## #.#.# #.#.# #...# #...# #...#", "N": "#...# ##..# #.#.# #..## #...# #...# #...#", "O": ".###. #...# #...# #...# #...# #...# .###.",
    "P": "####. #...# #...# ####. #.... #.... #....", "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#", "R": "####. #...# #...# ####. #.#.. #..#. #...#",
    "S": ".#### #.... #.... .###. ....# ....# ####.", "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..", "U": "#...# #...# #...# #...# #...# #...# .###.",
    "V": "#...# #...# #...# #...# #...# .#.#. ..#..", "W": "#...# #...# #...# #.#.# #.#.# ##.## #...#", "X": "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    "Y": "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..", "Z": "##### ....# ...#. ..#.. .#... #.... #####",
    "0": ".###. #...# #..## #.#.# ##..# #...# .###.", "1": "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.", "2": ".###. #...# ....# ...#. ..#.. .#... #####",
    "3": "##### ...#. ..#.. ...#. ....# #...# .###.", "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.", "5": "##### #.... ####. ....# ....# #...# .###.",
    "6": "..##. .#... #.... ####. #...# #...# .###.", "7": "##### ....# ...#. ..#.. .#... .#... .#...", "8": ".###. #...# #...# .###. #...# #...# .###.",
    "9": ".###. #...# #...# .#### ....# ...#. .##..",
    ".": "..... ..... ..... ..... ..... ..##. ..##.", ",": "..... ..... ..... ..... ..##. ..#.. .#...", ":": "..... ..##. ..##. ..... ..##. ..##. .....",
    ";": "..... ..##. ..##. ..... ..##. ..#.. .#...", "_": "..... ..... ..... ..... ..... ..... #####", "-": "..... ..... ..... ##### ..... ..... .....",
    "+": "..... ..#.. ..#.. ##### ..#.. ..#.. .....", "=": "..... ..... ##### ..... ##### ..... .....", "/": "....# ....# ...#. ..#.. .#... #.... #....",
    "(": "...#. ..#.. .#... .#... .#... ..#.. ...#.", ")": ".#... ..#.. ...#. ...#. ...#. ..#.. .#...", "%": "##..# ##..# ...#. ..#.. .#... #..## #..##",
    "'": "..#.. ..#.. .#... ..... ..... ..... .....", '"': ".#.#. .#.#. .#.#. ..... ..... ..... .....", "!": "..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#..",
    "?": ".###. #...# ....# ...#. ..#.. ..... ..#..", "#": ".#.#. ##### .#.#. .#.#. .#.#. ##### .#.#.", "<": "...#. ..#.. .#... #.... .#... ..#.. ...#.",
    ">": ".#... ..#.. ...#. ....# ...#. ..#.. .#...", "[": ".###. .#... .#... .#... .#... .#... .###.", "]": ".###. ...#. ...#. ...#. ...#. ...#. .###.",
    "*": "..... #.#.# .###. ##### .###. #.#.# .....", "|": "..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#..", " ": "..... ..... ..... ..... ..... ..... .....",
}
FONT = {ch: tuple(rows.split()) for ch, rows in _G.items()}
assert all(len(r) == 7 and all(len(x) == 5 for x in r) for r in FONT.values())
UNKNOWN = ("#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#####")


class Canvas:
    """An RGB image as one bytearray per row; every operation is a whole-number rectangle, so the result is exact and deterministic."""

    def __init__(self, width: int, height: int, fill: Rgb = PAGE):
        self.w, self.h = width, height
        self.rows = [bytearray(bytes(fill) * width) for _ in range(height)]

    def rect(self, x: int, y: int, w: int, h: int, colour: Rgb) -> None:
        x0, x1 = max(x, 0), min(x + w, self.w)
        if x1 <= x0:
            return
        chunk = bytes(colour) * (x1 - x0)
        for yy in range(max(y, 0), min(y + h, self.h)):
            self.rows[yy][x0 * 3 : x1 * 3] = chunk

    def frame(self, x: int, y: int, w: int, h: int, colour: Rgb, t: int = 2) -> None:
        self.rect(x, y, w, t, colour); self.rect(x, y + h - t, w, t, colour); self.rect(x, y, t, h, colour); self.rect(x + w - t, y, t, h, colour)

    def text(self, x: int, y: int, text: str, colour: Rgb = INK, scale: int = 2) -> int:
        """Draw `text` (capitals) and return its width in pixels; characters outside the font become a box."""
        for i, ch in enumerate(text.upper()):
            glyph = FONT.get(ch, UNKNOWN)
            for gy, row in enumerate(glyph):
                for gx, c in enumerate(row):
                    if c == "#":
                        self.rect(x + (i * 6 + gx) * scale, y + gy * scale, scale, scale, colour)
        return len(text) * 6 * scale

    def sprite(self, sprite: rule.Sprite, x: int, y: int, zoom: int, mapper=None) -> None:
        """Draw the opaque pixels of `sprite` at a whole-number `zoom` (nearest neighbour); `mapper` recolours each pixel (a vision, or one ink for a silhouette)."""
        for py in range(sprite.height):
            for px in range(sprite.width):
                r, g, b, a = sprite.rgba[py * sprite.width + px]
                if a:
                    self.rect(x + px * zoom, y + py * zoom, zoom, zoom, mapper((r, g, b)) if mapper else (r, g, b))

    def png(self) -> bytes:
        raw = b"".join(b"\x00" + bytes(row) for row in self.rows)

        def chunk(kind: bytes, body: bytes) -> bytes:
            return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")


def wrap(text: str, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + ([cur] if cur else [])


def zoom_for(size: int, target: int = 140) -> int:
    return max(1, round(target / size))


def vision_mapper(vision: str | None):
    if vision is None:
        return None
    if vision == "grey":
        return lambda c: (lambda y: (y, y, y))(round(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]))
    return lambda c: tuple(max(0, min(255, round(v * 255))) for v in simulate(tuple(x / 255 for x in c), vision))  # `simulate` works in 0..1


# ---- inputs ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class Entry:
    def __init__(self, key: str, draft_id: str, source_asset_id: str, sprite: rule.Sprite, detail: str | None = None, parent_revision: str | None = None):
        self.key, self.draft_id, self.source_asset_id, self.sprite = key, draft_id, source_asset_id, sprite
        self.detail, self.parent_revision = detail, parent_revision  # parent_revision (ADR D22): the draft is the next revision of `source_asset_id`


def load_set(set_id: str, root: Path | None = None) -> tuple[list[Entry], dict, str]:
    base = (root or keyset.DRAFTS) / set_id
    record = json.loads((base / "draft_set.json").read_text())
    entries = []
    for e in record["entries"]:
        image = pixels.decode_png((base / e["draft_id"] / "preview.png").read_bytes(), max_dim=1024)
        size = image.width // SCALE
        entries.append(Entry(e["visual_key"], e["draft_id"], e["source_asset_id"], keyset.sprite_from_preview((base / e["draft_id"] / "preview.png").read_bytes(), size),
                             e.get("detail"), e.get("parent_revision")))
    import hashlib

    return entries, record, "sha256:" + hashlib.sha256((base / "draft_set.json").read_bytes()).hexdigest()


def fallback_text(key: str) -> str:
    keys = yaml.safe_load((REPO / "visual_assets" / "catalog" / "definitions" / "visual_keys.yaml").read_text())["keys"]
    for k in keys:
        if k["key"] == key:
            m = re.search(r"the fallback is (.*)$", k["description"])
            return m.group(1) if m else "none stated"
    return "key not registered"


def load_recorded(path: str | None) -> dict:
    """The owner's decisions and the findings for a set, from the one recorded file (never hand-kept text in this module)."""
    return yaml.safe_load((REPO / path).read_text(encoding="utf-8")) if path else {}


PROFILES = {
    "icons-owner-fixes-v1": {
        "proposed": fixes.PROPOSED,
        "pending": fixes.PENDING,
        "not_proposed": fixes.NOT_PROPOSED,
        "evaluate": fixes.evaluate,
        "recorded": "visual_assets/icons/owner_fixes_decisions.yaml",
    },
}


def groups_for(keys: set[str]) -> list[tuple[str, list[list[str]]]]:
    """Every must-differ group (the key-set groups and the v2 groups) that contains one of `keys`, as named lists of classes of keys."""
    out = []
    for name, classes in {**{f"key set: {n}": c for n, c in keyset.GROUPS.items()}, **{f"v2: {n}": c for n, c in v2groups.GROUPS.items()}}.items():
        if any(k in keys for cls in classes for k in cls):
            out.append((name, classes))
    return out


# ---- the six images ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def title(c: Canvas, set_id: str, what: str, digest: str) -> int:
    c.text(24, 20, f"{set_id}: {what}", INK, 3)
    c.text(24, 56, f"draft set hash {digest[:23]}...   DRAFT ONLY: NOTHING HERE IS ADOPTED, RELEASED OR READ BY THE GAME", DIM, 2)
    return 110


def message_canvas(set_id: str, what: str, message: str, digest: str) -> Canvas:
    c = Canvas(1700, 260)
    y = title(c, set_id, what, digest)
    for line in wrap(message, 110):
        c.text(24, y, line, INK, 2)
        y += 22
    return c


def panel(c: Canvas, sp: rule.Sprite, x: int, y: int, side: int, zoom: int, bg: Rgb, mapper=None) -> None:
    """A square panel of `side` pixels with the sprite centred in it at a whole-number zoom."""
    c.rect(x, y, side, side, bg)
    c.sprite(sp, x + (side - sp.width * zoom) // 2, y + (side - sp.height * zoom) // 2, zoom, mapper)


def sheet_overview(set_id: str, shown: list[Entry], digest: str) -> Canvas:
    rows = [(e, zoom_for(e.sprite.width)) for e in sorted(shown, key=lambda e: e.key)]
    heights = [max(e.sprite.width * z, 90) + 40 for e, z in rows]
    c = Canvas(2000, 150 + sum(heights))
    y = title(c, set_id, "overview: every proposed draft, true size and zoomed, dark and light panels", digest)
    for x, text in ((24, "KEY, SIZE, DRAFT"), (470, "TRUE SIZE"), (640, "ZOOMED"), (1250, "FALLBACK TODAY (WHAT THE UI SHOWS WITHOUT THE ICON)")):
        c.text(x, y - 26, text, DIM, 2)
    for (e, z), h in zip(rows, heights):
        side = max(e.sprite.width * z, 90) + 24
        c.text(24, y + 8, e.key, INK, 2)
        c.text(24, y + 34, f"{e.sprite.width}X{e.sprite.width} PX, ZOOM {z}X", DIM, 2)
        c.text(24, y + 58, f"DRAFT {e.draft_id}", DIM, 2)
        panel(c, e.sprite, 470, y, 64, 1, DARK); panel(c, e.sprite, 546, y, 64, 1, LIGHT)
        panel(c, e.sprite, 640, y, side, z, DARK); panel(c, e.sprite, 640 + side + 16, y, side, z, LIGHT)
        for i, line in enumerate(wrap(fallback_text(e.key), 62)):
            c.text(1250, y + 8 + i * 22, line, INK, 2)
        y += h
    return c


def sheet_before_after(set_id: str, shown: list[Entry], digest: str, adopted: dict[str, rule.Sprite]) -> Canvas:
    pairs = [(e, adopted[e.key]) for e in sorted(shown, key=lambda e: e.key) if e.key in adopted]
    if not pairs:
        return message_canvas(set_id, "before and after", "No draft in this set revises an adopted icon, so there is nothing to compare: these are new icons.", digest)
    sides = [max(e.sprite.width * zoom_for(e.sprite.width), 90) + 24 for e, _ in pairs]
    c = Canvas(2000, 150 + sum(s + 70 for s in sides))
    y = title(c, set_id, "before and after: the adopted drawing (r0001) beside the proposed revision (r0002)", digest)
    for (e, old), side in zip(pairs, sides):
        z = zoom_for(e.sprite.width)
        c.text(24, y, e.key, INK, 2)
        y += 30
        x = 24
        for label, sp, colour in (("ADOPTED R0001", old, DIM), ("PROPOSED R0002", e.sprite, GREEN)):
            panel(c, sp, x, y, side, z, DARK); panel(c, sp, x + side + 12, y, side, z, LIGHT)
            if sp is e.sprite:
                c.frame(x - 6, y - 6, 2 * side + 24, side + 12, GREEN)
            c.text(x, y + side + 12, label, colour, 2)
            x += 2 * side + 90
        y += side + 52
    return c


def sheet_groups(set_id: str, digest: str, sprites: dict[str, rule.Sprite], proposed: set[str], groups: list[tuple[str, list[list[str]]]], visions: bool) -> Canvas:
    rows = [("on a dark panel", DARK, None), ("on a light panel", LIGHT, None)] if not visions else [(name, DARK, v) for name, v in VISIONS]
    layout = []
    for name, classes in groups:
        native = max(sprites[k].width for cls in classes for k in cls)
        z = zoom_for(sprites[classes[0][0]].width, 100 if visions else 130)
        icons, gaps = sum(len(cls) for cls in classes), len(classes)
        while z > 2 and 420 + icons * (native * z + 36) + gaps * 36 > 1960:  # a long group (eleven badges) gets a smaller whole-number zoom so it fits the canvas
            z -= 1
        side = native * z + 24
        layout.append((name, classes, z, side))
    c = Canvas(2000, 150 + sum(56 + len(rows) * (side + 14) + 56 for _, _, _, side in layout))
    what = "colour vision: the groups in five visions (an approximation for the eye, not a verdict)" if visions else "groups: every must-differ group the drafts belong to, side by side"
    y = title(c, set_id, what, digest)
    for name, classes, z, side in layout:
        c.text(24, y, name.upper(), INK, 2)
        c.text(24, y + 24, "GREEN FRAME = A PROPOSED REVISION. ICONS OF ONE CLASS MAY SHARE A SILHOUETTE; CLASSES ARE SEPARATED BY A GAP.", DIM, 2)
        y += 56
        for label, bg, vision in rows:
            c.text(24, y + side // 2 - 8, label.upper(), DIM, 2)
            x = 420
            mapper = vision_mapper(vision)
            for cls in classes:
                for k in cls:
                    panel(c, sprites[k], x, y, side, z, bg, mapper)
                    if k in proposed:
                        c.frame(x - 3, y - 3, side + 6, side + 6, GREEN)
                    x += side + 12
                x += 36
            y += side + 14
        x = 420
        for cls in classes:
            for k in cls:
                c.text(x, y, k.split(".")[-1][: max(6, side // 6)], DIM, 1)
                x += side + 12
            x += 36
        y += 44
    return c


def sheet_markers(set_id: str, digest: str, shown: list[Entry], sprites: dict[str, rule.Sprite]) -> Canvas:
    glyphs = [e for e in sorted(shown, key=lambda e: e.key) if e.key.startswith("icon.marker.")]
    if not glyphs:
        return message_canvas(set_id, "map markers", "This set proposes no location glyph, so there is nothing to show over the map. (A location glyph is drawn over the shared plate on the darkest and the brightest terrain fill, and in a small map scene.)", digest)
    plate = sprites["icon.plate.location"]
    cell = 16 * 4
    c = Canvas(2000, 150 + 230 * len(glyphs) + 60 + len(SCENE) * cell + 40)
    y = title(c, set_id, "map markers: the glyph over the plate on the darkest and the brightest terrain (flat fills of terrain-v1)", digest)
    for e in glyphs:
        c.text(24, y + 80, e.key, INK, 2)
        x = 420
        for label, fill in (("DARKEST (FLOOR)", FLOOR), ("BRIGHTEST (SNOW)", SNOW)):
            c.rect(x, y, 3 * cell, 3 * cell, fill)
            c.sprite(plate, x + cell, y + cell, 4); c.sprite(e.sprite, x + cell, y + cell, 4)
            c.text(x, y + 3 * cell + 8, label, DIM, 2)
            x += 3 * cell + 40
        y += 3 * cell + 40
    c.text(24, y, "A SMALL MAP SCENE AT 4X, THE GLYPHS ON THEIR PLATES", DIM, 2)
    y += 30
    for ry, row in enumerate(SCENE):
        for rx, ch in enumerate(row):
            c.rect(24 + rx * cell, y + ry * cell, cell, cell, SCENE_FILLS[ch])
    for (mx, my), e in zip(SCENE_MARKERS, (glyphs * 4)[:4]):
        c.sprite(plate, 24 + mx * cell, y + my * cell, 4); c.sprite(e.sprite, 24 + mx * cell, y + my * cell, 4)
    return c


def sheet_silhouettes(set_id: str, digest: str, shown: list[Entry], sprites: dict[str, rule.Sprite], adopted: dict[str, rule.Sprite], pending: dict[str, str] | None = None) -> Canvas:
    proposals = silsheet.load_proposals()["slots"]
    z = 5
    slots = []
    for key in sorted(pending or {}):  # proposed slots still to be drawn: the silhouettes the owner is asked to approve (option letters from the proposals file)
        neigh = [n for n in proposals[key].get("neighbours", []) if n in sprites]
        cells = [("ADOPTED", adopted.get(key) or sprites[key])] + [(f"OPTION {tag}", silsheet.sprite_of(o["rows"])) for tag, o in proposals[key]["options"].items()]
        cells += [(n.split(".")[-1][:12].upper(), sprites[n]) for n in neigh]
        slots.append((Entry(key, "pending", key, silsheet.sprite_of(next(iter(proposals[key]["options"].values()))["rows"])), cells))
    for e in sorted(shown, key=lambda e: e.key):
        neigh = [n for n in proposals.get(e.key, {}).get("neighbours", []) if n in sprites]
        cells = [("ADOPTED", adopted.get(e.key)), ("PROPOSED", e.sprite)] + [(n.split(".")[-1][:12].upper(), sprites[n]) for n in neigh]
        slots.append((e, [(label, sp) for label, sp in cells if sp is not None]))
    side = lambda e: max(e.sprite.width, 16) * z + 24  # noqa: E731
    cell_w = lambda e: 2 * side(e) + 6 + 20  # noqa: E731
    per_line = lambda e: max(1, (1960 - 24) // cell_w(e))  # noqa: E731
    lines = lambda e, cells: -(-len(cells) // per_line(e))  # noqa: E731
    c = Canvas(2000, 150 + sum(28 + lines(e, cells) * (side(e) + 52) + 24 for e, cells in slots))
    y = title(c, set_id, "silhouettes: one colour, outline only (judge the shape, not the colours)", digest)
    for e, cells in slots:
        c.text(24, y, e.key, INK, 2)
        y += 28
        for i, (label, sp) in enumerate(cells):
            col, row = i % per_line(e), i // per_line(e)
            x0, y0 = 24 + col * cell_w(e), y + row * (side(e) + 52)
            for n, (bg, ink) in enumerate(((DARK, LIGHT), (LIGHT, DARK))):
                panel(c, sp, x0 + n * (side(e) + 6), y0, side(e), z, bg, lambda _c, ink=ink: ink)
                if label == "PROPOSED" or label.startswith("OPTION"):
                    c.frame(x0 + n * (side(e) + 6) - 2, y0 - 2, side(e) + 4, side(e) + 4, GREEN)
            c.text(x0, y0 + side(e) + 8, label, GREEN if label == "PROPOSED" or label.startswith("OPTION") else DIM, 2)
        y += lines(e, cells) * (side(e) + 52) + 24
    return c


# ---- the README ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def latest_revision(source_asset_id: str) -> str | None:
    from visual_assets.store import records

    try:
        revs = records.list_revisions(source_asset_id)
    except Exception:  # an unreadable or missing source is "not adopted yet" for the purpose of a command
        return None
    revoked = records.revoked_revisions(source_asset_id) if revs else set()
    live = [r for r in revs if r not in revoked]
    return live[-1] if live else None


def adopted_intakes() -> dict[str, str]:
    """intake id -> adoption id, for every draft that is already adopted (read from the catalog's adoption records)."""
    from visual_assets.store import records

    out = {}
    for path in records.adoptions_dir().glob("*.json"):
        adoption = records.load_adoption(path.stem)
        out[adoption.intake_id] = adoption.adoption_id
    return out


def next_revision_name(parent: str) -> str:
    return f"r{int(parent[1:]) + 1:04d}"


def commands_mode(shown: list[Entry]) -> str:
    """`set` when the drafts declare revisions (ADR D22: `draft keep --revises`), so ONE `adopt-set` adopts the whole set; `slot` for a set that predates it (per-slot `review` and `adopt --parent`).
    A set with revision drafts of which some are already adopted falls back to per-slot commands for the rest, because `adopt-set` refuses an adopted draft."""
    declares = any(e.parent_revision for e in shown)
    adopted = adopted_intakes()
    return "set" if declares and not any(e.draft_id in adopted for e in shown) else "slot"


def set_commands(set_id: str, shown: list[Entry], not_proposed: dict[str, dict] | None = None) -> str:
    """The ONE `adopt-set` command with the NEW / REVISION summary the owner will be shown again before typing the set id."""
    py = "/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python"
    revisions = [e for e in shown if e.parent_revision]
    lines = [f"cd {REPO}", f"PY={py}", ""]
    for key, spec in sorted((not_proposed or {}).items()):
        lines += [f"# {key} is a draft in this set that is NOT proposed; adopt-set adopts EVERY draft, so drop it first (no approval is recorded by a drop, the set hash changes):",
                  f"$PY -m visual_assets.store draft drop {set_id} --slot {spec['slot']} --reason \"owner declined\"", ""]
    lines += [f"# one decision for the whole set, ALL or NONE: {len(shown) - len(revisions)} new, {len(revisions)} revisions (the typed confirmation is the set id; the store re-renders every source first)"]
    for e in sorted(shown, key=lambda e: e.key):
        lines.append(f"#   {e.key}: " + (f"NEW source asset {e.source_asset_id} r0001" if not e.parent_revision else
                                          f"REVISION of {e.source_asset_id}: {e.parent_revision} -> {next_revision_name(e.parent_revision)} (parent {e.parent_revision} must still be the latest unrevoked revision)"))
    lines += [f"$PY -m visual_assets.store adopt-set {set_id} \\",
              '  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" \\',
              '  --licence-evidence "<your own evidence reference>" --review-evidence "<what you reviewed, e.g. the images in this folder>"', ""]
    return "\n".join(lines)


def owner_commands(set_id: str, shown: list[Entry], not_proposed: dict[str, dict] | None = None) -> str:
    if commands_mode(shown) == "set":
        return set_commands(set_id, shown, not_proposed)
    py = "/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python"
    lines = [f"cd {REPO}", f"PY={py}", ""]
    new = []
    already = adopted_intakes()
    for e in sorted(shown, key=lambda e: e.key):
        existing = e.key.replace(".", "_")
        parent = latest_revision(existing)
        if e.draft_id in already:
            lines += [f"# {e.key}: draft {e.draft_id} is ALREADY ADOPTED (adoption {already[e.draft_id]}); nothing to run", ""]
        elif parent:
            lines += [f"# {e.key}: a new revision of the adopted source {existing} (parent {parent})",
                      f"$PY -m visual_assets.store review {e.draft_id}",
                      f"$PY -m visual_assets.store adopt {e.draft_id} --visual-key {e.key} --source-asset-id {existing} --parent {parent} \\",
                      '  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" --licence-evidence "<your own evidence reference>"', ""]
        else:
            new.append(e)
    if new:
        lines += [f"# {len(new)} new icons: one decision for the whole set (all or nothing)",
                  f"$PY -m visual_assets.store adopt-set {set_id} \\",
                  '  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" \\',
                  '  --licence-evidence "<your own evidence reference>" --review-evidence "<what you reviewed, e.g. the images in this folder>"', ""]
    return "\n".join(lines)


def intro(shown: list[Entry]) -> list[str]:
    adopted = adopted_intakes()
    done = [e for e in shown if e.draft_id in adopted]
    if shown and len(done) == len(shown):
        return ["These images are the record of a review that is finished: EVERY DRAFT SHOWN IS NOW ADOPTED by the owner (see the commands section for each adoption id); a draft is read by the game only through an adoption."]
    return ["These images are for your review. NOTHING IS ADOPTED" + (f" YET ({len(done)} of {len(shown)} drafts shown are already adopted)" if done else "") + ": a draft is not read by the game, and the only way to adopt is the commands at the bottom,",
            "which you run in your own terminal (they refuse without one)."]


def readme(set_id: str, digest: str, shown: list[Entry], profile: dict, result: dict | None, images: dict[str, str]) -> str:
    out = [f"REVIEW SHEETS FOR THE DRAFT SET {set_id}", f"draft set hash {digest}", "", *intro(shown), "Every image is at a whole-number zoom with nearest-neighbour pixels, labelled.", "", "WHAT EACH IMAGE SHOWS"]
    out += [f"  {name}  {text}" for name, text in images.items()]
    out += ["", "THE DRAFTS SHOWN", *[f"  {e.key}  ({e.sprite.width}x{e.sprite.width})  draft {e.draft_id}" for e in sorted(shown, key=lambda e: e.key)]]
    if profile.get("not_proposed"):
        out += ["", "NOT PROPOSED (drafts that exist in the set but are NOT candidates)", *[f"  {k}: {v}" for k, v in sorted(profile["not_proposed"].items())]]
    if profile.get("pending"):
        slots = silsheet.load_proposals()["slots"]
        out += ["", "PENDING YOUR APPROVAL BEFORE ANY DRAWING (proposed slots whose earlier draft was rejected; see 06_silhouettes.png, the green-framed OPTION cells)"]
        for k, v in sorted(profile["pending"].items()):
            out.append(f"  {k}: {v}")
            out += [f"    OPTION {tag}: {o['label']}" for tag, o in slots[k]["options"].items()]
    out += ["", "RECORDED RESULTS (as measured; thresholds unchanged)"]
    if result:
        out.append(f"  sheet rule on the set as it would stand with these in place: {result['result']} (key-set groups {result['key_set_rule']['result']}, v2 groups {result['v2_rule']['result']})")
        g = {**result["key_set_rule"]["groups"], **result["v2_rule"]["groups"]}
        out.append("  smallest silhouette difference by group: " + ", ".join(f"{n} {v['min_shape_px_across_classes']} px" for n, v in g.items()))
        for n in ("rarity", "status"):
            if n in g and g[n]["min_dL_by_vision"]:
                out.append(f"  {n} smallest L* gap by vision (needed 6): " + ", ".join(f"{v} {d}" for v, d in g[n]["min_dL_by_vision"].items()))
        out.append(f"  spec compliance (every proportion measured from the pixels): {'every row met' if result['compliance_all_ok'] else 'SOME ROWS NOT MET'} ({sum(len(r) for r in result['compliance'].values())} rows over {len(result['compliance'])} icons)")
        out.append("  lint: " + ("no warnings" if not any(v["warnings"] for v in result["lint"].values()) else "WARNINGS, see the review doc"))
    else:
        out.append("  no recorded evaluation module for this set; see docs/assets/icon_set_v2_review.md")
    recorded = load_recorded(profile.get("recorded"))
    decisions = [f"  - {d['date']}  {d['about']}: \"{d['answer']}\"" for d in recorded.get("decisions", [])]
    out += ["", "OWNER DECISIONS (recorded verbatim in " + str(profile.get("recorded", "no recorded file")) + ")", *(decisions or ["  none recorded"])]
    out += ["", "FINDINGS FOR YOU", *[f"  - {f}" for f in recorded.get("findings", ["see docs/assets/icon_set_v2_review.md"])]]
    if commands_mode(shown) == "set":
        out += ["", "YOUR COMMAND (own terminal; fill the placeholders yourself, the licence decision must be CLEARED; ONE decision for the whole set, all or nothing)", "",
                owner_commands(set_id, shown, {k: {"slot": k} for k in profile.get("not_proposed", {})}),  # icon keys carry no detail value: the slot is the key
                "This set's drafts declare revisions (draft keep --revises), so adopt-set adopts the new icons and the revisions together; the confirmation lists every slot as NEW or REVISION.", ""]
    else:
        out += ["", "YOUR COMMANDS (own terminal; fill the placeholders yourself, the licence decision must be CLEARED; each slot is its own decision)", "", owner_commands(set_id, shown),
                "adopt-set adopts revisions of existing sources only for drafts kept with --revises; this set predates that, so its revisions are adopted one slot at a time with --parent.", ""]
    return "\n".join(out)


def generate(set_id: str, out_dir: Path | None = None, root: Path | None = None) -> dict:
    """Write the folder and return what went into each image (for tests)."""
    out_dir = (out_dir or DEFAULT_ROOT / set_id).expanduser().resolve()
    if REPO in out_dir.parents or out_dir == REPO:
        raise ValueError(f"review folders live outside every repository (got {out_dir}); the default is {DEFAULT_ROOT}/<set>")
    entries, _record, digest = load_set(set_id, root)
    profile = PROFILES.get(set_id, {})
    not_proposed = profile.get("not_proposed", {})
    pending = profile.get("pending", {})
    shown = [e for e in entries if e.key not in not_proposed and e.key not in pending]
    adopted = {k: s for k, s in la.all_icon_sprites().items()}
    sprites = {**adopted, **{e.key: e.sprite for e in shown}}
    adopted_old = {e.key: adopted[e.key] for e in shown if e.key in adopted and adopted[e.key] != e.sprite}
    groups = groups_for({e.key for e in shown})
    images = {
        "01_overview.png": "every proposed draft at its true size and zoomed, on a dark and a light panel, beside its fallback today",
        "02_before_after.png": "the adopted drawing (r0001) next to the proposed revision (r0002, green frame)",
        "03_groups.png": "every must-differ group the drafts belong to, side by side (green frame = proposed)",
        "04_colour_vision.png": "those groups in colour, greyscale and three simulated visions (an approximation for the eye, never a verdict)",
        "05_map_markers.png": "location glyphs on the plate over the darkest and the brightest terrain, and a small map scene (or a note when the set has none)",
        "06_silhouettes.png": "one-colour silhouettes: judge the outline only",
    }
    canvases = {
        "01_overview.png": sheet_overview(set_id, shown, digest),
        "02_before_after.png": sheet_before_after(set_id, shown, digest, adopted_old),
        "03_groups.png": sheet_groups(set_id, digest, sprites, {e.key for e in shown}, groups, False) if groups else message_canvas(set_id, "groups", "None of these drafts belongs to a must-differ group.", digest),
        "04_colour_vision.png": sheet_groups(set_id, digest, sprites, {e.key for e in shown}, groups, True) if groups else message_canvas(set_id, "colour vision", "None of these drafts belongs to a must-differ group.", digest),
        "05_map_markers.png": sheet_markers(set_id, digest, shown, sprites),
        "06_silhouettes.png": sheet_silhouettes(set_id, digest, shown, sprites, adopted_old, pending),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, canvas in canvases.items():
        (out_dir / name).write_bytes(canvas.png())
    result = profile["evaluate"](root or keyset.DRAFTS) if "evaluate" in profile and root is None else None
    (out_dir / "README.txt").write_text(readme(set_id, digest, shown, profile, result, images), encoding="utf-8")
    return {"out_dir": str(out_dir), "set_id": set_id, "draft_set_hash": digest, "tiles": {"01_overview": [e.key for e in shown], "02_before_after": sorted(adopted_old), "03_groups": [n for n, _ in groups]},
            "files": {n: (out_dir / n).stat().st_size for n in FILES}}


def add_arguments(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--set", dest="set_id", required=True)
    ap.add_argument("--out", type=Path, default=None, help="default: ~/Work/asset-review/<set>/")


def run(args: argparse.Namespace) -> int:
    """`python -m visual_assets.review review-sheets --set <id> [--out DIR]`."""
    info = generate(args.set_id, args.out)
    print(f"wrote {info['out_dir']}")
    for name, size in info["files"].items():
        print(f"  {name}  {size} bytes")
    return 0
