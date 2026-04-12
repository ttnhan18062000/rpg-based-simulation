import pytest
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.models.snapshot import Snapshot
from src.core.models.strategy import ProjectRecord, ProjectKind, ConcernRecord, ConcernKind, ObjectiveKind, StrategicStatus, ObjectiveRecord
from src.ai.brain import AIBrain
from src.ai.states.base import AIContext
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig

@pytest.fixture
def brain():
    config = SimulationConfig()
    rng = DeterministicRNG(0)
    return AIBrain(config, rng)

from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def base_world():
    grid = Grid(100, 100)
    spatial = SpatialHash(cell_size=10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.tick = 100
    return world

def test_persistence_boost_prevents_switching(brain, base_world):
    """Verify that the persistence boost prevents switching to a slightly better project."""
    hero = Entity(id=1, kind="hero")
    base_world.entities[hero.id] = hero
    
    # Hero is committed to Project A (priority 2.0)
    # worked on it for 80 ticks
    prj_a = ProjectRecord(
        project_id="project_a", kind=ProjectKind.QUEST, label="Old Project", 
        priority=2.0, committed_at=20, abandonment_cost=1.0
    )
    hero.mind.strategic.projects.append(prj_a)
    hero.mind.strategic.current_project_id = "project_a"
    
    # A new project B appears with priority 2.5
    # Without persistence boost, 2.5 > 2.0 -> switch.
    # With boost (80 ticks * 1.0 = +0.8 boost approx), 2.8 > 2.5 -> stick.
    prj_b = ProjectRecord(
        project_id="project_b", kind=ProjectKind.QUEST, label="New Project",
        priority=2.5, created_tick=100
    )
    hero.mind.strategic.projects.append(prj_b)
    
    # Create snapshot for brain context
    from src.core.models.snapshot import Snapshot
    snapshot = Snapshot.from_world(base_world)
    
    # Run brain decision pass
    state, proposal = brain.decide(hero, snapshot)
    
    # Find strategic updates
    strat_up = next((u for u in proposal.updates if hasattr(u, 'current_project_id')), None)
    
    # Should STILL be project_a
    # If no update is sent, it means it sticks to current
    if strat_up and strat_up.current_project_id:
        assert strat_up.current_project_id == "project_a"

def test_project_lock_prevents_switching(brain, base_world):
    """Verify that project_lock_until strictly prevents any switches."""
    hero = Entity(id=1, kind="hero")
    base_world.entities[hero.id] = hero
    
    # Project A is locked until tick 150
    hero.mind.strategic.current_project_id = "project_a"
    hero.mind.strategic.project_lock_until = 150
    
    prj_a = ProjectRecord(
        project_id="project_a", kind=ProjectKind.QUEST, label="Old Project", 
        priority=2.0, committed_at=100
    )
    hero.mind.strategic.projects.append(prj_a)
    
    # A CRITICAL concern appears (priority 10.0!)
    # Should definitely switch normally, but locked.
    concern = ConcernRecord(
        concern_id="critical_threat", kind=ConcernKind.THREAT, label="DEATH", priority=10.0
    )
    hero.mind.strategic.concerns.append(concern)
    
    snapshot = Snapshot.from_world(base_world)
    state, proposal = brain.decide(hero, snapshot)
    
    strat_up = next((u for u in proposal.updates if hasattr(u, 'current_project_id')), None)
    
    # Should STILL be project_a (or no update sent)
    if strat_up and strat_up.current_project_id:
        assert strat_up.current_project_id == "project_a"

def test_interruption_threshold_overridden_by_major_threat(brain, base_world):
    """Verify that a massive threat CAN overcome the interruption threshold."""
    hero = Entity(id=1, kind="hero")
    base_world.entities[hero.id] = hero
    
    # Project A is committed but has a high interruption threshold (0.5)
    prj_a = ProjectRecord(
        project_id="project_a", kind=ProjectKind.QUEST, label="Old Project", 
        priority=2.0, committed_at=95, # Only 5 ticks in
        interruption_threshold=0.5
    )
    hero.mind.strategic.projects.append(prj_a)
    hero.mind.strategic.current_project_id = "project_a"
    
    # Concern C with priority 5.0 appears
    # 5.0 > 2.0 + 0.5 (threshold) -> Switch!
    concern = ConcernRecord(
        concern_id="survival_threat", kind=ConcernKind.THREAT, label="Giant", priority=5.0
    )
    hero.mind.strategic.concerns.append(concern)
    
    snapshot = Snapshot.from_world(base_world)
    state, proposal = brain.decide(hero, snapshot)
    
    strat_up = next((u for u in proposal.updates if hasattr(u, 'current_project_id')), None)
    
    assert strat_up is not None
    # Should switch to survival or stabilization or similar promoted from concern
    assert "project" in strat_up.current_project_id
    assert strat_up.interrupted_project_id == "project_a"
