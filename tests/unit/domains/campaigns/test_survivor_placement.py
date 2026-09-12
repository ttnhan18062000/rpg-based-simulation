"""
tests/unit/domains/campaigns/test_survivor_placement.py
────────────────────────────────────────────────────────────────────────────────
Unit tests for src/domains/campaigns/survivor_placement.py —
TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import BuildingState
from src.domains.campaigns.survivor_placement import (
    SurvivorReconstructionContext,
    resolve_survivor_position,
)
from src.engine.legality import LegalityServiceV2
from src.core.enums import ReasonCode


def _entity_at(entity_id: int, pos: tuple[float, float]):
    return (
        V2EntityBuilder(entity_id)
        .kind("HERO")
        .location(*pos)
        .build()
    )


def _empty_ctx(entities=None) -> SurvivorReconstructionContext:
    return SurvivorReconstructionContext(
        terrain={},
        blocked_tiles=set(),
        buildings={},
        entities=entities if entities is not None else {},
    )


# ---------------------------------------------------------------------------
# The staleness reproduction: this is the test the __slots__ declaration's own
# comment names. Confirms the reconstruction context deterministically takes
# LegalityServiceV2.verify_occupancy()'s uncached direct-.entities-scan path
# (src/engine/legality.py's "path 3"), never the cached
# SpatialQueryService.get_occupancy_map() path, even when the same context
# object is reused across a loop that mutates .entities in place.
# ---------------------------------------------------------------------------

def test_reconstruction_context_slots_force_uncached_occupancy_scan():
    entities = {1: _entity_at(1, (5.0, 5.0))}
    ctx = _empty_ctx(entities)

    # First check: (7, 7) is free -- no entity there yet.
    ok, _reason = LegalityServiceV2.verify_occupancy((7.0, 7.0), ctx)
    assert ok is True

    # Mutate .entities on the SAME context object -- simulating a second survivor
    # being placed at (7, 7) later in the same reconstruction pass.
    entities[2] = _entity_at(2, (7.0, 7.0))

    # Second check, same tile, same object: if verify_occupancy() took the cached
    # get_occupancy_map() path, this would incorrectly return True/LEGAL (the map
    # cached before entity 2 existed). The uncached path must see the mutation.
    ok2, reason2 = LegalityServiceV2.verify_occupancy((7.0, 7.0), ctx)
    assert ok2 is False
    assert reason2 == ReasonCode.OCCUPANCY_VIOLATION

    # And the cache attribute must never have been successfully written -- proves
    # get_occupancy_map()'s object.__setattr__ call really did raise, not just that
    # the end-to-end answer happened to be right for some other reason.
    assert getattr(ctx, "_occupancy_map_cache", "NOT_SET") == "NOT_SET"


def test_reconstruction_context_slots_are_exactly_the_documented_set():
    """Guards against silent drift: the __slots__ list must stay exactly this
    set. Adding any attribute here (including one of the three names the
    mechanism depends on staying absent) risks silently re-enabling the cached
    occupancy path -- see the class docstring."""
    assert SurvivorReconstructionContext.__slots__ == (
        "terrain", "blocked_tiles", "buildings", "building_tiles",
        "transient_claims", "entities",
    )
    ctx = _empty_ctx()
    for forbidden in ("occupancy_snapshot", "occupancy_map", "_occupancy_map_cache"):
        assert not hasattr(ctx, forbidden)


# ---------------------------------------------------------------------------
# resolve_survivor_position
# ---------------------------------------------------------------------------

def test_resolve_survivor_position_uses_carried_position_when_free():
    ctx = _empty_ctx()
    pos = resolve_survivor_position(1, (10.0, 10.0), ctx, world_width=50, world_height=50, regions={})
    assert pos == (10.0, 10.0)


def test_resolve_survivor_position_probes_away_from_another_survivor():
    entities = {1: _entity_at(1, (10.0, 10.0))}
    ctx = _empty_ctx(entities)
    pos = resolve_survivor_position(2, (10.0, 10.0), ctx, world_width=50, world_height=50, regions={})
    assert pos != (10.0, 10.0)
    # Must land on a real, still-legal tile, not just "somewhere".
    ok, _ = LegalityServiceV2.verify_occupancy(pos, ctx)
    assert ok is True


def test_resolve_survivor_position_two_colliding_survivors_land_on_different_tiles():
    """Two survivors both carrying the same position must not collapse onto each
    other, or onto a shared default -- that's the bug this whole ticket fixes."""
    ctx = _empty_ctx()
    pos_a = resolve_survivor_position(1, (20.0, 20.0), ctx, world_width=50, world_height=50, regions={})
    ctx.entities[1] = _entity_at(1, pos_a)
    pos_b = resolve_survivor_position(2, (20.0, 20.0), ctx, world_width=50, world_height=50, regions={})
    assert pos_a != pos_b


def test_resolve_survivor_position_probes_away_from_blocked_tile():
    ctx = SurvivorReconstructionContext(
        terrain={}, blocked_tiles={(15, 15)}, buildings={}, entities={},
    )
    pos = resolve_survivor_position(1, (15.0, 15.0), ctx, world_width=50, world_height=50, regions={})
    assert pos != (15.0, 15.0)
    ok, _ = LegalityServiceV2.verify_occupancy(pos, ctx)
    assert ok is True


def test_resolve_survivor_position_probes_away_from_wall_terrain():
    ctx = SurvivorReconstructionContext(
        terrain={(15, 15): "WALL"}, blocked_tiles=set(), buildings={}, entities={},
    )
    pos = resolve_survivor_position(1, (15.0, 15.0), ctx, world_width=50, world_height=50, regions={})
    assert pos != (15.0, 15.0)


def test_resolve_survivor_position_probes_away_from_building():
    building = BuildingState(id=1, kind="SHOP", position=(15.0, 15.0))
    ctx = SurvivorReconstructionContext(
        terrain={}, blocked_tiles=set(), buildings={1: building}, entities={},
    )
    pos = resolve_survivor_position(1, (15.0, 15.0), ctx, world_width=50, world_height=50, regions={})
    assert pos != (15.0, 15.0)


def test_resolve_survivor_position_none_last_position_uses_deterministic_fallback():
    ctx = _empty_ctx()
    pos_1 = resolve_survivor_position(1, None, ctx, world_width=50, world_height=50, regions={})
    pos_2 = resolve_survivor_position(1, None, ctx, world_width=50, world_height=50, regions={})
    # Deterministic: same entity_id, same call, same result.
    assert pos_1 == pos_2
    ok, _ = LegalityServiceV2.verify_occupancy(pos_1, ctx)
    assert ok is True


def test_resolve_survivor_position_different_entities_missing_last_position_differ():
    """Two survivors both missing last_position must not both fall back to the
    same shared origin colliding -- the resolution chain's own deconfliction
    against .entities handles this, but only if the fallback origin computation
    itself feeds real, checked candidates rather than a bare constant return."""
    ctx = _empty_ctx()
    pos_a = resolve_survivor_position(1, None, ctx, world_width=50, world_height=50, regions={})
    ctx.entities[1] = _entity_at(1, pos_a)
    pos_b = resolve_survivor_position(2, None, ctx, world_width=50, world_height=50, regions={})
    assert pos_a != pos_b


def test_resolve_survivor_position_expands_search_beyond_fixed_probe_ring():
    """Pack every tile the fixed _DECONFLICT_PROBE_OFFSETS ring would reach
    around the origin, and confirm the expanding search finds a legal tile
    beyond it rather than exhausting immediately."""
    origin = (25, 25)
    packed = {origin}
    # _DECONFLICT_PROBE_OFFSETS covers offsets up to distance 2 from the origin --
    # pack a slightly larger box to guarantee the fixed ring is fully exhausted.
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            packed.add((origin[0] + dx, origin[1] + dy))
    ctx = SurvivorReconstructionContext(
        terrain={}, blocked_tiles=packed, buildings={}, entities={},
    )
    pos = resolve_survivor_position(
        1, (float(origin[0]), float(origin[1])), ctx, world_width=50, world_height=50, regions={}
    )
    assert (int(pos[0]), int(pos[1])) not in packed
    ok, _ = LegalityServiceV2.verify_occupancy(pos, ctx)
    assert ok is True


def test_resolve_survivor_position_exhaustion_logs_warning_and_still_returns(caplog):
    """A world with no legal tile anywhere must not hang or raise -- it logs a
    warning (mirroring compiler.py's own LAW-SPAWN-OCCUPANCY exhaustion
    precedent) and returns a real, real-typed tuple anyway, never silently."""
    import logging

    blocked = {(x, y) for x in range(5) for y in range(5)}
    ctx = SurvivorReconstructionContext(
        terrain={}, blocked_tiles=blocked, buildings={}, entities={},
    )
    with caplog.at_level(logging.WARNING, logger="src.domains.campaigns.survivor_placement"):
        pos = resolve_survivor_position(
            99, (2.0, 2.0), ctx, world_width=5, world_height=5, regions={}
        )
    assert isinstance(pos, tuple) and len(pos) == 2
    assert any("could not be placed on a free tile" in r.message for r in caplog.records)
    assert any("99" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Terrain instability across episode seeds -- built from a real seed
# disagreement, not a hand-placed fixture.
# ---------------------------------------------------------------------------

def test_terrain_instability_real_seed_disagreement_triggers_fallback():
    """Compile the same real corpus world at two different episode seeds, find
    a tile the two compiles genuinely disagree on (walkable in one, blocked in
    the other), and confirm a survivor carrying that position through
    resolve_survivor_position() against the second compile is relocated away
    from it rather than accepted as-is."""
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    repo = WorldRepository("data/worlds")
    spec, ctx_load = repo.load_world_with_context("unit_faction_tension")

    disagreement = None
    for seed_a, seed_b in [(0, 1), (10, 11), (100, 101), (7, 8), (50, 51)]:
        state_a, _ = WorldCompiler.compile(spec, seed=seed_a, context=ctx_load)
        state_b, _ = WorldCompiler.compile(spec, seed=seed_b, context=ctx_load)
        for tile in state_a.blocked_tiles.union(state_b.blocked_tiles):
            walkable_in_a = tile not in state_a.blocked_tiles
            blocked_in_b = tile in state_b.blocked_tiles
            if walkable_in_a and blocked_in_b:
                disagreement = (tile, state_b)
                break
        if disagreement is not None:
            break

    assert disagreement is not None, (
        "expected at least one real blocked_tiles disagreement between two "
        "episode-seed compiles of unit_faction_tension -- if this now fails, "
        "the corpus or the compiler's own seed-dependence changed and this "
        "test's premise needs re-checking, not silencing"
    )
    blocked_tile, state_b = disagreement

    reconstruction_ctx = SurvivorReconstructionContext(
        terrain=state_b.terrain,
        blocked_tiles=state_b.blocked_tiles,
        buildings=state_b.buildings,
        entities={},
    )
    resolved = resolve_survivor_position(
        1,
        (float(blocked_tile[0]), float(blocked_tile[1])),
        reconstruction_ctx,
        world_width=spec.topology.width,
        world_height=spec.topology.height,
        regions={},  # region label lookup (exhaustion-warning-only) not under test here
    )
    assert (int(resolved[0]), int(resolved[1])) != blocked_tile
    ok, _ = LegalityServiceV2.verify_occupancy(resolved, reconstruction_ctx)
    assert ok is True
