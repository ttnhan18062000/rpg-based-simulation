"""Sample-map renderer (`TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-RENDER`): draws a world of `visual_assets_sample_map data` with the art of the rc-0009 runtime export.

    python -m tools.visual_assets_sample_map render frontier_living_world      # four PNGs and render_stats.json under reports/visual_assets/sample_map/<world>/
    python -m tools.visual_assets_sample_map render --all                      # the three worlds, then the page reports/visual_assets/sample_map/index.html

Evidence, never art: nothing here is intaken, adopted or put in a release candidate, and nothing is wired into the app. Everything is written under the gitignored
`reports/visual_assets/sample_map/`. The renderer PORTS the composition rule of `frontend/src/visualAssets/terrainBorders.ts` (`borderOverlays`, `composeCell`, `rotate`),
the detail pick of `pickDetail.ts` (32-bit FNV-1a) and the resolver order of `resolver.ts` (the picked value's image, then the default's, then the role fallback); it does not
import or edit the TS. Parity is tested on the rule's own test vectors and, where node and esbuild are installed, differentially against the real TS rule on random maps.

Two views per world, each labelled wherever a number or picture is quoted:
  exact  - the primary evidence: a terrain name draws with `terrain.<name>` only when that key is registered; every other name is a marked gap.
  alias  - the UNCONFIRMED proposals of `proposed_aliases` in the data file (asset-planner's, for rpg-planner, #519): a name with no exact key draws with its proposed alias.
The terrain is drawn by terrain NAME, never by `present_map`'s per-world integer code (the live client reads those codes as fixed Live Map codes; that is rpg's bug #523 and is
not worked around here).

What a gap looks like: a terrain name with no key (exact view) is a diagonal-striped cell; a key with no art in the release is the flat fill of the Live Map with a diagonal line
(the labelled role fallback of `terrainDrafts.ts`); an object (building, place, resource node) with no art is a checkered 10 x 10 marker. Buildings are drawn from their 24 x 24
icon scaled to one 16 x 16 cell (nearest neighbour, stated); places are the `icon.plate.location` plate with their marker glyph on it. Entities are counted in the data, not drawn.
"""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_ROOT = REPO / "reports" / "visual_assets" / "sample_map"
EXPORT_DIR = OUT_ROOT / "rc-0009-runtime"
TILE = 16

# ---- ported constants: `terrainBorders.ts`, `pickDetail.ts`, `terrainDrafts.ts` (a test compares each with the TS text) ----
DETAIL_SEED = 1
BORDER_DEPTH = 4
TERRAIN_PRIORITY = (2, 18, 14, 0, 20, 21, 8, 7, 16, 10, 19, 15, 9, 17, 6)  # lowest first, Live Map codes
CRISP_TERRAINS = frozenset({1, 3, 4, 5, 11, 12, 13, 22})
RANK = {code: index + 1 for index, code in enumerate(TERRAIN_PRIORITY)}
MASK_KEYS = {"edge": "border.edge", "outer_corner": "border.outer_corner", "inner_corner": "border.inner_corner"}
TERRAIN_DRAFT_KEYS = {
    0: "terrain.floor", 1: "terrain.wall", 2: "terrain.water", 3: "terrain.town", 4: "terrain.camp", 5: "terrain.sanctuary", 6: "terrain.forest", 7: "terrain.desert",
    8: "terrain.swamp", 9: "terrain.mountain", 10: "terrain.road", 11: "terrain.bridge", 12: "terrain.ruins", 13: "terrain.dungeon_entrance", 14: "terrain.lava",
    15: "terrain.grassland", 16: "terrain.snow", 17: "terrain.jungle", 18: "terrain.shallow_water", 19: "terrain.farmland", 20: "terrain.cave", 21: "terrain.volcanic",
    22: "terrain.graveyard",
}
CODE_OF_KEY = {key: code for code, key in TERRAIN_DRAFT_KEYS.items()}
TILE_COLORS = {
    0: "#1a1d27", 1: "#555b73", 2: "#1e3a5f", 3: "#2d4a3e", 4: "#4a2d2d", 5: "#2d3a4a", 6: "#1b3a1b", 7: "#3a3420", 8: "#2a2a3a", 9: "#3a3a3a", 10: "#5a5040", 11: "#4a6050",
    12: "#4a4035", 13: "#6a3040", 14: "#8a3000", 15: "#4a6030", 16: "#c8d8e8", 17: "#0a4a0a", 18: "#2a5070", 19: "#6a7a40", 20: "#3a3040", 21: "#5a2a1a", 22: "#4a4050",
}
OFFSET_BASIS = 0x811C9DC5
PRIME = 0x01000193

SIDES = ("N", "E", "S", "W")
SIDE_DELTA = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
SIDE_ROTATION = {"N": 0, "E": 90, "S": 180, "W": 270}
CORNERS = (  # corner, diagonal offset, the two sides next to it (first, second clockwise), rotation of the corner masks
    ("NE", (1, -1), ("N", "E"), 0),
    ("SE", (1, 1), ("E", "S"), 90),
    ("SW", (-1, 1), ("S", "W"), 180),
    ("NW", (-1, -1), ("W", "N"), 270),
)


def fnv1a32(text: str) -> int:
    h = OFFSET_BASIS
    for byte in text.encode("utf-8"):
        h = ((h ^ byte) * PRIME) & 0xFFFFFFFF
    return h


def pick_detail(visual_key: str, x: int, y: int, seed: int, values: list[str] | tuple[str, ...]) -> str:
    if not values:
        raise ValueError("a detail axis has at least one value")
    return values[fnv1a32(f"{visual_key}|{x}|{y}|{seed}") % len(values)]


def _higher(code: int, neighbour: int | None) -> bool:
    if neighbour is None or code in CRISP_TERRAINS or neighbour in CRISP_TERRAINS:
        return False
    own, other = RANK.get(code), RANK.get(neighbour)
    return own is not None and other is not None and other > own


def border_overlays(code_at, x: int, y: int, variants, seed: int = DETAIL_SEED) -> list[tuple]:
    """`borderOverlays`: (neighbour, kind, rotation, mask_key, detail) per piece in draw order. `variants(mask_key)` is the declared variant list of a mask (empty = not available)."""
    code = code_at(x, y)
    if code is None or code in CRISP_TERRAINS or code not in RANK:
        return []
    side_code: dict[str, int] = {}
    for side in SIDES:
        dx, dy = SIDE_DELTA[side]
        n = code_at(x + dx, y + dy)
        if _higher(code, n):
            side_code[side] = n
    corner_code: dict[str, int] = {}
    for corner, delta, _sides, _rotation in CORNERS:
        n = code_at(x + delta[0], y + delta[1])
        if _higher(code, n):
            corner_code[corner] = n
    neighbours = sorted(dict.fromkeys([*side_code.values(), *corner_code.values()]), key=lambda c: RANK[c])
    out: list[tuple] = []

    def piece(neighbour: int, kind: str, rotation: int) -> bool:
        mask_key = MASK_KEYS[kind]
        values = variants(mask_key)
        if not values:
            return False
        out.append((neighbour, kind, rotation, mask_key, pick_detail(f"border:{mask_key}:{neighbour}:{rotation}", x, y, seed, values)))
        return True

    for h in neighbours:
        used: set[str] = set()
        edges: list[str] = []
        inner: list[tuple] = []
        for c in CORNERS:
            a, b = c[2]
            if side_code.get(a) == h and side_code.get(b) == h and a not in used and b not in used:
                inner.append(c)
                used.update((a, b))
        for side in SIDES:
            if side_code.get(side) == h and side not in used:
                edges.append(side)
        inner_available = len(variants(MASK_KEYS["inner_corner"])) > 0
        if not inner_available:
            for c in inner:
                edges.extend(c[2])
        for side in [s for s in SIDES if s in edges]:
            piece(h, "edge", SIDE_ROTATION[side])
        if inner_available:
            for c in inner:
                piece(h, "inner_corner", c[3])
        for c in CORNERS:
            if corner_code.get(c[0]) == h and side_code.get(c[2][0]) != h and side_code.get(c[2][1]) != h:
                piece(h, "outer_corner", c[3])
    return out


def rotate(pixels: bytes, rotation: int) -> bytes:
    """`rotate`: `rotation` degrees (a multiple of 90) clockwise of a 16 x 16 RGBA image."""
    out = bytearray(len(pixels))
    turns = rotation // 90
    for y in range(TILE):
        for x in range(TILE):
            sx, sy = x, y
            for _ in range(turns):
                sx, sy = sy, TILE - 1 - sx
            out[(y * TILE + x) * 4:(y * TILE + x) * 4 + 4] = pixels[(sy * TILE + sx) * 4:(sy * TILE + sx) * 4 + 4]
    return bytes(out)


def _allowed(kind: str, x: int, y: int, depth: int) -> bool:
    north = y < depth
    east = x >= TILE - depth
    if kind == "edge":
        return north
    if kind == "outer_corner":
        return north and east
    return north or east


def compose_cell(base: bytes, overlays, tile_of, mask_of) -> bytes:
    """`composeCell`: the cell's own tile with each overlay's fringe (the NEIGHBOUR tile's pixels where the rotated mask is opaque, capped to the outer BORDER_DEPTH pixels)."""
    out = bytearray(base)
    for neighbour, kind, rotation, mask_key, detail in overlays:
        tile = tile_of(neighbour)
        mask = mask_of(mask_key, detail)
        if tile is None or mask is None:
            continue
        flags = bytearray(TILE * TILE * 4)
        for y in range(TILE):
            for x in range(TILE):
                if _allowed(kind, x, y, BORDER_DEPTH):
                    flags[(y * TILE + x) * 4 + 3] = 255
        allowed = rotate(bytes(flags), rotation)
        rotated = rotate(mask, rotation)
        for i in range(TILE * TILE):
            if allowed[i * 4 + 3] > 0 and rotated[i * 4 + 3] >= 128:
                out[i * 4:i * 4 + 4] = tile[i * 4:i * 4 + 4]
    return bytes(out)


# ---- PNG ----

def encode_png(width: int, height: int, rows: list[bytearray] | list[bytes]) -> bytes:
    """An RGBA 8-bit PNG, filter 0, one zlib stream at a fixed level (deterministic for one zlib build)."""
    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")


def upscale2(row: bytes) -> bytearray:
    """Nearest-neighbour x2 of one RGBA row."""
    out = bytearray(len(row) * 2)
    for c in range(4):
        out[c::8] = row[c::4]
        out[4 + c::8] = row[c::4]
    return out


def _hex(colour: str) -> tuple[int, int, int]:
    return int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16)


def flat_with_diagonal(code: int) -> bytes:
    """The labelled role fallback of `drawDraftCell`: the Live Map flat fill with a diagonal line from bottom-left to top-right (white at 35 %)."""
    r, g, b = _hex(TILE_COLORS[code])
    out = bytearray()
    for y in range(TILE):
        for x in range(TILE):
            if x + y == TILE - 1:
                out += bytes((round(r + (255 - r) * 0.35), round(g + (255 - g) * 0.35), round(b + (255 - b) * 0.35), 255))
            else:
                out += bytes((r, g, b, 255))
    return bytes(out)


def no_key_hatch() -> bytes:
    """A terrain name with no key at all: diagonal stripes in two plum shades (not a Live Map colour, so it cannot be mistaken for art or for a role fallback)."""
    out = bytearray()
    for y in range(TILE):
        for x in range(TILE):
            out += bytes((0x8A, 0x2A, 0x6A, 255)) if ((x + y) // 2) % 2 == 0 else bytes((0x2A, 0x10, 0x28, 255))
    return bytes(out)


def gap_marker() -> bytes:
    """An object with no art: a checkered 10 x 10 marker (magenta and black) centred in a transparent cell."""
    out = bytearray(TILE * TILE * 4)
    for y in range(3, 13):
        for x in range(3, 13):
            colour = (0xFF, 0x00, 0xFF, 255) if ((x + y) % 2 == 0) else (0, 0, 0, 255)
            out[(y * TILE + x) * 4:(y * TILE + x) * 4 + 4] = bytes(colour)
    return bytes(out)


def over(dst: bytearray, offset: int, src: bytes, i: int) -> None:
    """Source-over of one RGBA source pixel onto the destination pixel at `offset` (integer arithmetic, destination assumed opaque)."""
    a = src[i * 4 + 3]
    if a == 0:
        return
    if a == 255:
        dst[offset:offset + 4] = src[i * 4:i * 4 + 4]
        return
    for c in range(3):
        dst[offset + c] = (src[i * 4 + c] * a + dst[offset + c] * (255 - a) + 127) // 255
    dst[offset + 3] = 255


def scale_to_cell(rgba: bytes, width: int, height: int) -> bytes:
    """Nearest-neighbour resize of a width x height RGBA image to one 16 x 16 cell (stated in the legend)."""
    if (width, height) == (TILE, TILE):
        return rgba
    out = bytearray(TILE * TILE * 4)
    for y in range(TILE):
        for x in range(TILE):
            sx, sy = x * width // TILE, y * height // TILE
            out[(y * TILE + x) * 4:(y * TILE + x) * 4 + 4] = rgba[(sy * width + sx) * 4:(sy * width + sx) * 4 + 4]
    return bytes(out)


# ---- the release art ----

class Release:
    """The rc-0009 runtime export: `entries` by (key, detail), declared detail axes, decoded 16 x 16 tiles and icons, read with the store's PNG decoder."""

    def __init__(self, export_dir: Path):
        from visual_assets.store import pixels

        self.dir = export_dir
        manifest = json.loads((export_dir / "runtime_manifest.json").read_text())
        self.release_id = manifest["release_id"]
        self.entries = {(e["visual_key"], e.get("detail")): e for e in manifest["entries"]}
        self.axes = {d["visual_key"]: d for d in manifest["details"]}
        self._pixels = pixels
        self._cache: dict[str, tuple[int, int, bytes]] = {}

    def image(self, key: str, detail: str | None) -> tuple[int, int, bytes] | None:
        entry = self.entries.get((key, detail))
        if entry is None:
            return None
        if entry["file"] not in self._cache:
            img = self._pixels.decode_png((self.dir / entry["file"]).read_bytes())
            self._cache[entry["file"]] = (img.width, img.height, img.rgba)
        return self._cache[entry["file"]]

    def tile(self, key: str, x: int, y: int) -> tuple[bytes | None, str | None]:
        """The 16 x 16 tile of `key` for cell (x, y) by the resolver's order (picked value, then default), or (None, reason). Returns (rgba, picked detail)."""
        axis = self.axes.get(key)
        if axis is None:
            img = self.image(key, None)
            return (img[2], None) if img else (None, None)
        picked = pick_detail(key, x, y, DETAIL_SEED, axis["values"])
        for detail in (picked, axis["default"]):
            img = self.image(key, detail)
            if img:
                return img[2], detail
        return None, picked

    def variants(self, mask_key: str) -> list[str]:
        axis = self.axes.get(mask_key)
        return [v for v in (axis["values"] if axis else []) if self.image(mask_key, v) is not None]

    def mask(self, mask_key: str, detail: str) -> bytes | None:
        img = self.image(mask_key, detail)
        return img[2] if img else None


# ---- drawing a world ----

def key_for_name(row: dict, view: str) -> str | None:
    """The key a terrain row draws with in a view: the exact key, or in the alias view the unconfirmed proposed alias when there is no exact key."""
    if row["key"]:
        return row["key"]
    return row.get("proposed_alias") if view == "alias" else None


def draw_world(data: dict, release: Release, view: str) -> tuple[list[bytearray], dict]:
    """Rows of the x1 canvas (16 px per cell) and the statistics of the drawing."""
    width, height = data["width"], data["height"]
    names, rle = data["terrain_names"], data["terrain_rle"]
    cell_name = [names[i] for i, run in zip(rle[0::2], rle[1::2]) for _ in range(run)]
    row_by_name = {r["name"]: r for r in data["terrain"]}
    key_of = {name: key_for_name(row_by_name[name], view) for name in names}
    code_of = {name: CODE_OF_KEY.get(key) for name, key in key_of.items() if key}

    def code_at(x: int, y: int) -> int | None:
        if 0 <= x < width and 0 <= y < height:
            return code_of.get(cell_name[y * width + x])
        return None

    stats = {"cells": width * height, "terrain_no_key": {}, "terrain_key_without_art": {}, "terrain_drawn": {}, "bordered_cells": 0, "border_pieces": 0, "objects_drawn": {}, "objects_gap": {}}
    canvas = [bytearray(width * TILE * 4) for _ in range(height * TILE)]
    hatch, mark = no_key_hatch(), gap_marker()

    def base_tile(name: str, x: int, y: int) -> tuple[bytes, str]:
        key = key_of[name]
        if key is None:
            return hatch, "no_key"
        tile, detail = release.tile(key, x, y)
        if tile is not None:
            return tile, "art"
        return flat_with_diagonal(CODE_OF_KEY[key]), "key_without_art"

    def neighbour_tile(code: int, x: int, y: int) -> bytes | None:
        key = TERRAIN_DRAFT_KEYS.get(code)
        return release.tile(key, x, y)[0] if key else None

    for y in range(height):
        for x in range(width):
            name = cell_name[y * width + x]
            tile, status = base_tile(name, x, y)
            if status == "no_key":
                stats["terrain_no_key"][name] = stats["terrain_no_key"].get(name, 0) + 1
            elif status == "key_without_art":
                stats["terrain_key_without_art"][key_of[name]] = stats["terrain_key_without_art"].get(key_of[name], 0) + 1
            else:
                stats["terrain_drawn"][key_of[name]] = stats["terrain_drawn"].get(key_of[name], 0) + 1
            overlays = border_overlays(code_at, x, y, release.variants) if status == "art" else []
            if overlays:
                tile = compose_cell(tile, overlays, lambda c, x=x, y=y: neighbour_tile(c, x, y), release.mask)
                stats["bordered_cells"] += 1
                stats["border_pieces"] += len(overlays)
            for r in range(TILE):
                canvas[y * TILE + r][x * TILE * 4:(x + 1) * TILE * 4] = tile[r * TILE * 4:(r + 1) * TILE * 4]

    def stamp(cx: int, cy: int, rgba: bytes) -> None:
        if not (0 <= cx < width and 0 <= cy < height):
            return
        for r in range(TILE):
            for c in range(TILE):
                over(canvas[cy * TILE + r], (cx * TILE + c) * 4, rgba, r * TILE + c)

    aliases = data["proposed_aliases"]

    def kind_key(family: str, prefix: str, kind: str) -> str | None:
        rows = {r["name"]: r for r in data["kinds"][family]}
        row = rows.get(kind, {})
        if row.get("key"):
            return row["key"]
        return row.get("proposed_alias") if view == "alias" else None

    def count(table: str, label: str) -> None:
        stats[table][label] = stats[table].get(label, 0) + 1

    plate = release.image("icon.plate.location", None)
    for b in data["buildings"]:
        key = kind_key("building", "icon.building.", b["kind"])
        img = release.image(key, None) if key else None
        if img:
            stamp(int(b["x"]), int(b["y"]), scale_to_cell(img[2], img[0], img[1]))
            count("objects_drawn", f"building:{b['kind']}")
        else:
            stamp(int(b["x"]), int(b["y"]), mark)
            count("objects_gap", f"building:{b['kind']}")
    for p in data["places"]:
        if plate:
            stamp(int(p["x"]), int(p["y"]), scale_to_cell(plate[2], plate[0], plate[1]))
        key = kind_key("place", "icon.marker.", p["kind"])
        img = release.image(key, None) if key else None
        if img:
            stamp(int(p["x"]), int(p["y"]), scale_to_cell(img[2], img[0], img[1]))
            count("objects_drawn", f"place:{p['kind']}")
        else:
            stamp(int(p["x"]), int(p["y"]), mark)
            count("objects_gap", f"place:{p['kind']}")
    for n in data["resource_nodes"]:
        key = kind_key("resource_node", "icon.marker.", n["kind"])
        img = release.image(key, None) if key else None
        if img:
            stamp(int(n["x"]), int(n["y"]), scale_to_cell(img[2], img[0], img[1]))
            count("objects_drawn", f"resource_node:{n['kind']}")
        else:
            stamp(int(n["x"]), int(n["y"]), mark)
            count("objects_gap", f"resource_node:{n['kind']}")
    assert aliases["label"]
    for table in ("terrain_no_key", "terrain_key_without_art", "terrain_drawn", "objects_drawn", "objects_gap"):
        stats[table] = dict(sorted(stats[table].items()))
    stats["terrain_cells_in_gap"] = sum(stats["terrain_no_key"].values()) + sum(stats["terrain_key_without_art"].values())
    stats["view"] = view
    return canvas, stats


def render_world(data: dict, release: Release, out_dir: Path) -> dict:
    """Write `<view>_x1.png` and `<view>_x2.png` per view and `render_stats.json`; return the statistics (with the PNG hashes)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {"world_id": data["world_id"], "release_id": release.release_id, "cell_pixels_x1": TILE, "views": {}}
    for view in ("exact", "alias"):
        canvas, stats = draw_world(data, release, view)
        w, h = data["width"] * TILE, data["height"] * TILE
        files = {}
        for scale in (1, 2):
            rows = canvas if scale == 1 else [r for row in canvas for r in (upscale2(row), upscale2(row))]
            png = encode_png(w * scale, h * scale, rows)
            name = f"{view}_x{scale}.png"
            (out_dir / name).write_bytes(png)
            files[name] = {"bytes": len(png), "sha256": hashlib.sha256(png).hexdigest(), "width": w * scale, "height": h * scale}
            del rows
        stats["files"] = files
        result["views"][view] = stats
        del canvas
    (out_dir / "render_stats.json").write_text(json.dumps(result, sort_keys=True, indent=1) + "\n")
    return result


def write_page(results: list[dict], datas: dict[str, dict], out_root: Path | None = None) -> Path:
    """One static HTML page: per world the exact view (primary evidence) and the alias view (UNCONFIRMED), the numbers of each view, and the legend. Images are referenced relatively."""
    import html

    root = out_root or OUT_ROOT
    esc = html.escape
    parts = [
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>Sample map: the adopted art on three compiled worlds</title>",
        "<style>body{font:14px/1.45 system-ui,sans-serif;margin:16px;background:#14161c;color:#e6e6e6}h1,h2,h3{margin:.6em 0 .3em}img{image-rendering:pixelated;max-width:100%;height:auto;border:1px solid #444}",
        "table{border-collapse:collapse;margin:.4em 0}td,th{border:1px solid #444;padding:2px 8px;text-align:left}.alias{outline:2px dashed #d9a441}.note{color:#d9a441}code{background:#222;padding:0 3px}.row{display:flex;flex-wrap:wrap;gap:16px}</style></head><body>",
        "<h1>Sample map: the adopted art (rc-0009) on three compiled worlds</h1>",
        "<p><b>Evidence, not a shipped asset</b>: this picture is never intaken, adopted or put in a release candidate; nothing is wired into the Live Map. Cells are drawn by terrain <i>name</i> (the presenter's own code table), not by <code>present_map</code>'s per-world integer code.</p>",
        "<h2>Legend</h2><ul>",
        "<li><b>Exact view</b> (primary evidence): a terrain name draws with <code>terrain.&lt;name&gt;</code> only when that key is registered. A name with no key is a <b>diagonal-striped plum cell</b> (a gap).</li>",
        "<li><b class=\"note\">Alias view (dashed outline) - unconfirmed: asset-planner proposal for rpg-planner (#519)</b>: a name with no exact key draws with its proposed alias. It shows how far the art goes, not a decision.</li>",
        "<li>A key with no art in the release would be the Live Map flat fill with a white diagonal line (none occurs in rc-0009: all 23 terrain keys have art).</li>",
        "<li>An object with no art (building, place, resource node) is a <b>checkered magenta and black 10 x 10 marker</b>. Buildings are drawn from their 24 x 24 icon scaled to one 16 x 16 cell (nearest neighbour); places are the location plate with their marker glyph. Entities are counted in the data, not drawn.</li>",
        "<li>Borders: the composition rule of <code>terrainBorders.ts</code> ported to Python and proven on the rule's own test vectors; only cells whose terrain has a Live Map rank fringe. Scale: 16 px per cell (x1); the x2 files double it.</li></ul>",
    ]
    for res in results:
        data = datas[res["world_id"]]
        parts.append(f"<h2>{esc(res['world_id'])} ({data['width']} x {data['height']} cells)</h2><p>{esc(data['role'])}</p><div class=\"row\">")
        for view, label, css in (("exact", "Exact view (primary evidence)", ""), ("alias", "Alias view - unconfirmed: asset-planner proposal for rpg-planner (#519)", " alias")):
            st = res["views"][view]
            parts.append(f"<div><h3>{esc(label)}</h3><a href=\"{esc(res['world_id'])}/{view}_x2.png\"><img class=\"{css.strip()}\" src=\"{esc(res['world_id'])}/{view}_x1.png\" alt=\"{esc(label)}\" width=\"{min(data['width'] * 4, 640)}\"></a>")
            parts.append(f"<table><tr><th>cells with art</th><td>{sum(st['terrain_drawn'].values())} of {st['cells']}</td></tr><tr><th>cells in the gap (no key)</th><td>{sum(st['terrain_no_key'].values())}</td></tr><tr><th>cells whose key has no art</th><td>{sum(st['terrain_key_without_art'].values())}</td></tr><tr><th>cells with a border fringe</th><td>{st['bordered_cells']}</td></tr><tr><th>objects drawn / in the gap</th><td>{sum(st['objects_drawn'].values())} / {sum(st['objects_gap'].values())}</td></tr></table>")
            if st["terrain_no_key"]:
                parts.append("<p>Gap terrain names: " + ", ".join(f"<code>{esc(n)}</code> {c}" for n, c in st["terrain_no_key"].items()) + "</p>")
            if st["objects_gap"]:
                parts.append("<p>Object gaps: " + ", ".join(f"<code>{esc(n)}</code> {c}" for n, c in st["objects_gap"].items()) + "</p>")
            parts.append("</div>")
        parts.append("</div>")
    parts.append("</body></html>\n")
    path = root / "index.html"
    root.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))
    return path


# ---- committed evidence copies (the only thing of this batch under docs/): small x1 crops, at most 256 KiB in all ----

EVIDENCE_DIR = REPO / "docs" / "assets" / "sample_map"
EVIDENCE_CAP_BYTES = 256 * 1024
# name -> (world, (x0, y0, x1, y1) in cells, half-open): where a gap shows best. Chosen from the data (see the README), not tuned for looks.
EVIDENCE_CROPS = {
    "frontier_town": ("frontier_living_world", (4, 8, 52, 40)),          # Hometown: town hall, shops, inn, blacksmith, healer, the CITY plate, wood node, herb patch
    "highland_pass": ("highland_traverse", (80, 84, 128, 116)),          # the mountain pass: mountain and forest, an iron vein and a frost shard cluster
    "dungeon_ruin": ("dungeon_crawl", (56, 76, 101, 116)),               # the ruin block, its place marker and the forest edge
    "frontier_camp_ruin": ("frontier_living_world", (104, 24, 152, 56)),  # the goblin camp (CAMP place, berry thicket) and the haunted battlefield (RUIN place, ruin terrain)
    "highland_river": ("highland_traverse", (124, 26, 172, 58)),         # River Ford: the river terrain, the watchtower and a herb patch
}


def crop_rows(canvas: list[bytearray], box: tuple[int, int, int, int]) -> list[bytearray]:
    x0, y0, x1, y1 = box
    return [bytearray(canvas[y][x0 * TILE * 4:x1 * TILE * 4]) for y in range(y0 * TILE, y1 * TILE)]


def evidence_files(datas: dict[str, dict], release: Release) -> dict[str, bytes]:
    """`<crop>_<view>_x1.png` for every crop and both views, drawn by the same code as the full renders."""
    out: dict[str, bytes] = {}
    for name, (world, box) in EVIDENCE_CROPS.items():
        for view in ("exact", "alias"):
            canvas, _ = draw_world(datas[world], release, view)
            rows = crop_rows(canvas, box)
            out[f"{name}_{view}_x1.png"] = encode_png((box[2] - box[0]) * TILE, (box[3] - box[1]) * TILE, rows)
    return out


def write_evidence(datas: dict[str, dict], release: Release, out_dir: Path | None = None) -> dict[str, int]:
    """Write the evidence crops under `docs/assets/sample_map/` (or `out_dir` in a test); refuse when they exceed the cap."""
    files = evidence_files(datas, release)
    total = sum(len(b) for b in files.values())
    if total > EVIDENCE_CAP_BYTES:
        raise SystemExit(f"the evidence crops are {total} B, over the {EVIDENCE_CAP_BYTES} B cap; shrink a crop box, do not raise the cap")
    target = out_dir or EVIDENCE_DIR
    target.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (target / name).write_bytes(data)
    return {name: len(data) for name, data in sorted(files.items())}
