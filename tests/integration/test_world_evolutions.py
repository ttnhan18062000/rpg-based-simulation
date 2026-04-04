import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


import pytest
from src.config import SimulationConfig
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.platform.rng import DeterministicRNG
from src.core.entities.entity import Entity, Vector2
from src.core.world.regions import Region, Location
from src.systems.infrastructure.base import SystemContext
from src.systems.calamity.calamity_system import CalamitySystem
from src.systems.world.generator import EntityGenerator
from src.core.models.enums import Material, EnemyTier, EntityRole, AIState

class MockEmit:
    def __call__(self, event_name, msg, *args, **kwargs):
        pass

@pytest.fixture
def mock_ctx():
    cfg = SimulationConfig(
        grid_width=100, 
        grid_height=100,
        raid_interval_days=20,
        raid_base_strength=5,
        camp_radius=8,
        camp_max_guards=5,
        town_center_x=50,
        town_center_y=50
    )
    
    rng = DeterministicRNG(seed=123)
    grid = Grid(cfg.grid_width, cfg.grid_height)
    spatial = SpatialHash(cfg.spatial_cell_size)
    world = WorldState(seed=123, grid=grid, spatial_index=spatial)
    
    # Initialize the generator properly
    generator = EntityGenerator(cfg, rng)
    
    ctx = SystemContext(
        config=cfg,
        world=world,
        rng=rng,
        generator=generator,
        faction_reg=None,
        emit=MockEmit()
    )
    return ctx

def test_raid_trigger(mock_ctx):
    sys = CalamitySystem(mock_ctx.config, mock_ctx.rng)
    world = mock_ctx.world
    
    # Fast forward ticks to hit a raid interval
    raid_tick = mock_ctx.config.raid_interval_days * 100
    world.tick = raid_tick
    
    sys._check_faction_raids(mock_ctx, raid_tick)
    
    # Expect 5 + (20 // 10) = 7 enemies
    expected_size = mock_ctx.config.raid_base_strength + (world.world_day // 10)
    
    raiders = [e for e in world.entities.values() if e.mind.ai_state == AIState.RAID]
    assert len(raiders) == expected_size
    assert all(e.spatial.home_pos is None for e in raiders) # Raiders shouldn't have homes

def test_camp_reinforcements(mock_ctx):
    sys = CalamitySystem(mock_ctx.config, mock_ctx.rng)
    world = mock_ctx.world
    
    # Setup a mock region and camp
    camp_pos = Vector2(50, 50)
    camp = Location(location_id="camp_1", name="Goblin Camp", location_type="enemy_camp", pos=camp_pos, region_id="reg_1")
    region = Region(region_id="reg_1", name="Test Region", terrain=Material.FOREST, center=Vector2(50, 50), radius=20, difficulty=1)
    region.locations.append(camp)
    world.regions.append(region)
    
    # Tick 500: Camp is empty -> Spawn 1 guard
    world.tick = 500
    sys._check_camp_reinforcements(mock_ctx, 500)
    print("ALL ENTITIES: ", list(world.entities.values()))
    guards_1 = [e for e in world.entities.values() if e.spatial.home_pos and e.spatial.home_pos.manhattan(camp_pos) <= mock_ctx.config.camp_radius]
    assert len(guards_1) == 1
    assert camp.reinforcement_level == 0
    
    # Manually populate camp to full
    for i in range(5):
        guard = Entity(id=world.allocate_entity_id(), kind="goblin")
        guard.identity.role = EntityRole.MOB
        guard.spatial.home_pos = camp_pos
        guard.spatial.pos = camp_pos
        world.add_entity(guard)
        
    world.tick = 1000
    # Tick 1000: Camp is full -> Increment reinforcement level
    sys._check_camp_reinforcements(mock_ctx, 1000)
    assert camp.reinforcement_level == 1
    
    # Next reinforcement check: spawn at higher tier
    # Empty camp
    for g in list(world.entities.values()):
        world.remove_entity(g.id)
        
    world.tick = 1500
    sys._check_camp_reinforcements(mock_ctx, 1500)
    guards_new = list(world.entities.values())
    assert len(guards_new) == 1
    assert guards_new[0].identity.tier == 2 # Base region difficulty (1) + reinforcement level (1) = 2

def test_generator_scaling(mock_ctx):
    world = mock_ctx.world
    gen = mock_ctx.generator
    
    world.tick = 0
    # Day 0 mob
    mob_day_0 = gen.spawn_race(world, "goblin", tier=0, difficulty_tier=1)
    base_hp_day_0 = mob_day_0.combat.max_hp
    
    world.tick = 400 * 100 # Day 400
    # Day 400 mob
    mob_day_400 = gen.spawn_race(world, "goblin", tier=0, difficulty_tier=1)
    base_hp_day_400 = mob_day_400.combat.max_hp
    
    # HP multiplier is 1.0 + (400/200)*0.5 = 2.0. Base stats also have some randomness, but day 400 should be ~2x
    # Allow some leeway for the + randomness (15-25 base range) -> 1.5x to 3x increase
    assert base_hp_day_400 > base_hp_day_0 * 1.2
