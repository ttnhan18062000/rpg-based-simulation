"""Prototypes of the owner-fixes proposals (TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES): silhouettes for the owner's approval, then the full drawing."""
from canvas import Canvas, K
S1, S2, S3, S4, S5 = "#555b73", "#717e8f", "#91a2ab", "#c8d8e8", "#eafeff"
DARK, BONE, GOLD, GOLD2, DGOLD, BROWN, TAN = "#252530", "#f0ecd8", "#e8c040", "#c7b04f", "#a87022", "#5a2a1a", "#8e8c75"
EMBER, ROSE, WINE, TEAL, TEAL2, SLATE = "#d04030", "#854b4d", "#6a3040", "#467c8c", "#2d4a3e", "#3a3040"

def ruins_arch():
    """A broken stone arch with rubble at its feet: a tall left pillar whose arch springs across and breaks off, a short broken right stub, an open gap, loose bricks on the ground."""
    c = Canvas(16)
    c.rect(3, 4, 3, 8, S3); c.rect(3, 4, 1, 8, S4); c.rect(5, 4, 1, 8, S2)           # left pillar
    c.pix([(6, 3), (7, 3), (8, 4)], S3); c.pix([(6, 4), (7, 4)], S2); c.pix([(9, 5)], S4)   # the arch springing right, breaking off in a jag
    c.rect(10, 8, 3, 4, S3); c.rect(10, 8, 1, 4, S4); c.rect(12, 8, 1, 4, S2); c.cut([(11, 8)])   # broken right stub
    c.rect(7, 11, 2, 1, S3); c.pix([(9, 11)], S2)                                      # fallen bricks in the gap
    c.outline(); return c

def common_silver():
    """A silver bead: 7x7 round, light fill with a bright highlight and a shaded lower right."""
    c = Canvas(8)
    for y, (x0, x1) in enumerate([(2, 4), (1, 5), (0, 6), (0, 6), (0, 6), (1, 5), (2, 4)]):
        c.rect(x0, y, x1 - x0 + 1, 1, S4)
    for p in [(4, 4), (5, 4), (3, 5), (4, 5), (5, 3), (5, 2)]: c.set(*p, S3)
    c.set(2, 1, S5); c.set(1, 2, S5)
    # outline: the silhouette's ring is the shape's own edge (as the other badges): edge pixels become the dark ink
    edge = [p for p in c.px if any((p[0] + dx, p[1] + dy) not in c.px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for p in edge: c.set(*p, K)
    return c

def buff_arrow():
    """The adopted buff frame with its chevron replaced by a solid up arrow (the mirror of the debuff's down arrow), the round green frame unchanged."""
    from tests.visual_assets import icon_draft_set as ds
    s = ds.draft_sprites()["icon.status.frame_buff"]
    c = Canvas(16)
    for i, p in enumerate(s.rgba):
        if p[3]:
            col = "#%02x%02x%02x" % p[:3]
            c.set(i % 16, i // 16, col)
    for p in [(7, 3), (8, 3), (6, 4), (9, 4), (5, 5), (10, 5), (4, 6), (11, 6)]: pass
    for p in [k for k, v in c.px.items() if v == BONE]: c.px[p] = "#4a6050"   # clear the old chevron back to the frame's interior
    c.rect(7, 3, 2, 1, BONE); c.rect(6, 4, 4, 1, BONE); c.rect(5, 5, 6, 1, BONE)  # solid head
    c.rect(7, 6, 2, 5, BONE)                                                         # shaft
    return c

def rogue_hood():
    """A hooded cowl: a dark cloak with a peaked hood, a deep face opening and two light eye glints, shoulders flaring below."""
    c = Canvas(24)
    c.poly([(12, 3), (17, 7), (18, 13), (21, 20), (3, 20), (6, 13), (7, 7)], SLATE)             # hood and shoulders
    c.poly([(12, 3), (17, 7), (18, 13), (15, 13), (14, 6)], S1)                                 # lit right edge of the hood
    c.ellipse(8, 8, 8, 9, DARK)                                                                # the face opening
    c.rect(9, 12, 2, 1, GOLD); c.rect(13, 12, 2, 1, GOLD)                                       # eye glints
    c.rect(7, 18, 10, 2, "#2d4a3e")                                                            # cloak hem band
    c.outline(); return c

def rogue_mask():
    """A domino mask: wide and short, two eye holes, a nose notch and tie cords either side."""
    c = Canvas(24)
    c.poly([(3, 9), (8, 7), (12, 9), (16, 7), (21, 9), (20, 15), (15, 17), (12, 14), (9, 17), (4, 15)], SLATE)
    c.ellipse(6, 10, 4, 4, DARK); c.ellipse(14, 10, 4, 4, DARK)                                  # eye holes
    c.pix([(7, 11), (15, 11)], GOLD)
    c.line(3, 11, 1, 13, TAN); c.line(21, 11, 23, 13, TAN)                                       # cords
    c.outline(); return c

def camp_tent():
    """A tent with crossed spears above it: a wide low tent with a dark doorway, two spears crossing clear above its apex with steel heads at the top."""
    c = Canvas(16)
    c.line(3, 2, 12, 7, TAN); c.line(12, 2, 3, 7, TAN)                                               # the two spear shafts, crossing above the apex
    c.rect(2, 1, 2, 2, S4); c.rect(12, 1, 2, 2, S4)                                                  # spear heads at the top ends
    c.poly([(8, 8), (14, 12.5), (2, 12.5)], EMBER); c.poly([(8, 8), (14, 12.5), (8, 12.5)], WINE)   # tent
    c.poly([(8, 9.6), (9.8, 12.5), (6.2, 12.5)], DARK)                                               # doorway
    c.outline(); return c

def camp_tent_fit():
    """Option A fitted to the live area (12x12 with a 2 px margin, outline included): the same tent with two spears crossing above its apex, drawn smaller."""
    c = Canvas(16)
    c.line(4, 4, 11, 9, TAN); c.line(11, 4, 4, 9, TAN)                                                # spear shafts crossing above the apex
    c.rect(3, 3, 2, 2, S4); c.rect(11, 3, 2, 2, S4)                                                   # spear heads
    c.poly([(8, 9), (13, 13), (3, 13)], EMBER); c.poly([(8, 9), (13, 13), (8, 13)], WINE)             # tent
    c.poly([(8, 10.2), (9.6, 13), (6.4, 13)], DARK)                                                   # doorway
    c.outline(); return c

def camp_tent_planted_fit():
    """Option B fitted to the live area: the tent with one upright spear each side."""
    c = Canvas(16)
    c.rect(3, 4, 1, 8, TAN); c.rect(12, 4, 1, 8, TAN)
    c.rect(3, 3, 1, 2, S4); c.rect(12, 3, 1, 2, S4)
    c.poly([(8, 5), (11.5, 13), (4.5, 13)], EMBER); c.poly([(8, 5), (11.5, 13), (8, 13)], WINE)
    c.poly([(8, 9), (9.4, 13), (6.6, 13)], DARK)
    c.outline(); return c

def camp_tent_planted():
    """Alternate B: the same tent with a spear planted upright on each side (not crossed), so the tent reads first."""
    c = Canvas(16)
    c.rect(2, 3, 1, 9, TAN); c.rect(13, 3, 1, 9, TAN)                                                # upright shafts
    c.rect(2, 1, 1, 2, S4); c.rect(13, 1, 1, 2, S4); c.pix([(1, 3), (3, 3), (12, 3), (14, 3)], S4) if False else None
    c.poly([(8, 4), (12, 12.5), (4, 12.5)], EMBER); c.poly([(8, 4), (12, 12.5), (8, 12.5)], WINE)
    c.poly([(8, 8), (9.8, 12.5), (6.2, 12.5)], DARK)
    c.outline(); return c

def tool_box():
    """A toolbox: a wide red body with a lighter lid band, a flat arched carry handle, a gold latch and rivets."""
    c = Canvas(24)
    c.rect(3, 9, 18, 12, EMBER); c.rect(3, 9, 18, 4, WINE); c.rect(3, 12, 18, 1, "#2d1722")
    c.rect(3, 17, 18, 4, EMBER); c.rect(3, 20, 18, 1, "#2d1722")
    c.rect(9, 5, 6, 1, S3); c.rect(8, 6, 1, 3, S3); c.rect(15, 6, 1, 3, S3); c.rect(9, 6, 1, 1, S4)  # handle
    c.rect(10, 11, 4, 4, GOLD); c.rect(11, 12, 2, 1, DGOLD)                                        # latch
    c.pix([(5, 15), (18, 15), (5, 19), (18, 19)], S4)
    c.outline(); return c

import math
def _rotp(c, cx, cy, ux, uy, fn):
    n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
    for y in range(c.h):
        for x in range(c.w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            col = fn(dx * ux + dy * uy, -dx * uy + dy * ux)
            if col: c.set(x, y, col)

def hammer_tongs_crossed():
    """A smith's hammer crossed with tongs, inside the 20x20 live area: hammer handle bottom left to a flat-faced head top right, tongs from the bottom right to closed jaws top left, riveted at the crossing."""
    c = Canvas(24)
    def hammer(u, v):
        if abs(v) <= 1.1 and -9.0 <= u <= 3: return TAN if v < 0 else BROWN
        if 3 < u <= 6.6 and abs(v) <= 3.0: return S4 if (v < -1.6 or u < 3.8) else S3 if v < 1.6 else S2
        return None
    _rotp(c, 11.5, 11.5, 1, -1, hammer)
    c.line(5, 5, 13, 13, S3); c.line(6, 5, 14, 13, S3); c.line(5, 6, 13, 14, S2)
    c.line(13, 13, 19, 18, S3); c.line(14, 13, 19, 19, S2)
    c.line(13, 13, 20, 15, S3); c.line(13, 14, 20, 16, S2)
    c.rect(4, 3, 3, 2, S4)                                                       # jaws (flat tips)
    c.rect(11, 11, 3, 3, GOLD); c.rect(12, 12, 1, 1, TAN)                       # the rivet at the crossing (a worn centre)
    c.outline(); return c


CREAM, THATCH, THATCH2, STONE = "#f0ecd8", "#c7b04f", "#a87022", "#8e8c75"
def cottage():
    """A timber-framed cottage: a steep thatched roof with deep eaves, cream plaster walls in a dark timber frame, small shuttered windows with dark leaded panes, an arched wooden door and a stone chimney."""
    c = Canvas(24)
    c.rect(16, 4, 3, 6, S3); c.rect(18, 4, 1, 6, S3); c.rect(15, 3, 5, 1, S3)                       # stone chimney behind the roof
    c.poly([(12, 3), (22.5, 12.5), (1.5, 12.5)], THATCH); c.poly([(12, 3), (22.5, 12.5), (12, 12.5)], THATCH2)   # thatched roof
    for x, y in ((9, 7), (13, 6), (15, 9), (7, 10), (11, 10), (17, 11), (5, 12), (19, 12)): c.set(x, y, TAN)   # thatch texture
    c.rect(4, 13, 16, 8, CREAM)                                                                    # plaster walls
    c.rect(4, 13, 16, 1, BROWN); c.rect(4, 20, 16, 1, BROWN)                                       # beams
    c.rect(4, 13, 1, 8, BROWN); c.rect(19, 13, 1, 8, BROWN); c.rect(11, 13, 2, 8, BROWN)           # posts
    c.pix([(5, 14), (6, 15), (17, 14), (16, 15)], BROWN)                                           # braces
    c.rect(9, 16, 6, 5, "#8a3000"); c.rect(10, 15, 4, 1, "#8a3000"); c.rect(11, 16, 2, 5, BROWN); c.set(13, 18, GOLD)   # arched door of planks with a latch
    for x in (6, 16):
        c.rect(x, 15, 2, 2, DARK); c.rect(x - 1, 15, 1, 2, "#4a6030"); c.rect(x + 2, 15, 1, 2, "#4a6030")  # small leaded window with green shutters
    c.outline(); return c

def debuff_thorned():
    """The debuff frame reshaped as a spiked ball (a morning star's head, the registry's 'spiked frame'): a dark interior inside a red rim with eight sharp triangular spikes, and a solid bone down arrow. Everything is computed from pixel centres about the canvas centre (8, 8), so the silhouette is exactly mirror-symmetric."""
    import math
    c = Canvas(16)
    cx = cy = 8.0
    for y in range(16):
        for x in range(16):
            r = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if r <= 5.6: c.set(x, y, "#2d1722")
            if 4.6 <= r <= 5.6: c.set(x, y, "#d04030")
    for ang in range(0, 360, 45):
        a = math.radians(ang); px, py = math.cos(a), math.sin(a)
        base, tip, half = 5.0, 7.9, 1.4
        c.poly([(cx + px * base - py * half, cy + py * base + px * half), (cx + px * base + py * half, cy + py * base - px * half), (cx + px * tip, cy + py * tip)], "#d04030")
    c.rect(7, 4, 2, 4, BONE); c.rect(5, 8, 6, 1, BONE); c.rect(6, 9, 4, 1, BONE); c.rect(7, 10, 2, 1, BONE)   # solid down arrow: shaft, then a head of 6, 4 and 2 px
    c.outline(); return c

def tankard():
    """The adopted inn mug, silhouette unchanged, with wooden stave lines and two iron hoops."""
    from tests.visual_assets import icon_lookalikes as la
    s = la.all_icon_sprites()["icon.building.inn"]
    c = Canvas(24)
    for i, p in enumerate(s.rgba):
        if p[3]: c.set(i % 24, i // 24, "#%02x%02x%02x" % p[:3])
    for x in (8, 11):                                                                # stave seams
        for y in range(10, 19):
            if c.px.get((x, y)) in (THATCH2, THATCH): c.set(x, y, BROWN)
    for y in (11, 17):                                                               # iron hoops
        for x in range(5, 16):
            if c.px.get((x, y)) in (THATCH2, THATCH, BROWN): c.set(x, y, S1)
    return c

OPTIONS = {
    "icon.marker.ruins": [("A", "broken arch with rubble", ruins_arch)],
    "icon.rarity.common": [("A", "silver bead", common_silver)],
    "icon.status.frame_buff": [("A", "solid up arrow", buff_arrow)],
    "icon.class.rogue": [("A", "hooded cowl", rogue_hood), ("B", "domino mask", rogue_mask)],  # the owner chose A on 2026-10-08
    "icon.marker.enemy_camp": [("A", "tent with crossed spears, fitted to the live area", camp_tent_fit), ("B", "tent with two planted spears, fitted to the live area", camp_tent_planted_fit)],  # the owner chose A (2026-10-08); the first drawing broke the live-area margin, so it is fitted and re-confirmed
    "icon.item.tool": [("A", "hammer and tongs, crossed", hammer_tongs_crossed)],
    "icon.building.hero_house": [("A", "timber-framed cottage", cottage)],
    "icon.status.frame_debuff": [("A", "thorned frame", debuff_thorned)],
    "icon.building.inn": [("A", "tankard with staves and hoops", tankard)],  # the toolbox was rejected by the owner (theme, 2026-10-08)
}
if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/vboxuser/Work/rpg-aseprite-mcp")
    from render import render
    items = []
    for key, opts in OPTIONS.items():
        for tag, label, fn in opts:
            c = fn(); print(key, tag, c.bbox(), c.lint()["warn"], c.lint()["colors"]); items.append((f"{key}{tag}", c))
    render(items, "sheet_fix1.png", scale=10, cols=4)


CHOSEN = {"icon.marker.ruins": "A", "icon.rarity.common": "A", "icon.status.frame_buff": "A", "icon.class.rogue": "A", "icon.marker.enemy_camp": "A", "icon.item.tool": "A", "icon.building.hero_house": "A", "icon.status.frame_debuff": "A", "icon.building.inn": "A"}  # all approved by the owner on 2026-10-08 (the tool: hammer and tongs)
def chosen():
    """The six approved drawings (owner's answers, 2026-10-08), keyed by visual key."""
    return {k: next(fn for tag, _, fn in OPTIONS[k] if tag == t)() for k, t in CHOSEN.items()}
