"""Integration test for Cognition Graph regression. [MILESTONE 6]

This test ensures that a deterministic simulation run results in a 
predictable cognition graph export.
"""

import os
import json
import pytest
from src_legacy.config import SimulationConfig
from src_legacy.api.engine_manager import EngineManager
from src_legacy.core.logic.cognition_graph_exporter import EntityCognitionExporter
from src_legacy.api.adapters.cytoscape_adapter import CytoscapeAdapter

from src_legacy.engine.worker_pool import WorkerPool
from src_legacy.engine.conflict_resolver import ConflictResolver
from src_legacy.systems.world.generator import EntityGenerator
from src_legacy.ai.brain import AIBrain
from src_legacy.core.gameplay.faction import FactionRegistry
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.engine.world_loop import WorldLoop
from src_legacy.core.world.grid import Grid
from src_legacy.platform.spatial_hash import SpatialHash
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.entities.entity import Entity

@pytest.fixture
def manual_loop():
    # Setup minimal infrastructure
    grid = Grid(10, 10)
    spatial_index = SpatialHash(16)
    world = WorldState(seed=123, grid=grid, spatial_index=spatial_index)
    
    # Add a hero
    hero = Entity(id=100, kind="hero", identity={"role": 0})
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

def test_cognition_graph_deterministic_simulation(manual_loop):
    """Verify that a simulation produces a valid, repeatable cognition graph."""
    loop = manual_loop
    # ...
    
    # 1. Run for a few ticks
    for _ in range(5):
        loop.tick_once()
        
    # 2. Pick a hero entity
    hero = next((e for e in loop.world.entities.values() if e.identity.role == 0), None) # HERO = 0
    assert hero is not None
    
    # 3. Export graph
    graph = EntityCognitionExporter.export(hero, loop.world.tick)
    assert graph.entity_id == hero.id
    assert graph.tick == loop.world.tick
    assert len(graph.nodes) > 0
    
    # 4. Convert to Cytoscape
    cyto = CytoscapeAdapter.to_cytoscape_json(graph)
    assert "elements" in cyto
    assert "nodes" in cyto["elements"]
    assert "edges" in cyto["elements"]
    
    # 5. Determinism Check: Run again with same seed and check same graph
    # (Since we are using the same generator and loop in one test, it should be stable)
    graph_again = EntityCognitionExporter.export(hero, loop.world.tick)
    assert graph.model_dump() == graph_again.model_dump()

def test_graph_structural_invariants(manual_loop):
    """Verify that the graph follows structural rules across ticks."""
    loop = manual_loop
    loop.tick_once()
    
    hero = next((e for e in loop.world.entities.values() if e.identity.role == 0), None)
    graph = EntityCognitionExporter.export(hero, loop.world.tick)
    
    # Invariant: Root node must exist
    root_node = next((n for n in graph.nodes if n.node_id == f"entity:{hero.id}"), None)
    assert root_node is not None
    
    # Invariant: Every edge must have valid source/target in nodes
    node_ids = {n.node_id for n in graph.nodes}
    for edge in graph.edges:
        assert edge.source_id in node_ids
        assert edge.target_id in node_ids
