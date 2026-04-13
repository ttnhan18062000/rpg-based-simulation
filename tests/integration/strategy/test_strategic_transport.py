import pytest
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.enums import ActionType, StrategicStatus, DirectiveKind, ProjectKind
from src.actions.base import ActionProposal, StrategicUpdate
from src.core.models.strategy import DirectiveRecord, ProjectRecord, ConcernRecord
from src.systems.gameplay.action_system import ActionSystem
from src.platform.rng import DeterministicRNG

from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def base_world():
    """Create a minimal world with one entity."""
    grid = Grid(10, 10)
    spatial_index = SpatialHash(16)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial_index)
    entity = Entity(id=1, kind="hero")
    world.entities[entity.id] = entity
    return world

def test_strategic_update_multi_record_transport(base_world):
    """Verify that a single proposal can carry multiple strategic updates."""
    actor = base_world.entities[1]
    rng = DeterministicRNG(42)
    from src.config import SimulationConfig
    config = SimulationConfig()
    from src.core.models.enums import ConcernKind
    
    update = StrategicUpdate(
        directives_add=[DirectiveRecord(directive_id="d1", kind=DirectiveKind.PERSONAL, label="Stay Safe")],
        projects_add_or_update=[ProjectRecord(project_id="p1", kind=ProjectKind.EXPLORATION, label="Find Gold", status=StrategicStatus.ACTIVE)],
        concerns_add_or_update=[ConcernRecord(concern_id="c1", kind=ConcernKind.THREAT, label="Low HP", priority=5.0)]
    )
    
    proposal = ActionProposal(
        actor_id=actor.id,
        verb=ActionType.REST,
        updates=[update]
    )
    
    ActionSystem.apply_action_state_transitions(base_world, config, [proposal], rng)
    
    # Verify all records arrived
    assert len(actor.mind.strategic.directives) == 1
    assert actor.mind.strategic.directives[0].directive_id == "d1"
    
    assert len(actor.mind.strategic.projects) == 1
    assert actor.mind.strategic.projects[0].project_id == "p1"
    
    assert len(actor.mind.strategic.concerns) == 1
    assert actor.mind.strategic.concerns[0].concern_id == "c1"

def test_strategic_update_repeated_id_last_one_wins(base_world):
    """Verify that repeated IDs in a single update follow last-one-wins semantics."""
    actor = base_world.entities[1]
    rng = DeterministicRNG(42)
    
    # Repeated IDs in the same list
    update = StrategicUpdate(
        projects_add_or_update=[
            ProjectRecord(project_id="base_p", kind=ProjectKind.EXPLORATION, label="Old Label", status=StrategicStatus.ACTIVE),
            ProjectRecord(project_id="base_p", kind=ProjectKind.EXPLORATION, label="New Label", status=StrategicStatus.ACTIVE)
        ]
    )
    
    from src.config import SimulationConfig
    config = SimulationConfig()
    
    proposal = ActionProposal(actor_id=actor.id, verb=ActionType.REST, updates=[update])
    ActionSystem.apply_action_state_transitions(base_world, config, [proposal], rng)
    
    assert len(actor.mind.strategic.projects) == 1
    assert actor.mind.strategic.projects[0].label == "New Label"

def test_strategic_update_idempotency_over_ticks(base_world):
    """Verify that applying the same update multiple times is idempotent."""
    actor = base_world.entities[1]
    rng = DeterministicRNG(42)
    from src.config import SimulationConfig
    config = SimulationConfig()
    
    update = StrategicUpdate(
        directives_add=[DirectiveRecord(directive_id="d1", kind=DirectiveKind.PERSONAL, label="Stay Safe")]
    )
    
    proposal = ActionProposal(actor_id=actor.id, verb=ActionType.REST, updates=[update])
    
    # Apply twice
    ActionSystem.apply_action_state_transitions(base_world, config, [proposal], rng)
    ActionSystem.apply_action_state_transitions(base_world, config, [proposal], rng)
    
    assert len(actor.mind.strategic.directives) == 1
    assert actor.mind.strategic.directives[0].directive_id == "d1"

def test_strategic_update_target_routing(base_world):
    """Verify that strategic updates can be routed to a target entity."""
    actor = base_world.entities[1]
    
    # Create target
    target = Entity(id=2, kind="hero")
    base_world.entities[target.id] = target
    
    rng = DeterministicRNG(42)
    from src.config import SimulationConfig
    config = SimulationConfig()
    
    # Update for target
    update = StrategicUpdate(
        target_id=target.id,
        directives_add=[DirectiveRecord(directive_id="d1", kind=DirectiveKind.PERSONAL, label="Stay Safe")]
    )
    
    proposal = ActionProposal(actor_id=actor.id, verb=ActionType.REST, updates=[update])
    ActionSystem.apply_action_state_transitions(base_world, config, [proposal], rng)
    
    # Actor should be unchanged
    assert len(actor.mind.strategic.directives) == 0
    # Target should have the update
    assert len(target.mind.strategic.directives) == 1
    assert target.mind.strategic.directives[0].directive_id == "d1"
