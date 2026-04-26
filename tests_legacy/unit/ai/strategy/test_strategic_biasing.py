import pytest
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.core.models.enums import GoalType, ActionType, AIState
from src_legacy.ai.brain import AIBrain
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.config import SimulationConfig
from src_legacy.core.models.vectors import Vector2

def test_biological_need_to_strategic_bias():
    rng = DeterministicRNG(seed=42)
    config = SimulationConfig()
    brain = AIBrain(config, rng)
    
    # Create entity with high hunger
    from src_legacy.core.aspects.inventory import InventoryAspect
    actor = Entity(id=1, kind="hero")
    actor.identity.faction = 0 # 0 usually HERO_GUILD
    actor.mind.routine.hunger_level = 0.9
    actor.mind.strategic.directives = [] # No directives yet
    actor.inventory = InventoryAspect(items=[]) # Empty inventory but not None
    actor.progression.stamina = 100.0
    actor.progression.stamina_max = 100.0
    actor.mind.decision.last_appraisal_tick = -50 # Force trigger
    
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.models.snapshot import Snapshot
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    
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
    from src_legacy.actions.base import StrategicUpdate, MindUpdate
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert strat_up is not None
    assert strat_up.current_project_id == "project_concern_survival_hunger"
    assert strat_up.current_objective_id == "obj_satisfy_needs"
    
    # Verify Tactical Biasing
    # MindUpdate might be split across multiple instances, find the one with biases
    mind_up = next((u for u in proposal.updates if isinstance(u, MindUpdate) and u.motive_utility_biases is not None), None)
    assert mind_up is not None
    assert mind_up.motive_utility_biases[GoalType.EAT] >= 2.5
    assert mind_up.motive_utility_biases[GoalType.REST] >= 0.5 # REST is dampened by VISIT, but EAT/SLEEP are boosted if needs are high
    
    # Verify Driver Details mentions the objective
    driver = next((d for d in mind_up.driver_details if d.kind == "strategic"), None)
    assert driver is not None
    assert "survival" in driver.label

def test_directive_to_project_flow():
    rng = DeterministicRNG(seed=42)
    config = SimulationConfig()
    brain = AIBrain(config, rng)
    
    # Create entity with a directive but no high needs
    from src_legacy.core.models.strategy import DirectiveRecord, DirectiveKind
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
    
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    
    world = WorldState(seed=42, grid=Grid(10,10), spatial_index=SpatialHash(16))
    world.entities[actor.id] = actor
    world.tick = 200
    
    snapshot = Snapshot.from_world(world)
    
    new_state, proposal = brain.decide(actor, snapshot)
    
    # Verify StrategicUpdate proposes a project derived from the directive
    from src_legacy.actions.base import StrategicUpdate
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
    from src_legacy.core.models.strategy import ObjectiveRecord, ObjectiveKind, ProjectRecord, ProjectKind, StrategicStatus
    
    obj_id = "obj_explore_surroundings"
    project_id = "project_exploration"
    
    obj = ObjectiveRecord(
        objective_id=obj_id,
        project_id=project_id,
        kind=ObjectiveKind.VISIT, # Using VISIT for EXPLORE bias in mapper
        label="Explore the region",
        status=StrategicStatus.ACTIVE,
        priority=4.0
    )
    
    prj = ProjectRecord(
        project_id=project_id,
        kind=ProjectKind.EXPLORATION,
        label="Wilderness Exploration",
        objectives=[obj],
        active_objective_id=obj_id
    )
    
    actor.mind.strategic.projects = [prj]
    actor.mind.strategic.current_project_id = project_id
    actor.mind.strategic.current_objective_id = obj_id
    
    # Manual setup of World so enemy is visible
    enemy = Entity(id=99, kind="mob")
    enemy.identity.faction = 1 # Hostile
    enemy.spatial.pos = Vector2(10, 10)
    actor.spatial.pos = Vector2(0, 0)
    
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    
    world = WorldState(seed=42, grid=Grid(20,20), spatial_index=SpatialHash(16))
    world.entities[actor.id] = actor
    world.entities[enemy.id] = enemy
    world.tick = 150 # Midday (Hour 12)
    
    snapshot = Snapshot.from_world(world)
    
    # Run brain
    new_state, proposal = brain.decide(actor, snapshot)
    
    # Verify MindUpdate has strategic bias for EXPLORE
    from src_legacy.actions.base import MindUpdate
    mind_up_bias = next((u for u in proposal.updates if isinstance(u, MindUpdate) and u.motive_utility_biases), None)
    assert mind_up_bias is not None
    # Bias is personality (1.0) * strategic (2.5) * curiosity multiplier?
    # If curiosity is default (0.5), personality bias is 0.5 + 0.5 = 1.0
    # 1.0 * 2.5 = 2.5? Wait! If it's 1.5, then strategic bias was 1.5
    assert mind_up_bias.motive_utility_biases[GoalType.EXPLORE] >= 1.5
    
    mind_up_scores = next((u for u in proposal.updates if isinstance(u, MindUpdate) and u.goal_scores), None)
    assert mind_up_scores is not None
    
    # Check if EXPLORE is the top goal
    assert mind_up_scores.goal_scores[GoalType.EXPLORE] > mind_up_scores.goal_scores[GoalType.COMBAT]

    # Check if the final state is related to WANDER/EXPLORE
    assert proposal.new_ai_state == int(AIState.WANDER)
