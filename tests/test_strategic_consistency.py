import pytest
from unittest.mock import MagicMock
from src.core.models.strategy import StrategicState, ProjectRecord, ObjectiveRecord, BlockerRecord
from src.actions.base import StrategicUpdate, PerceptionUpdate, SocialUpdate
from src.core.entities.entity import Entity
from src.core.models.world_state import WorldState
from src.systems.gameplay.action_system import ActionSystem
from src.ai.beliefs import BeliefService
from src.core.logic.social_state_applicator import SocialStateApplicator
from src.core.models.life_events import InterpretedLifeEvent
from src.core.models.enums import InterpretedLifeEventKind, ObjectiveKind, StrategicStatus, BlockerKind, ProjectKind
from src.core.aspects.mind import ThreatEstimate
from src.core.models.vectors import Vector2
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def mock_world():
    # Use real Grid to pass Snapshot.from_world validation
    grid = Grid(width=10, height=10)
    spatial = SpatialHash(cell_size=16)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    return world

def test_canonical_blocker_structure():
    """Verify that StrategicState has a blockers list and ObjectiveRecord uses IDs."""
    # Ensure all required fields for ObjectiveRecord are present
    obj = ObjectiveRecord(
        objective_id="obj1",
        project_id="p1",
        kind=ObjectiveKind.VISIT,
        label="Test Objective",
        blocker_ids=["blocker-a"]
    )
    
    # Ensure all required fields for ProjectRecord are present
    proj = ProjectRecord(
        project_id="p1", 
        objectives=[obj], 
        kind=ProjectKind.EXPLORATION, 
        label="Test Project"
    )
    
    strat = StrategicState(
        blockers=[BlockerRecord(blocker_id="blocker-a", kind=BlockerKind.KNOWLEDGE, label="The Wall")],
        projects=[proj]
    )
    
    assert "blocker-a" in obj.blocker_ids
    assert len(strat.blockers) == 1
    assert strat.blockers[0].blocker_id == "blocker-a"

def test_strategic_update_blocker_merging(mock_world):
    """Verify that ActionSystem merges blockers from StrategicUpdate into the canonical list."""
    entity = Entity(id=1, kind="test")
    mock_world.entities[1] = entity # CRITICAL: ActionSystem needs this to find the target
    
    # 1. Start with one blocker
    entity.mind.strategic.blockers.append(BlockerRecord(blocker_id="b1", kind=BlockerKind.KNOWLEDGE, label="Old Blocker"))
    
    # 2. Update to add/update b1 and add b2
    update = StrategicUpdate(
        target_id=1,
        blockers_add_or_update=[
            BlockerRecord(blocker_id="b1", kind=BlockerKind.KNOWLEDGE, label="Updated Blocker"),
            BlockerRecord(blocker_id="b2", kind=BlockerKind.KNOWLEDGE, label="New Blocker")
        ]
    )
    
    ActionSystem._apply_updates(mock_world, entity, [update], None)
    
    assert len(entity.mind.strategic.blockers) == 2
    b1 = next(b for b in entity.mind.strategic.blockers if b.blocker_id == "b1")
    assert b1.label == "Updated Blocker"
    
    # 3. Remove b1
    remove_update = StrategicUpdate(target_id=1, blockers_remove=["b1"])
    ActionSystem._apply_updates(mock_world, entity, [remove_update], None)
    
    assert len(entity.mind.strategic.blockers) == 1
    assert entity.mind.strategic.blockers[0].blocker_id == "b2"

def test_belief_decay_aoa_purity(mock_world):
    """Verify that BeliefService.decay_stale_beliefs returns an update and does not mutate in-place."""
    from src.core.aspects.mind import BeliefRecord
    
    entity = Entity(id=1, kind="test")
    # Add a stale belief
    belief = BeliefRecord(
        entity_id=2, 
        last_seen_tick=10, 
        confidence=1.0,
        pos=Vector2(x=5, y=5),
        threat=ThreatEstimate()
    )
    entity.mind.perception.entity_memory[2] = belief
    
    # Snapshooting (AOA Pillar 1)
    from src.core.models.snapshot import Snapshot
    mock_world.tick = 100
    mock_world.entities[1] = entity
    snap = Snapshot.from_world(mock_world)
    frozen_actor = snap.entities[1]
    
    # 1. Decay on frozen actor returns an update
    update = BeliefService.decay_stale_beliefs(frozen_actor, 100)
    assert isinstance(update, PerceptionUpdate)
    assert 2 in update.entity_memory
    assert update.entity_memory[2].confidence < 1.0
    
    # 2. Verify frozen actor was NOT mutated
    assert frozen_actor.mind.perception.entity_memory[2].confidence == 1.0

def test_social_applicator_aoa_purity(mock_world):
    """Verify that SocialStateApplicator returns updates and does not mutate the world."""
    actor = Entity(id=1, kind="test")
    mock_world.entities[1] = actor
    mock_world.tick = 50
    
    event = InterpretedLifeEvent(
        event_id="evt1",
        actor_id=1,
        tick=50,
        kind=InterpretedLifeEventKind.NEAR_DEATH,
        severity=5.0,
        turning_point_candidate=True
    )
    
    # Call applicator
    updates = SocialStateApplicator.apply_interpreted_event(event, mock_world)
    
    # 1. Verify updates were returned
    assert len(updates) > 0
    tp_up = next((u for u in updates if isinstance(u, PerceptionUpdate) and u.turning_points_add), None)
    assert tp_up is not None
    assert tp_up.turning_points_add[0].event_id == "evt1"
    
    # 2. Verify actor turning points are STILL EMPTY (no mutation)
    assert len(actor.mind.narrative.turning_points) == 0

def test_strategic_snapshot_isolation():
    """Verify that deep copying an entity results in a fully isolated strategic tree."""
    actor = Entity(id=1, kind="test")
    obj = ObjectiveRecord(
        objective_id="obj1", 
        project_id="p1",
        kind=ObjectiveKind.VISIT,
        label="Test Objective",
        blocker_ids=["b1"]
    )
    actor.mind.strategic.projects.append(ProjectRecord(
        project_id="p1", 
        kind=ProjectKind.EXPLORATION,
        label="Test Project",
        objectives=[obj]
    ))
    
    # Deep copy
    copy_actor = actor.copy()
    
    # Mutate the copy
    copy_actor.mind.strategic.projects[0].objectives[0].blocker_ids.append("b2")
    
    # Verify original is unchanged
    assert len(actor.mind.strategic.projects[0].objectives[0].blocker_ids) == 1
    assert "b2" not in actor.mind.strategic.projects[0].objectives[0].blocker_ids
    assert "b2" in copy_actor.mind.strategic.projects[0].objectives[0].blocker_ids
