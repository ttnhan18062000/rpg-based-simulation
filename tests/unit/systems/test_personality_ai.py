import pytest
from src.core.entities.entity import Vector2
from src.ai.states import AIContext, should_flee
from src.core.gameplay.faction import Faction
from src.core.models.snapshot import Snapshot
from src.actions.combat import CombatAction
from src.actions.base import ActionProposal
from src.core.models.enums import ActionType, EntityRole, Faction as FactionEnum, AIState
from src.config import SimulationConfig
from src.platform.rng import DeterministicRNG
from src.core.entities.entity_builder import EntityBuilder

class MockGrid:
    def __init__(self):
        self.width = 100
        self.height = 100
    def is_walkable(self, pos): return True
    def is_town(self, pos): return False
    def get_region_id_at(self, x, y): return "test_region"
    def has_adjacent_wall(self, x, y): return False
    def has_line_of_sight(self, x1, y1, x2, y2): return True

class MockWorld:
    def __init__(self, rng=None):
        self.grid = MockGrid()
        self.event_bus = None
        self.regions = []
        self.entities = {}
        self.tick = 1
        self.seed = 42
        self.rng = rng or DeterministicRNG(42)
        from collections import defaultdict
        self.faction_deaths_per_region = defaultdict(int)
    
    def allocate_entity_id(self):
        return len(self.entities) + 1
    
    def add_entity(self, ent):
        self.entities[ent.id] = ent

def test_grudge_accumulation():
    rng = DeterministicRNG(42)
    world = MockWorld(rng)
    
    attacker = (
        EntityBuilder(rng, 1).kind("monster")
        .at(Vector2(0, 0))
        .faction(FactionEnum.WOLF_PACK)
        .build()
    )
    defender = (
        EntityBuilder(rng, 2).kind("hero")
        .at(Vector2(1, 1))
        .faction(FactionEnum.HERO_GUILD)
        .build()
    )
    
    world.add_entity(attacker)
    world.add_entity(defender)
    
    # ... test logic (grudges are part of mind aspect)
    defender.mind.grudges[attacker.id] = 5.0
    assert defender.mind.grudges[1] == 5.0

def test_should_flee_logic():
    config = SimulationConfig()
    rng = DeterministicRNG(42)
    # Ensure no traits interfere with flee threshold
    actor = EntityBuilder(rng, 1).kind("hero").with_traits(trait_ids=[]).with_attributes().with_caps().build()
    
    # Threshold is base 0.3 (from SimulationConfig)
    # Case 1: Neutral mood (0.5) -> should flee at 30%
    actor.combat.max_hp = 100
    actor.mind.mood = 0.5
    actor.combat.hp = 35 # 35% > 30% -> Should NOT flee
    assert not should_flee(actor, config)
    actor.combat.hp = 25 # 25% < 30% -> Should flee
    assert should_flee(actor, config)
    
    # Case 2: Despair (0.0) -> should flee earlier (higher threshold)
    # mod = (0.5 - 0.0) * 0.2 = 0.1. Effective threshold = 0.3 + 0.1 = 0.4
    actor.mind.mood = 0.0
    actor.combat.hp = 45 # 45% > 40% -> Should NOT flee
    assert not should_flee(actor, config)
    actor.combat.hp = 35 # 35% < 40% -> Should flee
    assert should_flee(actor, config)
    
    # Case 3: Fury (1.0) -> should flee later (lower threshold)
    # mod = (0.5 - 1.0) * 0.2 = -0.1. Effective threshold = 0.3 - 0.1 = 0.2
    actor.mind.mood = 1.0
    actor.combat.hp = 25 # 25% > 20% -> Should NOT flee
    assert not should_flee(actor, config)
    actor.combat.hp = 15 # 15% < 20% -> Should flee
    assert should_flee(actor, config)

def test_locational_memory_on_death():
    rng = DeterministicRNG(42)
    world = MockWorld(rng)
    
    attacker = (
        EntityBuilder(rng, 1).kind("monster")
        .at(Vector2(10, 10))
        .faction(FactionEnum.GOBLIN_HORDE)
        .build()
    )
    victim = (
        EntityBuilder(rng, 2).kind("hero")
        .at(Vector2(10, 10))
        .faction(FactionEnum.HERO_GUILD)
        .build()
    )
    
    from src.core.world.regions import Region
    region = Region(region_id="deadly_forest", name="Deadly Forest", terrain=0, center=Vector2(10, 10), radius=5, difficulty=1)
    
    config = SimulationConfig()
    world.add_entity(attacker)
    world.add_entity(victim)
    world.regions = [region]
    combat = CombatAction(config, rng)
    
    # Victim is alive
    assert victim.combat.alive
    
    # Force a kill
    victim.combat.hp = 1
    attacker.combat.atk = 100
    
    proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
    combat.apply(proposal, world)
    
    if not victim.combat.alive:
        # Region should be marked as dangerous
        assert victim.mind.memory_locations.get("deadly_forest", 0) < 0
        # Killer should be remembered
        assert victim.mind.memory.get("last_killer_id") == attacker.id
        # Mood should be low
        assert victim.mind.mood == 0.2

def test_frontier_locational_penalty():
    rng = DeterministicRNG(42)
    hero = (
        EntityBuilder(rng, 1).kind("hero")
        .at(Vector2(5, 5))
        .faction(FactionEnum.HERO_GUILD)
        .build()
    )
    hero.mind.terrain_memory[(5, 5)] = 1
    
    from src.ai.perception import Perception
    from src.core.world.regions import Region
    from src.core.world.grid import Grid
    
    region1 = Region(region_id="safe", name="Safe", terrain=0, center=Vector2(5, 5), radius=10, difficulty=1)
    region2 = Region(region_id="trauma", name="Trauma", terrain=0, center=Vector2(50, 50), radius=10, difficulty=1)
    hero.mind.memory_locations["trauma"] = -1.0
    
    grid = Grid(100, 100)
    snapshot = Snapshot(
        tick=1, 
        seed=42,
        entities={1: hero},
        grid=grid,
        ground_items={},
        camps=(),
        buildings=(),
        resource_nodes=(),
        treasure_chests=(),
        regions=(region1, region2)
    )
    
    target = Perception.find_frontier_target(hero, snapshot, rng_val=0)
    assert target is not None
