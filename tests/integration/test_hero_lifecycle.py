import pytest
from src.config import SimulationConfig
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.platform.rng import DeterministicRNG
from src.core.entities.entity import Entity, Vector2
from src.core.models import Inventory
from src.core.models.enums import Faction
from src.systems.lifecycle.hero_lifecycle_system import HeroLifecycleSystem
from src.systems.infrastructure.base import SystemContext

class MockEmit:
    def __call__(self, event_name, msg, *args, **kwargs):
        pass

@pytest.fixture
def mock_ctx():
    cfg = SimulationConfig(grid_width=50, grid_height=50, death_tier_max=4)
    rng = DeterministicRNG(seed=123)
    grid = Grid(cfg.grid_width, cfg.grid_height)
    spatial = SpatialHash(cfg.spatial_cell_size)
    world = WorldState(seed=123, grid=grid, spatial_index=spatial)
    
    ctx = SystemContext(
        config=cfg,
        world=world,
        rng=rng,
        generator=None,
        faction_reg=None,
        emit=MockEmit()
    )
    return ctx

def _create_mock_hero(eid: int, pos: Vector2) -> Entity:
    ent = Entity(id=eid, kind="hero")
    ent.identity.identity.faction = Faction.HERO_GUILD
    ent.spatial.spatial.pos = pos
    ent.spatial.home_pos = Vector2(0, 0)
    ent.identity.display_name = f"Hero {eid}"
    ent.inventory = Inventory(max_slots=10)
    ent.hero_familiarity = {}
    return ent

def test_hero_lifecycle_system_permadeath(mock_ctx):
    sys = HeroLifecycleSystem(mock_ctx.config, mock_ctx.rng)
    
    hero = _create_mock_hero(1, Vector2(10, 10))
    hero.inventory.items = ["potion1", "potion2"]
    hero.inventory.accessory = "ring_of_power"
    hero.inventory.armor = "plate_mail"
    hero.inventory.weapon = "sword"
    
    mock_ctx.world.add_entity(hero)
    
    # 1st death -> Drops normal items
    sys.process_hero_death(mock_ctx, hero, 100)
    assert hero.identity.death_count == 1
    assert hero.inventory.accessory == "ring_of_power" # Still has accessory
    assert len(hero.inventory.items) == 0 # Dropped potions
    assert 1 in mock_ctx.world.entities # Hero is NOT permanently dead
    
    # 2nd death -> Drops accessory
    hero.inventory.items = ["potion3"] # Grabbed something else
    sys.process_hero_death(mock_ctx, hero, 200)
    assert hero.identity.death_count == 2
    assert hero.inventory.accessory is None # Dropped accessory!
    assert hero.inventory.armor == "plate_mail"
    
    # 3rd death -> Drops armor
    sys.process_hero_death(mock_ctx, hero, 300)
    assert hero.identity.death_count == 3
    assert hero.inventory.armor is None # Dropped armor!
    
    # 4th death -> Permadeath!
    sys.process_hero_death(mock_ctx, hero, 400)
    assert hero.identity.death_count == 4
    assert 1 not in mock_ctx.world.entities # Entity removed!
    
    # Should schedule replacement in 50 ticks
    assert len(sys._pending_hero_replacements) == 1
    assert sys._pending_hero_replacements[0]["tick"] == 450
    assert sys._pending_hero_replacements[0]["generation"] == 2
    
def test_hero_lifecycle_system_familiarity(mock_ctx):
    sys = HeroLifecycleSystem(mock_ctx.config, mock_ctx.rng)
    
    h1 = _create_mock_hero(1, Vector2(10, 10))
    h2 = _create_mock_hero(2, Vector2(10, 12))  # Distance 2 (Within Vision)
    
    mock_ctx.world.add_entity(h1)
    mock_ctx.world.add_entity(h2)
    
    # Simulate a tick
    sys.on_tick(mock_ctx, 100)
    
    assert h1.hero_familiarity[2] > 0.0
    assert h2.hero_familiarity[1] > 0.0
    assert h1.hero_familiarity[2] == h2.hero_familiarity[1]
