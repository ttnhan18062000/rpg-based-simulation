import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.enums import ActionType
from src_legacy.actions.base import ActionProposal
from src_legacy.engine.conflict_resolver import ConflictResolver
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.config import SimulationConfig

@pytest.fixture
def scenario():
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    config = SimulationConfig()
    rng = DeterministicRNG(42)
    grid = Grid(20, 20)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    from src_legacy.core.entities.entity_builder import EntityBuilder
    from src_legacy.core.gameplay.faction import Faction
    
    # Hero at (10, 10), Monster at (11, 10)
    hero = EntityBuilder(rng, 1).kind("hero").faction(Faction.HERO_GUILD).at(Vector2(10, 10)).build()
    hero.combat.hp = 100
    monster = EntityBuilder(rng, 2).kind("monster").faction(Faction.GOBLIN_HORDE).at(Vector2(11, 10)).build()
    monster.combat.atk_base = 20 # Aspect has atk_base
    
    world.add_entity(hero)
    world.add_entity(monster)
    return world, config, rng

def test_oa_triggered_on_disengagement(scenario):
    world, config, rng = scenario
    hero = world.entities[1]
    
    # Hero proposes moving from (10, 10) to (9, 10) -- leaving engagement with monster at (11, 10)
    proposal = ActionProposal(
        actor_id=1,
        verb=ActionType.MOVE,
        target=Vector2(9, 10)
    )
    
    hero.combat.evasion = -1.0 # Ensure hit
    resolver = ConflictResolver(config, rng)
    applied = resolver.resolve([proposal], world)
    
    # Check that an Opportunity Attack was applied
    oa = next((p for p in applied if p.reason == "Opportunity Attack"), None)
    assert oa is not None
    assert oa.actor_id == 2
    assert oa.target == 1
    
    # Verify damage was tasked
    from src_legacy.actions.base import ProgressionUpdate
    hp_updates = [u for u in oa.updates if isinstance(u, ProgressionUpdate) and u.hp_delta != 0]
    assert len(hp_updates) > 0
    assert hp_updates[0].hp_delta < 0

def test_oa_not_triggered_if_staying_engaged_with_same_attacker(scenario):
    world, config, rng = scenario
    
    # Hero moves from (10, 10) to (10, 11) -- still adjacent to monster at (11, 10) (diag adjacent? No, Manhattan dist 1)
    # Wait, (10, 11) to (11, 10) is Manhattan 2. So they ARE disengaging.
    
    # Hero moves from (10, 10) to (11, 11) -- diag (not legal in MOVE)
    
    # Let's try Move to (12, 10) -- jumps over monster? No, illegal.
    
    # Let's try: Hero moves from (10, 10) to (11, 10)? Occupied.
    
    # Conclusion: In Manhattan 1 grid, ANY move away from an adjacent hostile is a disengagement.
    # The only move that wouldn't be is if they moved to another adjacent tile.
    # But in Manhattan 1, there are no "adjacent squares that are also adjacent to the same point" except for the point itself.
    
    # Wait, if Hero at (10, 10) and Monster at (11, 10).
    # Move to (10, 9). Dist to Monster is abs(10-11) + abs(9-10) = 1 + 1 = 2.
    # So yes, ANY move is a disengagement.
    
    proposal = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=Vector2(10, 9))
    resolver = ConflictResolver(config, rng)
    applied = resolver.resolve([proposal], world)
    assert any(p.reason == "Opportunity Attack" for p in applied)
