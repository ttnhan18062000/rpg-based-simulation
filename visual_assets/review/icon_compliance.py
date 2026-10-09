"""Spec compliance table: every proportion a spec states, MEASURED from the pixels next to the spec value (`TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW`).

Why: the weapon sword passed naming ("steel sword") and every sheet-rule gate and was still wrong (a short 4 px blade, a lumpy grip wider than the guard, no pommel). Naming catches misreads, not bad
drawing; only measuring the drawing against its spec does. Each redrawn or new icon gets a row per spec proportion here; a row that fails is reported, never tuned away.

Each measurement reads the sprite only (silhouette, content pixels = opaque pixels that are not the dark outline, and a few named wood or bone colours). Pure Python, read-only.

    python -m visual_assets.review.icon_compliance      # prints the markdown tables of the redrawn icons
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import Callable

from visual_assets.review import icon_lookalikes as la
from visual_assets.review import icon_sheet_rule as rule

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


# CHECKS is the table of the adopted art as it stood after the recognisability redraw (r0001: the brick wall, the wrench, the 7 px bead); CHECKS_R2 is the table of the owner-fix revisions (r0002).
CHECKS: dict[str, Callable[[rule.Sprite], list[Row]]] = {
    "icon.item.weapon": sword, "icon.marker.ruins": ruins, "icon.item.trinket": trinket, "icon.item.tool": tool, "icon.class.ranger": ranger, "icon.rarity.common": bead,
}

SILVER, SILVER_LIGHT, SILVER_SHADE = (0xC8, 0xD8, 0xE8), (0xEA, 0xFE, 0xFF), (0x91, 0xA2, 0xAB)
TAN, EMBER, WINE, DARK, GOLD = (0x8E, 0x8C, 0x75), (0xD0, 0x40, 0x30), (0x6A, 0x30, 0x40), (0x25, 0x25, 0x30), (0xE8, 0xC0, 0x40)
STEEL = {(0xC8, 0xD8, 0xE8), (0x91, 0xA2, 0xAB), (0x71, 0x7E, 0x8F)}


def _live_margins(s: rule.Sprite) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox(silhouette(s))
    return x0, y0, s.width - 1 - x1, s.height - 1 - y1


def ruins_arch(s: rule.Sprite) -> list[Row]:
    c = content(s)
    x0, y0, x1, y1 = bbox(silhouette(s))
    bottom = max(y for (_, y) in c)
    # the height of a column is the unbroken run of stone standing on the bottom row: a pillar's is >= 8, the stub's 3 to 5, loose bricks and the arch's loose end are 1 or 0
    heights: dict[int, int] = {}
    for x in sorted({x for x, _ in c}):
        run = 0
        while (x, bottom - run) in c:
            run += 1
        heights[x] = run
    pillar = sorted(x for x, h in heights.items() if h >= 8)
    stub = sorted(x for x, h in heights.items() if 3 <= h <= 5 and x > max(pillar))
    top = min(y for (x, y) in c if x in pillar)
    mid_rows = range(top + 3, bottom - 1)
    gap = [x for x in range(max(pillar) + 1, min(stub)) if not any((x, y) in c for y in mid_rows)]
    arch = [p for p in c if p[0] > max(pillar) and p[1] <= top + 2]
    rubble = [p for p in c if p[0] in gap and p[1] >= bottom - 1]
    mx = _live_margins(s)
    return [
        Row("size", "12 px wide and 11 px tall, outline included", f"{x1 - x0 + 1} x {y1 - y0 + 1} px", (x1 - x0 + 1, y1 - y0 + 1) == (12, 11)),
        Row("tall left pillar", ">= 3 columns that are >= 8 px tall", f"{len(pillar)} columns, tallest {max(heights[x] for x in pillar)} px", len(pillar) >= 3),
        Row("springing arch", ">= 3 stone pixels to the right of the pillar in its top three rows", f"{len(arch)} px", len(arch) >= 3),
        Row("open gap", ">= 4 columns with no stone between the pillar and the stub", f"{len(gap)} columns", len(gap) >= 4),
        Row("broken right stub", ">= 3 columns that are 3 to 5 px tall, to the right of the gap", f"{len(stub)} columns", len(stub) >= 3),
        Row("rubble", ">= 2 loose pixels on the ground in the gap", f"{len(rubble)} px", len(rubble) >= 2),
        Row("live area", "margins of at least 2 px left, top and right on the 16x16 canvas", f"{mx[0]}, {mx[1]}, {mx[2]} px", min(mx[0], mx[1], mx[2]) >= 2),
    ]


def silver_bead(s: rule.Sprite) -> list[Row]:
    sil, c = silhouette(s), content(s)
    x0, y0, x1, y1 = bbox(sil)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    fill = len(sil) / (w * h)
    counts = {k: sum(1 for v in c.values() if v == k) for k in (SILVER, SILVER_LIGHT, SILVER_SHADE)}
    sprites = la.all_icon_sprites()
    mine = rule.lightness(rule.mean_colour(s), "normal")
    dark_tiers = {t: rule.lightness(rule.mean_colour(sprites[t]), "normal") for t in ("icon.tier.d", "icon.tier.e")}
    gap = min(mine - v for v in dark_tiers.values())
    near = min(rule.shape_distance(s, sprites[t]) for t in TIERS)
    return [
        Row("round, not square", "silhouette fills at most 80 % of its bounding box", f"{100 * fill:.0f} %", fill <= 0.80),
        Row("size", "7 x 7 px", f"{w} x {h} px", (w, h) == (7, 7)),
        Row("silver fill", ">= 12 px of silver (#c8d8e8)", f"{counts[SILVER]} px", counts[SILVER] >= 12),
        Row("highlight", "2 px of bright highlight (#eafeff)", f"{counts[SILVER_LIGHT]} px", counts[SILVER_LIGHT] == 2),
        Row("shade", ">= 4 px of shade (#91a2ab) on the lower right", f"{counts[SILVER_SHADE]} px", counts[SILVER_SHADE] >= 4),
        Row("lighter than the dark tier badges", "mean L* at least 20 above tier D and tier E", f"{gap:.1f} L* above the nearer one", gap >= 20),
        Row("distance from the tier badges", ">= 3 px (I1 floor) from every tier silhouette", f"{near} px", near >= 3),
    ]


def buff_arrow(s: rule.Sprite) -> list[Row]:
    before = la.all_icon_sprites()["icon.status.frame_buff"]
    changed = [(i % 16, i // 16) for i in range(256) if s.rgba[i] != before.rgba[i]]
    outside = [p for p in changed if not (4 <= p[0] <= 11 and 3 <= p[1] <= 11)]
    bone = sorted((i % 16, i // 16) for i, p in enumerate(s.rgba) if tuple(p[:3]) == (0xF0, 0xEC, 0xD8) and p[3])
    widths = [sum(1 for x, yy in bone if yy == y) for y in sorted({y for _, y in bone})]
    xs = [x for x, _ in bone]
    return [
        Row("frame unchanged", "no pixel outside the central 8 x 9 box differs from the adopted frame", f"{len(outside)} pixels differ outside the box ({len(changed)} in all)", not outside),
        Row("solid head", "head rows 2, 4 then 6 px wide", f"first rows {widths[:3]}", widths[:3] == [2, 4, 6]),
        Row("shaft", "2 px wide and 5 px tall below the head", f"rows {widths[3:]}", widths[3:] == [2] * 5),
        Row("solid, not an outline", "22 bone pixels in all, one filled shape", f"{len(bone)} px in {len(components(set(bone)))} piece(s)", len(bone) == 22 and len(components(set(bone))) == 1),
        Row("centred", "the arrow's columns centre on the canvas axis", f"columns {min(xs)} to {max(xs)} of 16", min(xs) + max(xs) == 15),
    ]


def rogue_hood(s: rule.Sprite) -> list[Row]:
    c = content(s)
    w = row_widths(c)
    ys = sorted(w)
    dark = [p for p, col in c.items() if col == DARK]
    dx0, dy0, dx1, dy1 = bbox(dark)
    gold = [p for p, col in c.items() if col == GOLD]
    narrowing = all(w[a] <= w[b] for a, b in zip(ys[:12], ys[1:13]))
    mx = _live_margins(s)
    return [
        Row("peaked hood", "the top row is 2 px wide or less and rows widen steadily to the shoulders", f"top row {w[ys[0]]} px; widest {max(w.values())} px; steady widening over the first 12 rows: {narrowing}", w[ys[0]] <= 2 and narrowing),
        Row("shoulders", "widest row 18 px", f"{max(w.values())} px", max(w.values()) == 18),
        Row("face opening", ">= 8 px wide and >= 8 px tall, dark", f"{dx1 - dx0 + 1} x {dy1 - dy0 + 1} px, {len(dark)} px", dx1 - dx0 + 1 >= 8 and dy1 - dy0 + 1 >= 8),
        Row("eye glints", "two separate gold marks of 2 px", f"{len(gold)} px in {len(components(set(gold)))} marks", len(gold) == 4 and len(components(set(gold))) == 2),
        Row("no brim", "the hood is never wider than the shoulders at its top half (a hat has a brim): the first 10 rows are at most 14 px wide", f"widest of the first 10 rows {max(w[y] for y in ys[:10])} px", max(w[y] for y in ys[:10]) <= 14),
        Row("live area", "margins of at least 2 px left, top and right on the 24x24 canvas", f"{mx[0]}, {mx[1]}, {mx[2]} px", min(mx[0], mx[1], mx[2]) >= 2),
    ]


def enemy_tent(s: rule.Sprite) -> list[Row]:
    c = content(s)
    x0, y0, x1, y1 = bbox(silhouette(s))
    tent = [p for p, col in c.items() if col in (EMBER, WINE)]
    door = [p for p, col in c.items() if col == DARK]
    tan = [p for p, col in c.items() if col == TAN]
    heads = components({p for p, col in c.items() if col in STEEL})
    mx = _live_margins(s)
    tx0, ty0, tx1, ty1 = bbox(tent)
    return [
        Row("live area", "margins of at least 2 px on all four sides of the 16x16 canvas", f"{mx[0]}, {mx[1]}, {mx[2]}, {mx[3]} px", min(mx) >= 2),
        Row("tent", "a peaked tent at least 8 px wide and 4 px tall in red (the fitted tent; the first, larger one was 9 wide)", f"{tx1 - tx0 + 1} x {ty1 - ty0 + 1} px, {len(tent)} px", tx1 - tx0 + 1 >= 8 and ty1 - ty0 + 1 >= 4),
        Row("doorway", ">= 4 dark pixels inside the tent (the fitted tent; the first one had 6)", f"{len(door)} px", len(door) >= 4),
        Row("two spear heads", "two separate steel heads of at least 4 px", f"{len(heads)} heads, {[len(h) for h in heads]} px", len(heads) == 2 and all(len(h) >= 4 for h in heads)),
        Row("crossed shafts", ">= 14 shaft pixels forming an X above the apex (reaching both sides in the top rows)", f"{len(tan)} px, columns {min(p[0] for p in tan)} to {max(p[0] for p in tan)}", len(tan) >= 14 and min(p[0] for p in tan) <= 4 and max(p[0] for p in tan) >= 11 and min(p[1] for p in tan) < ty0),
        Row("no sword", "no blade: the shafts are tan and the heads are 2 x 2", f"head sizes {[len(h) for h in heads]}", all(len(h) <= 6 for h in heads)),
    ]


def hammer_tongs(s: rule.Sprite) -> list[Row]:
    c = content(s)
    x0, y0, x1, y1 = bbox(silhouette(s))
    wood = [p for p, col in c.items() if col in WOOD]
    steel = [p for p, col in c.items() if col in STEEL]
    rivet = [p for p, col in c.items() if col == GOLD]
    head = [p for p in steel if p[0] > 11 and p[1] < 11]
    jaws = [p for p in steel if p[0] < 9 and p[1] < 9]
    pieces = components(set(c))
    mx = _live_margins(s)
    return [
        Row("size", "19 px wide and 19 px tall, outline included (an X, not a long weapon)", f"{x1 - x0 + 1} x {y1 - y0 + 1} px", (x1 - x0 + 1, y1 - y0 + 1) == (19, 19)),
        Row("live area", "margins of at least 2 px on all four sides of the 24x24 canvas", f"{mx[0]}, {mx[1]}, {mx[2]}, {mx[3]} px", min(mx) >= 2),
        Row("wooden handle", ">= 14 px of wood colour (the hammer's handle)", f"{len(wood)} px", len(wood) >= 14),
        Row("steel hammer head", ">= 20 steel pixels in the top right (a short heavy head; the outline the owner approved gives 22)", f"{len(head)} px", len(head) >= 20),
        Row("tong jaws", ">= 8 steel pixels in the top left (the closed jaws)", f"{len(jaws)} px", len(jaws) >= 8),
        Row("rivet at the crossing", "a gold rivet of at least 8 px", f"{len(rivet)} px", len(rivet) >= 8),
        Row("crossed, one piece", "the two tools touch: all content is one connected piece", f"{len(pieces)} piece(s)", len(pieces) == 1),
    ]


THATCH_C, THATCH2_C, CREAM_C, BROWN_C, DOOR_C, SHUTTER_C, MODERN_BLUE = (0xC7, 0xB0, 0x4F), (0xA8, 0x70, 0x22), (0xF0, 0xEC, 0xD8), (0x5A, 0x2A, 0x1A), (0x8A, 0x30, 0x00), (0x4A, 0x60, 0x30), (0x50, 0xA8, 0xE0)


def cottage(s: rule.Sprite) -> list[Row]:
    c = content(s)
    x0, y0, x1, y1 = bbox(silhouette(s))
    n = lambda col: sum(1 for v in c.values() if v == col)  # noqa: E731
    panes = components({p for p, v in c.items() if v == DARK})
    shutters = components({p for p, v in c.items() if v == SHUTTER_C})
    colours = len(set(c.values())) + 1
    return [
        Row("size", "20 px wide and 20 px tall, outline included", f"{x1 - x0 + 1} x {y1 - y0 + 1} px", (x1 - x0 + 1, y1 - y0 + 1) == (20, 20)),
        Row("thatched roof", ">= 80 px of thatch (two golds; the approved outline gives 84)", f"{n(THATCH_C) + n(THATCH2_C)} px", n(THATCH_C) + n(THATCH2_C) >= 80),
        Row("timber frame", ">= 40 px of timber brown", f"{n(BROWN_C)} px", n(BROWN_C) >= 40),
        Row("plaster walls", ">= 30 px of cream plaster (the approved outline gives 36)", f"{n(CREAM_C)} px", n(CREAM_C) >= 30),
        Row("small windows with dark panes", "two separate dark panes of 4 px", f"{len(panes)} panes {[len(p) for p in panes]}", len(panes) == 2 and all(len(p) == 4 for p in panes)),
        Row("shutters", "four separate green shutter strips", f"{len(shutters)} strips", len(shutters) == 4),
        Row("arched wooden door", ">= 20 px of door wood", f"{n(DOOR_C)} px", n(DOOR_C) >= 20),
        Row("no modern blue glass", "no pixel of the old window blue (#50a8e0)", f"{n(MODERN_BLUE)} px", n(MODERN_BLUE) == 0),
        Row("palette", "within the 24x24 budget of 12 colours (outline included)", f"{colours}", colours <= 12),
    ]


def spiked_debuff(s: rule.Sprite) -> list[Row]:
    import math

    c = content(s)
    sil = silhouette(s)
    x0, y0, x1, y1 = bbox(sil)
    red = {p for p, v in c.items() if v == EMBER}
    # a spike in each of the eight compass directions: red pixels beyond the ring, grouped by the 45-degree sector round the canvas centre (a diagonal spike rasterises into two loose pixels, so counting pieces would say twelve)
    tips = [q for q in red if math.hypot(q[0] + 0.5 - 8, q[1] + 0.5 - 8) > 6.2]
    spikes = sorted({round(math.degrees(math.atan2(q[1] + 0.5 - 8, q[0] + 0.5 - 8)) / 45) % 8 for q in tips})
    bone = {p for p, v in c.items() if v == (0xF0, 0xEC, 0xD8)}
    widths = [sum(1 for x, yy in bone if yy == y) for y in sorted({y for _, y in bone})]
    fill = len(sil) / ((x1 - x0 + 1) * (y1 - y0 + 1))
    flipped = {(15 - x, y) for x, y in sil}
    buff = la.all_icon_sprites()["icon.status.frame_buff"]
    diff = rule.shape_distance(s, buff)
    return [
        Row("size", "16 x 16 px, filling its canvas like the buff frame", f"{x1 - x0 + 1} x {y1 - y0 + 1} px", (x1 - x0 + 1, y1 - y0 + 1) == (16, 16)),
        Row("eight spikes", "a red spike beyond the ring in each of the eight compass directions", f"spikes in {len(spikes)} of 8 directions", len(spikes) == 8),
        Row("red rim", ">= 40 red pixels", f"{len(red)} px", len(red) >= 40),
        Row("solid down arrow", "20 bone pixels in one piece: a shaft 2 wide and 4 tall, then a head 6, 4 and 2 wide", f"{len(bone)} px, row widths {widths}", len(bone) == 20 and widths == [2, 2, 2, 2, 6, 4, 2] and len(components(bone)) == 1),
        Row("not a triangle (not a road sign)", "the silhouette fills at least 60 % of its bounding box (a triangle fills 50 %)", f"{100 * fill:.0f} %", fill >= 0.60),
        Row("symmetric", "the silhouette is mirror-symmetric left to right", f"{len(sil ^ flipped)} differing px", sil == flipped),
        Row("differs from the round buff frame", ">= 6 px (I1 at 16x16)", f"{diff} px", diff >= 6),
    ]


def tankard(s: rule.Sprite) -> list[Row]:
    before = la.all_icon_sprites()["icon.building.inn"]
    same_outline = silhouette(s) == silhouette(before)
    c = content(s)
    seam_cols = sorted({x for x in range(24) if sum(1 for y in range(10, 19) if c.get((x, y)) == BROWN_C) >= 7})
    hoops = [y for y in range(24) if sum(1 for x in range(24) if c.get((x, y)) == (0x55, 0x5B, 0x73)) >= 9]
    outside = [i for i in range(576) if s.rgba[i] != before.rgba[i] and not (5 <= i % 24 <= 15 and 10 <= i // 24 <= 18)]
    return [
        Row("same outline", "the silhouette is exactly the adopted tankard's", f"{len(silhouette(s) ^ silhouette(before))} differing px", same_outline),
        Row("stave seams", ">= 2 vertical dark brown seams of at least 7 px", f"columns {seam_cols}", len(seam_cols) >= 2),
        Row("iron hoops", "two steel-grey rows of at least 9 px", f"rows {hoops}", len(hoops) == 2),
        Row("foam and handle untouched", "no pixel outside the body box differs from the adopted drawing", f"{len(outside)} px differ outside the body", not outside),
    ]


CHECKS_R2: dict[str, Callable[[rule.Sprite], list[Row]]] = {
    "icon.marker.ruins": ruins_arch, "icon.rarity.common": silver_bead, "icon.status.frame_buff": buff_arrow, "icon.class.rogue": rogue_hood, "icon.marker.enemy_camp": enemy_tent,
    "icon.item.tool": hammer_tongs, "icon.building.hero_house": cottage, "icon.status.frame_debuff": spiked_debuff, "icon.building.inn": tankard,
}


def measure(sprites: dict[str, rule.Sprite], keys=None, checks=None) -> dict[str, list[Row]]:
    checks = CHECKS if checks is None else checks
    out = {}
    for k in keys or checks:
        try:
            out[k] = checks[k](sprites[k])
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
