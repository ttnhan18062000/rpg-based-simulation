import math
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, RegionState
from src.platform.rng import DeterministicRNG
from src.core.enums import Domain
from src.systems.world_systems.generator import EntityGenerator
from src.world.calamity import CalamityService
from src.world.raid import RaidService

def test_calamity_raid_maturity_advancement():
    # Initial state
    state = AuthoritativeState(tick=999, seed=42, maturity=0)
    
    # Process at tick 1000
    state_at_1000 = replace(state, tick=1000)
    generator = EntityGenerator(seed=42)
    update = CalamityService.process_world_dynamics(state_at_1000, generator)
    
    assert update.maturity_set == 1

def test_calamity_raid_spawning():
    generator = EntityGenerator(seed=42)
    # Raid occurs every 5 days (500 ticks)
    # TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION: the global raid
    # now targets a real CITY place instead of the hardcoded world origin, so this fixture needs
    # one. Previously it needed no places at all, which is exactly how the (0,0) assumption
    # survived unnoticed. Every corpus world has exactly one CITY (verified), so one here matches
    # production. The no-city case is covered by
    # tests/unit/world/test_raid_spawn_origin.py::test_global_raid_does_not_fire_with_no_city_to_raid.
    from src.core.state import PlaceState, PlaceKind
    city = PlaceState(place_id="city_1", region_id="hometown", kind=PlaceKind.CITY,
                      position=(130.0, 130.0))
    state = AuthoritativeState(tick=500, seed=42, maturity=2, places={"city_1": city})

    update = RaidService.check_for_raid(state, generator)

    # Raid size = Base (3) + Maturity (2) = 5
    assert len(update.entities_add) == 5
    for mob in update.entities_add:
        assert mob.kind == "goblin_raider"
        # Navigation target is the raided city, not the world origin (behaviour change above).
        assert mob.navigation.target == city.position
        # TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION: a raid mob's
        # navigation.target is a raw assignment with no accompanying strategic project, so any
        # capacity-gated goal scorer (confirmed real: GuildNeedScorer, once its own flag actually
        # reached a real run) would otherwise freely overwrite it. Zero project capacity is the
        # real, verified fix -- not a scorer-side faction filter, which broke a different, live,
        # intended case (non-hero-faction entities elsewhere in the corpus legitimately do run
        # the generic project/goal system).
        assert mob.strategic.profile.max_active_projects == 0


def test_calamity_raid_spawn_positions_are_the_ring_around_the_chosen_anchor():
    """
    Spawn positions are the deterministic ring around whatever anchor the global raid chose,
    independently recomputed from the same RNG call the service makes.

    Originally TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX asserted byte-identical positions against
    a hardcoded (0,0) origin. TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-
    REGION replaced that origin with a real anchor, so the expectation is now recomputed from
    `global_raid_anchor()` instead of from zero. The ring geometry it was really guarding is
    unchanged and still asserted.

    The fixture now carries a region: without one this test went *vacuously green* -- no anchor
    meant no raid, `entities_add` was empty, and the loop body never ran. The explicit
    non-empty assertion below is what stops that from recurring.
    """
    generator = EntityGenerator(seed=42)
    region = RegionState(id="hometown", name="Hometown", bounds=(100, 100, 160, 160))
    state = AuthoritativeState(tick=500, seed=42, maturity=2, regions={"hometown": region})

    update = RaidService.check_for_raid(state, generator)
    assert update.entities_add, "no raiders spawned -- this test would otherwise pass vacuously"

    anchor = RaidService.global_raid_anchor(state)
    assert anchor is not None

    rng = DeterministicRNG(state.seed)
    angle = rng.get_float(Domain.CALAMITY, state.tick, 0) * 2 * math.pi
    dist = RaidService.SANCTUARY_RADIUS + 10
    expected_spawn_pos = (
        anchor[0] + int(math.cos(angle) * dist),
        anchor[1] + int(math.sin(angle) * dist),
    )

    for i, mob in enumerate(update.entities_add):
        expected_pos = (
            expected_spawn_pos[0] + (i % 3) - 1,
            expected_spawn_pos[1] + (i // 3) - 1,
        )
        assert mob.navigation.position == expected_pos

def test_calamity_intensity_shift():
    from src.core.state import EntityState, IdentityComponent, CombatComponent
    from src.core.enums import Faction
    
    region = RegionState(id="wild", name="Wild", bounds=(0, 0, 10, 10), hazard_level=0.8, calamity_intensity=0.1)
    state = AuthoritativeState(tick=100, seed=42, regions={"wild": region})
    
    # Hero death in high-hazard region
    from src.core.builder import V2EntityBuilder
    hero = (V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .identity(faction=Faction.HERO_GUILD)
        .combat(hp=0)
        .combat(alive=False)
        .build())
    
    update = CalamityService.apply_calamity_consequences(state, [hero])
    assert update.world_updates["wild"].calamity_intensity_set == pytest.approx(0.15)
