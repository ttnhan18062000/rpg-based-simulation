import pytest
from src_legacy.core.state import AuthoritativeState
from src_legacy.world.raid import RaidService
from src_legacy.world.calamity import CalamityService
from src_legacy.systems.generator import EntityGenerator
from src_legacy.core.updates import StateUpdate

def test_raid_spawning():
    """
    Law: Raids must spawn periodically to threaten the town.
    """
    # Raid interval is 5 days = 500 ticks
    state = AuthoritativeState(tick=500, seed=1, entities={}, regions={}, maturity=1)
    generator = EntityGenerator(1)
    
    upd = RaidService.check_for_raid(state, generator)
    
    # Verify entities added (Base 3 + Maturity 1 = 4)
    assert len(upd.entities_add) == 4
    for ent in upd.entities_add:
        assert ent.kind == "goblin_raider"
        assert ent.navigation.target == (0, 0) # Targets town

def test_calamity_maturity():
    """
    Law: World maturity increases over time.
    """
    # Maturity interval is 1000
    state = AuthoritativeState(tick=1000, seed=1, entities={}, maturity=0)
    generator = EntityGenerator(1)
    
    upd = CalamityService.process_world_dynamics(state, generator)
    assert upd.maturity_set == 1

def test_calamity_boss_spawn():
    """
    Law: Calamities spawn in high-intensity regions.
    """
    from src_legacy.core.state import RegionState
    region = RegionState(
        id="danger_zone", name="Abyss",
        bounds=(-10, -10, 10, 10), calamity_intensity=0.5
    )
    
    # Tick >= 2000 (MIN_INTERVAL) and multiple of 5000 (FORCE_INTERVAL)
    state = AuthoritativeState(
        tick=5000, seed=1, last_calamity_tick=0,
        entities={}, regions={"danger_zone": region}
    )
    generator = EntityGenerator(1)
    
    upd = CalamityService.process_world_dynamics(state, generator)
    
    assert len(upd.entities_add) == 1
    assert upd.entities_add[0].kind == "world_boss"
    assert upd.last_calamity_tick_set == 5000
