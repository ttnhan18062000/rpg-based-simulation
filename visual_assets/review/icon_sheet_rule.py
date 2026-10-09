"""The icon sheet rule (I1-I3): a set-level shape and colour-vision check, predeclared before any icon art exists (`TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE`, D20).

`lint_sprite`'s `value_separation` only looks inside one sprite. Nothing else checks that two tiers, or a buff and a debuff frame, differ by more than hue. This module does, with the same
Machado simulation, Lab and CIE76 code as the pilot and AM5-S checks (`pilot_colour_vision`; nothing is copied). Pure Python, read-only, deterministic.

Three rules over **must-differ groups** (named lists of icon names, each split into *classes*: icons of one class may share a silhouette on purpose):

- **I1 shape.** Every pair from different classes of a group differs in its 1-bit alpha silhouette by at least `shape_min[size]` pixels (3 at 8x8, 6 at 16x16, 8 at 24x24). This is the non-hue cue.
- **I2 value.** Every pair of a group (same class or not) has interior mean colours (the sRGB mean of the opaque pixels that are not on the silhouette's outer boundary; the whole sprite if it
  has no interior) whose L* differ by at least `value_min`, under normal vision (this is the greyscale reading), protanopia, deuteranopia and tritanopia. The interior is measured because at 8x8
  the outline is more than half of a badge and would halve every difference (measured, `docs/assets/icon_criteria.md`).
- **I3 plate contrast.** Every distinct colour on a plate's outer rim differs in L* from the mean colour of every terrain tile by at least `plate_min` under all four visions.

Reported but not ruled: icon pixels outside the palette, and each terrain tile's darkest and lightest pixel L* (the mean is what I3 measures).

    python -m visual_assets.review.icon_sheet_rule      # prints the measured baselines on the synthetic sprites and on the terrain-v1 tiles
"""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from pathlib import Path

from visual_assets.review.pilot_colour_vision import VISIONS, Rgb, from_hex, mean, simulate, to_lab
from visual_assets.store import pixels

OPAQUE = 128  # alpha at or above this counts as part of the silhouette

Pixel = tuple[int, int, int, int]


@dataclass(frozen=True)
class Sprite:
    width: int
    height: int
    rgba: tuple[Pixel, ...]  # row-major

    def at(self, x: int, y: int) -> Pixel:
        return self.rgba[y * self.width + x]


@dataclass(frozen=True)
class Thresholds:
    shape_min: dict[int, int]  # canvas side -> minimum differing silhouette pixels
    value_min: float  # minimum L* difference of mean colours
    plate_min: float  # minimum L* difference between a plate rim colour and a terrain tile mean


# The user's answers by blocking question after the measured baselines (`docs/assets/icon_criteria.md`). 2026-10-06: I1 3 px at 8x8 and 6 px at 16x16, I2 6 L*, I3 12 L*; E and D may share a
# silhouette. 2026-10-07 (icon set v2): I1 8 px at 24x24. A canvas size with no threshold (anything else) raises KeyError instead of passing silently.
RULE = Thresholds(shape_min={8: 3, 16: 6, 24: 8}, value_min=6.0, plate_min=12.0)


def from_png(png: bytes) -> Sprite:
    image = pixels.decode_png(png)
    data = image.rgba
    return Sprite(image.width, image.height, tuple((data[i], data[i + 1], data[i + 2], data[i + 3]) for i in range(0, len(data), 4)))


def from_rows(rows: list[str], colours: dict[str, str]) -> Sprite:
    """A synthetic sprite from text rows: `.` is transparent, any other character looks up `colours` ('#rrggbb')."""
    width = len(rows[0])
    assert all(len(r) == width for r in rows), "rows must be the same length"
    out: list[Pixel] = []
    for row in rows:
        for ch in row:
            if ch == ".":
                out.append((0, 0, 0, 0))
            else:
                r, g, b = (round(c * 255) for c in from_hex(colours[ch]))
                out.append((r, g, b, 255))
    return Sprite(width, len(rows), tuple(out))


def silhouette(sprite: Sprite) -> frozenset[tuple[int, int]]:
    return frozenset((i % sprite.width, i // sprite.width) for i, p in enumerate(sprite.rgba) if p[3] >= OPAQUE)


def shape_distance(a: Sprite, b: Sprite) -> int:
    assert (a.width, a.height) == (b.width, b.height), "a must-differ group holds icons of one size"
    return len(silhouette(a) ^ silhouette(b))


def _side(sprite: Sprite) -> int:
    assert sprite.width == sprite.height, "icons are square"
    return sprite.width


def _boundary(sprite: Sprite) -> set[tuple[int, int]]:
    inside = silhouette(sprite)
    return {(x, y) for x, y in inside if any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def mean_colour(sprite: Sprite) -> Rgb:
    """Interior mean: opaque pixels off the silhouette's outer boundary (all opaque pixels if there are none)."""
    edge = _boundary(sprite)
    pick = [(p[0] / 255, p[1] / 255, p[2] / 255) for i, p in enumerate(sprite.rgba) if p[3] >= OPAQUE and (i % sprite.width, i // sprite.width) not in edge]
    if not pick:
        pick = [(p[0] / 255, p[1] / 255, p[2] / 255) for p in sprite.rgba if p[3] >= OPAQUE]
    assert pick, "an icon has opaque pixels"
    return mean(pick)


def lightness(rgb: Rgb, vision: str) -> float:
    return to_lab(simulate(rgb, vision))[0]


def value_distance(a: Sprite, b: Sprite, vision: str) -> float:
    return abs(lightness(mean_colour(a), vision) - lightness(mean_colour(b), vision))


def rim_colours(sprite: Sprite) -> list[str]:
    """Distinct '#rrggbb' of the opaque pixels on the silhouette's outer boundary (a 4-neighbour outside the silhouette, or the canvas edge)."""
    found: set[str] = set()
    for x, y in sorted(_boundary(sprite)):
        r, g, b, _ = sprite.at(x, y)
        found.add(f"#{r:02x}{g:02x}{b:02x}")
    return sorted(found)


def off_palette(sprite: Sprite, palette: set[str]) -> int:
    return sum(1 for p in sprite.rgba if p[3] >= OPAQUE and f"#{p[0]:02x}{p[1]:02x}{p[2]:02x}" not in palette)


def evaluate_sheet(
    icons: dict[str, Sprite],
    groups: dict[str, list[list[str]]],
    plates: dict[str, Sprite],
    tile_means: dict[str, Rgb],
    thresholds: Thresholds = RULE,
    palette: set[str] | None = None,
    shape_only: frozenset[str] | set[str] = frozenset(),
) -> dict:
    """The rule applied to a sheet. Returns every number and the verdict (`PASS` iff I1, I2 and I3 all hold).

    `shape_only` names groups checked by I1 alone (user's answer of 2026-10-07 for groups of different subjects, and for rarity badges against tier badges): I2 is skipped for them and the
    report says so (`value_checked: false`). Every other group gets I1 and I2 as before."""
    i1_fail: list[dict] = []
    i2_fail: list[dict] = []
    group_rows: dict[str, dict] = {}
    for gname in sorted(groups):
        classes = groups[gname]
        names = [n for c in classes for n in c]
        assert len(set(names)) == len(names), f"{gname}: an icon is in two classes"
        klass = {n: i for i, c in enumerate(classes) for n in c}
        sizes = {_side(icons[n]) for n in names}
        assert len(sizes) == 1, f"{gname}: one size per group"
        size = sizes.pop()
        need = thresholds.shape_min[size]
        shape_min = None
        value_min = {v: None for v in VISIONS}
        for a, b in itertools.combinations(sorted(names), 2):
            if klass[a] != klass[b]:
                d = shape_distance(icons[a], icons[b])
                shape_min = d if shape_min is None else min(shape_min, d)
                if d < need:
                    i1_fail.append({"group": gname, "a": a, "b": b, "shape_px": d, "need": need})
            for v in () if gname in shape_only else VISIONS:
                dv = value_distance(icons[a], icons[b], v)
                value_min[v] = dv if value_min[v] is None else min(value_min[v], dv)
                if dv < thresholds.value_min:
                    i2_fail.append({"group": gname, "a": a, "b": b, "vision": v, "dL": round(dv, 3), "need": thresholds.value_min})
        group_rows[gname] = {"size": size, "pairs": len(names) * (len(names) - 1) // 2, "min_shape_px_across_classes": shape_min, "value_checked": gname not in shape_only,
                             "min_dL_by_vision": {v: round(x, 3) for v, x in value_min.items() if x is not None}}
    i3_fail: list[dict] = []
    plate_rows: dict[str, dict] = {}
    for pname in sorted(plates):
        rims = rim_colours(plates[pname])
        worst = {v: None for v in VISIONS}
        for rim, (tname, tmean), v in itertools.product(rims, sorted(tile_means.items()), VISIONS):
            d = abs(lightness(from_hex(rim), v) - lightness(tmean, v))
            if worst[v] is None or d < worst[v][0]:
                worst[v] = (d, rim, tname)
            if d < thresholds.plate_min:
                i3_fail.append({"plate": pname, "rim": rim, "tile": tname, "vision": v, "dL": round(d, 3), "need": thresholds.plate_min})
        plate_rows[pname] = {"rim_colours": rims, "closest_by_vision": {v: {"dL": round(w[0], 3), "rim": w[1], "tile": w[2]} for v, w in worst.items() if w}}
    i1, i2, i3 = not i1_fail, not i2_fail, not i3_fail
    report = {
        "rule": {"i1": f"silhouette pixels differing >= {thresholds.shape_min} (by canvas side) across classes", "i2": f"dL* of mean colours >= {thresholds.value_min} in {list(VISIONS)}",
                 "i3": f"plate rim colour vs terrain tile mean, dL* >= {thresholds.plate_min} in {list(VISIONS)}"},
        "i1": i1, "i2": i2, "i3": i3, "result": "PASS" if (i1 and i2 and i3) else "FAIL",
        "groups": group_rows, "plates": plate_rows,
        "failing": {"i1": i1_fail, "i2": sorted(i2_fail, key=lambda f: f["dL"]), "i3": sorted(i3_fail, key=lambda f: f["dL"])},
    }
    if palette is not None:
        report["off_palette_pixels"] = {n: off_palette(s, palette) for n, s in sorted({**icons, **plates}.items()) if off_palette(s, palette)}
    return report


def tile_context(tiles: dict[str, list[Rgb]]) -> dict[str, dict]:
    """Per terrain tile: mean L* and darkest and lightest pixel L* under normal vision (context for I3, not ruled)."""
    out = {}
    for k, t in sorted(tiles.items()):
        ls = [lightness(c, "normal") for c in t]
        out[k] = {"mean": round(lightness(mean(t), "normal"), 1), "min": round(min(ls), 1), "max": round(max(ls), 1)}
    return out


def committed_palette(path: Path) -> set[str]:
    return set(json.loads(path.read_text())["colors"])
