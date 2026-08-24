"""Connected-component-aware fill-ratio and 90-degree rotation/repetition detection.

TCK-20260821-VISUAL-SHAPE-METRIC. Ports experiments/spatial_rendering/PROPOSAL.md:365-380's
BFS flood-fill shape, but -- unlike that inline example, and unlike this package's own
connectivity.py sibling (TCK-20260821-VISUAL-CONNECTIVITY-METRIC), which builds exactly one
walkable_tiles set and runs BFS once to answer "is the whole map one reachable region" --
this module must invoke the BFS once PER DISTINCT RAW TERRAIN-TYPE STRING VALUE, each
invocation scoped to that type's own tile set. This is the exact fix for the "real bug, caught
and fixed" PROPOSAL.md:358-385 documents: the original fill-ratio implementation aggregated
all tiles of one terrain type into a single bounding box with no connectivity check at all,
which produced a wrong, meaningless FOREST fill-ratio of 0.716 (two unrelated 1.000-fill-ratio
rectangles averaged together) instead of the correct 1.000/1.000 pair. No prototype script
exists to promote for this metric family (confirmed via
`find experiments/spatial_rendering/prototype/ -iname "*shape*"` -> no hits,
staging_artifacts/TCK-20260821-VISUAL-SHAPE-METRIC/investigation.md) -- this module is written
fresh from PROPOSAL.md's inline prose/code, same situation
TCK-20260821-VISUAL-CONNECTIVITY-METRIC's BFS was in before it was ported into connectivity.py.

Fill-ratio formula: PROPOSAL.md:204 ("tiles_of_type / bounding_box_area"), applied per
connected component per PROPOSAL.md:383-385's correction, not per terrain-type aggregate --
verified against real running code in investigation.md (dungeon_crawl: CAVE=0.9804,
FOREST-c0=1.0000, FOREST-c1=1.0000, RUIN=1.0000).

Rotation-detection heuristic: PROPOSAL.md:431 describes it only as "the transposed-coordinate
set comparison matched exactly" against bounding boxes 36x31 and 31x36. investigation.md
reconstructed the concrete method used here: normalize each component's tiles to its own
origin, then test three transforms of component a against component b (transpose,
rotate-90-CW, rotate-90-CCW), gated first on a bounding-box dimension swap. See
detect_rotation_match's own docstring for the corrected rotation formulas and the solid-
rectangle caveat.

This module returns raw structural facts only (ShapeComponent, floats, booleans) -- never a
grade/S-A-B-C-D-F band or a healthy/unhealthy verdict, and is not a
src.simulation_quality.scorers.base.PillarScorer subclass; it does not import
src.simulation_quality.* or src.observability.events (TCK-20260821-VISUAL-GRADE-SCORER and
TCK-20260821-VISUAL-QUALITY-CALIBRATION own scoring/grading and threshold calibration,
respectively).

Known limitation (documented, not solved, per this ticket's own Scope): fill-ratio does not
decompose composite shapes into constituent rectangles, so a shape formed by unioning several
stamped rectangles (e.g. frontier_extended's FOREST) can score *lower* than a single stamped
rectangle even though it is still just as artificial/non-organic -- PROPOSAL.md:393 names this
as a real gap, out of scope for this ticket to fix.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class ShapeComponent:
    terrain_type: str
    tiles: frozenset[tuple[int, int]]
    size: int
    bbox: tuple[int, int, int, int]  # (min_x, min_y, max_x, max_y)
    fill_ratio: float


def group_terrain_by_type(
    terrain: dict[tuple[int, int], str],
) -> dict[str, set[tuple[int, int]]]:
    """Groups tile positions by their raw, non-normalized terrain-type string value.

    The grouping key is exactly the string as it appears in terrain.values() -- no
    .upper()/.lower() normalization here. The real corpus contains distinct raw keys like
    'PLAIN' and 'plain' as separate terrain-type strings (a known casing fragmentation,
    documented by this ticket's sibling tickets); only the exclusion test in
    connected_components is case-insensitive, never the grouping key itself.
    """
    grouped: dict[str, set[tuple[int, int]]] = {}
    for pos, tval in terrain.items():
        grouped.setdefault(tval, set()).add(pos)
    return grouped


def _bfs_component(
    start: tuple[int, int],
    tile_set: set[tuple[int, int]],
    visited: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Single BFS flood-fill over one pre-scoped tile_set, 4-connectivity."""
    comp: list[tuple[int, int]] = []
    q: deque[tuple[int, int]] = deque([start])
    visited.add(start)
    while q:
        x, y = q.popleft()
        comp.append((x, y))
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nb = (x + dx, y + dy)
            # Membership checked against the precomputed tile_set, not a live predicate --
            # mirrors connectivity.py's documented reason: an unbounded live re-check would
            # flood-fill past any tile absent from the terrain dict.
            if nb in tile_set and nb not in visited:
                visited.add(nb)
                q.append(nb)
    return comp


def compute_bbox(tiles: frozenset[tuple[int, int]] | set[tuple[int, int]]) -> tuple[int, int, int, int]:
    """(min_x, min_y, max_x, max_y) over this component's own tile coordinates only --
    never the terrain-type's aggregate bounding box (that was the pre-fix bug,
    PROPOSAL.md Section 5c)."""
    xs = [x for x, _y in tiles]
    ys = [y for _x, y in tiles]
    return (min(xs), min(ys), max(xs), max(ys))


def compute_fill_ratio(tiles: frozenset[tuple[int, int]] | set[tuple[int, int]]) -> float:
    """len(tiles) / bounding_box_area, where bounding_box_area =
    (max_x - min_x + 1) * (max_y - min_y + 1), computed per connected component.

    Formula: PROPOSAL.md:204 ('tiles_of_type / bounding_box_area'), applied per component
    per PROPOSAL.md:383-385's correction, verified against real running code in
    investigation.md (dungeon_crawl: CAVE=0.9804, FOREST-c0=1.0000, FOREST-c1=1.0000,
    RUIN=1.0000).
    """
    min_x, min_y, max_x, max_y = compute_bbox(tiles)
    bbox_area = (max_x - min_x + 1) * (max_y - min_y + 1)
    return len(tiles) / bbox_area


def connected_components(
    terrain: dict[tuple[int, int], str],
    min_size: int = 20,
    excluded_types: frozenset[str] = frozenset({"PLAIN", "ROAD"}),
) -> list[ShapeComponent]:
    """Groups terrain by raw type string (group_terrain_by_type), then runs BFS
    flood-fill labeling ONCE PER DISTINCT TYPE, scoped to that type's own tile set --
    never one global BFS across all terrain (that is connectivity.py's walkability
    question, a different question). Components smaller than min_size are dropped.
    Types whose UPPERCASED value is in excluded_types are skipped entirely -- the
    exclusion test is case-insensitive; grouping itself stays keyed on raw casing
    (investigation.md's confirmed corpus dump: 'PLAIN'/'plain'/'ROAD'/'road' all occur
    as distinct raw values in the real corpus).
    """
    grouped = group_terrain_by_type(terrain)
    components: list[ShapeComponent] = []

    for tval, tile_set in grouped.items():
        if tval.upper() in excluded_types:
            continue

        visited: set[tuple[int, int]] = set()
        for start in tile_set:
            if start in visited:
                continue
            raw_component = _bfs_component(start, tile_set, visited)
            if len(raw_component) < min_size:
                continue
            tiles = frozenset(raw_component)
            components.append(
                ShapeComponent(
                    terrain_type=tval,
                    tiles=tiles,
                    size=len(tiles),
                    bbox=compute_bbox(tiles),
                    fill_ratio=compute_fill_ratio(tiles),
                )
            )

    return components


def _normalize(
    tiles: frozenset[tuple[int, int]], min_x: int, min_y: int
) -> frozenset[tuple[int, int]]:
    """{(x - min_x, y - min_y) for x, y in tiles} -- shift a component's tiles to its own
    origin."""
    return frozenset((x - min_x, y - min_y) for x, y in tiles)


def detect_rotation_match(a: ShapeComponent, b: ShapeComponent) -> bool:
    """Tests whether component b's tile pattern matches a 90-degree rotation (or
    transpose) of component a's tile pattern.

    Gated first on bounding-box dimension swap: w_a == h_b and h_a == w_b, where
    w = max_x - min_x, h = max_y - min_y (bounding-box EXTENTS, not tile counts -- see the
    corrected-formula note below). If the dimensions do not swap, returns False
    immediately -- no tile comparison needed.

    If gated, normalizes both components' tiles to their own origin (_normalize) and
    tests three transforms of a's normalized set against b's normalized set:
      - transpose:      (x, y) -> (y, x)
      - rotate-90-CW:    (x, y) -> (y, w_a - x)
      - rotate-90-CCW:   (x, y) -> (h_a - y, x)
    Returns True if ANY of the three transformed sets equals b's normalized tile set.

    NOTE (fixed during Review, TCK-20260821-VISUAL-SHAPE-METRIC): w_a/h_a here are
    bounding-box EXTENTS (max_x - min_x, max_y - min_y), not tile-count widths/heights --
    the formula must NOT subtract an additional 1, since that offset is only correct if
    w_a/h_a were counts (max_x - min_x + 1). Verified directly: for a 3-wide x 2-tall
    rectangle (w_a=2, h_a=1), (x, y) -> (y, w_a - x) correctly produces a 2-wide x 3-tall
    rotated shape with all-non-negative coordinates; the "- 1" variant produces negative
    coordinates and never matches any real rotated pair.

    CAVEAT (do not remove or soften this docstring paragraph): for solid
    (fill_ratio == 1.0) rectangular components, all three transforms coincide identically
    -- a filled rectangle's tile set is invariant under any of them once the bounding-box
    dimensions swap correctly. This function's True result does NOT by itself distinguish
    "true 90-degree rotation" from any other dimension-swapping symmetry for such shapes;
    it is diagnostic only for non-rectangular, textured components
    (investigation.md, TCK-20260821-VISUAL-SHAPE-METRIC).
    """
    a_min_x, a_min_y, a_max_x, a_max_y = a.bbox
    b_min_x, b_min_y, b_max_x, b_max_y = b.bbox

    w_a = a_max_x - a_min_x
    h_a = a_max_y - a_min_y
    w_b = b_max_x - b_min_x
    h_b = b_max_y - b_min_y

    if not (w_a == h_b and h_a == w_b):
        return False

    a_norm = _normalize(a.tiles, a_min_x, a_min_y)
    b_norm = _normalize(b.tiles, b_min_x, b_min_y)

    transpose = frozenset((y, x) for x, y in a_norm)
    rotate_cw = frozenset((y, w_a - x) for x, y in a_norm)
    rotate_ccw = frozenset((h_a - y, x) for x, y in a_norm)

    return b_norm in (transpose, rotate_cw, rotate_ccw)
