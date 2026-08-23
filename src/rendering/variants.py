"""Trail-activity liveliness and cross-spec total-variation-distance (TVD) diversity.

TCK-20260821-VISUAL-VARIANTS-METRIC. total_variation_distance was written fresh from
experiments/spatial_rendering/PROPOSAL.md:409-413's inline formula -- that section
describes it as code run inline during investigation, never committed to a named
prototype script under experiments/spatial_rendering/prototype/ (confirmed: no
variants/tvd-named file exists there). The formula was independently reproduced this
session and matches PROPOSAL.md's own cited TVD(sandbox_world, dungeon_crawl) ~= 0.2315
anchor to full precision (0.23161981243456373), and dungeon_crawl's structural
same-spec/different-seed invariance (0.0 exactly, since none of its four composed
modules declare terrain_variants), per
staging_artifacts/TCK-20260821-VISUAL-VARIANTS-METRIC/investigation.md.

compute_terrain_histogram is reused directly from this package's density.py sibling
(TCK-20260821-VISUAL-DENSITY-METRIC), never reimplemented -- normalize_histogram exists
here only because TVD's contract requires proportions, not raw counts, and no other
module in this package needs that step (see plan.md Decision 4).

select_trail_entity is a standalone hashlib.sha256(f"{world_id}:{seed}")-derived
selection over a sorted active-entity-ID list -- deliberately NOT DeterministicRNG/
Domain (src/platform/rng.py, src/core/enums.py). Reusing the replay-critical simulation-
randomness mechanism for read-only QA entity selection would be exactly the "hidden,
parallel use of an authoritative mechanism for a non-authoritative purpose" this
project's Durable State Rule warns against, and minting a new Domain value would be a
durable, project-wide addition disproportionate to selecting one entity for a
diagnostic trail (see plan.md Decision 2).

This module returns raw structural facts only -- floats and ints, never a grade or
healthy/unhealthy verdict -- and is not a src.simulation_quality.scorers.base.PillarScorer
subclass; it does not import src.simulation_quality.* or src.observability.events
(TCK-20260821-VISUAL-GRADE-SCORER and TCK-20260821-VISUAL-QUALITY-CALIBRATION own
scoring/grading and threshold calibration, respectively). This module defines zero
classes: every function here returns a primitive float/int/dict, unlike density.py/
shape.py, which need DensityResult/ShapeComponent to bundle multiple derived fields.
"""
from __future__ import annotations

import hashlib

from src.rendering.density import compute_terrain_histogram


def normalize_histogram(raw: dict[str, int]) -> dict[str, float]:
    """Converts a raw terrain-type-count histogram (compute_terrain_histogram's output)
    into proportions summing to 1.0, the input contract total_variation_distance requires.
    Empty/zero-total input returns {} rather than raising ZeroDivisionError."""
    total = sum(raw.values())
    if total == 0:
        return {}
    return {k: v / total for k, v in raw.items()}


def total_variation_distance(h1: dict[str, float], h2: dict[str, float]) -> float:
    """0.5 * sum(|h1[k] - h2[k]|) over the union of keys -- standard TVD between two
    categorical distributions. h1/h2 MUST already be normalized proportions (see
    normalize_histogram); this function performs no normalization itself and has no
    awareness of which world/seed produced its inputs -- see module docstring's AC #4
    note. Written fresh from PROPOSAL.md:409-413, unmodified from that formula's shape."""
    keys = set(h1) | set(h2)
    return 0.5 * sum(abs(h1.get(k, 0) - h2.get(k, 0)) for k in keys)


def compute_trail_activity(unique_tiles_visited: int, ticks_sampled: int) -> float:
    """unique_tiles_visited / ticks_sampled, zero-guarded. ticks_sampled MUST be the
    length of the tick window the trail was collected over (total_ticks in
    render_trail.py's terms), NOT the count of recorded position samples (len(trail),
    which is smaller whenever sample_every > 1) -- investigation.md verified the cited
    "~2-3 tiles/100+ ticks" evidence is stated per total ticks run, not per sample count;
    using len(trail) as the denominator would silently produce a materially different,
    non-anchor-matching ratio (e.g. 2/20=0.10 vs the correct 2/200=0.01)."""
    if ticks_sampled == 0:
        return 0.0
    return unique_tiles_visited / ticks_sampled


def select_trail_entity(world_id: str, seed: int, entities: dict) -> int:
    """Deterministically selects one active entity ID to trail-track, given (world_id,
    seed, entities). entities is dict[int, EntityState] -- the same type as
    AuthoritativeState.entities (src/core/state.py:1095, confirmed by direct read).

    Filters to active entities first (EntityState.active, a direct passthrough property
    to self.lifecycle.active -- confirmed src/core/state.py:771-773), THEN sorts the
    surviving IDs (removing any dict-insertion-order dependency), THEN reduces
    hashlib.sha256(f"{world_id}:{seed}".encode()).digest() to an index into that sorted
    list via int.from_bytes(..., "big") % len(sorted_ids).

    Deterministic per (world_id, seed, active-entity-set); independent of dict
    insertion/iteration order (see Decision 2 in plan.md for why this does not reuse
    DeterministicRNG/Domain). Raises ValueError if no active entities exist."""
    active_ids = sorted(eid for eid, ent in entities.items() if ent.active)
    if not active_ids:
        raise ValueError(f"select_trail_entity: no active entities in world {world_id!r}")
    digest = hashlib.sha256(f"{world_id}:{seed}".encode()).digest()
    index = int.from_bytes(digest, "big") % len(active_ids)
    return active_ids[index]
