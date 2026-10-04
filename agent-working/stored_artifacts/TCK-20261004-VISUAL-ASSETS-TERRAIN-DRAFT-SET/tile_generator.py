"""Procedural 16x16 terrain tiles for draft set terrain-v1. Every tile is periodic (all coordinates wrap mod 16) so it repeats seamlessly.
Palette family: each terrain's ramp is derived from its Live Map fill colour (d2 < d1 < b < l1 < l2); light from the top-left (highlights on the top-left of features,
shadows bottom-right). Accents are few and named."""
S = 16
FILLS = {0:'#1a1d27',1:'#555b73',2:'#1e3a5f',3:'#2d4a3e',4:'#4a2d2d',5:'#2d3a4a',7:'#3a3420',8:'#2a2a3a',9:'#3a3a3a',10:'#5a5040',11:'#4a6050',12:'#4a4035',
         13:'#6a3040',14:'#8a3000',15:'#4a6030',16:'#c8d8e8',17:'#0a4a0a',18:'#2a5070',19:'#6a7a40',20:'#3a3040',21:'#5a2a1a',22:'#4a4050'}
NAMES = {0:'floor',1:'wall',2:'water',3:'town',4:'camp',5:'sanctuary',7:'desert',8:'swamp',9:'mountain',10:'road',11:'bridge',12:'ruins',13:'dungeon_entrance',
         14:'lava',15:'grassland',16:'snow',17:'jungle',18:'shallow_water',19:'farmland',20:'cave',21:'volcanic',22:'graveyard'}

def rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
def hexc(c): return '#%02x%02x%02x' % tuple(max(0, min(255, round(v))) for v in c)
def mul(c, f): return tuple(v * f for v in c)
def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
def lift(c, t): return mix(c, (255, 255, 255), t)

def ramp(code):
    b = rgb(FILLS[code])
    if code == 16:  # snow is already light: darken for shade, brighten only a little
        return {'d2': hexc(mul(b, .70)), 'd1': hexc(mul(b, .85)), 'b': hexc(b), 'l1': hexc(lift(b, .45)), 'l2': '#ffffff'}
    return {'d2': hexc(mul(b, .58)), 'd1': hexc(mul(b, .80)), 'b': hexc(b), 'l1': hexc(lift(b, .18)), 'l2': hexc(lift(b, .38))}

def noise(x, y, k=0): return ((x * 73856093) ^ (y * 19349663) ^ (k * 83492791)) % 100

class T:
    def __init__(self, code):
        self.code, self.p = code, ramp(code)
        self.g = [[self.p['b']] * S for _ in range(S)]
    def set(self, x, y, c): self.g[y % S][x % S] = self.p.get(c, c)
    def get(self, x, y): return self.g[y % S][x % S]
    def speckle(self, c, pct, k):
        for y in range(S):
            for x in range(S):
                if noise(x, y, k) < pct: self.set(x, y, c)

def floor(t):
    for y in range(S):
        for x in range(S):
            if x % 8 == 0 or y % 8 == 0: t.set(x, y, 'd2')
            elif x % 8 == 1 or y % 8 == 1: t.set(x, y, 'l1')
            elif x % 8 == 7 or y % 8 == 7: t.set(x, y, 'd1')
    t.speckle('l1', 4, 1)
def wall(t):
    for y in range(S):
        off = 0 if (y // 4) % 2 == 0 else 4
        for x in range(S):
            if y % 4 == 0 or (x - off) % 8 == 0: t.set(x, y, 'd2')
            elif y % 4 == 1: t.set(x, y, 'l1')
            elif y % 4 == 3: t.set(x, y, 'd1')
            elif y % 4 == 2: t.set(x, y, 'l1' if noise(x, y, 30) < 60 else 'b')
    t.speckle('d1', 4, 2); t.speckle('l2', 3, 3)
def water(t):
    for i, y in enumerate((1, 5, 9, 13)):
        x0 = (i * 7 + 2) % S
        for dx in range(6): t.set(x0 + dx, y, 'l1')
        t.set(x0 + 1, y - 1, 'l2'); t.set(x0 + 2, y - 1, 'l2')
        for dx in range(1, 7): t.set(x0 + dx, y + 1, 'd1')
    t.speckle('d1', 3, 4)
def town(t):
    for y in range(S):
        off = 0 if (y // 4) % 2 == 0 else 2
        for x in range(S):
            sx, sy = (x - off) % 4, y % 4
            if sx == 3 or sy == 3: t.set(x, y, 'd2')
            elif sx == 0 and sy == 0: t.set(x, y, 'l2')
            elif sx == 0 or sy == 0: t.set(x, y, 'l1')
            elif sx == 2 and sy == 2: t.set(x, y, 'd1')
def camp(t):
    for cx, cy, r in ((3, 4, 3), (11, 3, 2), (8, 11, 3), (14, 13, 2)):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r: t.set(x, y, 'd1')
    for x, y in ((2, 3), (10, 2), (7, 10), (13, 12)): t.set(x, y, 'l1')
    for x, y in ((5, 7), (6, 7), (12, 8), (13, 8), (1, 12), (2, 12)): t.set(x, y, 'l2')
    for x, y in ((9, 6), (3, 13), (14, 1)): t.set(x, y, '#d8742a')
    t.speckle('d2', 3, 5)
def sanctuary(t):
    for y in range(S):
        for x in range(S):
            if (x + y) % 8 == 0: t.set(x, y, 'd1')
    cx = cy = 7
    for d in range(-4, 5):
        t.set(cx + d, cy, 'l1'); t.set(cx, cy + d, 'l1')
        t.set(cx + d, cy + 1, 'd1'); t.set(cx + 1, cy + d, 'd1')
    t.set(cx, cy, 'l2'); t.set(cx - 1, cy - 1, 'l2')
    t.speckle('l1', 2, 6)
def desert(t):
    for y in range(S):
        for x in range(S):
            m = (x + 2 * y) % 8
            if m == 0: t.set(x, y, 'l1')
            elif m == 1: t.set(x, y, 'l1' if noise(x, y, 7) < 50 else 'b')
            elif m == 4: t.set(x, y, 'd1')
            elif m == 5: t.set(x, y, 'd2' if noise(x, y, 8) < 20 else 'd1')
    t.speckle('l1', 3, 9)
def swamp(t):
    for cx, cy, rx, ry in ((4, 4, 3, 2), (11, 9, 4, 2), (3, 13, 2, 1)):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0: t.set(x, y, 'd1')
        t.set(cx - rx + 1, cy - 1, 'l1'); t.set(cx - rx + 2, cy - 1, 'l1')
    for x, y in ((8, 2), (14, 5), (6, 8)):
        t.set(x, y, '#3f5f3a'); t.set(x, y - 1, '#5a7a4a'); t.set(x, y + 1, 'd2'); t.set(x + 1, y, '#3f5f3a')
    t.speckle('l1', 2, 10)
def mountain(t):
    def peak(cx, cy, h):
        for dy in range(h + 1):
            for dx in range(-dy, dy + 1):
                x, y = cx + dx, cy + dy
                t.set(x, y, 'l1' if dx < 0 else ('d1' if dx > 0 else 'l2'))
                if dy == h: t.set(x, y, 'd2')
        t.set(cx, cy, '#aab0b8'); t.set(cx - 1, cy + 1, '#9aa0a8'); t.set(cx, cy + 1, '#9aa0a8')
    peak(4, 1, 6); peak(11, 8, 6)
    t.speckle('d2', 3, 11)
def road(t):
    for y in (4, 10):
        for x in range(S): t.set(x, y, 'd1'); t.set(x, y + 1, 'd2'); t.set(x, y - 1, 'l1')
    t.speckle('l1', 8, 12); t.speckle('d1', 6, 13)
def bridge(t):
    for y in range(S):
        for x in range(S):
            if x % 4 == 3: t.set(x, y, 'd2')
            elif x % 4 == 0: t.set(x, y, 'l1')
            elif (y + 3 * (x // 4)) % 6 == 0 and x % 4 == 1: t.set(x, y, 'd1')
    for x in (1, 5, 9, 13):
        t.set(x, 1, 'l2'); t.set(x, 9, 'l2')
def ruins(t):
    for y in range(S):
        for x in range(S):
            row = y // 5
            off = (row * 3) % 8
            if y % 5 == 0 or (x - off) % 8 == 0: t.set(x, y, 'd2')
            elif y % 5 == 1: t.set(x, y, 'l1')
    for x, y in ((3, 2), (4, 3), (5, 3), (9, 8), (10, 9), (11, 9), (12, 10)): t.set(x, y, 'd2')
    for x, y in ((6, 1), (7, 1), (7, 2), (13, 7), (14, 7), (2, 12), (3, 12)): t.set(x, y, '#4a6a3a')
    t.speckle('d1', 6, 14)
def dungeon_entrance(t):
    for y in range(S):
        off = 0 if (y // 4) % 2 == 0 else 4
        for x in range(S):
            if y % 4 == 0 or (x - off) % 8 == 0: t.set(x, y, 'd1')
    for y in range(4, 14):
        for x in range(5, 11):
            top = y - 4
            if top < 2 and (x < 6 + (1 - top) or x > 9 - (1 - top)): continue
            t.set(x, y, '#1a0a10')
    for x in range(5, 11): t.set(x, 3, 'l1')
    for y in range(4, 14): t.set(4, y, 'l1')
    for x in range(4, 12): t.set(x, 14, 'd2')
    t.set(5, 12, 'd1'); t.set(10, 12, 'd1')
def lava(t):
    for x in range(S):
        for y in range(S):
            t.set(x, y, 'l1' if noise(x, y, 15) < 55 else 'b')
    for cx, cy in ((3, 3), (11, 4), (6, 11), (14, 13)):
        for y in range(cy - 3, cy + 4):
            for x in range(cx - 3, cx + 4):
                if (x - cx) ** 2 + (y - cy) ** 2 <= 5: t.set(x, y, '#3a1200')
        t.set(cx - 1, cy - 1, '#5a2008'); t.set(cx, cy - 1, '#5a2008')
    for x, y in ((7, 7), (0, 8), (9, 1), (15, 15)): t.set(x, y, '#ffb030')
def grassland(t):
    for x, y in ((2, 2), (6, 1), (10, 3), (13, 2), (4, 6), (8, 7), (12, 6), (1, 10), (5, 11), (9, 10), (14, 11), (3, 14), (7, 14), (11, 13)):
        t.set(x, y - 1, 'l2'); t.set(x, y, 'l1'); t.set(x + 1, y, 'b'); t.set(x, y + 1, 'd1'); t.set(x - 1, y, 'd1')
    for x, y in ((6, 9), (13, 14)): t.set(x, y, '#d8d070')
    t.speckle('d1', 4, 16)
def snow(t):
    for cx, cy in ((4, 4), (12, 10)):
        for y in range(cy - 2, cy + 3):
            for x in range(cx - 4, cx + 5):
                if ((x - cx) / 4) ** 2 + ((y - cy) / 2) ** 2 <= 1.0: t.set(x, y, 'l1' if y <= cy else 'd1')
        for x in range(cx - 2, cx + 4): t.set(x, cy + 3, 'd2')
    t.speckle('l2', 5, 17); t.speckle('d2', 2, 18)
def jungle(t):
    for cx, cy, r in ((3, 3, 3), (10, 2, 3), (14, 8, 3), (6, 9, 3), (1, 13, 3), (11, 14, 3)):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d = (x - cx) ** 2 + (y - cy) ** 2
                if d <= r * r: t.set(x, y, 'l1' if (x - cx) + (y - cy) < -2 else ('d1' if (x - cx) + (y - cy) > 2 else 'b'))
        t.set(cx - 1, cy - 1, '#3aa03a'); t.set(cx, cy - 1, 'l2')
    t.speckle('d2', 8, 19)
def shallow_water(t):
    for y in (2, 7, 12):
        for x in range(S):
            if (x + y * 2) % 7 < 3: t.set(x, y, 'l1')
    for x, y in ((3, 4), (4, 4), (11, 9), (12, 9), (7, 14), (8, 14)): t.set(x, y, '#7a8a78')
    for x, y in ((5, 5), (13, 10), (9, 15)): t.set(x, y, '#5a6a60')
    t.speckle('l2', 3, 20)
def farmland(t):
    for y in range(S):
        for x in range(S):
            m = y % 4
            if m == 0: t.set(x, y, '#4d3d28')
            elif m == 1: t.set(x, y, '#5a4a30' if x % 2 else '#4d3d28')
            elif m == 2: t.set(x, y, 'l1')
            elif m == 3: t.set(x, y, 'b')
    for y in (2, 6, 10, 14):
        for x in range(0, S, 4): t.set(x, y, '#8aa04a'); t.set(x, y - 1, '#a6bc5c')
def cave(t):
    for cx, cy, r in ((3, 3, 3), (10, 4, 3), (6, 11, 3), (13, 13, 2)):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    t.set(x, y, 'l1' if (x - cx) + (y - cy) < -1 else ('d1' if (x - cx) + (y - cy) > 1 else 'b'))
    for x, y in ((8, 8), (9, 8), (9, 9), (1, 8), (1, 9), (14, 2)): t.set(x, y, '#18121e')
    t.speckle('d2', 5, 21)
def volcanic(t):
    for y in range(S):
        for x in range(S):
            if (x * 5 + y * 3) % 11 < 3: t.set(x, y, 'd1')
    zig = [(0, 4), (1, 4), (2, 5), (3, 5), (4, 6), (5, 6), (6, 7), (7, 7), (8, 8), (9, 8), (10, 9), (11, 9), (12, 10), (13, 10), (14, 11), (15, 11)]
    for x, y in zig: t.set(x, y, '#c8501a'); t.set(x, y + 1, 'd2')
    for x, y in ((3, 12), (4, 12), (4, 13), (11, 2), (12, 2), (12, 3)): t.set(x, y, '#c8501a')
    t.set(7, 7, '#ffb030'); t.set(12, 2, '#ffb030')
    t.speckle('l1', 5, 22)
def graveyard(t):
    for x, y in ((2, 3), (6, 12), (13, 6), (9, 2), (1, 9), (14, 13)):
        t.set(x, y, '#6a6040'); t.set(x + 1, y - 1, '#6a6040'); t.set(x - 1, y - 1, '#5a5030')
    for sx, sy in ((3, 5), (10, 9)):
        for y in range(sy, sy + 5):
            for x in range(sx, sx + 4):
                t.set(x, y, 'l1' if x == sx or y == sy else 'b' if x < sx + 3 and y < sy + 4 else 'd2')
        t.set(sx, sy, 'd1'); t.set(sx + 3, sy, 'd1')
        t.set(sx + 1, sy + 1, 'd2'); t.set(sx + 1, sy + 2, 'd2'); t.set(sx, sy + 2, 'd2'); t.set(sx + 2, sy + 2, 'd2')
    t.speckle('d1', 4, 23)

DRAW = {0: floor, 1: wall, 2: water, 3: town, 4: camp, 5: sanctuary, 7: desert, 8: swamp, 9: mountain, 10: road, 11: bridge, 12: ruins, 13: dungeon_entrance,
        14: lava, 15: grassland, 16: snow, 17: jungle, 18: shallow_water, 19: farmland, 20: cave, 21: volcanic, 22: graveyard}

def tile(code):
    t = T(code); DRAW[code](t); return t.g

def ops(code):
    g = tile(code); base = ramp(code)['b']
    px = [{'x': x, 'y': y, 'color': g[y][x]} for y in range(S) for x in range(S) if g[y][x] != base]
    return [{'op': 'pixels', 'pixels': px}]

def mean_colour(code):
    g = tile(code); n = S * S
    return tuple(sum(rgb(g[y][x])[i] for y in range(S) for x in range(S)) / n for i in range(3))

if __name__ == '__main__':
    for code in DRAW:
        m = mean_colour(code); f = rgb(FILLS[code])
        print(f"{code:2d} {NAMES[code]:17s} fill {FILLS[code]} mean {hexc(m)} diff {sum(abs(a-b) for a,b in zip(m,f)):5.1f} overrides {len(ops(code)[0]['pixels'])}")
