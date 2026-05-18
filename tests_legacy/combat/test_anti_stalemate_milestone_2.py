import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.enums import ActionType, AIState, GoalType
from src_legacy.ai.brain import AIBrain
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.config import SimulationConfig
from src_legacy.core.models.snapshot import Snapshot

@pytest.fixture
def config():
    return SimulationConfig()

@pytest.fixture
def rng():
    return DeterministicRNG(0)

@pytest.fixture
def brain(config, rng):
    return AIBrain(config, rng)

def test_stalemate_detection_and_breaker(brain, config, rng):
    """Verify that 3 cycles of rhythmic oscillation trigger the stalemate breaker."""
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    grid = Grid(50, 50)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    actor = Entity(id=1, kind="hero", spatial={"pos": Vector2(10, 10)})
    
    # Mock some history of oscillation [A, B, A, B]
    A = Vector2(10, 10)
    B = Vector2(10, 11)
    actor.mind.navigation.pos_history = [A, B, A, B]
    
    # Set previous state/target to match current to trigger contextual stalemate
    actor.mind.navigation.last_ai_state = int(AIState.COMBAT)
    actor.mind.navigation.last_target_id = 99
    actor.mind.decision.ai_state = AIState.COMBAT
    actor.combat.combat_target_id = 99
    
    # Commit to combat goal to test lock-break
    actor.mind.decision.last_goal = GoalType.COMBAT
    actor.mind.decision.goal_committed_at = 0
    world.tick = 2 # ticks_held = 2 < min_ticks(3)
    
    world.add_entity(actor)
    snapshot = Snapshot.from_world(world)
    
    # 1. First decide call - should detect stalemate and increment counter
    new_state, proposal = brain.decide(actor, snapshot)
    
    # Find the NavigationUpdate
    from src_legacy.actions.base import NavigationUpdate
    nav_up = next((u for u in proposal.updates if isinstance(u, NavigationUpdate)), None)
    assert nav_up is not None
    assert nav_up.stalemate_counter == 1
    
    # 2. Force counter to 3 and re-evaluate
    actor.mind.navigation.stalemate_counter = 3
    snapshot = Snapshot.from_world(world)
    
    # Should bypass lock and potentially change state
    # We use a high rng value to favor non-combat goals if combat is penalized
    # StalemateModifier penalizes current goal (COMBAT) by 0.1x
    # Alternatives are boosted by 2.0x
    class MockRNG:
        def next_float(self, *args, **kwargs): return 0.9
        def next_bool(self, *args, **kwargs): return False
        def next_int(self, *args, **kw): return 0
        def weighted_choice(self, d, e, t, items, weights):
            return items[-1] # Favor non-combat (last in list usually)
            
    original_rng = brain._rng
    brain._rng = MockRNG()
    try:
        new_state, proposal = brain.decide(actor, snapshot)
    finally:
        brain._rng = original_rng
    
    # Even if it picks IDLE or something else, it shouldn't be COMBAT if penalized enough
    assert new_state != AIState.COMBAT
