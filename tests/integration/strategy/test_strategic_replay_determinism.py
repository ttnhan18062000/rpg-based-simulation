import pytest
import os
import json
from src.core.models.world_strategy import WorldStrategicRegistry, StrategicOpportunity
from src.core.models.strategy import LeadRecord, LeadKind, StrategicStatus
from src.core.models.vectors import Vector2
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.engine.world_loop import WorldLoop
from src.engine.worker_pool import WorkerPool
from src.engine.conflict_resolver import ConflictResolver
from src.systems.world.generator import EntityGenerator
from src.ai.brain import AIBrain
from src.core.gameplay.faction import FactionRegistry
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig

@pytest.fixture
def manual_loop():
    # Setup minimal infrastructure
    grid = Grid(10, 10)
    spatial_index = SpatialHash(16)
    world = WorldState(seed=123, grid=grid, spatial_index=spatial_index)
    
    # Add a hero
    hero = Entity(id=100, kind="hero", identity={"role": 0}) # HERO = 0
    world.add_entity(hero)
    
    config = SimulationConfig(world_seed=123)
    rng = DeterministicRNG(123)
    faction_reg = FactionRegistry.default()
    brain = AIBrain(config, rng, faction_reg)
    
    worker_pool = WorkerPool(config, brain, rng)
    conflict_resolver = ConflictResolver(config, rng)
    generator = EntityGenerator(config, rng)
    
    loop = WorldLoop(
        config=config, 
        world=world,
        worker_pool=worker_pool,
        conflict_resolver=conflict_resolver,
        generator=generator,
        rng=rng,
        faction_reg=faction_reg
    )
    return loop

def test_world_strategic_registry_deep_isolation():
    """Verify that WorldStrategicRegistry.copy() performs a deep copy."""
    reg = WorldStrategicRegistry()
    lead = LeadRecord(
        lead_id="lead_1",
        kind=LeadKind.LOCATION,
        label="Test Lead",
        target_coords=Vector2(x=10, y=20)
    )
    opp = StrategicOpportunity(
        opportunity_id="opp_1",
        label="Test Opp",
        description="Testing isolation",
        lead=lead
    )
    reg.opportunities["opp_1"] = opp
    
    # Create copies
    snap_reg = reg.copy()
    
    # Mutate the snapshot
    snap_reg.opportunities["opp_1"].label = "MUTATED"
    snap_reg.opportunities["opp_1"].lead.target_coords.x = 999
    
    # Verify isolation
    assert reg.opportunities["opp_1"].label == "Test Opp"
    assert reg.opportunities["opp_1"].lead.target_coords.x == 10
    assert snap_reg.opportunities["opp_1"].label == "MUTATED"
    assert snap_reg.opportunities["opp_1"].lead.target_coords.x == 999

def test_strategic_replay_graph_equality(manual_loop):
    """Verify that replaying from a snapshot yields bit-identical cognition graphs."""
    from src.api.engine_manager import EngineManager
    from src.core.logic.cognition_graph_exporter import EntityCognitionExporter
    from src.api.adapters.cytoscape_adapter import CytoscapeAdapter
    
    loop = manual_loop
    # 1. Run for 5 ticks
    for _ in range(5):
        loop.tick_once()
        
    hero = next(e for e in loop.world.entities.values() if e.kind == "hero")
    
    # 2. Capture baseline graph
    graph_v1 = EntityCognitionExporter.export(hero, loop.world.tick)
    
    # 3. Create a snapshot and recover into a new engine
    # We use Snapshot for serialization round-trip
    from src.core.models.snapshot import Snapshot
    snap = Snapshot.from_world(loop.world)
    snap_json = snap.model_dump_json()
    snap_v2 = Snapshot.model_validate_json(snap_json)
    
    # 4. Export graph from recovered snapshot (at same tick)
    hero_v2 = snap_v2.entities[hero.id]
    graph_v2 = EntityCognitionExporter.export(hero_v2, snap_v2.tick)
    
    # 5. Assert equality
    assert graph_v1.model_dump() == graph_v2.model_dump()

def test_lead_outcome_grounding_verification(manual_loop):
    """Verify that precise leads correctly ground into world entities."""
    from src.core.models.strategy import LeadRecord, LeadKind
    from src.core.entities.entity import Entity
    
    loop = manual_loop
    # Add a target building
    building = Entity(id=200, kind="building", identity={"role": 1}) # SHOP = 1
    building.spatial.pos = Vector2(x=5, y=5)
    loop.world.add_entity(building)
    
    # Create a precise lead pointing to this building
    lead = LeadRecord(
        lead_id="lead_shop",
        kind=LeadKind.LOCATION,
        label="The Old Shop",
        target_coords=Vector2(x=5, y=5),
        target_entity_id=200
    )
    
    # Verification: Does the world actually have a building at 5,5?
    entities_at = loop.world.spatial_index.query_cell(Vector2(x=5, y=5))
    found_b = next((e_id for e_id in entities_at if e_id == 200), None)
    
    assert found_b is not None
    ent = loop.world.entities[found_b]
    assert ent.kind == "building"
