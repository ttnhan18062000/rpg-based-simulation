"""Integration tests for the Calamity (World Boss) system."""

import pytest
from unittest.mock import MagicMock
from src.core.enums import AIState, EnemyTier, EntityRole, Faction, HeroClass, Rarity, Domain, ActionType
from src.core.models import Vector2, Entity
from src.core.grid import Grid
from src.systems.spatial_hash import SpatialHash
from src.core.world_state import WorldState
from src.systems.generator import EntityGenerator
from src.engine.world_loop import WorldLoop
from src.config import SimulationConfig
from src.systems.rng import DeterministicRNG
from src.ai.brain import AIBrain
from src.engine.worker_pool import WorkerPool
from src.engine.conflict_resolver import ConflictResolver

@pytest.fixture
def basic_setup():
    import src
    print(f"DEBUG_PATH: {src.__file__}")
    config = SimulationConfig()
    grid = Grid(100, 100)
    spatial = SpatialHash(5)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    rng = DeterministicRNG(42)
    
    brain = AIBrain(config, rng)
    worker_pool = MagicMock() # Mock worker pool to avoid hangs
    conflict_resolver = ConflictResolver(config, rng)
    generator = EntityGenerator(config, rng)
    
    loop = WorldLoop(config, world, worker_pool, conflict_resolver, generator, rng=rng)
    return world, config, rng, generator, loop

def test_calamity_spawning(basic_setup):
    """Verify that World Bosses spawn correctly with legend stats."""
    world, config, rng, gen, loop = basic_setup
    
    # Force a calamity spawn
    boss = gen.spawn_calamity(world, "gorath")
    
    print(f"DEBUG: boss.is_world_boss={boss.is_world_boss}")
    print(f"DEBUG: boss.stats={boss.stats}")
    print(f"DEBUG: boss.kind={boss.kind}")
    
    assert boss.is_world_boss is True
    assert boss.role == EntityRole.WORLD_BOSS
    assert boss.display_name == "Gorath the World-Breaker"
    assert boss.stats.hp >= 500, f"Boss stats too low: {boss.stats}. Kind: {boss.kind}, BossFlag: {boss.is_world_boss}"
    assert boss.stats.atk >= 100 # 20 base * 5x mult
    
    # Check legendary loot
    assert boss.inventory.weapon is not None
    assert boss.inventory.weapon == "gorath_cleaver"

def test_calamity_bounty_generation(basic_setup):
    """Verify that bounties are generated for heroes when a boss spawns."""
    world, config, rng, gen, loop = basic_setup
    
    # Create a hero using the constructor directly since allocate_hero might not exist
    hero = Entity(id=world.allocate_entity_id(), kind="hero", pos=Vector2(10, 10))
    hero.faction = Faction.HERO_GUILD
    hero.display_name = "Test Hero"
    hero.stats.level = 20  # Minimum for calamity_hunter quest
    world.add_entity(hero)
    
    # Trigger spawn tick (5000)
    world.tick = 5000
    loop._check_calamity_spawns()
    
    # Check hero quests
    assert len(hero.quests) > 0
    from src.core.quests import QuestType
    bounty = next((q for q in hero.quests if q.quest_type == QuestType.BOUNTY), None)
    assert bounty is not None
    assert "Bounty:" in bounty.title

def test_calamity_kill_rewards(basic_setup):
    """Verify fame gain and title assignment on boss kill."""
    world, config, rng, gen, loop = basic_setup
    from src.actions.combat import CombatAction
    from src.actions.base import ActionProposal
    
    combat = CombatAction(config, rng)
    
    # Setup hero and boss
    hero = Entity(id=world.allocate_entity_id(), kind="hero", pos=Vector2(10, 10))
    hero.faction = Faction.HERO_GUILD
    hero.display_name = "DragonSlayer"
    hero.stats.level = 20
    world.add_entity(hero)
    
    boss = gen.spawn_calamity(world, "gorath")
    boss.pos = Vector2(10, 11)
    boss.stats.hp = 1 # One-shot for testing
    world.add_entity(boss)
    
    # Force a bounty quest to the hero to test fame gain
    from src.core.quests import Quest, QuestType
    bounty = Quest(
        quest_id="bounty_gorath",
        quest_type=QuestType.BOUNTY,
        title=f"Bounty: {boss.display_name}",
        description="Test bounty",
        target_kind=boss.display_name,
        target_count=1,
        gold_reward=1000,
        xp_reward=1000
    )
    hero.quests.append(bounty)
    
    # Hero performs a killing blow
    proposal = ActionProposal(hero.id, ActionType.ATTACK, boss.id)
    combat.apply(proposal, world)
    
    assert not boss.alive
    assert hero.stats.fame >= 100
    assert any("Slayer of" in t for t in hero.titles)
    assert hero.stats.atk > 0 
