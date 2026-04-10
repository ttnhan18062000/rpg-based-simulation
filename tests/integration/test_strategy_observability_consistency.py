import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.core.models.strategy import ConcernRecord, ConcernKind
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.entities.entity_builder import EntityBuilder
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.platform.rng import DeterministicRNG
from src.api.presenters.ai_presenter import AIPresenter
from src.systems.infrastructure.telemetry_system import TelemetrySystem
from src.systems.infrastructure.base import SystemContext
from src.utils.replay import ReplayRecorder

@pytest.fixture
def test_rng():
    return DeterministicRNG(seed=42)

@pytest.fixture
def base_world():
    grid = Grid(100, 100)
    world = WorldState(seed=42, grid=grid, spatial_index=SpatialHash(cell_size=10))
    return world

@pytest.fixture
def test_entity(base_world, test_rng):
    builder = EntityBuilder(test_rng, entity_id=1)
    entity = builder.kind("hero").with_identity(display_name="Test Hero").build()
    entity.world = base_world
    base_world.entities[1] = entity
    return entity

def test_strategy_observability_consistency(test_entity, base_world, test_rng, tmp_path):
    """Verify that a strategic shift is consistently observable across all surfaces."""
    tick = 100
    base_world.tick = tick
    
    # 1. Inject a strategic concern
    concern = ConcernRecord(
        concern_id="threat_1",
        kind=ConcernKind.THREAT,
        label="Bandit Raid",
        priority=5.0,
        urgency=0.9,
        created_tick=tick
    )
    test_entity.mind.strategic.concerns.append(concern)
    
    # 2. Verify API Visibility (AIPresenter)
    explanation = AIPresenter.get_explanation(test_entity)
    api_concern = next((c for c in explanation.strategy.concerns if c.concern_id == "threat_1"), None)
    assert api_concern is not None
    assert api_concern.priority == 5.0
    assert api_concern.visibility == "private"
    
    # 3. Verify Telemetry collection (TelemetrySystem)
    with patch("src.utils.metrics.SIM_STRATEGIC_PRESSURE_CONCERNS") as mock_gauge:
        mock_config = MagicMock()
        mock_emit = MagicMock()
        ctx = SystemContext(
            config=mock_config,
            world=base_world,
            rng=test_rng,
            generator=None,
            faction_reg=None,
            emit=mock_emit
        )
        
        telemetry = TelemetrySystem(mock_config, test_rng)
        telemetry.on_tick(ctx, tick)
        
        mock_gauge.labels.assert_called_with(kind="threat")
        mock_gauge.labels.return_value.set.assert_called_with(1)
        
    # 4. Verify Replay Recording (ReplayRecorder)
    replay_path = tmp_path / "test_replay.json"
    recorder = ReplayRecorder(path=replay_path, seed=42)
    recorder.record_tick(tick=tick, applied_actions=[], world=base_world)
    
    # Check the recorded snapshot for the entity
    snapshot = recorder._ticks[0]
    # entities is a list of dicts
    entity_snap = next(e for e in snapshot["entities"] if e["id"] == 1)
    
    assert entity_snap["strategy"]["concern_count"] == 1
    assert "project_id" in entity_snap["strategy"]
    assert "interrupted_by" in entity_snap["strategy"]
