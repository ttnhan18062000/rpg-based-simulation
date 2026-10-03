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
    # TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION: the global
    # world-clock raid (check_for_raid) is RETIRED -- measured over 2 corpus worlds, it had never
    # produced a raid. What this test really exercises is raid composition, which survives as
    # spawn_raid on the camp path, so it now drives that with an explicit origin/target. The
    # retirement itself is asserted in tests/unit/world/test_global_raid_retired.py.
    generator = EntityGenerator(seed=42)
    state = AuthoritativeState(tick=500, seed=42, maturity=2)

    raid_size = RaidService.RAID_BASE_SIZE + state.maturity
    update = RaidService.spawn_raid(
        state, generator, origin=(120.0, 120.0), target=(130.0, 130.0), raid_size=raid_size,
    )

    # Raid size = Base (3) + Maturity (2) = 5
    assert len(update.entities_add) == 5
    for mob in update.entities_add:
        assert mob.kind == "goblin_raider"
        # Navigation target is whatever the caller passed -- spawn_raid has no opinion of its own.
        assert mob.navigation.target == (130.0, 130.0)
        # TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION: a raid mob's
        # navigation.target is a raw assignment with no accompanying strategic project, so any
        # capacity-gated goal scorer (confirmed real: GuildNeedScorer, once its own flag actually
        # reached a real run) would otherwise freely overwrite it. Zero project capacity is the
        # real, verified fix -- not a scorer-side faction filter, which broke a different, live,
        # intended case (non-hero-faction entities elsewhere in the corpus legitimately do run
        # the generic project/goal system).
        assert mob.strategic.profile.max_active_projects == 0


def test_calamity_raid_spawn_positions_are_the_ring_around_the_given_origin():
    """
    Spawn positions are the deterministic ring around the origin the caller passed, independently
    recomputed from the same RNG call the service makes.

    Originally TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX asserted byte-identical positions against a
    hardcoded (0,0) origin, because the only caller then passed (0,0).
    TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION retired that caller,
    so the expectation is recomputed from an explicit origin instead of from zero. The ring geometry
    this test was really guarding is unchanged and still asserted.

    The explicit non-empty assertion matters: an earlier revision of this test went *vacuously
    green* -- its fixture produced no raiders, so the loop body never ran and it asserted nothing.
    """
    generator = EntityGenerator(seed=42)
    state = AuthoritativeState(tick=500, seed=42, maturity=2)
    anchor = (120.0, 120.0)

    update = RaidService.spawn_raid(
        state, generator, origin=anchor, target=(130.0, 130.0), raid_size=5,
    )
    assert update.entities_add, "no raiders spawned -- this test would otherwise pass vacuously"

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
