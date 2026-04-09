import pytest
from src.core.entities.entity import Entity
from src.core.models.snapshot import Snapshot
from src.core.models.enums import GoalType, ActionType, AIState
from src.ai.brain import AIBrain
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.core.models.vectors import Vector2

def test_biological_need_to_strategic_bias():
    rng = DeterministicRNG(seed=42)
    config = SimulationConfig()
    brain = AIBrain(config, rng)
    
    # Create entity with high hunger
    from src.core.aspects.inventory import InventoryAspect
    actor = Entity(id=1, kind="hero")
    actor.identity.faction = 0 # 0 usually HERO_GUILD
    actor.mind.routine.hunger_level = 0.9
    actor.mind.strategic.directives = [] # No directives yet
    actor.inventory = InventoryAspect(items=[]) # Empty inventory but not None
    
    from src.core.models.world_state import WorldState
    from src.core.models.snapshot import Snapshot
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    
    # Real minimal objects
    grid = Grid(width=10, height=10)
    spatial = SpatialHash(cell_size=16)
    
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.entities[actor.id] = actor
    world.tick = 100
    
    # Generate snapshot
    snapshot = Snapshot.from_world(world)
    
    new_state, proposal = brain.decide(actor, snapshot)
    
    # Verify StrategicUpdate was proposed
    from src.actions.base import StrategicUpdate, MindUpdate
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert strat_up is not None
    assert strat_up.current_project_id == "project_survival"
    assert strat_up.current_objective_id == "obj_satisfy_needs"
    
    # Verify Tactical Biasing
    # MindUpdate might be split across multiple instances, find the one with biases
    mind_up = next((u for u in proposal.updates if isinstance(u, MindUpdate) and u.motive_utility_biases), None)
    assert mind_up is not None
    assert mind_up.motive_utility_biases[GoalType.EAT] > 4.0
    assert mind_up.motive_utility_biases[GoalType.REST] > 4.0 # REST usually linked to SLEEP in EAT logic here
    
    # Verify Driver Details mentions the objective
    driver = next((d for d in mind_up.driver_details if d.kind == "strategic"), None)
    assert driver is not None
    assert "obj_satisfy_needs" in driver.label

def test_directive_to_project_flow():
    rng = DeterministicRNG(seed=42)
    config = SimulationConfig()
    brain = AIBrain(config, rng)
    
    # Create entity with a directive but no high needs
    from src.core.models.strategy import DirectiveRecord, DirectiveKind
    actor = Entity(id=2, kind="hero")
    actor.identity.faction = 0
    actor.mind.routine.hunger_level = 0.2 # low hunger
    
    # Add a directive
    directive = DirectiveRecord(
        directive_id="dir_contracts",
        kind=DirectiveKind.PROFESSIONAL,
        label="Complete contracts",
        priority=2.0
    )
    actor.mind.strategic.directives = [directive]
    
    from src.core.models.world_state import WorldState
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    
    world = WorldState(seed=42, grid=Grid(10,10), spatial_index=SpatialHash(16))
    world.entities[actor.id] = actor
    world.tick = 200
    
    snapshot = Snapshot.from_world(world)
    
    new_state, proposal = brain.decide(actor, snapshot)
    
    # Verify StrategicUpdate proposes a project derived from the directive
    from src.actions.base import StrategicUpdate
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert strat_up is not None
    assert strat_up.current_project_id == "project_dir_contracts"
    assert "Complete contracts" in strat_up.projects_add_or_update[0].label

def test_strategic_bias_impact_on_selection():
    rng = DeterministicRNG(seed=42)
    config = SimulationConfig()
    brain = AIBrain(config, rng)
    
    # Scenario: Hero is near an enemy but has an active strategic objective to EXPLORE.
    # We want to see if the EXPLORE bias overcomes a slight COMBAT utility.
    
    actor = Entity(id=3, kind="hero")
    actor.identity.faction = 0
    
    # Mocking strategic state directly
    from src.core.models.strategy import ObjectiveRecord, ObjectiveKind
    actor.mind.strategic.current_objective_id = "obj_explore_surroundings"
    
    # Manual setup of World so enemy is visible
    enemy = Entity(id=99, kind="mob")
    enemy.identity.faction = 1 # Hostile
    enemy.spatial.pos = Vector2(10, 10)
    actor.spatial.pos = Vector2(0, 0)
    
    from src.core.models.world_state import WorldState
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    
    world = WorldState(seed=42, grid=Grid(20,20), spatial_index=SpatialHash(16))
    world.entities[actor.id] = actor
    world.entities[enemy.id] = enemy
    world.tick = 150 # Midday (Hour 12)
    
    snapshot = Snapshot.from_world(world)
    
    # Run brain
    new_state, proposal = brain.decide(actor, snapshot)
    
    # Verify MindUpdate has strategic bias for EXPLORE
    from src.actions.base import MindUpdate
    mind_up_bias = next((u for u in proposal.updates if isinstance(u, MindUpdate) and u.motive_utility_biases), None)
    assert mind_up_bias is not None
    assert mind_up_bias.motive_utility_biases[GoalType.EXPLORE] > 2.0
    
    mind_up_scores = next((u for u in proposal.updates if isinstance(u, MindUpdate) and u.goal_scores), None)
    assert mind_up_scores is not None
    print(f"DEBUG: Goal Scores: {mind_up_scores.goal_scores}")
    
    # Check if EXPLORE is the top goal
    assert mind_up_scores.goal_scores[GoalType.EXPLORE] > mind_up_scores.goal_scores[GoalType.COMBAT]

    # Check if the final state is related to WANDER/EXPLORE
    assert proposal.new_ai_state == int(AIState.WANDER)
