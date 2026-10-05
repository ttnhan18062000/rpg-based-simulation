"""Border masks for draft set terrain-v1 (TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS). 16 x 16, 1-bit alpha: opaque pixels are the shape (colour is irrelevant, the client shows the
higher neighbour's own tile pixels there), everything else transparent. Authored for ONE orientation, the client rotates in 90-degree clockwise steps (docs/assets/pilot_terrain_m5_criteria.md, AM5-B):
edge = north side, outer_corner = north-east, inner_corner = north plus east. Depth cap 4 px (approved 2026-10-06).

Design rules: every edge profile starts and ends at depth 2, so any two variants meet seamlessly along a coast; depth changes by at most 1 per column (a ragged lump line, no cliffs);
no isolated pixel; the inner corner is the union of the edge profile and its east-side turn, so it joins its neighbours' edges. Deterministic, pure Python."""

SIZE = 16
CAP = 4
# Depth (rows from the cell edge) of the opaque fringe in each column, per variant.
EDGE_PROFILES = {
    "v1": [2, 2, 3, 3, 4, 3, 3, 2, 2, 3, 4, 4, 3, 3, 2, 2],
    "v2": [2, 3, 3, 2, 2, 3, 4, 4, 3, 2, 3, 3, 4, 3, 3, 2],
    "v3": [2, 2, 2, 3, 4, 4, 3, 3, 3, 4, 3, 2, 2, 3, 3, 2],
}
# North-east corner blobs (pixels), per variant.
CORNERS = {
    "v1": {(13, 0), (14, 0), (15, 0), (14, 1), (15, 1), (15, 2)},
    "v2": {(12, 0), (13, 0), (14, 0), (15, 0), (13, 1), (14, 1), (15, 1), (14, 2), (15, 2), (15, 3)},
    "v3": {(12, 0), (13, 0), (14, 0), (15, 0), (13, 1), (14, 1), (15, 1), (15, 2)},
}


def edge(variant):
    return {(x, y) for x, depth in enumerate(EDGE_PROFILES[variant]) for y in range(depth)}


def inner_corner(variant):
    north = edge(variant)
    east = {(SIZE - 1 - y, x) for x, y in north}  # one clockwise quarter turn: north strip -> east strip
    return north | east


def masks():
    """{(kind, variant): set of opaque (x, y)}"""
    out = {}
    for v in EDGE_PROFILES:
        out[("edge", v)] = edge(v)
        out[("outer_corner", v)] = set(CORNERS[v])
        out[("inner_corner", v)] = inner_corner(v)
    return out
