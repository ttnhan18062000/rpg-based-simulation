from canvas import Canvas, K
def m8(rows): return {(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == "#"}
SHAPES = {
 "common":   m8(["........", "..####..", ".######.", ".######.", ".######.", ".######.", "..####..", "........"]),
 "uncommon": m8(["...##...", "..####..", ".######.", ".######.", "..####..", "...##...", "........", "........"]),
 "rare":     m8(["...##...", "...##...", "..####..", "########", "########", "..####..", "...##...", "...##..."]),
}
def badge(shape, fill, hi=None):
    c = Canvas(8)
    bg = set()
    stack = [(x, y) for x in range(-1, 9) for y in (-1, 8)] + [(x, y) for y in range(-1, 9) for x in (-1, 8)]
    while stack:
        p = stack.pop()
        if p in bg or p in shape or not (-1 <= p[0] <= 8 and -1 <= p[1] <= 8): continue
        bg.add(p); stack += [(p[0]+1, p[1]), (p[0]-1, p[1]), (p[0], p[1]+1), (p[0], p[1]-1)]
    for (x, y) in shape:
        edge = any((x+dx, y+dy) in bg for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)))
        c.set(x, y, K if edge else fill)
    return c
FILLS = {"common": "#555b73", "uncommon": "#48b858", "rare": "#9060d0"}
def all_badges(fills=FILLS):
    out = {n: badge(SHAPES[n], fills[n]) for n in SHAPES}
    out["common"].set(2, 2, "#91a2ab")  # a highlight so the round shape reads as a bead
    return out
if __name__ == "__main__":
    for n, c in all_badges().items(): c.show(n)
