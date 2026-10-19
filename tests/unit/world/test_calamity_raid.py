import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, RegionState
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

def test_the_camp_raid_spawner_is_retired():
    """D70 (TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70): `RaidService.spawn_raid` conjured raiders from nothing and is gone."""
    assert not hasattr(RaidService, "spawn_raid")


def test_calamity_intensity_shift():
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
