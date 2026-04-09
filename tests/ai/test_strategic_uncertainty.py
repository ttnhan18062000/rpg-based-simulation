import pytest
from src.core.entities.entity import Entity
from src.core.models.snapshot import Snapshot
from src.core.models.enums import GoalType, ActionType, AIState
from src.ai.brain import AIBrain
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.core.models.vectors import Vector2
from src.core.models.strategy import (
    StrategicStatus, ObjectiveKind, LeadKind, LeadRecord, ObjectiveRecord, 
    BlockerRecord, BlockerKind, ProjectRecord, ProjectKind
)
from src.actions.base import StrategicUpdate, MindUpdate

def test_strategic_detour_knowledge_blocker():
    """Verify that a knowledge blocker triggers a strategic investigation detour. [PHASE 3]"""
    rng = DeterministicRNG(seed=42)
    config = SimulationConfig()
    brain = AIBrain(config, rng)
    
    actor = Entity(id=1, kind="hero")
    actor.identity.faction = 0 # HERO_GUILD
    
    # 1. Setup a blocked objective
    project_id = "project_secret_ruins"
    obj_id = "obj_visit_ruins"
    
    ruins_obj = ObjectiveRecord(
        objective_id=obj_id,
        project_id=project_id,
        kind=ObjectiveKind.VISIT,
        label="Find the Secret Ruins",
        status=StrategicStatus.ACTIVE,
        priority=3.0,
        # NO target_pos -> Location unknown
    )
    
    # Add a knowledge blocker
    ruins_obj.blockers.append(BlockerRecord(
        blocker_id="blocker_missing_loc",
        kind=BlockerKind.KNOWLEDGE,
        label="Unknown Location",
        discovered_tick=0
    ))
    
    ruins_prj = ProjectRecord(
        project_id=project_id,
        kind=ProjectKind.EXPLORATION,
        label="Ruins Exploration",
        priority=3.0,
        objectives=[ruins_obj],
        active_objective_id=obj_id
    )
    
    actor.mind.strategic.projects = [ruins_prj]
    actor.mind.strategic.current_project_id = project_id
    actor.mind.strategic.current_objective_id = obj_id
    
    # 2. Add a Lead (Rumor)
    lead = LeadRecord(
        lead_id="lead_ruins_rumor",
        kind=LeadKind.LOCATION,
        label="Old Man's Tale",
        target_coords=Vector2(x=15, y=20),
        discovered_tick=10
    )
    actor.mind.strategic.leads = [lead]
    
    # 3. Setup World/Snapshot
    from src.core.models.world_state import WorldState
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    
    world = WorldState(seed=42, grid=Grid(50,50), spatial_index=SpatialHash(16))
    world.entities[actor.id] = actor
    world.tick = 100
    
    snapshot = Snapshot.from_world(world)
    
    # 4. Run Brain Decide
    new_state, proposal = brain.decide(actor, snapshot)
    
    # 5. Verify Detour Proposal
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert strat_up is not None
    
    # It should have updated the project with a new investigate objective
    assert strat_up.current_objective_id.startswith("detour_investigate_")
    
    detour_prj = next((p for p in strat_up.projects_add_or_update if p.project_id == project_id), None)
    assert detour_prj is not None
    assert any(o.kind == ObjectiveKind.INVESTIGATE for o in detour_prj.objectives)
    
    # Verify the new objective has the target_pos from the lead
    new_obj = next(o for o in detour_prj.objectives if o.objective_id == strat_up.current_objective_id)
    assert new_obj.target_pos == Vector2(x=15, y=20)

def test_investigating_state_tactical_execution():
    """Verify that an INVESTIGATE objective triggers the INVESTIGATING state and moves toward target. [PHASE 3]"""
    rng = DeterministicRNG(seed=42)
    config = SimulationConfig()
    brain = AIBrain(config, rng)
    
    actor = Entity(id=2, kind="hero")
    actor.identity.faction = 0
    actor.spatial.pos = Vector2(0, 0)
    
    # 1. Setup active investigate objective
    lead_pos = Vector2(10, 10)
    investigate_obj = ObjectiveRecord(
        objective_id="detour_ruins",
        project_id="prj_1",
        kind=ObjectiveKind.INVESTIGATE,
        label="Investigate Lead",
        status=StrategicStatus.ACTIVE,
        priority=4.0,
        target_pos=lead_pos
    )
    
    prj = ProjectRecord(
        project_id="prj_1",
        kind=ProjectKind.INVESTIGATION,
        label="Active Lead",
        objectives=[investigate_obj],
        active_objective_id=investigate_obj.objective_id
    )
    actor.mind.strategic.projects = [prj]
    actor.mind.strategic.current_project_id = prj.project_id
    actor.mind.strategic.current_objective_id = investigate_obj.objective_id
    
    from src.core.models.world_state import WorldState
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    
    world = WorldState(seed=42, grid=Grid(20,20), spatial_index=SpatialHash(16))
    world.entities[actor.id] = actor
    snapshot = Snapshot.from_world(world)
    
    # 2. Run Brain
    new_state, proposal = brain.decide(actor, snapshot)
    
    # 3. Verify INVESTIGATING state selected
    assert proposal.new_ai_state == int(AIState.INVESTIGATING)
    
    # 4. Verify Movement Proposal toward lead
    assert proposal.verb == ActionType.MOVE
    # Propose_move_toward should move closer to (10,10) from (0,0)
    assert proposal.target.x in [0, 1]
    assert proposal.target.y in [0, 1]
    assert proposal.target != actor.spatial.pos
    assert actor.spatial.pos.manhattan(lead_pos) > proposal.target.manhattan(lead_pos)
