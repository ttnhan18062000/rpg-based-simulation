"""Unit tests for Strategic Layer services and model integrity.
[CONSOLIDATED FROM test_strategic_reprioritization.py and test_strategic_consistency.py]
"""

import pytest
from unittest.mock import MagicMock
from src_legacy.core.logic.concern_generation import ConcernGenerationService
from src_legacy.core.logic.directive_mutation_service import DirectiveMutationService
from src_legacy.core.logic.project_mutation_service import ProjectMutationService
from src_legacy.core.models.strategy import StrategicState, ProjectRecord, ProjectKind, StrategicStatus, ConcernKind, ObjectiveRecord, ObjectiveKind, BlockerRecord, BlockerKind, ConcernRecord
from src_legacy.ai.cognition_capacity import CognitionCapacityProfile
from src_legacy.actions.base import StrategicUpdate, PerceptionUpdate
from src_legacy.core.models.life_events import InterpretedLifeEvent, TurningPointRecord
from src_legacy.core.models.enums import InterpretedLifeEventKind, TurningPointKind, ObjectiveKind
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.entities.entity import Entity
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.systems.gameplay.action_system import ActionSystem

@pytest.fixture
def mock_world():
    world = MagicMock()
    world.tick = 100
    world.entities = {}
    world.get_entity.side_effect = lambda eid: world.entities.get(eid)
    # Add real grid for some tests that might need it
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    world.grid = Grid(width=10, height=10)
    world.spatial_index = SpatialHash(cell_size=16)
    return world

@pytest.fixture
def actor():
    return Entity(id=1, kind="hero")

@pytest.fixture
def rng():
    return DeterministicRNG(seed=42)

# --- Model Integrity Tests ---

def test_canonical_blocker_structure():
    """Verify that StrategicState has a blockers list and ObjectiveRecord uses IDs."""
    obj = ObjectiveRecord(
        objective_id="obj1",
        project_id="p1",
        kind=ObjectiveKind.VISIT,
        label="Test Objective",
        blocker_ids=["blocker-a"]
    )
    
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
    
    copy_actor = actor.copy()
    copy_actor.mind.strategic.projects[0].objectives[0].blocker_ids.append("b2")
    
    assert len(actor.mind.strategic.projects[0].objectives[0].blocker_ids) == 1
    assert "b2" not in actor.mind.strategic.projects[0].objectives[0].blocker_ids
    assert "b2" in copy_actor.mind.strategic.projects[0].objectives[0].blocker_ids

def test_belief_decay_aoa_purity(actor):
    """Verify that BeliefService.decay_stale_beliefs returns an update and does not mutate in-place."""
    from src_legacy.core.aspects.mind import BeliefRecord, ThreatEstimate
    from src_legacy.ai.beliefs import BeliefService
    from src_legacy.core.models.snapshot import Snapshot
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    
    # Use real world/grid to avoid MagicMock Pydantic validation errors [PHASE 5 FIX]
    world = WorldState(seed=42, grid=Grid(10, 10), spatial_index=SpatialHash(cell_size=16))
    world.tick = 100
    
    # Add a stale belief
    belief = BeliefRecord(
        entity_id=2, 
        last_seen_tick=10, 
        confidence=1.0,
        pos=Vector2(x=5, y=5),
        threat=ThreatEstimate(overall=0.5, survivability=0.5, confidence=1.0, melee_threat=0.5, ranged_threat=0.0)
    )
    actor.mind.perception.entity_memory[2] = belief
    
    world.entities = {actor.id: actor}
    snap = Snapshot.from_world(world)
    frozen_actor = snap.entities[actor.id]
    
    # 1. Decay on frozen actor returns an update
    update = BeliefService.decay_stale_beliefs(frozen_actor, 100)
    assert update is not None
    assert 2 in update.entity_memory
    assert update.entity_memory[2].confidence < 1.0
    
    # 2. Verify frozen actor was NOT mutated
    assert frozen_actor.mind.perception.entity_memory[2].confidence == 1.0

def test_social_applicator_aoa_purity(mock_world, actor):
    """Verify that SocialStateApplicator returns updates and does not mutate the world."""
    from src_legacy.actions.base import PerceptionUpdate
    from src_legacy.core.logic.social_state_applicator import SocialStateApplicator
    
    mock_world.entities = {actor.id: actor}
    mock_world.tick = 50
    
    event = InterpretedLifeEvent(
        event_id="evt1",
        actor_id=actor.id,
        tick=50,
        kind=InterpretedLifeEventKind.NEAR_DEATH,
        severity=5.0,
        turning_point_candidate=True
    )
    
    # Applicator returns a list of updates
    updates = SocialStateApplicator.apply_interpreted_event(event, mock_world)
    
    # 1. Verify updates were returned
    assert len(updates) > 0
    tp_up = next((u for u in updates if isinstance(u, PerceptionUpdate) and u.turning_points_add), None)
    assert tp_up is not None
    assert tp_up.turning_points_add[0].event_id == "evt1"
    
    # 2. Verify actor turning points are STILL EMPTY (no mutation)
    assert len(actor.mind.narrative.turning_points) == 0

# --- Service Logic Tests ---

def test_concern_generation_near_death(mock_world, actor, rng):
    updates = StrategicUpdate(target_id=actor.id)
    event = InterpretedLifeEvent(
        event_id="ev_1",
        kind=InterpretedLifeEventKind.NEAR_DEATH,
        tick=mock_world.tick,
        actor_id=actor.id,
        severity=8.0
    )
    
    from src_legacy.ai.cognition_capacity import CognitionCapacityBuilder
    profile = CognitionCapacityBuilder.build(actor)
    # Force stability to 1.0 to ensure deterministic 4.5 priority
    from src_legacy.ai.cognition_capacity import CognitionCapacityProfile
    stable_profile = profile.model_copy(update={"judgment_stability": 1.0})
    
    ConcernGenerationService.generate(mock_world, actor, event, updates, rng, profile=stable_profile)
    
    assert len(updates.concerns_add_or_update) == 1
    concern = updates.concerns_add_or_update[0]
    assert concern.kind == ConcernKind.THREAT
    assert "Survival" in concern.label
    assert concern.priority == 4.5

def test_directive_mutation_near_death(mock_world, actor, rng):
    updates = StrategicUpdate(target_id=actor.id)
    tp = TurningPointRecord(
        event_id="ev_1",
        kind=TurningPointKind.NEAR_DEATH,
        tick=mock_world.tick,
        salience_score=0.9
    )
    
    prev_tp = TurningPointRecord(event_id="prev", kind=TurningPointKind.NEAR_DEATH, tick=0, salience_score=1.0)
    actor.mind.narrative.turning_points = [prev_tp, prev_tp, tp]
    
    DirectiveMutationService.evaluate_mutation(mock_world, actor, tp, updates, rng)
    
    assert len(updates.directives_add) == 1
    directive = updates.directives_add[0]
    assert "Safety" in directive.label
    assert directive.priority == 3.5

def test_project_mutation_interruption(mock_world, actor):
    updates = StrategicUpdate(target_id=actor.id)
    
    project = ProjectRecord(
        project_id="prj_1",
        kind=ProjectKind.EXPLORATION,
        label="Explore",
        priority=1.0,
        status=StrategicStatus.ACTIVE,
        interruption_threshold=0.5
    )
    actor.mind.strategic.projects = [project]
    actor.mind.strategic.current_project_id = "prj_1"
    
    # Use real ConcernRecord [PHASE 5 FIX]
    updates.concerns_add_or_update.append(ConcernRecord(
        concern_id="c1", kind=ConcernKind.THREAT, label="High Threat", priority=3.0
    ))
    
    event = InterpretedLifeEvent(event_id="ev_1", kind=InterpretedLifeEventKind.NEAR_DEATH, tick=100, actor_id=actor.id)
    
    ProjectMutationService.process_interruption(mock_world, actor, event, None, updates)
    
    found_pivot = any(p.kind == ProjectKind.DEVELOPMENT for p in updates.projects_add_or_update)
    assert found_pivot, "Project should have pivoted to DEVELOPMENT given threat during exploration"

def test_strategic_update_blocker_merging(mock_world, actor):
    """Verify that ActionSystem merges blockers from StrategicUpdate correctly."""
    from src_legacy.systems.gameplay.action_system import ActionSystem
    mock_world.entities = {actor.id: actor}
    
    actor.mind.strategic.blockers.append(BlockerRecord(blocker_id="b1", kind=BlockerKind.KNOWLEDGE, label="Old Blocker"))
    
    update = StrategicUpdate(
        target_id=actor.id,
        blockers_add_or_update=[
            BlockerRecord(blocker_id="b1", kind=BlockerKind.KNOWLEDGE, label="Updated Blocker"),
            BlockerRecord(blocker_id="b2", kind=BlockerKind.KNOWLEDGE, label="New Blocker")
        ]
    )
    
    ActionSystem._apply_updates(mock_world, actor, [update], None)
    
    assert len(actor.mind.strategic.blockers) == 2
    b1 = next(b for b in actor.mind.strategic.blockers if b.blocker_id == "b1")
    assert b1.label == "Updated Blocker"
    
    remove_update = StrategicUpdate(target_id=actor.id, blockers_remove=["b1"])
    ActionSystem._apply_updates(mock_world, actor, [remove_update], None)
    
    assert len(actor.mind.strategic.blockers) == 1
    assert actor.mind.strategic.blockers[0].blocker_id == "b2"
