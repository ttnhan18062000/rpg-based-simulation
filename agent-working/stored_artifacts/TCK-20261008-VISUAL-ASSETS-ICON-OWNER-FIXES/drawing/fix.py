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

OPTIONS = {
    "icon.marker.ruins": [("A", "broken arch with rubble", ruins_arch)],
    "icon.rarity.common": [("A", "silver bead", common_silver)],
    "icon.status.frame_buff": [("A", "solid up arrow", buff_arrow)],
    "icon.class.rogue": [("A", "hooded cowl", rogue_hood), ("B", "domino mask", rogue_mask)],  # the owner chose A on 2026-10-08
    "icon.marker.enemy_camp": [("A", "tent with crossed spears, fitted to the live area", camp_tent_fit), ("B", "tent with two planted spears, fitted to the live area", camp_tent_planted_fit)],  # the owner chose A (2026-10-08); the first drawing broke the live-area margin, so it is fitted and re-confirmed
    "icon.item.tool": [("A", "toolbox", tool_box)],
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


CHOSEN = {"icon.marker.ruins": "A", "icon.rarity.common": "A", "icon.status.frame_buff": "A", "icon.class.rogue": "A", "icon.marker.enemy_camp": "A", "icon.item.tool": "A"}
def chosen():
    """The six approved drawings (owner's answers, 2026-10-08), keyed by visual key."""
    return {k: next(fn for tag, _, fn in OPTIONS[k] if tag == t)() for k, t in CHOSEN.items()}
