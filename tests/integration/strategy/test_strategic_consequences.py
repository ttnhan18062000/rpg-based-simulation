"""Integration tests for Phase 5 Strategic Consequences.

Verifies that interpreted life events correctly generate concerns,
mutate directives, and trigger history-sensitive project interruptions.
"""

import pytest
import uuid
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.models.strategy import StrategicStatus, ConcernKind, ProjectKind, DirectiveKind
from src.ai.brain import AIBrain
from src.core.models.snapshot import Snapshot
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.core.models.life_events import InterpretedLifeEvent
from src.core.models.enums import InterpretedLifeEventKind

@pytest.fixture
def base_world():
    grid = Grid(100, 100)
    spatial = SpatialHash(cell_size=10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.entities = {}
    return world

def test_near_death_triggers_survival_consequences(base_world):
    """Verify that a NEAR_DEATH event generates a concern and suspends the current project."""
    hero = Entity(id=1, kind="hero")
    hero.spatial.pos = Vector2(25, 25)
    base_world.entities[1] = hero
    
    # 1. Setup Active Project
    from src.core.models.strategy import ProjectRecord
    current_prj = ProjectRecord(
        project_id="quest_alpha", kind=ProjectKind.QUEST, label="Exploring Ruins", priority=2.0, status=StrategicStatus.ACTIVE
    )
    hero.mind.strategic.projects.append(current_prj)
    hero.mind.strategic.current_project_id = "quest_alpha"
    
    # 2. Trigger NEAR_DEATH event
    event = InterpretedLifeEvent(
        event_id=f"evt_{uuid.uuid4().hex[:6]}",
        kind=InterpretedLifeEventKind.NEAR_DEATH,
        tick=100,
        actor_id=1,
        location=Vector2(25, 25),
        severity=0.8,
        turning_point_candidate=True
    )
    
    # 3. Apply via SocialStateApplicator (which now chains StrategicConsequenceService)
    from src.core.logic.social_state_applicator import SocialStateApplicator
    updates = [] # To collect generated IntentUpdates
    SocialStateApplicator.apply_interpreted_event(event, base_world, updates=updates)
    
    # 4. Verify Updates
    assert len(updates) > 0
    strat_up = next((u for u in updates if hasattr(u, 'concerns_add_or_update')), None)
    assert strat_up is not None
    
    # Verify Concern
    survival_c = next((c for c in strat_up.concerns_add_or_update if "Recovery" in c.label), None)
    assert survival_c is not None
    assert survival_c.priority > 4.0
    assert survival_c.visibility == "private"
    
    # Verify Project Suspension
    suspended_prj = next((p for p in strat_up.projects_add_or_update if p.project_id == "quest_alpha"), None)
    assert suspended_prj is not None
    assert suspended_prj.status == StrategicStatus.SUSPENDED
    assert "Strategic Interrupt" in suspended_prj.suspension_reason
    assert event.event_id in suspended_prj.interrupted_by_event_ids

def test_betrayal_mutates_directives(base_world):
    """Verify that a salient betrayal turning point adds an 'Avenge' directive."""
    villain = Entity(id=2, kind="villain")
    hero = Entity(id=1, kind="hero")
    base_world.entities[1] = hero
    base_world.entities[2] = villain
    
    # 1. Trigger BETRAYAL event
    event = InterpretedLifeEvent(
        event_id="evt_betrayal_1",
        kind=InterpretedLifeEventKind.BETRAYAL,
        tick=100,
        actor_id=1,
        subject_ids=[2],
        location=Vector2(10, 10),
        severity=0.9,
        turning_point_candidate=True
    )
    
    # 2. Apply
    from src.core.logic.social_state_applicator import SocialStateApplicator
    updates = []
    SocialStateApplicator.apply_interpreted_event(event, base_world, updates=updates)
    
    # 3. Verify Directive Acquisition
    strat_up = next((u for u in updates if hasattr(u, 'directives_add')), None)
    assert strat_up is not None
    
    avenge_d = next((d for d in strat_up.directives_add if "Avenge" in d.label), None)
    assert avenge_d is not None
    assert avenge_d.priority >= 3.0
    assert avenge_d.kind == DirectiveKind.PERSONAL

def test_home_threat_appraisal(base_world):
    """Verify that an event in a home region generates a specific threat concern."""
    hero = Entity(id=1, kind="hero")
    base_world.entities[1] = hero
    
    # Setup Home Attachment in 'forest'
    from src.core.world.regions import Region
    from src.core.models.enums import Material, AttachmentKind
    from src.core.models.lived_structure import PlaceAttachment
    
    forest = Region(region_id="forest", name="Forest", terrain=Material.FOREST, center=Vector2(50, 50), radius=100, difficulty=1)
    base_world.regions = [forest]
    
    hero.mind.place_attachments.append(PlaceAttachment(
        location_pos=Vector2(50, 50), kind=AttachmentKind.HOME, importance=1.0
    ))
    
    # Trigger event in forest
    event = InterpretedLifeEvent(
        event_id="evt_raid",
        kind=InterpretedLifeEventKind.HOME_DAMAGED, # New enum kind
        tick=200,
        actor_id=1,
        location=Vector2(50, 50),
        severity=0.7
    )
    
    # Apply
    from src.core.logic.social_state_applicator import SocialStateApplicator
    updates = []
    SocialStateApplicator.apply_interpreted_event(event, base_world, updates=updates)
    
    # Verify Concern
    strat_up = next((u for u in updates if hasattr(u, 'concerns_add_or_update')), None)
    home_c = next((c for c in strat_up.concerns_add_or_update if "Home" in c.label), None)
    assert home_c is not None
    assert home_c.attachment_relevance == 1.0
