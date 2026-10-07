from canvas import Canvas, K
LEAF, GRASS, DARKBROWN = "#48b858", "#4a6030", "#5a2a1a"
S1, S2, S3, S4, DARK, BONE, GOLD, GOLD2, DGOLD = "#555b73", "#717e8f", "#91a2ab", "#c8d8e8", "#252530", "#f0ecd8", "#e8c040", "#c7b04f", "#a87022"
def tree():
    c = Canvas(16); c.ellipse(4, 4, 9, 6, GRASS); c.ellipse(3, 3, 8, 6, LEAF); c.rect(7, 10, 2, 3, DARKBROWN); c.outline(); return c
def ruins():
    """Ruined masonry: two broken column stubs of different heights with jagged tops, a fallen block between them, on a ground slab."""
    c = Canvas(16)
    c.rect(3, 11, 10, 2, S2); c.rect(3, 11, 10, 1, S3)                                    # ground slab
    c.rect(4, 5, 4, 6, S3); c.rect(4, 5, 1, 6, S4); c.rect(7, 5, 1, 6, S2)                # tall stub
    c.pix([(5, 4), (4, 4), (7, 4)], S3); c.pix([(4, 4)], S4); c.cut([(6, 5), (6, 6)]); c.pix([(5, 3)], S4)   # jagged teeth, a chipped notch
    c.rect(10, 8, 3, 3, S3); c.rect(10, 8, 1, 3, S4); c.rect(12, 8, 1, 3, S2)             # low stub
    c.cut([(11, 8)]); c.pix([(10, 7), (12, 7)], S3)                                       # its own teeth
    c.rect(8, 9, 2, 2, S1); c.pix([(8, 9)], S2)                                           # fallen block between, below both tops
    c.outline(); return c
def door():
    c = Canvas(16); c.rect(3, 6, 10, 7, S2); c.ellipse(3, 3, 10, 8, S2); c.rect(5, 8, 6, 5, DARK); c.ellipse(5, 6, 6, 5, DARK); c.pix([(3, 7), (3, 8), (4, 5), (5, 4), (6, 3), (7, 3)], S3); c.rect(3, 12, 10, 1, S1); c.outline(); return c
def obelisk():
    """A real obelisk: slim straight shaft (3 px, then 4), a pointed pyramid tip in light stone, a 2 px plinth. No rounded top, no flare, no cap."""
    c = Canvas(16)
    c.pix([(7, 3)], S4); c.rect(7, 4, 2, 1, S4)                                            # pointed tip (1 px, then 2)
    c.rect(6, 5, 4, 6, S3); c.rect(6, 5, 1, 6, S4); c.rect(9, 5, 1, 6, S2)                # shaft
    c.pix([(8, 5)], S4)
    c.rect(5, 11, 6, 2, S2); c.rect(5, 11, 6, 1, S3)                                       # plinth
    c.pix([(7, 7), (8, 8), (7, 9)], GOLD); c.outline(); return c
def skull():
    c = Canvas(16); c.ellipse(3, 3, 10, 8, BONE); c.rect(5, 10, 6, 3, BONE); c.rect(10, 5, 2, 6, S4); c.rect(5, 7, 2, 2, K); c.rect(9, 7, 2, 2, K); c.pix([(8, 9), (7, 10)], K); c.pix([(6, 12), (8, 12), (10, 12)], K); c.outline(); return c
ALL = {"resource_grove": tree, "ruins": ruins, "dungeon_entrance": door, "shrine": obelisk, "boss_arena": skull}
if __name__ == "__main__":
    for n, f in ALL.items(): f().show(n)
