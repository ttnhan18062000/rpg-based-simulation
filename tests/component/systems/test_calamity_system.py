import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


"""Integration tests for the Calamity (World Boss) system."""

import pytest
from unittest.mock import MagicMock
from src.core.models.enums import AIState, EnemyTier, EntityRole, Faction, HeroClass, Rarity, Domain, ActionType
from src.core.entities.entity import Vector2, Entity
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.core.models.world_state import WorldState
from src.systems.world.generator import EntityGenerator
from src.engine.world_loop import WorldLoop
from src.config import SimulationConfig
from src.platform.rng import DeterministicRNG
from src.ai.brain import AIBrain
from src.engine.worker_pool import WorkerPool
from src.engine.conflict_resolver import ConflictResolver

@pytest.fixture(autouse=True)
def setup_registries():
    from src.core.registry.registry_loader import load_all_registries
    load_all_registries()

@pytest.fixture
def basic_setup():
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
    

    
    assert boss.identity.is_world_boss is True
    assert boss.identity.role == EntityRole.WORLD_BOSS
    assert boss.identity.display_name == "Gorath the World-Breaker"
    assert boss.combat.hp >= 500, f"Boss stats too low: {boss.combat.hp}. Kind: {boss.kind}, BossFlag: {boss.identity.is_world_boss}"
    assert boss.combat.atk_base >= 100 # 20 base * 5x mult
    
    # Check legendary loot
    assert boss.inventory.weapon is not None
    assert boss.inventory.weapon == "gorath_cleaver"

def test_calamity_bounty_generation(basic_setup):
    """Verify that bounties are generated for heroes when a boss spawns."""
    world, config, rng, gen, loop = basic_setup
    
    # Create a hero using the constructor directly
    hero = Entity(id=world.allocate_entity_id(), kind="hero")
    hero.spatial.pos = Vector2(10, 10)
    hero.identity.faction = Faction.HERO_GUILD
    hero.identity.role = EntityRole.HERO
    hero.identity.display_name = "Test Hero"
    hero.progression.level = 20  # Minimum for calamity_hunter quest
    world.add_entity(hero)
    
    # Trigger spawn tick (5000)
    world.tick = 5000
    loop._system_manager.tick(world, 5000)
    
    # Check hero quests
    assert len(hero.progression.quests) > 0
    from src.core.gameplay.quests import QuestType
    bounty = next((q for q in hero.progression.quests if q.quest_type == QuestType.BOUNTY), None)
    assert bounty is not None
    assert "Bounty:" in bounty.title

def test_calamity_kill_rewards(basic_setup):
    """Verify fame gain and title assignment on boss kill."""
    world, config, rng, gen, loop = basic_setup
    from src.actions.combat import CombatAction
    from src.actions.base import ActionProposal
    
    combat = CombatAction(config, rng)
    
    # Setup hero and boss
    hero = Entity(id=world.allocate_entity_id(), kind="hero")
    hero.spatial.pos = Vector2(10, 10)
    hero.identity.faction = Faction.HERO_GUILD
    hero.identity.display_name = "DragonSlayer"
    hero.progression.level = 20
    world.add_entity(hero)
    
    boss = gen.spawn_calamity(world, "gorath")
    boss.spatial.pos = Vector2(10, 11)
    boss.combat.hp = 1 # One-shot for testing
    world.add_entity(boss)
    
    # Force a bounty quest to the hero to test fame gain
    from src.core.gameplay.quests import Quest, QuestType
    bounty = Quest(
        quest_id="bounty_gorath",
        quest_type=QuestType.BOUNTY,
        title=f"Bounty: {boss.identity.display_name}",
        description="Test bounty",
        target_kind=boss.identity.display_name,
        target_count=1,
        gold_reward=1000,
        xp_reward=1000
    )
    hero.progression.quests.append(bounty)
    
    # Hero performs a killing blow
    proposal = ActionProposal(actor_id=hero.id, verb=ActionType.ATTACK, target=boss.id)
    combat.apply(proposal, world)
    
    # Authoritative application of trace results (AOA PHASE 5)
    loop._action_system.apply_action_state_transitions(world, config, [proposal], rng=rng)
    
    assert not boss.combat.alive
    assert hero.progression.fame >= 100
    assert any("Slayer of" in t for t in hero.identity.titles)
    assert hero.combat.atk_base > 0
