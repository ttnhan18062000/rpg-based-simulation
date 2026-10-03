"""Pixel-perfect polylines (pure; no Aseprite)."""

from __future__ import annotations

import pytest

from visual_assets.drawing.errors import AdapterError
from visual_assets.drawing.technique.stroke import stroke_pixels

# ============================================================ pure: strokes


def removable_l_corners(path, protected, cyclic=False):
    """Independent check: L-corner pixels of `path` that are not protected."""
    n = len(path)
    idx = range(n) if cyclic else range(1, n - 1)
    out = []
    for i in idx:
        a, b, c = path[i - 1], path[i], path[(i + 1) % n]
        if (abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 and abs(b[0] - c[0]) + abs(b[1] - c[1]) == 1
                and abs(a[0] - c[0]) == 1 and abs(a[1] - c[1]) == 1 and b not in protected):
            out.append(b)
    return out


def test_stroke_freehand_staircase_is_cleaned_only_with_pixel_perfect():
    trace = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]
    assert stroke_pixels(trace, pixel_perfect=True) == [(0, 0), (1, 1), (2, 2)]
    assert stroke_pixels(trace, pixel_perfect=False) == trace


def test_stroke_long_segment_corners_are_intentional_and_kept():
    assert stroke_pixels([(0, 0), (3, 0), (3, 3)]) == [
        (0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3)]


def test_stroke_mixed_long_and_unit_segments():
    # (4,0) borders a long segment: kept. (4,1) and (5,1) are both unit-step trace; the staircase
    # (4,0)-(4,1)-(5,1)-(5,2) loses ONE corner (the first one found, (4,1)), leaving a diagonal step.
    out = stroke_pixels([(0, 0), (4, 0), (4, 1), (5, 1), (5, 2)])
    assert out == [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 1), (5, 2)]
    assert (4, 0) in out and out[0] == (0, 0) and out[-1] == (5, 2)


def test_stroke_closed_box_keeps_all_corners_and_full_perimeter():
    box = stroke_pixels([(1, 1), (5, 1), (5, 4), (1, 4)], closed=True)
    for corner in [(1, 1), (5, 1), (5, 4), (1, 4)]:
        assert corner in box
    assert box[0] == box[-1] and len(box) == len(set(box)) + 1  # closed: start repeated at the end
    perimeter = {(x, 1) for x in range(1, 6)} | {(x, 4) for x in range(1, 6)} | \
                {(1, y) for y in range(1, 5)} | {(5, y) for y in range(1, 5)}
    assert set(box) == perimeter


def test_stroke_closed_first_and_last_vertex_are_judged_by_their_wrap_around_neighbours():
    # (0,0) has a unit step to (1,0) but a long segment arriving from (0,5); (0,5) likewise leaves
    # to a long segment: both are intentional corners only because of the wrap-around neighbour.
    out = stroke_pixels([(0, 0), (1, 0), (1, 5), (0, 5)], closed=True)
    for corner in [(0, 0), (1, 0), (1, 5), (0, 5)]:
        assert corner in out


def test_stroke_closed_unit_step_loop_is_cleaned_all_the_way_round():
    ring = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3), (2, 3), (1, 3), (0, 3), (0, 2), (0, 1)]
    out = stroke_pixels(ring, closed=True)
    body = out[:-1]
    assert out[0] == out[-1] and len(body) == len(set(body)) and len(body) >= 3
    assert not {(0, 0), (3, 0), (3, 3), (0, 3)} & set(body)  # all four square corners rounded off
    assert len(body) == len(ring) - 4
    assert not removable_l_corners(body, set(), cyclic=True)
    assert stroke_pixels(ring, closed=True, pixel_perfect=False)[:-1] == ring


def test_stroke_tiny_unit_loop_never_collapses_below_three_pixels():
    out = stroke_pixels([(0, 0), (1, 0), (1, 1), (0, 1)], closed=True)
    assert len(set(out)) >= 3


def test_stroke_duplicate_consecutive_points_are_ignored():
    assert stroke_pixels([(0, 0), (0, 0), (1, 0), (1, 0), (1, 1), (2, 1), (2, 2)]) == [
        (0, 0), (1, 1), (2, 2)]
    assert stroke_pixels([(2, 2), (2, 2)]) == [(2, 2)]


def test_stroke_property_random_dense_walks():
    import random
    rng = random.Random(20261002)
    for _ in range(300):
        n = rng.randint(3, 40)
        x, y = rng.randint(0, 20), rng.randint(0, 20)
        walk = [(x, y)]
        for _ in range(n):
            dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            x, y = x + dx, y + dy
            walk.append((x, y))
        raw = stroke_pixels(walk, pixel_perfect=False)
        assert raw == walk  # unit steps rasterise to themselves
        out = stroke_pixels(walk, pixel_perfect=True)
        assert out[0] == walk[0] and out[-1] == walk[-1]  # endpoints preserved
        it = iter(walk)
        assert all(p in it for p in out)  # output is a subsequence of the raw path
        # every interior point of a unit-step walk is trace, so no removable L corner may remain
        assert not removable_l_corners(out, {out[0], out[-1]})
        assert out == stroke_pixels(walk, pixel_perfect=True)  # deterministic


def test_stroke_property_mixed_segments_never_remove_a_protected_vertex():
    import random
    rng = random.Random(7)
    for _ in range(300):
        pts = [(rng.randint(0, 15), rng.randint(0, 15)) for _ in range(rng.randint(2, 6))]
        deduped = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        if any(max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 1 for a, b in zip(deduped, deduped[1:])):
            continue  # only vertex lists whose every segment is long: all corners are intentional
        out = stroke_pixels(pts, pixel_perfect=True)
        assert out == stroke_pixels(pts, pixel_perfect=False)  # nothing to clean
        assert out[0] == deduped[0] and out[-1] == deduped[-1]


def test_stroke_straight_and_diagonal_lines_unchanged_by_cleanup():
    for a, b in [((0, 0), (7, 0)), ((0, 0), (0, 5)), ((0, 0), (6, 6)), ((0, 0), (7, 3))]:
        assert stroke_pixels([a, b], pixel_perfect=True) == stroke_pixels([a, b], pixel_perfect=False)


def test_stroke_single_point_and_empty():
    assert stroke_pixels([(2, 3)]) == [(2, 3)]
    with pytest.raises(AdapterError):
        stroke_pixels([])


