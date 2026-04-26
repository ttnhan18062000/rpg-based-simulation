import pytest
from src_legacy.world.generation import WorldGenerator

def test_world_generation_determinism():
    """
    Phase 9: Verify that world generation is 100% deterministic given the same seed.
    """
    seed = 42
    num_entities = 15
    
    # Generate two independent worlds with the exact same seed
    world_a = WorldGenerator.generate_world(seed, num_entities)
    world_b = WorldGenerator.generate_world(seed, num_entities)
    
    # 1. Regions should match
    assert len(world_a.regions) > 0
    assert world_a.regions.keys() == world_b.regions.keys()
    for r_id in world_a.regions:
        assert world_a.regions[r_id] == world_b.regions[r_id]
        
    # 2. Buildings (Camps/Town) should match
    assert len(world_a.buildings) > 0
    assert world_a.buildings.keys() == world_b.buildings.keys()
    for b_id in world_a.buildings:
        assert world_a.buildings[b_id].position == world_b.buildings[b_id].position
        assert world_a.buildings[b_id].kind == world_b.buildings[b_id].kind
        
    # 3. Resource Nodes should match
    assert len(world_a.resource_nodes) > 0
    assert world_a.resource_nodes.keys() == world_b.resource_nodes.keys()
    for n_id in world_a.resource_nodes:
        assert world_a.resource_nodes[n_id].position == world_b.resource_nodes[n_id].position
        
    # 4. Entities should match exactly
    assert len(world_a.entities) == num_entities
    assert world_a.entities.keys() == world_b.entities.keys()
    for e_id in world_a.entities:
        ent_a = world_a.entities[e_id]
        ent_b = world_b.entities[e_id]
        assert ent_a.position == ent_b.position
        assert ent_a.kind == ent_b.kind
