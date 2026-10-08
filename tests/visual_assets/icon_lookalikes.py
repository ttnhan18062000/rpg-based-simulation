"""Whole-sheet look-alike report: for every icon, its nearest neighbours across ALL families by silhouette (`TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS`). Deterministic, report-only.

The sheet rule (I1) compares silhouettes only inside a group of icons that share a panel; this report compares every icon with every other one, so a cross-family twin surfaces (the weapon sword and
the rogue dagger passed every gate and still read alike). Report only: no threshold here fails a build, and no icon is changed because of it; a person decides what a close pair means.

Method (so the numbers can be reproduced): each silhouette (every pixel with alpha > 0) is cropped to its bounding box, scaled by nearest neighbour so that it fits a 24x24 canvas, keeping its aspect
ratio, and centred. The distance of two icons is the number of canvas pixels in exactly one silhouette (XOR) out of 576, so size differences between a 8x8 badge and a 24x24 panel icon do not hide a
shared shape; the same measure at the icons' own size is I1's. Pairs are listed nearest first.

    python -m tests.visual_assets.icon_lookalikes      # prints the report as JSON for the 14 adopted and the 22 v2 icons
"""

from __future__ import annotations

import itertools
import json
import sys

from tests.visual_assets import icon_draft_set as keyset
from tests.visual_assets import icon_sheet_rule as rule
from tests.visual_assets import icon_v2_draft_set as v2set

CANVAS = 24
CLOSE = 60  # pairs at or under this many XOR pixels (about a tenth of the canvas) are listed as "close"; a reading aid, not a pass or fail


def normalised(sprite: rule.Sprite, canvas: int = CANVAS) -> frozenset[tuple[int, int]]:
    cells = [(i % sprite.width, i // sprite.width) for i, p in enumerate(sprite.rgba) if p[3]]
    if not cells:
        return frozenset()
    x0, x1 = min(c[0] for c in cells), max(c[0] for c in cells)
    y0, y1 = min(c[1] for c in cells), max(c[1] for c in cells)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    scale = min(canvas / w, canvas / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    ox, oy = (canvas - nw) // 2, (canvas - nh) // 2
    solid = set(cells)
    out = set()
    for ty in range(nh):
        for tx in range(nw):
            sx, sy = x0 + min(w - 1, int(tx / scale)), y0 + min(h - 1, int(ty / scale))
            if (sx, sy) in solid:
                out.add((ox + tx, oy + ty))
    return frozenset(out)


def distance(a: frozenset, b: frozenset) -> int:
    return len(a ^ b)


def all_icon_sprites() -> dict[str, rule.Sprite]:
    """The 14 adopted icons (kept drafts of `icons-key-v1`, plate included) and the 22 v2 drafts."""
    return {**keyset.draft_sprites(), **v2set.v2_sprites()}


def family_of(key: str) -> str:
    return key.split(".")[1]


def report(sprites: dict[str, rule.Sprite], neighbours: int = 3, close: int = CLOSE) -> dict:
    shapes = {k: normalised(s) for k, s in sprites.items()}
    pairs = sorted(((distance(shapes[a], shapes[b]), a, b) for a, b in itertools.combinations(sorted(shapes), 2)))
    nearest = {}
    for key in sorted(shapes):
        mine = sorted((distance(shapes[key], shapes[o]), o) for o in shapes if o != key)[:neighbours]
        nearest[key] = [{"key": o, "xor_px": d, "cross_family": family_of(o) != family_of(key)} for d, o in mine]
    return {
        "method": f"bounding box fitted to {CANVAS}x{CANVAS} by nearest neighbour, XOR pixels out of {CANVAS * CANVAS}; report only",
        "close_threshold_xor_px": close,
        "icons": len(shapes),
        "close_pairs": [{"a": a, "b": b, "xor_px": d, "cross_family": family_of(a) != family_of(b)} for d, a, b in pairs if d <= close],
        "closest_cross_family_pairs": [{"a": a, "b": b, "xor_px": d} for d, a, b in pairs if family_of(a) != family_of(b)][:10],
        "nearest": nearest,
    }


if __name__ == "__main__":
    if "--proposed" in sys.argv:  # the set with the owner-fix revisions (icons-owner-fixes-v1) in place of the adopted r0001 drawings
        from tests.visual_assets import icon_owner_fixes_draft_set

        print(json.dumps(report(icon_owner_fixes_draft_set.proposed_sprites()), indent=1))
    else:
        print(json.dumps(report(all_icon_sprites()), indent=1))
    sys.exit(0)
