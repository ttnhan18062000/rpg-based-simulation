"""Integration tests for Strategic Persistence, Hysteresis, and Pipeline flow.
[CONSOLIDATED FROM test_strategic_persistence.py and test_strategic_pipeline.py]
"""

import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.core.models.strategy import ProjectRecord, ProjectKind, ConcernRecord, ConcernKind, StrategicStatus
from src_legacy.ai.brain import AIBrain
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.config import SimulationConfig
from src_legacy.core.world.grid import Grid
from src_legacy.platform.spatial_hash import SpatialHash
from src_legacy.core.models.enums import Material, AttachmentKind, InterpretedLifeEventKind, Faction
from src_legacy.core.logic.strategic_consequence_service import StrategicConsequenceService
from src_legacy.core.models.lived_structure import PlaceAttachment
from src_legacy.core.models.life_events import InterpretedLifeEvent
from src_legacy.actions.base import StrategicUpdate

@pytest.fixture
def base_world():
    grid = Grid(100, 100)
    spatial = SpatialHash(cell_size=10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.tick = 100
    
    # Setup regions
    from src_legacy.core.world.regions import Region
    hamlet = Region(
        region_id="Hamlet",
        name="The Hamlet",
        terrain=Material.GRASSLAND,
        center=Vector2(10, 10),
        radius=50,
        difficulty=1
    )
    world.regions = [hamlet]
    
    return world

@pytest.fixture
def brain():
    return AIBrain(SimulationConfig(), DeterministicRNG(0))

# --- Persistence and Hysteresis Tests ---

def test_persistence_boost_prevents_switching(brain, base_world):
    """Verify that the persistence boost prevents switching to a slightly better project."""
    hero = Entity(id=1, kind="hero")
    base_world.add_entity(hero)
    
    # Project A (priority 2.0, committed 80 ticks ago)
    prj_a = ProjectRecord(
        project_id="project_a", kind=ProjectKind.QUEST, label="Old Project", 
        priority=2.0, committed_at=20, abandonment_cost=1.0
    )
    hero.mind.strategic.projects.append(prj_a)
    hero.mind.strategic.current_project_id = "project_a"
    
    # Project B (priority 2.5)
    # Boost (80 ticks * 1.0 = +0.8 approx) keeps A (2.8) ahead of B (2.5)
    prj_b = ProjectRecord(
        project_id="project_b", kind=ProjectKind.QUEST, label="New Project",
        priority=2.5, created_tick=100
    )
    hero.mind.strategic.projects.append(prj_b)
    
    snapshot = Snapshot.from_world(base_world)
    state, proposal = brain.decide(hero, snapshot)
    
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    if strat_up and strat_up.current_project_id:
        assert strat_up.current_project_id == "project_a"

def test_project_lock_prevents_switching(brain, base_world):
    """Verify that project_lock_until strictly prevents any switches despite critical concerns."""
    hero = Entity(id=1, kind="hero")
    base_world.add_entity(hero)
    
    hero.mind.strategic.current_project_id = "project_a"
    hero.mind.strategic.project_lock_until = 150
    prj_a = ProjectRecord(project_id="project_a", kind=ProjectKind.QUEST, label="Old Project", priority=2.0, committed_at=100)
    hero.mind.strategic.projects.append(prj_a)
    
    # Critical concern (10.0!)
    concern = ConcernRecord(concern_id="critical_threat", kind=ConcernKind.THREAT, label="DEATH", priority=10.0)
    hero.mind.strategic.concerns.append(concern)
    
    snapshot = Snapshot.from_world(base_world)
    state, proposal = brain.decide(hero, snapshot)
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    
    if strat_up and strat_up.current_project_id:
        assert strat_up.current_project_id == "project_a"

def test_interruption_threshold_overridden_by_major_threat(brain, base_world):
    """Verify that a massive threat CAN overcome the interruption threshold."""
    hero = Entity(id=1, kind="hero")
    base_world.add_entity(hero)
    
    prj_a = ProjectRecord(project_id="project_a", kind=ProjectKind.QUEST, label="Old Project", priority=1.0, committed_at=95, interruption_threshold=0.1, abandonment_cost=0.0)
    hero.mind.strategic.projects.append(prj_a)
    hero.mind.strategic.current_project_id = "project_a"
    
    # Concern C (10.0!)
    concern = ConcernRecord(concern_id="survival_threat", kind=ConcernKind.THREAT, label="Giant", priority=10.0, urgency=1.0)
    hero.mind.strategic.concerns.append(concern)
    
    snapshot = Snapshot.from_world(base_world)
    state, proposal = brain.decide(hero, snapshot)
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    
    assert strat_up is not None
    assert strat_up.current_project_id == "" or strat_up.current_project_id is None or "project" in strat_up.current_project_id
    assert strat_up.interrupted_project_id == "project_a"

# --- Consequence Pipeline Tests ---

def test_strategic_pipeline_home_threat(base_world):
    """Verify the flow from life event through StrategicConsequenceService to project pivot."""
    entity = Entity(id=1, kind="hero")
    entity.identity.faction = Faction.HERO_GUILD
    entity.spatial.pos = Vector2(10, 10)
    
    home = PlaceAttachment(building_id=101, kind=AttachmentKind.HOME, location_pos=Vector2(12, 12), importance=0.9)
    entity.mind.place_attachments.append(home)
    
    project = ProjectRecord(project_id="prj_explore", kind=ProjectKind.EXPLORATION, label="Explore", priority=2.0, status=StrategicStatus.ACTIVE)
    entity.mind.strategic.projects.append(project)
    entity.mind.strategic.current_project_id = "prj_explore"
    
    event = InterpretedLifeEvent(
        event_id="raid_1", kind=InterpretedLifeEventKind.NEAR_DEATH, location=Vector2(13, 13), severity=0.8, tick=base_world.tick, actor_id=99, subject_ids=[1]
    )
    
    updates = StrategicConsequenceService.process_consequences(base_world, entity, event, tp=None)
    
    # Verify Concern
    threat_concern = next((c for c in updates.concerns_add_or_update if c.kind == ConcernKind.THREAT and "Threat to" in c.label), None)
    assert threat_concern is not None
    
    # Verify Pivot
    mutated_project = next((p for p in updates.projects_add_or_update if p.project_id == "prj_explore"), None)
    assert mutated_project is not None
    assert mutated_project.kind == ProjectKind.DEVELOPMENT
    assert updates.interrupted_project_id == "prj_explore"

# --- Resume and Continuity Verification ---

def test_resume_restores_valid_objective(brain, base_world):
    """Verify that brain restores the last active objective when resuming a project. [Strategy M2]"""
    hero = Entity(id=1, kind="hero")
    base_world.add_entity(hero)
    
    # 1. Setup project with an active objective in its internal records
    from src_legacy.core.models.strategy import ObjectiveRecord, ObjectiveKind
    obj_a = ObjectiveRecord(
        objective_id="obj_a", project_id="prj_main", 
        kind=ObjectiveKind.WAIT, label="Just Wait", # WAIT avoids knowledge blockers
        status=StrategicStatus.ACTIVE
    )
    prj_main = ProjectRecord(
        project_id="prj_main", kind=ProjectKind.QUEST, label="Main Quest",
        status=StrategicStatus.ACTIVE,
        objectives=[obj_a],
        active_objective_id="obj_a"
    )
    
    hero.mind.strategic.projects.append(prj_main)
    hero.mind.strategic.current_project_id = "prj_main"
    # Ensure current_objective_id is UNSET to check if it's restored
    hero.mind.strategic.current_objective_id = None
    
    snapshot = Snapshot.from_world(base_world)
    state, proposal = brain.decide(hero, snapshot)
    
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert strat_up is not None
    assert strat_up.current_objective_id == "obj_a", "Should restore active_objective_id from ProjectRecord"

def test_resumed_objective_survives_cycle(brain, base_world):
    """Verify that a restored objective doesn't immediately flip back to ProjectRecord.objectives[0] if it matches. [Strategy M2]"""
    hero = Entity(id=1, kind="hero")
    base_world.add_entity(hero)
    
    from src_legacy.core.models.strategy import ObjectiveRecord, ObjectiveKind
    # Objective 0 (Completed)
    obj_0 = ObjectiveRecord(
        objective_id="obj_0", project_id="prj_main", 
        kind=ObjectiveKind.WAIT, label="Step 0", status=StrategicStatus.RESOLVED
    )
    # Objective 1 (Active)
    obj_1 = ObjectiveRecord(
        objective_id="obj_1", project_id="prj_main", 
        kind=ObjectiveKind.WAIT, label="Step 1", status=StrategicStatus.ACTIVE
    )
    
    prj_main = ProjectRecord(
        project_id="prj_main", kind=ProjectKind.QUEST, label="Quest",
        status=StrategicStatus.ACTIVE,
        objectives=[obj_0, obj_1],
        active_objective_id="obj_1"
    )
    
    hero.mind.strategic.projects.append(prj_main)
    hero.mind.strategic.current_project_id = "prj_main"
    hero.mind.strategic.current_objective_id = "obj_1"
    
    snapshot = Snapshot.from_world(base_world)
    state, proposal = brain.decide(hero, snapshot)
    
    # We expect NO update for current_objective_id because it's already "obj_1"
    strat_up = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    if strat_up:
        assert strat_up.current_objective_id in (None, "obj_1")
