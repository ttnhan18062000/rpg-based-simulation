import json
import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.core.models.strategy import (
    StrategicState, ProjectRecord, ProjectKind, 
    DirectiveRecord, DirectiveKind, ConcernRecord, ConcernKind,
    StrategicStatus
)
from src_legacy.actions.base import StrategicUpdate, ActionProposal, ActionType
from src_legacy.systems.gameplay.action_system import ActionSystem
from src_legacy.core.world.grid import Grid
from src_legacy.platform.spatial_hash import SpatialHash
from src_legacy.core.models.vectors import Vector2

@pytest.fixture
def base_world():
    grid = Grid(10, 10)
    spatial = SpatialHash(cell_size=10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    return world

def test_snapshot_strategic_isolation(base_world):
    """Verify that Snapshot.from_world deep-copies and freezes strategic state."""
    hero = Entity(id=1, kind="hero")
    prj = ProjectRecord(project_id="prj1", kind=ProjectKind.QUEST, label="Live Project")
    hero.mind.strategic.projects.append(prj)
    hero.mind.strategic.current_project_id = "prj1"
    
    base_world.add_entity(hero)
    
    # 1. Take Snapshot
    snap = Snapshot.from_world(base_world)
    snap_hero = snap.entities[1]
    
    # 2. Mutate Live State
    hero.mind.strategic.current_project_id = "MUTATED"
    hero.mind.strategic.projects[0].label = "MUTATED LABEL"
    
    # 3. Verify Snapshot remains isolated
    assert snap_hero.mind.strategic.current_project_id == "prj1"
    assert snap_hero.mind.strategic.projects[0].label == "Live Project"
    
    # 4. Verify Snapshot is frozen
    with pytest.raises(Exception): # Pydantic v2 raises ValidationError or TypeError on frozen mutation
        snap_hero.mind.strategic.current_project_id = "TRY_MUTATION"

def test_strategic_update_merging_identical_ids(base_world):
    """Verify that ActionSystem merges updates with identical IDs correctly."""
    hero = Entity(id=1, kind="hero")
    base_world.add_entity(hero)
    
    # Initial project
    p1 = ProjectRecord(project_id="p1", kind=ProjectKind.QUEST, label="Initial", priority=1.0)
    hero.mind.strategic.projects.append(p1)
    
    # Update 1: Update p1 priority
    up1 = StrategicUpdate(
        projects_add_or_update=[
            ProjectRecord(project_id="p1", kind=ProjectKind.QUEST, label="Updated", priority=2.0)
        ]
    )
    
    # Update 2: Another update to same p1 in same list (Edge case)
    up2 = StrategicUpdate(
        projects_add_or_update=[
            ProjectRecord(project_id="p1", kind=ProjectKind.QUEST, label="Final", priority=3.0)
        ]
    )
    
    # Apply via ActionSystem
    ActionSystem.apply_strategic_update(hero, up1)
    assert hero.mind.strategic.projects[0].priority == 2.0
    assert hero.mind.strategic.projects[0].label == "Updated"
    
    ActionSystem.apply_strategic_update(hero, up2)
    assert hero.mind.strategic.projects[0].priority == 3.0
    assert hero.mind.strategic.projects[0].label == "Final"
    assert len(hero.mind.strategic.projects) == 1, "Duplicate project records created for same ID!"

def test_serialization_round_trip():
    """Verify that StrategicState survives full JSON serialization round-trip."""
    state = StrategicState(
        current_project_id="prj_123",
        projects=[
            ProjectRecord(project_id="prj_123", kind=ProjectKind.QUEST, label="Round Trip Test")
        ],
        directives=[
            DirectiveRecord(directive_id="d1", kind=DirectiveKind.PERSONAL, label="Strong Directive")
        ]
    )
    
    # 1. Serialize to JSON
    json_data = state.model_dump_json()
    
    # 2. Deserialize back
    new_state = StrategicState.model_validate_json(json_data)
    
    # 3. Verify parity
    assert new_state.current_project_id == "prj_123"
    assert len(new_state.projects) == 1
    assert new_state.projects[0].label == "Round Trip Test"
    assert new_state.directives[0].directive_id == "d1"

def test_strategic_update_coercion_from_dict():
    """Verify that StrategicUpdate correctly coerces dicts to models (worker transport emulation)."""
    raw_update = {
        "projects_add_or_update": [
            {
                "project_id": "prj_dict",
                "kind": ProjectKind.QUEST.value, # Pydantic expects int or enum
                "label": "From Dict",
                "status": StrategicStatus.ACTIVE.value
            }
        ],
        "current_project_id": "prj_dict"
    }
    
    # This simulates what happens when receiving a proposal from a worker via Kafka/JSON
    up = StrategicUpdate.model_validate(raw_update)
    
    assert isinstance(up.projects_add_or_update[0], ProjectRecord)
    assert up.projects_add_or_update[0].label == "From Dict"
    assert up.current_project_id == "prj_dict"
