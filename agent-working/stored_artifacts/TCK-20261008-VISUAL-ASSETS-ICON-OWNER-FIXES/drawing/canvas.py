import json, sys
sys.path.insert(0, "/home/vboxuser/Work/rpg-aseprite-mcp")
from visual_assets.drawing.technique.lint import lint_grid

K = "#0e1018"
class Canvas:
    def __init__(self, w, h=None):
        self.w, self.h = w, h or w
        self.px = {}
    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h: self.px[(x, y)] = c
    def pix(self, pts, c):
        for x, y in pts: self.set(x, y, c)
    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w): self.set(xx, yy, c)
    def ellipse(self, x, y, w, h, c):
        cx, cy, rx, ry = x + (w - 1) / 2, y + (h - 1) / 2, w / 2, h / 2
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0: self.set(xx, yy, c)
    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0); sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1; err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1: break
            e2 = 2 * err
            if e2 >= dy: err += dy; x0 += sx
            if e2 <= dx: err += dx; y0 += sy
    def poly(self, pts, c):
        n = len(pts)
        for yy in range(self.h):
            for xx in range(self.w):
                px, py = xx + 0.5, yy + 0.5; inside = False; j = n - 1
                for i in range(n):
                    xi, yi = pts[i]; xj, yj = pts[j]
                    if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi: inside = not inside
                    j = i
                if inside: self.set(xx, yy, c)
    def cut(self, pts):
        for p in pts: self.px.pop(p, None)
    def outline(self, c=K):
        ring = {(x + dx, y + dy) for (x, y) in self.px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - set(self.px)
        for p in ring:
            self.set(*p, c)
    def grid(self):
        return [[(self.px[(x, y)] + "ff") if (x, y) in self.px else "#00000000" for x in range(self.w)] for y in range(self.h)]
    def colours(self):
        return sorted(set(self.px.values()))
    def ascii(self):
        cols = self.colours(); letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"; m = {c: letters[i] for i, c in enumerate(cols)}
        rows = ["".join(m[self.px[(x, y)]] if (x, y) in self.px else "." for x in range(self.w)) for y in range(self.h)]
        return rows, {v: k for k, v in m.items()}
    def lint(self):
        r = lint_grid(self.grid())
        return {"warn": [f["code"] + str(f.get("pairs", "")) for f in r["findings"] if f["level"] == "warn"], "info": sorted({f["code"] for f in r["findings"] if f["level"] != "warn"}), "colors": r["stats"].get("colors"), "budget": r["stats"].get("color_budget")}
    def bbox(self):
        xs = [x for x, _ in self.px]; ys = [y for _, y in self.px]
        return (min(xs), min(ys), max(xs), max(ys))
    def sil(self): return set(self.px)
    def ops(self):
        runs = []
        for y in range(self.h):
            x = 0
            while x < self.w:
                c = self.px.get((x, y))
                if c is None: x += 1; continue
                x2 = x
                while x2 < self.w and self.px.get((x2, y)) == c: x2 += 1
                runs.append([x, y, x2 - x, 1, c]); x = x2
        merged = []
        for r in runs:
            for m in merged:
                if m[0] == r[0] and m[2] == r[2] and m[4] == r[4] and m[1] + m[3] == r[1]: m[3] += 1; break
            else: merged.append(r)
        return [{"op": "rect", "x": x, "y": y, "width": w, "height": h, "color": c} for x, y, w, h, c in merged]
    def show(self, name):
        rows, leg = self.ascii()
        print(f"== {name} {self.w}x{self.h} bbox={self.bbox()} colours={len(leg)} lint={self.lint()}")
        print("\n".join(rows)); print(leg)
