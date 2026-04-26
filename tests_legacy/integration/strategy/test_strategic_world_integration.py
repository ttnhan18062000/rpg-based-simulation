import pytest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.systems.world.strategy_world_integration_system import StrategicWorldIntegrationSystem
from src_legacy.core.models.world_strategy import StrategicOpportunity
from src_legacy.core.models.enums import StrategicStatus
from src_legacy.systems.infrastructure.base import SystemContext
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.core.world.grid import Grid
from src_legacy.platform.spatial_hash import SpatialHash

def create_mock_world():
    grid = Grid(100, 100)
    spatial = SpatialHash(16)
    return WorldState(seed=1, grid=grid, spatial_index=spatial)

def test_world_strategic_registry_persistence():
    """Verify that WorldStrategicRegistry is preserved in snapshots."""
    from src_legacy.core.models.strategy import LeadRecord, LeadKind
    world = create_mock_world()
    # Add an opportunity
    opp = StrategicOpportunity(
        opportunity_id="test_opp",
        label="Liberate the Region",
        description="A test opportunity",
        lead=LeadRecord(lead_id="test_lead", kind=LeadKind.LOCATION, label="Test Lead"),
        status=StrategicStatus.ACTIVE,
        expires_tick=100
    )
    world.strategic_registry.opportunities["test_opp"] = opp
    
    # Take snapshot
    snap = Snapshot.from_world(world)
    
    # Recover
    new_world = WorldState.from_snapshot(snap, world.spatial_index)
    
    assert "test_opp" in new_world.strategic_registry.opportunities
    assert new_world.strategic_registry.opportunities["test_opp"].label == "Liberate the Region"

def test_strategic_world_integration_system_pruning():
    """Verify that the system prunes expired world opportunities."""
    from src_legacy.core.models.strategy import LeadRecord, LeadKind
    world = create_mock_world()
    world.tick = 60
    
    # Active opportunity
    opp1 = StrategicOpportunity(
        opportunity_id="active",
        label="Active Opp",
        description="test",
        lead=LeadRecord(lead_id="l1", kind=LeadKind.LOCATION, label="l1"),
        status=StrategicStatus.ACTIVE,
        expires_tick=100
    )
    # Expired opportunity
    opp2 = StrategicOpportunity(
        opportunity_id="expired",
        label="Expired Opp",
        description="test",
        lead=LeadRecord(lead_id="l2", kind=LeadKind.LOCATION, label="l2"),
        status=StrategicStatus.ACTIVE,
        expires_tick=40
    )
    
    world.strategic_registry.opportunities["active"] = opp1
    world.strategic_registry.opportunities["expired"] = opp2
    
    from src_legacy.config import SimulationConfig
    from src_legacy.systems.world.generator import EntityGenerator
    cfg = SimulationConfig()
    rng = DeterministicRNG(1)
    gen = EntityGenerator(cfg, rng)
    system = StrategicWorldIntegrationSystem(cfg, rng)
    ctx = SystemContext(world=world, config=cfg, rng=rng, generator=gen, emit=None, faction_reg=None)
    system.on_tick(ctx, 60)
    
    assert "active" in world.strategic_registry.opportunities
    assert "expired" not in world.strategic_registry.opportunities

def test_telemetry_strategic_metrics():
    """Verify that TelemetrySystem collects strategic metrics."""
    from src_legacy.systems.infrastructure.telemetry_system import TelemetrySystem
    from src_legacy.utils.metrics import SIM_STRATEGIC_WORLD_OPPORTUNITIES
    from src_legacy.config import SimulationConfig
    
    from src_legacy.core.models.strategy import LeadRecord, LeadKind
    world = create_mock_world()
    opp = StrategicOpportunity(
        opportunity_id="test_opp",
        label="Liberate",
        description="test",
        lead=LeadRecord(lead_id="l3", kind=LeadKind.LOCATION, label="l3"),
        status=StrategicStatus.ACTIVE,
        expires_tick=100
    )
    world.strategic_registry.opportunities["test_opp"] = opp
    
    from src_legacy.systems.world.generator import EntityGenerator
    cfg = SimulationConfig()
    rng = DeterministicRNG(1)
    gen = EntityGenerator(cfg, rng)
    system = TelemetrySystem(cfg, rng)
    ctx = SystemContext(world=world, config=cfg, rng=rng, generator=gen, emit=None, faction_reg=None)
    
    # This will set the gauge
    system.on_tick(ctx, 1)
    
    # Check gauge value (using prometheus_client internal access for testing)
    assert SIM_STRATEGIC_WORLD_OPPORTUNITIES._value.get() == 1
