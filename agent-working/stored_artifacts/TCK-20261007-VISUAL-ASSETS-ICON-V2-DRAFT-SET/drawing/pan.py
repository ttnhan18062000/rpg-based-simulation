from canvas import Canvas, K
S1, S2, S3, S4, S5, DARK, BONE, SNOW2 = "#555b73", "#717e8f", "#91a2ab", "#c8d8e8", "#eafeff", "#252530", "#f0ecd8", "#d9ecf3"
GOLD, GOLD2, DGOLD, BROWN, TAN, EMBER, ROSE, WINE, VIOLET, SKY, LEAF, GRASS, TEAL = "#e8c040", "#c7b04f", "#a87022", "#5a2a1a", "#8e8c75", "#d04030", "#854b4d", "#6a3040", "#9060d0", "#50a8e0", "#48b858", "#4a6030", "#467c8c"
# ---- buildings (24x24, core 18x18 at 3..20, then the outline ring)
def store():
    c = Canvas(24); c.ellipse(4, 9, 16, 12, DGOLD); c.ellipse(4, 9, 12, 9, GOLD2); c.rect(8, 6, 8, 4, DGOLD); c.rect(8, 6, 4, 3, GOLD2)
    c.rect(7, 8, 10, 2, BROWN); c.rect(7, 8, 3, 1, TAN)  # tie
    c.pix([(9, 4), (10, 5), (14, 4), (13, 5)], DGOLD)  # gathered top
    c.ellipse(9, 12, 7, 7, GOLD); c.ellipse(9, 12, 5, 5, "#fff3b0" if False else GOLD2); c.rect(12, 14, 1, 3, DGOLD)  # coin with a mark
    c.outline(); return c
def guild():
    c = Canvas(24); c.rect(5, 3, 2, 18, TAN); c.pix([(5, 3), (6, 3)], GOLD)
    c.rect(7, 5, 13, 10, EMBER); c.rect(16, 5, 4, 10, WINE); c.cut([(13, 14), (14, 14), (14, 13), (13, 13), (12, 14), (15, 14), (12, 13), (15, 13)][:0])
    for i in range(5): c.cut([(x, 14 - i) for x in range(13 - 0, 15) if False])
    c.poly([(12.0, 15), (15.0, 15), (13.5, 11.5)], "#000000"); 
    for (x, y), v in list(c.px.items()):
        if v == "#000000": del c.px[(x, y)]
    c.poly([(9.5, 7), (13.5, 7), (13.5, 12), (11.5, 10.5), (9.5, 12)], GOLD); c.outline(); return c
def inn():
    c = Canvas(24); c.rect(5, 8, 11, 12, DGOLD); c.rect(5, 8, 3, 12, GOLD2); c.rect(13, 8, 3, 12, BROWN)
    c.ellipse(14, 10, 6, 8, DGOLD); c.ellipse(16, 12, 3, 4, "#000000")
    for (x, y), v in list(c.px.items()):
        if v == "#000000": del c.px[(x, y)]
    c.ellipse(4, 4, 6, 5, BONE); c.ellipse(8, 3, 6, 5, BONE); c.ellipse(11, 4, 6, 5, BONE); c.rect(5, 7, 11, 2, BONE); c.rect(12, 6, 4, 3, S4); c.rect(5, 19, 11, 1, BROWN)
    c.outline(); return c
def house():
    c = Canvas(24); c.poly([(12, 3), (21, 11), (3, 11)], EMBER); c.poly([(12, 3), (21, 11), (12, 11)], WINE)
    c.rect(5, 11, 14, 9, SNOW2); c.rect(12, 11, 7, 9, S4); c.rect(10, 14, 4, 6, DARK); c.rect(6, 13, 3, 3, SKY); c.rect(15, 13, 3, 3, SKY); c.rect(17, 4, 2, 4, S2); c.rect(3, 11, 18, 1, S2)
    c.outline(); return c
def hall():
    c = Canvas(24); c.rect(3, 17, 18, 3, VIOLET); c.rect(3, 17, 18, 1, "#c8d8e8"); c.poly([(3, 7), (12, 9), (12, 18), (3, 16)], BONE); c.poly([(21, 7), (12, 9), (12, 18), (21, 16)], S4)
    c.rect(11, 8, 2, 10, S1)
    for yy in (10, 12, 14): c.rect(5, yy, 5, 1, S3); c.rect(14, yy, 5, 1, S3)
    c.rect(9, 17, 6, 3, GOLD); c.outline(); return c
# ---- classes
def ranger():
    c = Canvas(24)
    for t in range(0, 15): pass
    c.line(7, 3, 5, 11, TAN); c.line(5, 11, 7, 20, TAN); c.line(8, 3, 6, 11, TAN); c.line(6, 11, 8, 20, TAN); c.line(7, 3, 7, 20, BONE)
    c.line(6, 12, 20, 12, DGOLD); c.line(19, 11, 20, 12, S4); c.line(19, 13, 20, 12, S4); c.poly([(20, 12), (17, 10), (17, 14)], S4)
    c.pix([(9, 11), (9, 13), (10, 10), (10, 14)], LEAF); c.outline(); return c
def mage():
    c = Canvas(24); c.poly([(12, 3), (18, 16), (6, 16)], VIOLET); c.poly([(12, 3), (18, 16), (12, 16)], "#6a3040"); c.ellipse(3, 15, 18, 5, VIOLET); c.ellipse(3, 15, 18, 3, "#9060d0")
    c.rect(8, 12, 8, 2, GOLD); c.rect(11, 11, 2, 4, GOLD2); c.pix([(15, 6), (14, 9)], GOLD); c.rect(4, 18, 16, 2, "#6a3040"); c.outline(); return c
def rogue():
    c = Canvas(24); c.poly([(19, 3), (21, 5), (9, 14), (7, 12)], S4); c.poly([(19, 3), (21, 5), (14, 10), (13, 8)], S5)
    c.line(8, 13, 12, 17, GOLD); c.line(7, 14, 11, 18, GOLD); c.line(6, 14, 4, 16, TAN); c.rect(4, 17, 5, 3, BROWN); c.rect(3, 18, 3, 3, BROWN)
    c.line(10, 14, 6, 18, GOLD2); c.outline(); return c
# ---- items
def weapon():
    c = Canvas(24); c.poly([(19, 3), (21, 3), (21, 5), (9, 17), (7, 15)], S4); c.poly([(20, 3), (21, 4), (13, 12), (12, 11)], S5)
    c.line(6, 12, 12, 18, GOLD); c.line(7, 11, 13, 17, GOLD2); c.rect(4, 16, 4, 3, BROWN); c.rect(3, 18, 3, 3, BROWN); c.outline(); return c
def armor():
    c = Canvas(24); c.ellipse(3, 4, 8, 7, S3); c.ellipse(13, 4, 8, 7, S3); c.rect(6, 7, 12, 12, S3); c.poly([(6, 17), (18, 17), (14, 21), (10, 21)], S3)
    c.rect(6, 7, 3, 12, S4); c.rect(15, 7, 3, 12, S2); c.rect(11, 9, 2, 9, S1); c.rect(10, 10, 4, 2, GOLD2); c.cut([(11, 7), (12, 7), (11, 6), (12, 6)]); c.outline(); return c
def trinket():
    c = Canvas(24); c.ellipse(5, 2, 14, 12, "#000000")
    for (x, y), v in list(c.px.items()):
        if v == "#000000": del c.px[(x, y)]
    c.line(6, 3, 12, 14, S4); c.line(18, 3, 12, 14, S4); c.line(7, 3, 12, 13, S4); c.line(17, 3, 12, 13, S1)
    c.ellipse(7, 12, 10, 9, GOLD); c.ellipse(9, 14, 6, 5, SKY); c.pix([(10, 15), (10, 16)], S5); c.pix([(14, 17), (13, 18)], "#2a5070"); c.outline(); return c
def tool():
    c = Canvas(24); c.line(5, 20, 17, 8, BROWN); c.line(6, 20, 18, 8, BROWN); c.line(5, 19, 17, 7, BROWN)
    c.poly([(3, 9), (9, 3), (21, 3), (21, 9), (15, 7), (9, 9)], S3); c.poly([(9, 3), (21, 3), (20, 5), (10, 5)], S4); c.rect(14, 5, 7, 2, S2); c.outline(); return c
def consumable():
    c = Canvas(24); c.ellipse(5, 9, 14, 12, "#8e8c75"); c.ellipse(6, 10, 12, 10, SNOW2); c.ellipse(7, 13, 10, 7, EMBER); c.rect(14, 14, 3, 4, WINE)
    c.rect(9, 5, 6, 5, SNOW2); c.rect(9, 3, 6, 3, GOLD2); c.pix([(8, 11), (7, 12)], S5); c.outline(); return c
def material():
    c = Canvas(24); c.poly([(12, 3), (19, 7), (21, 14), (16, 20), (7, 20), (3, 13), (6, 7)], S2); c.poly([(12, 3), (19, 7), (21, 14), (16, 20), (12, 12)], S1)
    c.poly([(12, 3), (6, 7), (3, 13), (7, 20), (11, 13)], S3); c.poly([(12, 3), (8, 7), (7, 11), (12, 10)], S4)
    c.pix([(14, 9), (15, 9), (14, 10), (9, 15), (10, 15), (16, 15)], GOLD); c.outline(); return c
BUILD = {"store": store, "guild": guild, "inn": inn, "hero_house": house, "class_hall": hall}
CLASSES = {"ranger": ranger, "mage": mage, "rogue": rogue}
ITEMS = {"weapon": weapon, "armor": armor, "trinket": trinket, "tool": tool, "consumable": consumable, "material": material}
if __name__ == "__main__":
    import loc
    from render import render
    items = [(n, f()) for n, f in loc.ALL.items()] + [(n, f()) for d in (BUILD, CLASSES, ITEMS) for n, f in d.items()]
    for n, c in items: print(n, c.bbox(), len(c.colours()), c.lint())
    render(items, "sheet_a.png", scale=5, cols=5)
