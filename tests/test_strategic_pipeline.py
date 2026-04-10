import pytest
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.logic.strategic_consequence_service import StrategicConsequenceService
from src.core.models.lived_structure import PlaceAttachment
from src.core.models.enums import AttachmentKind, InterpretedLifeEventKind, Faction, StrategicStatus, ProjectKind, ConcernKind, Material
from src.core.models.life_events import InterpretedLifeEvent
from src.core.models.vectors import Vector2
from src.core.models.strategy import ProjectRecord
from src.core.world.grid import Grid
from src.core.world.regions import Region
from src.platform.spatial_hash import SpatialHash
from src.actions.base import StrategicUpdate
from unittest.mock import MagicMock

@pytest.fixture
def base_world():
    grid = Grid(100, 100)
    world = WorldState(seed=42, grid=grid, spatial_index=SpatialHash(cell_size=10))
    world.tick = 100
    
    # Setup regions
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

def test_strategic_pipeline_home_threat(base_world):
    # 1. Setup Entity with Home Attachment
    entity = Entity(id=1, kind="hero")
    entity.identity.faction = Faction.HERO_GUILD
    entity.spatial.pos = Vector2(10, 10)
    entity.spatial.region_id = "Hamlet"
    
    home = PlaceAttachment(
        building_id=101,
        kind=AttachmentKind.HOME,
        location_pos=Vector2(12, 12),
        importance=0.9
    )
    entity.mind.place_attachments.append(home)
    
    # Setup a dummy project
    project = ProjectRecord(
        project_id="prj_explore_1",
        kind=ProjectKind.EXPLORATION,
        label="Explore the Wilds",
        priority=2.0,
        status=StrategicStatus.ACTIVE
    )
    entity.mind.strategic.projects.append(project)
    entity.mind.strategic.current_project_id = project.project_id
    
    # 2. Simulate Extreme Threat Event at Home
    event = InterpretedLifeEvent(
        event_id="raid_1",
        kind=InterpretedLifeEventKind.NEAR_DEATH,
        location=Vector2(13, 13), # Close to home
        severity=0.8,
        tick=base_world.tick,
        actor_id=99, # The raider
        subject_ids=[1] # The hero
    )
    
    # 3. Process Consequence Pipeline
    updates = StrategicConsequenceService.process_consequences(base_world, entity, event, tp=None)
    
    # 4. Verify Concerns
    assert len(updates.concerns_add_or_update) > 0
    threat_concern = next((c for c in updates.concerns_add_or_update if c.kind == ConcernKind.THREAT and "Threat to" in c.label), None)
    assert threat_concern is not None
    assert threat_concern.priority >= 3.0
    
    # 5. Verify Project Pivot/Suspension
    assert len(updates.projects_add_or_update) > 0
    mutated_project = next((p for p in updates.projects_add_or_update if p.project_id == project.project_id), None)
    assert mutated_project is not None
    assert mutated_project.kind == ProjectKind.DEVELOPMENT # Pivoted from EXPLORE
    
    # 6. Verify Interrupted Project ID is recorded
    assert updates.interrupted_project_id == project.project_id
