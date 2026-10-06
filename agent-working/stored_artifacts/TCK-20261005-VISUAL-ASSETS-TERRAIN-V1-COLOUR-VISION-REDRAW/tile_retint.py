"""Re-tint a terrain-v1 tile so its 16 x 16 mean equals the Live Map flat fill (TCK-20261005-VISUAL-ASSETS-TERRAIN-V1-COLOUR-VISION-REDRAW).

Offset rule: the drawing comes unchanged from `tile_generator.tile(code)`. Every pixel that uses one of the tile's own five ramp colours (d2 d1 b l1 l2) is shifted by one
RGB offset; named accents (berries, embers, glow, ...) are untouched. The offset starts at (fill - mean) * 256 / n_ramp_pixels and is refined (at most 40 passes) against the
8-bit, clipped result, so rounding and clipping at 0 / 255 are compensated where the channel allows it. Deterministic; pure Python."""
import tile_generator as g

N = g.S * g.S


def mean_of(grid):
    return tuple(sum(g.rgb(grid[y][x])[i] for y in range(g.S) for x in range(g.S)) / N for i in range(3))


def shifted(grid, cells, off):
    out = [row[:] for row in grid]
    clipped = set()
    for x, y in cells:
        raw = tuple(c + o for c, o in zip(g.rgb(grid[y][x]), off))
        for i, v in enumerate(raw):
            if round(v) < 0 or round(v) > 255:
                clipped.add(i)
        out[y][x] = g.hexc(raw)
    return out, clipped


def retint(code):
    """-> (grid of '#rrggbb', report dict)."""
    grid = g.tile(code)
    ramp = set(g.ramp(code).values())
    cells = [(x, y) for y in range(g.S) for x in range(g.S) if grid[y][x] in ramp]
    fill = g.rgb(g.FILLS[code])
    before = mean_of(grid)
    off = tuple((f - m) * N / len(cells) for f, m in zip(fill, before))
    best = None
    for _ in range(40):
        out, clipped = shifted(grid, cells, off)
        mean = mean_of(out)
        err = tuple(f - m for f, m in zip(fill, mean))
        if best is None or sum(abs(e) for e in err) < best[0]:
            best = (sum(abs(e) for e in err), out, off, clipped, mean)
        if max(abs(e) for e in err) < 0.05:
            break
        off = tuple(o + e * N / len(cells) for o, e in zip(off, err))
    _, out, off, clipped, mean = best
    return out, {"offset": tuple(round(o, 2) for o in off), "ramp_pixels": len(cells), "clipped_channels": sorted("rgb"[i] for i in clipped),
                 "mean_before": tuple(round(v, 2) for v in before), "mean_after": tuple(round(v, 2) for v in mean), "fill": fill}
