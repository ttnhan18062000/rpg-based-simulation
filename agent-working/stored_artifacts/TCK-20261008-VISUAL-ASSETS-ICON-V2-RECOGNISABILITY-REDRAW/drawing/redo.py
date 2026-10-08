from canvas import Canvas, K
from pan import S1, S2, S3, S4, S5, DARK, BONE, SNOW2, GOLD, GOLD2, DGOLD, BROWN, TAN, EMBER, WINE, SKY, LEAF, GRASS
def weapon():
    """Sword to spec: upright, point up, 20 px tall; blade 12 px (60%) x 4 px with a light centre line; 12 px gold crossguard 2 thick; 2 px grip (narrower than the guard); 4x2 gold pommel."""
    c = Canvas(24)
    c.rect(11, 3, 2, 1, S4)                                   # 2 px tip
    c.rect(10, 4, 4, 11, S3); c.rect(10, 4, 1, 11, S4); c.rect(13, 4, 1, 11, S1); c.rect(11, 5, 1, 9, S5)   # blade y3..14, edge light left, shade right, light centre line
    c.rect(6, 15, 12, 1, GOLD); c.rect(6, 16, 12, 1, DGOLD)  # crossguard, 12 x 2
    c.rect(11, 17, 2, 2, BROWN)                               # grip 2 x 2
    c.rect(10, 19, 4, 1, GOLD); c.rect(10, 20, 4, 1, DGOLD)  # pommel 4 x 2
    c.outline(); return c
def trinket():
    """Pendant: a thin 1 px chain loop that rises to a point (a teardrop loop closed by a bail ring at the apex), a round gold pendant with a blue gem hanging at its foot."""
    c = Canvas(24)
    left = [(11, 4), (10, 4), (9, 5), (8, 6), (7, 7), (6, 9), (6, 11), (6, 13), (7, 14)]
    for i, (x, y) in enumerate(left):
        col = S4 if i % 2 == 0 else GOLD2
        c.set(x, y, col); c.set(23 - x, y, col)
    c.pix([(11, 2), (12, 2), (10, 3), (13, 3)], GOLD2); c.pix([(11, 3), (12, 3)], GOLD)  # bail ring at the apex
    c.ellipse(7, 12, 10, 8, GOLD)
    c.ellipse(9, 13, 6, 5, SKY); c.pix([(9, 14), (10, 13)], S5); c.pix([(13, 16), (14, 15)], "#2a5070")
    c.pix([(7, 15), (7, 16)], GOLD2)
    c.outline(); return shifted(c, 0, 1)
import math
def shifted(c, dx, dy):
    n = Canvas(c.w, c.h)
    for (x, y), col in c.px.items(): n.set(x + dx, y + dy, col)
    return n
def _rot(c, cx, cy, ux, uy, fn):
    """Paint cells by coordinates along (u) and across (v) an axis through (cx, cy) pointing (ux, uy)."""
    n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
    for y in range(c.h):
        for x in range(c.w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u, v = dx * ux + dy * uy, -dx * uy + dy * ux
            col = fn(u, v)
            if col: c.set(x, y, col)
def tool():
    """Wrench (the catalog's tool category is a repair kit and a spirit lantern, no mining tool): diagonal, handle bottom left to head top right, an open jaw at the head, a hole in the handle's end."""
    c = Canvas(24)
    def paint(u, v):
        if abs(v) <= 1.6 and -11.5 <= u <= 0.5: return S4 if v < -0.7 else S3 if v < 0.9 else S2        # handle, 3 px across
        if u * u + v * v <= 4.8 ** 2 and not (u > 1.0 and abs(v) < 1.8): return S4 if v < -2.5 else S3 if v < 2.5 else S2   # round head with an open jaw
        if (u + 12.4) ** 2 + v * v <= 3.0 ** 2 and not ((u + 12.4) ** 2 + v * v <= 1.2 ** 2): return S3    # ring at the handle's end
        return None
    _rot(c, 16.5, 7.5, 1, -1, paint)
    c.outline(); return c
def ranger():
    """Longbow, seen from the archer's side: vertical, tall curved limbs bulging to the right, a string pulled back to a V, an arrow nocked at the string that crosses the bow; no stock."""
    c = Canvas(24)
    arc = [(10, 3), (12, 4), (14, 6), (15, 8), (16, 10), (16, 11), (16, 12), (16, 13), (15, 15), (14, 17), (12, 19), (10, 20)]
    for (x0, y0), (x1, y1) in zip(arc, arc[1:]):
        c.line(x0, y0, x1, y1, BROWN); c.line(x0 - 1, y0, x1 - 1, y1, TAN)
    c.line(10, 3, 6, 11, BONE); c.line(10, 20, 6, 11, BONE)    # string pulled back to the nock
    c.line(6, 11, 20, 11, TAN)                                  # arrow shaft
    c.poly([(22, 11.5), (18, 9), (18, 14)], S4)               # broad arrowhead
    c.pix([(7, 9), (8, 10), (7, 13), (8, 12), (6, 9), (6, 13)], LEAF)   # fletching
    c.outline(); return shifted(c, -2, 0)

def ruins():
    """A ruined wall: masonry with visible brick courses (alternating light and dark rows, staggered joints) and a broken top edge shaped like a U (two towers of different heights either side of a low jagged gap, so the outline never slopes like a boot); the fallen bricks lie in the gap."""
    c = Canvas(16)
    tops = {**{x: 4 for x in (3, 4, 5)}, **{x: 8 for x in (6, 7, 8, 9)}, **{x: 3 for x in (10, 11, 12)}}   # top y of each column
    for r, y0 in enumerate((10, 8, 6, 4)):                                   # courses, bottom first, 2 rows each (the highest is cut by the tower tops)
        for x in range(3, 13):
            if tops[x] <= y0 + 1: c.rect(x, max(y0, tops[x]), 1, y0 + 2 - max(y0, tops[x]), S4 if r % 2 == 0 else S2)
        for jx in range(3 + 2 + (0 if r % 2 == 0 else 2), 13, 4):
            if tops[jx] <= y0 + 1: c.rect(jx, max(y0, tops[jx]), 1, y0 + 2 - max(y0, tops[jx]), S1)   # staggered mortar joints
    c.rect(10, 3, 3, 1, S2)                                                  # the right tower's top row
    c.cut([(7, 8), (9, 9)]); c.pix([(5, 4)], S2)                             # a jag in the gap, a chipped corner
    c.rect(6, 6, 2, 1, S3); c.pix([(8, 7)], S4)                              # fallen bricks lying in the gap
    c.outline(); return c
