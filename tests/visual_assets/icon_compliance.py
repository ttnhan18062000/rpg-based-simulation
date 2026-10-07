"""Spec compliance table: every proportion a spec states, MEASURED from the pixels next to the spec value (`TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW`).

Why: the weapon sword passed naming ("steel sword") and every sheet-rule gate and was still wrong (a short 4 px blade, a lumpy grip wider than the guard, no pommel). Naming catches misreads, not bad
drawing; only measuring the drawing against its spec does. Each redrawn or new icon gets a row per spec proportion here; a row that fails is reported, never tuned away.

Each measurement reads the sprite only (silhouette, content pixels = opaque pixels that are not the dark outline, and a few named wood or bone colours). Pure Python, read-only.

    python -m tests.visual_assets.icon_compliance      # prints the markdown tables of the redrawn icons
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import Callable

from tests.visual_assets import icon_lookalikes as la
from tests.visual_assets import icon_sheet_rule as rule

OUTLINE = (0x0E, 0x10, 0x18)
WOOD = {(0x5A, 0x2A, 0x1A), (0x8E, 0x8C, 0x75)}  # the two bow-limb colours (brown and tan)
BONE = (0xF0, 0xEC, 0xD8)
GEM = (0x50, 0xA8, 0xE0)
TIERS = tuple(f"icon.tier.{t}" for t in ("e", "d", "c", "b", "a", "s", "ss", "sss"))


@dataclass(frozen=True)
class Row:
    item: str
    spec: str
    measured: str
    ok: bool


def content(s: rule.Sprite) -> dict[tuple[int, int], tuple[int, int, int]]:
    out = {}
    for i, p in enumerate(s.rgba):
        if p[3] and tuple(p[:3]) != OUTLINE:
            out[(i % s.width, i // s.width)] = tuple(p[:3])
    return out


def silhouette(s: rule.Sprite) -> set[tuple[int, int]]:
    return {(i % s.width, i // s.width) for i, p in enumerate(s.rgba) if p[3]}


def bbox(cells) -> tuple[int, int, int, int]:
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return min(xs), min(ys), max(xs), max(ys)


def row_widths(cells) -> dict[int, int]:
    out: dict[int, int] = {}
    for _, y in cells:
        out[y] = out.get(y, 0) + 1
    return out


def components(cells) -> list[set]:
    left, out = set(cells), []
    while left:
        stack, comp = [left.pop()], set()
        while stack:
            x, y = stack.pop()
            comp.add((x, y))
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in left:
                    left.discard(n)
                    stack.append(n)
        out.append(comp)
    return out


def _in(lo: float, value: float, hi: float) -> bool:
    return lo <= value <= hi


def sword(s: rule.Sprite) -> list[Row]:
    sil, c = silhouette(s), content(s)
    x0, y0, x1, y1 = bbox(sil)
    total = y1 - y0 + 1
    w = row_widths(c)
    ys = sorted(w)
    guard = [y for y in ys if w[y] >= 9]
    g0 = guard[0]
    blade_rows = [y for y in ys if y < g0]
    below = [y for y in ys if y > guard[-1]]
    grip_rows = []
    for y in below:  # the grip is the run of equally wide rows right under the guard; whatever follows is the pommel (if it is wider than the grip)
        if grip_rows and w[y] != w[grip_rows[0]]:
            break
        grip_rows.append(y)
    pommel = [y for y in below if y > grip_rows[-1] and w[y] > w[grip_rows[0]]]
    blade_w = max(w[y] for y in blade_rows)
    top_w = w[blade_rows[0]]
    axis = sum(x for x, _ in c) / len(c)
    return [
        Row("orientation", "upright, point up, centred on the vertical axis", f"height {total} px, width {x1 - x0 + 1} px, tip row {top_w} px wide, content centre x {axis:.1f} of canvas centre {(s.width - 1) / 2:.1f}", total > x1 - x0 + 1 and top_w <= 2 and abs(axis - (s.width - 1) / 2) <= 1.0),
        Row("total height", "20 px", f"{total} px", total == 20),
        Row("blade length", ">= 60 % of the total height", f"{len(blade_rows)} px = {100 * len(blade_rows) / total:.0f} %", len(blade_rows) / total >= 0.60),
        Row("blade width", "3 to 4 px", f"{blade_w} px", _in(3, blade_w, 4)),
        Row("crossguard width", "9 to 12 px", f"{max(w[y] for y in guard)} px", _in(9, max(w[y] for y in guard), 12)),
        Row("crossguard thickness", "2 px", f"{len(guard)} px", len(guard) == 2),
        Row("grip width", "never wider than the guard or the blade", f"{max(w[y] for y in grip_rows) if grip_rows else 'none'} px (guard {max(w[y] for y in guard)}, blade {blade_w})", bool(grip_rows) and max(w[y] for y in grip_rows) <= min(max(w[y] for y in guard), blade_w)),
        Row("grip length", "2 to 3 px", f"{len(grip_rows)} px", _in(2, len(grip_rows), 3)),
        Row("pommel", "present, wider than the grip", f"{len(pommel)} row(s), {max((w[y] for y in pommel), default=0)} px wide", bool(pommel) and max(w[y] for y in pommel) > max(w[y] for y in grip_rows)),
    ]


def ruins(s: rule.Sprite) -> list[Row]:
    c = content(s)
    w = row_widths(c)
    wall_bottom = max(y for y in w if w[y] >= 8)
    tops: dict[int, int] = {}
    anchored = set()
    for x in sorted({x for x, _ in c}):
        y = wall_bottom
        while (x, y) in c:
            anchored.add((x, y))
            y -= 1
        if (x, wall_bottom) in c:
            tops[x] = y + 1
    column = min(tops, key=lambda x: (tops[x], x))
    seq = [c[(column, y)] for y in range(tops[column], wall_bottom + 1)]
    bands = [k for i, k in enumerate(seq) if i == 0 or seq[i - 1] != k]
    order = [tops[x] for x in sorted(tops)]
    steps = sorted(set(order))
    monotone = order == sorted(order) or order == sorted(order, reverse=True)
    loose = [g for g in components({p for p in c if p not in anchored}) if len(g) >= 2]
    slab = [y for y in w if y > wall_bottom]
    return [
        Row("brick courses", ">= 4 alternating light and dark rows (read down the tallest column)", f"{len(bands)} colour bands", len(bands) >= 4 and all(bands[i] != bands[i + 1] for i in range(len(bands) - 1))),
        Row("broken top edge: distinct heights", ">= 3 column heights", f"{len(steps)} ({steps})", len(steps) >= 3),
        Row("broken top edge: U-shaped, not a slope", "heights go up and down (not monotone) and the middle is lower than both ends", f"heights left to right {order}", not monotone and max(order[len(order) // 3 : 2 * len(order) // 3 + 1]) > max(order[0], order[-1])),
        Row("fallen brick", ">= 1 loose group of 2 px or more, not part of the wall", f"{len(loose)} ({[len(g) for g in loose]} px)", len(loose) >= 1),
        Row("nothing under the wall", "no ground slab or matched pair of bricks below the wall's bottom course", f"{len(slab)} row(s) below the wall's bottom row", len(slab) == 0),
        Row("wall width", "about 10 px", f"{max(w.values())} px", _in(9, max(w.values()), 12)),
    ]


def trinket(s: rule.Sprite) -> list[Row]:
    c = content(s)
    w = row_widths(c)
    ys = sorted(w)
    per_row = {y: components({p for p in c if p[1] == y}) for y in ys}
    # the pendant begins at the first row below the ring where the two chain strands have merged into one run of 4 px or more
    pend0 = next(y for y in ys if y > ys[0] + 3 and len(per_row[y]) == 1 and len(per_row[y][0]) >= 4)
    pend = [y for y in ys if y >= pend0]
    chain_rows = [y for y in ys if ys[0] + 3 < y < pend0]
    longest = max((len(r) for y in chain_rows for r in per_row[y]), default=0)
    two = sum(1 for y in chain_rows if len(per_row[y]) == 2)
    gem = [p for p, col in c.items() if col == GEM or col == (0x2A, 0x50, 0x70)]
    gx0, gy0, gx1, gy1 = bbox(gem)
    cx0, _, cx1, _ = bbox({p for p in c if p[1] in chain_rows})
    return [
        Row("bail ring at the apex", "a ring of 4 px or less at the top row", f"top row {w[ys[0]]} px wide", w[ys[0]] <= 4),
        Row("chain thickness", "1 px strands (never a ribbon)", f"longest horizontal run in the chain rows {longest} px", longest <= 2),
        Row("chain loop", "two separate strands from the apex down to the pendant", f"{two} of {len(chain_rows)} chain rows have 2 strands", two >= len(chain_rows) - 1),
        Row("chain loop width", "wider than the pendant's neck so it rises to a point: >= 12 px", f"{cx1 - cx0 + 1} px", cx1 - cx0 + 1 >= 12),
        Row("pendant width", ">= 9 px", f"{max(w[y] for y in pend)} px", max(w[y] for y in pend) >= 9),
        Row("pendant height", ">= 8 px", f"{len(pend)} px", len(pend) >= 8),
        Row("gem", ">= 5 px wide and >= 4 px tall", f"{gx1 - gx0 + 1} x {gy1 - gy0 + 1} px", gx1 - gx0 + 1 >= 5 and gy1 - gy0 + 1 >= 4),
    ]


def _axis(cells) -> tuple[float, float]:
    n = len(cells)
    mx, my = sum(x for x, _ in cells) / n, sum(y for _, y in cells) / n
    sxx = sum((x - mx) ** 2 for x, _ in cells) / n
    syy = sum((y - my) ** 2 for _, y in cells) / n
    sxy = sum((x - mx) * (y - my) for x, y in cells) / n
    tr, det = sxx + syy, sxx * syy - sxy * sxy
    l1, l2 = tr / 2 + math.sqrt(max(tr * tr / 4 - det, 0)), tr / 2 - math.sqrt(max(tr * tr / 4 - det, 0))
    angle = 0.5 * math.degrees(math.atan2(-2 * sxy, sxx - syy))  # image y points down: positive angle = rises to the right
    return angle, math.sqrt(l1 / max(l2, 1e-9))


def _hull_area(cells) -> int:
    pts = sorted({(x + dx, y + dy) for x, y in cells for dx in (0, 1) for dy in (0, 1)})

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return round(abs(sum(hull[i][0] * hull[(i + 1) % len(hull)][1] - hull[(i + 1) % len(hull)][0] * hull[i][1] for i in range(len(hull)))) / 2)


def tool(s: rule.Sprite) -> list[Row]:
    c = content(s)
    cells = set(c)
    angle, elong = _axis(cells)
    x0, y0, x1, y1 = bbox(silhouette(s))
    solidity = len(cells) / _hull_area(cells)
    # a hole is drawn in the outline colour (the style has no see-through pixels inside an icon): a group of outline-coloured pixels with no transparent neighbour
    sil = silhouette(s)
    ink = {p for p in sil if p not in c}
    enclosed = [comp for comp in components(ink) if all(n in sil for x, y in comp for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))]
    return [
        Row("orientation", "diagonal: long axis rises to the right at 35 to 55 degrees", f"{angle:.0f} degrees", _in(35, angle, 55)),
        Row("elongation", "long axis at least 2 times the short axis", f"{elong:.1f}", elong >= 2.0),
        Row("open jaw", "a notch in the head: solidity (pixels over convex hull) at most 0.90", f"{solidity:.2f}", solidity <= 0.90),
        Row("hole in the handle end", ">= 1 enclosed hole (outline-coloured, no transparent neighbour)", f"{len(enclosed)} ({[len(e) for e in enclosed]} px)", len(enclosed) >= 1),
    ]


def ranger(s: rule.Sprite) -> list[Row]:
    c = content(s)
    sil = silhouette(s)
    x0, y0, x1, y1 = bbox(sil)
    wood = {p for p, col in c.items() if col in WOOD}
    wx0, wy0, wx1, wy1 = bbox(wood)
    string = [p for p, col in c.items() if col == BONE]
    # the longest horizontal content run and its thickness: a stock would be a thick bar, an arrow shaft is one row
    runs = []
    for y in range(s.height):
        xs = sorted(x for (x, yy) in c if yy == y)
        best = cur = 1 if xs else 0
        for a, b in zip(xs, xs[1:]):
            cur = cur + 1 if b == a + 1 else 1
            best = max(best, cur)
        runs.append(best)
    long_rows = [y for y, r in enumerate(runs) if r >= 8]
    tip_x = [x for x, y in wood if y in (wy0, wy1)]
    belly = max(x for x, _ in wood)
    deviation = belly - (sum(tip_x) / len(tip_x))
    return [
        Row("orientation", "vertical bow, at least 18 px tall", f"{wy1 - wy0 + 1} px tall (whole icon {y1 - y0 + 1})", wy1 - wy0 + 1 >= 18),
        Row("curved limbs", "the belly stands at least 4 px away from the line between the tips", f"{deviation:.0f} px", deviation >= 4),
        Row("string", ">= 14 visible string pixels", f"{len(string)} px", len(string) >= 14),
        Row("arrow nocked", "a horizontal shaft of at least 12 px that crosses the bow", f"longest run {max(runs)} px", max(runs) >= 12),
        Row("no stock or bar", "no horizontal bar thicker than 2 rows", f"{len(long_rows)} row(s) with a run of 8 px or more", len(long_rows) <= 2),
    ]


def bead(s: rule.Sprite) -> list[Row]:
    sil, c = silhouette(s), content(s)
    x0, y0, x1, y1 = bbox(sil)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    fill = len(sil) / (w * h)
    base = {col for col in c.values()}
    hi = [p for p, col in c.items() if sum(col) > 3 * 0x80]
    sprites = la.all_icon_sprites()
    near = min(rule.shape_distance(s, sprites[t]) for t in TIERS)
    return [
        Row("round, not square", "silhouette fills at most 80 % of its bounding box (a circle is 79 %, a square 100 %, an octagon about 88 %)", f"{100 * fill:.0f} %", fill <= 0.80),
        Row("size", "7 px across (never the tier's 8)", f"{w} x {h} px", w == 7 and h == 7),
        Row("highlight", "one lighter pixel inside", f"{len(hi)} lighter pixel(s) among {len(base)} fills", len(hi) == 1),
        Row("distance from the tier badges", ">= 3 px (I1 floor) from every tier silhouette", f"{near} px", near >= 3),
    ]


CHECKS: dict[str, Callable[[rule.Sprite], list[Row]]] = {
    "icon.item.weapon": sword, "icon.marker.ruins": ruins, "icon.item.trinket": trinket, "icon.item.tool": tool, "icon.class.ranger": ranger, "icon.rarity.common": bead,
}


def measure(sprites: dict[str, rule.Sprite], keys=None) -> dict[str, list[Row]]:
    out = {}
    for k in keys or CHECKS:
        try:
            out[k] = CHECKS[k](sprites[k])
        except (ValueError, KeyError, IndexError, ZeroDivisionError) as exc:  # a drawing so far from its spec that a part cannot even be found
            out[k] = [Row("measurable", "every part named in the spec can be found in the pixels", f"could not be measured ({type(exc).__name__}: {exc})", False)]
    return out


def markdown(rows: dict[str, list[Row]]) -> str:
    out = []
    for key, rs in rows.items():
        out += [f"**`{key}`**: {'all measurements within the spec' if all(r.ok for r in rs) else 'SPEC NOT MET'}", "", "| Measurement | Spec | Measured from the pixels | |", "|---|---|---|---|"]
        out += [f"| {r.item} | {r.spec} | {r.measured} | {'ok' if r.ok else '**FAIL**'} |" for r in rs]
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    rows = measure(la.all_icon_sprites())
    sys.stdout.write(markdown(rows))
    sys.exit(0 if all(r.ok for rs in rows.values() for r in rs) else 1)
