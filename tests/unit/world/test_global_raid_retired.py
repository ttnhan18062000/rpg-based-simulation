"""The global world-clock raid is retired.

TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION.

`RaidService.check_for_raid` fired on a `tick % 500` cadence and passed `origin=(0, 0),
target=(0, 0)` literally, so every raider spawned on the radius-25 ring around world coordinate
(0,0) -- outside every region -- and sat there. Measured over 2 corpus worlds / 4 raid events:
12/12 raiders off-region, and in the world where they never drifted into one, zero raider combat
and bit-identical regional influence. It had never once produced a raid.

Retiring it stops the creation of regionless, inert entities. The camp-triggered path, which has
real provenance, survives and is asserted here to still work.
"""

from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate
from src.engine.world_dynamics import WorldDynamicsSystem
from src.systems.world_systems.generator import EntityGenerator
from src.world.raid import RaidService


def test_global_world_clock_raid_surface_is_absent():
    """`check_for_raid` is gone, not merely guarded.

    A guarded-but-present entry point invites a future caller to re-enable a mechanic that has
    never functioned. If world-clock raids return they do so as a declared feature with a
    settlement-Place target (PLACE-01: a bare coordinate is not a Place).
    """
    assert not hasattr(RaidService, "check_for_raid")
    # The withdrawn re-anchoring attempt's helpers must not linger either.
    assert not hasattr(RaidService, "global_raid_anchor")
    assert not hasattr(RaidService, "city_places")


def test_no_raiders_spawn_on_the_former_cadence_tick():
    """Tick 500 was the global raid's cadence tick. Nothing spawns there now.

    Logic ID: WORLD-032 (retired)
    """
    region = RegionState(id="hometown", name="Hometown", bounds=(100, 100, 160, 160))
    state = AuthoritativeState(tick=500, seed=42, regions={"hometown": region})

    refined = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), EntityGenerator(42))

    raiders = [e for e in refined.entities_add if e.kind == "goblin_raider"]
    assert raiders == [], f"{len(raiders)} raider(s) still spawned on the retired cadence"


def test_no_entity_is_created_at_the_world_origin_ring_on_the_cadence_tick():
    """The specific defect: durable entities on the radius-25 ring around (0,0).

    Asserted as "nothing lands outside every region", which is the property that actually
    mattered -- the raiders were unreachable debris, not merely oddly placed.
    """
    region = RegionState(id="hometown", name="Hometown", bounds=(100, 100, 160, 160))
    state = AuthoritativeState(tick=500, seed=42, regions={"hometown": region})

    refined = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), EntityGenerator(42))

    x0, y0, x1, y1 = region.bounds
    outside = [
        e.navigation.position for e in refined.entities_add
        if not (x0 <= e.navigation.position[0] <= x1 and y0 <= e.navigation.position[1] <= y1)
    ]
    assert outside == [], f"entities created outside every region: {outside}"


def test_camp_triggered_spawn_raid_is_retired_too():
    """D70 (TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70): the camp path's `spawn_raid` is gone as well, so no raid composition
    survives and no raider can be conjured at a camp."""
    assert not hasattr(RaidService, "spawn_raid")
