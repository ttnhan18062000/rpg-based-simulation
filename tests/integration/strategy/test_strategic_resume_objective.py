"""Integration test for Strategic Resume Reliability. [Batch 5]
Verifies that suspended objectives correctly benefit from resume_reliability scoring
and regain focus when the current project is no longer overwhelmingly superior.
"""
import pytest
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.strategy import StrategicStatus, ProjectKind, ProjectRecord, ObjectiveRecord, ObjectiveKind
from src.ai.brain import AIBrain
from src.core.models.snapshot import Snapshot
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.actions.base import StrategicUpdate

@pytest.fixture
def mock_world():
    grid = Grid(100, 100)
    spatial = SpatialHash(cell_size=10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.entities = {}
    return world

@pytest.fixture
def brain():
    config = SimulationConfig()
    return AIBrain(config, DeterministicRNG(0))

def test_objective_resume_reliability(mock_world, brain):
    """Verify that a suspended objective is resumed correctly."""
    hero = Entity(id=1, kind="hero")
    mock_world.add_entity(hero)
    
    # 1. Setup a suspended project with an objective
    obj1 = ObjectiveRecord(objective_id="obj_1", project_id="prj_old", kind=ObjectiveKind.SCOUT, label="Old Scout", priority=5.0)
    prj_old = ProjectRecord(
        project_id="prj_old", 
        label="Old Quest", 
        kind=ProjectKind.QUEST, 
        status=StrategicStatus.SUSPENDED,
        objectives=[obj1],
        priority=5.0
    )
    hero.mind.strategic.projects.append(prj_old)
    
    # 2. Setup a currently active project with low priority and NO threshold
    prj_cur = ProjectRecord(
        project_id="prj_cur", 
        label="Current Filler", 
        kind=ProjectKind.QUEST, 
        status=StrategicStatus.ACTIVE,
        priority=0.1,
        interruption_threshold=0.0,
        abandonment_cost=0.0
    )
    hero.mind.strategic.projects.append(prj_cur)
    hero.mind.strategic.current_project_id = "prj_cur"
    
    # boost the attributes to get high resume_reliability
    from src.core.gameplay.attributes import Attributes, AttributeCaps, recalc_derived_stats
    hero.progression.attributes = Attributes(int_=15, wis=15, per=15)
    hero.progression.attribute_caps = AttributeCaps(int_cap=20, wis_cap=20, per_cap=20)
    recalc_derived_stats(hero, hero.progression.attributes)

    # 3. Decision pass
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    
    update = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert update is not None
    
    # Should have switched back to prj_old due to high resume_reliability boost
    assert update.current_project_id == "prj_old"
    assert update.current_objective_id == "obj_1"
    
    # Check drivers
    driver = next((d for d in update.strategic_drivers if d.label == "Project Switch"), None)
    assert driver is not None
    assert "prj_old" in driver.description
