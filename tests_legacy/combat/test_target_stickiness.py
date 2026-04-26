import pytest
from src_legacy.ai.states import AIContext
from src_legacy.ai.goals.scorers import CombatGoal
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.config import SimulationConfig
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.core.gameplay.faction import FactionRegistry

@pytest.fixture
def ctx():
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    config = SimulationConfig()
    rng = DeterministicRNG(42)
    grid = Grid(20, 20)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    from src_legacy.core.entities.entity_builder import EntityBuilder
    from src_legacy.core.gameplay.faction import Faction
    
    hero = EntityBuilder(rng, 1).kind("hero").faction(Faction.HERO_GUILD).at(Vector2(10, 10)).build()
    # Two identical monsters at same distance
    m1 = EntityBuilder(rng, 2).kind("monster").faction(Faction.GOBLIN_HORDE).at(Vector2(12, 10)).build()
    m2 = EntityBuilder(rng, 3).kind("monster").faction(Faction.GOBLIN_HORDE).at(Vector2(10, 12)).build()
    
    world.add_entity(hero)
    world.add_entity(m1)
    world.add_entity(m2)
    
    snapshot = Snapshot.from_world(world)
    return AIContext(hero, snapshot, config, rng, FactionRegistry.default())

def test_target_stickiness_bias(ctx):
    from unittest.mock import patch
    scorer = CombatGoal()
    
    # Initially no target, base score
    score1 = scorer.score(ctx)
    
    # Set M1 as current engagement target
    ctx.actor.mind.navigation.engagement_target_id = 2
    
    from unittest.mock import patch
    from src_legacy.ai.states import AIContext
    
    m1 = ctx.snapshot.entities[2]
    m2 = ctx.snapshot.entities[3]
    
    with patch.object(AIContext, 'nearest_enemy', return_value=m1):
        score_engaged = scorer.score(ctx)
    
    with patch.object(AIContext, 'nearest_enemy', return_value=m2):
        score_not_engaged = scorer.score(ctx)
    
    # score_engaged should be higher than score_not_engaged due to stickiness bonus (0.3)
    assert score_engaged > score_not_engaged
    assert score_engaged >= score_not_engaged + 0.29 # Close to 0.3 bonus
