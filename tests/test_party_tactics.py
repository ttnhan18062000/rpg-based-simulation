import pytest
from unittest.mock import MagicMock
from src.core.entities.entity import Entity
from src.ai.states.base import AIContext
from src.ai.strategy.objective_to_goal_mapper import ObjectiveToGoalMapper
from src.core.models.enums import GoalType, ObjectiveKind, GroupKind
from src.core.models.strategy import ObjectiveRecord, ProjectRecord, ProjectKind
from src.core.models.lived_structure import GroupRecord
from src.core.models.snapshot import Snapshot
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def mock_context():
    # Setup a mock world/snapshot/context
    grid = Grid(width=10, height=10)
    spatial_index = SpatialHash(cell_size=8)
    from src.core.models.world_state import WorldState
    world = WorldState(seed=42, grid=grid, spatial_index=spatial_index)
    
    actor = Entity(id=1, kind="hero")
    world.add_entity(actor)
    
    snap = Snapshot.from_world(world)
    config = MagicMock()
    rng = MagicMock()
    faction_reg = MagicMock()
    
    ctx = AIContext(actor=actor, snapshot=snap, config=config, rng=rng, faction_reg=faction_reg)
    return ctx

def test_vanguard_biases(mock_context):
    from src.core.models.lived_structure import GroupRecord
    from src.core.models.snapshot import Snapshot
    
    # 1. Update live world state
    actor = mock_context.actor
    actor.identity.group_id = "gp_test"
    
    group = GroupRecord(
        group_id="gp_test",
        kind=GroupKind.PARTY,
        member_ids={actor.id, 2},
        member_roles={actor.id: "vanguard"}
    )
    
    # We need to find the world to add the group
    # Since mock_context.snapshot was built from a world, let's just make a new one
    grid = Grid(width=10, height=10)
    spatial_index = SpatialHash(cell_size=8)
    from src.core.models.world_state import WorldState
    world = WorldState(seed=42, grid=grid, spatial_index=spatial_index)
    world.add_entity(actor)
    world.group_registry["gp_test"] = group
    
    # 2. Re-create context with new snapshot
    snap = Snapshot.from_world(world)
    mock_context.snapshot = snap
    
    # 3. Set project and objective
    prj = ProjectRecord(project_id="prj_1", kind=ProjectKind.QUEST, label="Test Quest")
    obj = ObjectiveRecord(objective_id="obj_kill", kind=ObjectiveKind.KILL, project_id="prj_1", label="Kill Target")
    prj.objectives.append(obj)
    prj.active_objective_id = "obj_kill"
    
    actor.mind.strategic.projects.append(prj)
    actor.mind.strategic.current_project_id = "prj_1"
    actor.mind.strategic.current_objective_id = "obj_kill"
    
    biases = ObjectiveToGoalMapper.get_tactical_biases(mock_context)
    assert biases[GoalType.COMBAT] > 1.0

def test_support_biases(mock_context):
    from src.core.models.lived_structure import GroupRecord
    from src.core.models.snapshot import Snapshot
    from src.core.models.world_state import WorldState
    
    actor = mock_context.actor
    actor.identity.group_id = "gp_test"
    group = GroupRecord(
        group_id="gp_test",
        kind=GroupKind.PARTY,
        member_ids={actor.id, 2},
        member_roles={actor.id: "support"}
    )
    
    world = WorldState(seed=42, grid=Grid(width=10, height=10), spatial_index=SpatialHash())
    world.add_entity(actor)
    world.group_registry["gp_test"] = group
    
    mock_context.snapshot = Snapshot.from_world(world)
    
    prj = ProjectRecord(project_id="prj_1", kind=ProjectKind.QUEST, label="Test Quest")
    obj = ObjectiveRecord(objective_id="obj_kill", kind=ObjectiveKind.KILL, project_id="prj_1", label="Kill Target")
    prj.objectives.append(obj)
    prj.active_objective_id = "obj_kill"
    
    actor.mind.strategic.projects.append(prj)
    actor.mind.strategic.current_project_id = "prj_1"
    actor.mind.strategic.current_objective_id = "obj_kill"
    
    biases = ObjectiveToGoalMapper.get_tactical_biases(mock_context)
    assert biases[GoalType.SOCIAL] > 1.0

def test_protector_biases(mock_context):
    from src.core.models.lived_structure import GroupRecord
    from src.core.models.snapshot import Snapshot
    from src.core.models.world_state import WorldState
    
    actor = mock_context.actor
    actor.identity.group_id = "gp_test"
    group = GroupRecord(
        group_id="gp_test",
        kind=GroupKind.PARTY,
        member_ids={actor.id, 2},
        member_roles={actor.id: "protector"}
    )
    
    world = WorldState(seed=42, grid=Grid(width=10, height=10), spatial_index=SpatialHash())
    world.add_entity(actor)
    world.group_registry["gp_test"] = group
    
    mock_context.snapshot = Snapshot.from_world(world)
    
    prj = ProjectRecord(project_id="prj_1", kind=ProjectKind.QUEST, label="Test Quest")
    obj = ObjectiveRecord(objective_id="obj_kill", kind=ObjectiveKind.KILL, project_id="prj_1", label="Kill Target")
    prj.objectives.append(obj)
    prj.active_objective_id = "obj_kill"
    
    actor.mind.strategic.projects.append(prj)
    actor.mind.strategic.current_project_id = "prj_1"
    actor.mind.strategic.current_objective_id = "obj_kill"
    
    biases = ObjectiveToGoalMapper.get_tactical_biases(mock_context)
    assert biases[GoalType.SOCIAL] > 1.5
