"""Synthetic sprites for the icon sheet rule and the baseline measurement that backs its thresholds (`TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE`).

These are mock-ups, not icons: no art exists yet. They exist so every threshold of `icon_sheet_rule` comes with a measured baseline instead of a guess, and so the tests can plant
the failures the rule must catch. Pure Python.

    python -m tests.visual_assets.icon_sheet_synthetic      # prints the baseline measurements as JSON
"""

from __future__ import annotations

import itertools
import json

from tests.visual_assets import icon_palette
from tests.visual_assets.icon_sheet_rule import (
    RULE,
    Sprite,
    Thresholds,
    committed_palette,
    evaluate_sheet,
    lightness,
    mean_colour,
    shape_distance,
    tile_context,
    value_distance,
)
from tests.visual_assets.pilot_colour_vision import VISIONS, from_hex, mean
from visual_assets.store import pixels  # noqa: F401  (kept so a missing store fails here, not in a half-run)

OUTLINE = "#0e1018"
GRADES = ("e", "d", "c", "b", "a", "s", "ss", "sss")
TODAY_CHIPS = {"e": "#6b7280", "d": "#94a3b8", "c": "#34d399", "b": "#60a5fa", "a": "#fb923c", "s": "#f87171", "ss": "#f59e0b", "sss": "#ffd700"}  # ClassHallPanel GRADE_COLORS


def _mask(rows: list[str]) -> set[tuple[int, int]]:
    return {(x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch == "#"}


OCTAGON = _mask(["..####..", ".######.", "########", "########", "########", "########", ".######.", "..####.."])
DIAMOND = _mask(["...##...", "..####..", ".######.", "########", "########", ".######.", "..####..", "...##..."])


def _holes(shell: set, rects: list[tuple[int, int, int, int]]) -> set:
    cut = {(x, y) for x0, y0, w, h in rects for x in range(x0, x0 + w) for y in range(y0, y0 + h)}
    return shell - cut


# the ladder of the style guide (E-D plain, C-B pips, A frame, S/SS/SSS stars), as pixel shapes: pips are 2x2 holes, the frame is a 4x4 hole, "stars" reuse the pip steps on a diamond
LADDER_SHAPES = {
    "e": OCTAGON, "d": OCTAGON,
    "c": _holes(OCTAGON, [(3, 3, 2, 2)]),
    "b": _holes(OCTAGON, [(1, 3, 2, 2), (5, 3, 2, 2)]),
    "a": _holes(OCTAGON, [(2, 2, 4, 4)]),
    "s": DIAMOND,
    "ss": _holes(DIAMOND, [(3, 3, 2, 2)]),
    "sss": _holes(DIAMOND, [(1, 3, 2, 2), (5, 3, 2, 2)]),
}
LADDER_CLASSES = [["e", "d"], ["c"], ["b"], ["a"], ["s"], ["ss"], ["sss"]]  # E and D share a silhouette by the ladder's own rule: only value separates them


def badge(shape: set, fill: str, outline: str = OUTLINE) -> Sprite:
    rgba = []
    for y in range(8):
        for x in range(8):
            if (x, y) not in shape:
                rgba.append((0, 0, 0, 0))
                continue
            edge = any((x + dx, y + dy) not in shape for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            r, g, b = (round(c * 255) for c in from_hex(outline if edge else fill))
            rgba.append((r, g, b, 255))
    return Sprite(8, 8, tuple(rgba))


def palette_by_lightness() -> list[tuple[float, str]]:
    return sorted((lightness(from_hex(c), "normal"), c) for c in committed_palette(icon_palette.PALETTE_FILE))


def ladder_fills(targets: tuple[float, ...]) -> list[str]:
    """For each target L*, the palette colour nearest in L* (a ladder whose steps are as even as the palette allows)."""
    pal = palette_by_lightness()
    return [min(pal, key=lambda lc: abs(lc[0] - t))[1] for t in targets]


def best_ladder(count: int = 8, lo: float = 18.0, hi: float = 97.0) -> tuple[float, list[str]]:
    """The largest L* gap g for which `count` palette colours within [lo, hi] (normal vision) can be chosen so that EVERY pair differs by at least g in L* under all four visions
    (greedy from the dark end, binary search on g). It is the palette's capacity for an `count`-step value ladder; a heuristic, so a lower bound on what the palette can do."""
    pal = [(l, c) for l, c in palette_by_lightness() if lo <= l <= hi]
    by_vision = {c: {v: lightness(from_hex(c), v) for v in VISIONS} for _, c in pal}
    best: tuple[float, list[str]] = (0.0, [])
    low, high = 0.0, hi - lo
    for _ in range(40):
        g = (low + high) / 2
        picked: list[str] = []
        for _l, c in pal:
            if all(abs(by_vision[c][v] - by_vision[q][v]) >= g for q in picked for v in VISIONS):
                picked.append(c)
        if len(picked) >= count:
            best, low = (g, picked[:count]), g
        else:
            high = g
    return best


def ladder_sheet(fills: dict[str, str], shapes: dict[str, set] = LADDER_SHAPES) -> dict[str, Sprite]:
    return {g: badge(shapes[g], fills[g]) for g in GRADES}


def _disc(r: float, cx: float = 7.5, cy: float = 7.5) -> set:
    return {(x, y) for x in range(16) for y in range(16) if (x - cx) ** 2 + (y - cy) ** 2 <= r * r}


def _triangle_down() -> set:
    return {(x, y) for y in range(1, 15) for x in range(16) if abs(x - 7.5) <= (14 - y) * 0.55 + 0.5}


def frame(shape: set, fill: str, outline: str = OUTLINE) -> Sprite:
    rgba = []
    for y in range(16):
        for x in range(16):
            if (x, y) not in shape:
                rgba.append((0, 0, 0, 0))
                continue
            edge = any((x + dx, y + dy) not in shape for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            r, g, b = (round(c * 255) for c in from_hex(outline if edge else fill))
            rgba.append((r, g, b, 255))
    return Sprite(16, 16, tuple(rgba))


def plate(rim: str, fill: str = "#3e3d52") -> Sprite:
    rgba = []
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            corner = (x in (0, 15)) and (y in (0, 15))
            if corner:
                rgba.append((0, 0, 0, 0))
                continue
            r, g, b = (round(c * 255) for c in from_hex(rim if edge else fill))
            rgba.append((r, g, b, 255))
    return Sprite(16, 16, tuple(rgba))


def real_tiles() -> dict[str, list]:
    return icon_palette._tiles()


def baseline() -> dict:
    out: dict = {}
    # I1: pixel distances of the ladder mock, plus the two failures the rule must catch
    gap, picked = best_ladder()
    out["palette_best_8_step_ladder_gap_dL"] = round(gap, 2)
    fills = dict(zip(GRADES, picked, strict=True))
    sheet = ladder_sheet(fills)
    out["ladder_fills"] = fills
    out["i1_ladder_pair_px"] = {f"{a}-{b}": shape_distance(sheet[a], sheet[b]) for a, b in itertools.combinations(GRADES, 2)}
    out["i1_ladder_min_across_classes"] = min(v for k, v in out["i1_ladder_pair_px"].items() if k not in ("e-d",))
    out["i1_one_pixel_difference_px"] = shape_distance(badge(OCTAGON, "#555b73"), badge(OCTAGON - {(0, 2)}, "#555b73"))
    buff, debuff = frame(_disc(7), "#48b858"), frame(_triangle_down(), "#d04030")
    out["i1_buff_vs_debuff_px"] = shape_distance(buff, debuff)
    out["i1_recoloured_only_px"] = shape_distance(frame(_disc(7), "#48b858"), frame(_disc(7), "#d04030"))
    # I2: lightness steps
    out["i2_ladder_min_dL_by_vision"] = {v: round(min(value_distance(sheet[a], sheet[b], v) for a, b in itertools.combinations(GRADES, 2)), 2) for v in VISIONS}
    chips = {g: badge(LADDER_SHAPES[g], TODAY_CHIPS[g]) for g in GRADES}
    out["i2_todays_grade_chips_min_dL_by_vision"] = {v: round(min(value_distance(chips[a], chips[b], v) for a, b in itertools.combinations(GRADES, 2)), 2) for v in VISIONS}
    out["i2_todays_grade_chips_pairs_below_8"] = {v: sum(1 for a, b in itertools.combinations(GRADES, 2) if value_distance(chips[a], chips[b], v) < 8.0) for v in VISIONS}
    out["i2_buff_vs_debuff_dL_by_vision"] = {v: round(value_distance(buff, debuff, v), 2) for v in VISIONS}
    # I3: candidate rims against the real terrain-v1 tiles
    tiles = real_tiles()
    means = {k: mean(t) for k, t in tiles.items()}
    out["terrain_tile_L"] = tile_context(tiles)
    rims = {"outline_near_black": OUTLINE, "plate_rim_proposed": "#9ea4b6", "light_rim_a9aebf": "#a9aebf", "mid_rim_8e94a6": "#8e94a6", "bone": "#f0ecd8"}
    out["i3_rim_min_dL_by_vision"] = {}
    for name, rim in rims.items():
        report = evaluate_sheet({}, {}, {name: plate(rim)}, means, Thresholds(RULE.shape_min, RULE.value_min, 0.0))
        row = report["plates"][name]["closest_by_vision"]
        out["i3_rim_min_dL_by_vision"][name] = {v: {"dL": row[v]["dL"], "tile": row[v]["tile"]} for v in VISIONS}
    # palette ramps: the lightness steps the palette itself offers
    pal = icon_palette.build_palette()
    ramp_steps = {}
    for seed in icon_palette.RAMP_SEEDS:
        cols = [e["color"] for e in pal["entries"] if e["role"] == "ramp" and e["source"].startswith(seed + " ")]
        seed_colour = icon_palette.terrain_fills()[seed]
        cols = [c for c in _ramp_order(seed_colour)]
        ramp_steps[seed] = [round(lightness(from_hex(c), "normal"), 1) for c in cols]
    out["palette_ramp_L"] = ramp_steps
    return out


def _ramp_order(seed_colour: str) -> list[str]:
    from visual_assets.drawing.technique.ramps import make_ramp

    return make_ramp(seed_colour, icon_palette.RAMP_STEPS, base_index=icon_palette.RAMP_BASE_INDEX)


if __name__ == "__main__":
    print(json.dumps(baseline(), indent=1))
    _ = (mean_colour,)
