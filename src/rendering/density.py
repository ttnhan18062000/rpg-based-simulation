"""Entity nearest-neighbor coefficient of variation and terrain-type histogram.

TCK-20260821-VISUAL-DENSITY-METRIC. The nearest-neighbor CV formula was never
committed to a named prototype script under experiments/spatial_rendering/prototype/ —
experiments/spatial_rendering/PROPOSAL.md:399-403 and :470 describe it as one-off
verification code, structurally the same situation
TCK-20260821-VISUAL-CONNECTIVITY-METRIC's BFS algorithm was in before it was ported
into src/rendering/connectivity.py. The formula was re-traced and verified directly
against the real corpus (sandbox_world seed 42 tick 0, dungeon_crawl seed 42 tick 0):
population standard deviation of per-entity nearest Euclidean distance divided by the
mean, over active entities only, reproduces the documented ~0.648 / ~0.678 values to
6+ significant figures (0.6478017242079448 / 0.6782405727873148). See
staging_artifacts/TCK-20260821-VISUAL-DENSITY-METRIC/investigation.md for the full
trace, including the ruled-out sample-stdev variant (0.667/0.689, does not match).

compute_terrain_histogram is a verbatim extraction of the counting logic already
committed at experiments/spatial_rendering/prototype/render_world.py:90-95 — not a
reimplementation.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class DensityResult:
    cv: float
    entity_count: int
    nn_distances: list[float]


def compute_density_cv(entities: dict) -> DensityResult:
    active_positions = [
        ent.position for ent in entities.values() if ent.active
    ]
    entity_count = len(active_positions)

    if entity_count < 2:
        return DensityResult(cv=0.0, entity_count=entity_count, nn_distances=[])

    nn_distances: list[float] = []
    for i, (ax, ay) in enumerate(active_positions):
        nearest = min(
            ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
            for j, (bx, by) in enumerate(active_positions)
            if i != j
        )
        nn_distances.append(nearest)

    # population std (ddof=0), NOT stdev() (ddof=1) -- see investigation.md,
    # sample-std produces 0.667 not 0.648 for sandbox_world.
    cv = statistics.pstdev(nn_distances) / statistics.mean(nn_distances)

    return DensityResult(cv=cv, entity_count=entity_count, nn_distances=nn_distances)


def compute_terrain_histogram(terrain: dict) -> dict[str, int]:
    histogram: dict[str, int] = {}
    for tval in terrain.values():
        histogram[tval] = histogram.get(tval, 0) + 1
    return histogram
