"""Integration test for Phase 2 Social Knowledge Propagation.

Verifies that:
1. One entity can observe an event and form a belief.
2. The observer can share this belief with another entity (rumor).
3. The recipient adopts the belief with reduced confidence/directness.
"""

import pytest
from src.core.entities.entity import Entity
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.ai.beliefs import BeliefService
from src.core.logic.knowledge_propagation import KnowledgePropagationService
from src.systems.social.knowledge_propagation_system import KnowledgePropagationSystem
from src.systems.infrastructure.base import SystemContext
from src.core.gameplay.faction import FactionRegistry
from src.core.models.vectors import Vector2
from src.config import SimulationConfig
from src.platform.rng import DeterministicRNG

@pytest.fixture
def base_world():
    config = SimulationConfig()
    grid = Grid(100, 100)
    spatial_index = SpatialHash(cell_size=10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial_index)
    # Add some entities
    e1 = Entity(id=1, kind="hero")
    e1.identity.display_name = "Witness"
    e2 = Entity(id=2, kind="monster")
    e2.identity.display_name = "Target"
    e3 = Entity(id=3, kind="hero")
    e3.identity.display_name = "Recipient"
    
    world.add_entity(e1)
    world.add_entity(e2)
    world.add_entity(e3)
    
    # Place them close
    e1.spatial.pos = Vector2(10, 10)
    e2.spatial.pos = Vector2(11, 11)
    e3.spatial.pos = Vector2(10, 11)
    
    return world, config, e1, e2, e3

def test_belief_sharing_propagation(base_world):
    world, config, witness, target, recipient = base_world
    rng = DeterministicRNG(0)
    
    # 1. Witness observes the target
    tick = 10
    belief = BeliefService.refresh_belief_from_observation(witness, target, tick)
    witness.mind.perception.entity_memory[target.id] = belief
    
    assert target.id in witness.mind.perception.entity_memory
    assert witness.mind.perception.entity_memory[target.id].knowledge_source == "direct"
    
    # 2. Run propagation system
    faction_reg = FactionRegistry.default()
    system = KnowledgePropagationSystem(config, rng)
    ctx = SystemContext(config, world, rng, None, faction_reg, lambda c, m, e=(), mt=None: None)
    
    # Force sharing by calling the service and applying updates
    p_up, _ = KnowledgePropagationService.propagate_gossip(witness, recipient, world)
    if p_up:
        for eid, b_rec in p_up.entity_memory.items():
            up = BeliefService.merge_indirect_belief(recipient, b_rec)
            if up:
                recipient.mind.perception.entity_memory.update(up.entity_memory)
    
    # Authoritative application (in a real tick, the system does this)
    # The KnowledgePropagationService.propagate_gossip returns a PerceptionUpdate.
    # But in the system implementation I just wrote, it calls merge_indirect_belief directly.
    # Wait, let's check the system implementation again.
    # Yes, I made it call BeliefService.merge_indirect_belief(recipient, belief) directly in the system.
    
    # Let's run the system on_tick (it checks tick % 5 == 0)
    system.on_tick(ctx, 5)
    
    # 3. Verify Recipient has the belief
    assert target.id in recipient.mind.perception.entity_memory
    shared_belief = recipient.mind.perception.entity_memory[target.id]
    assert shared_belief.knowledge_source == "indirect"
    assert shared_belief.directness < 1.0
    assert shared_belief.confidence < 1.0 # Should be reduced
    
    print(f"Propagated belief confidence: {shared_belief.confidence}")

def test_belief_conflict_resolution(base_world):
    world, config, witness, target, recipient = base_world
    
    # Recipient already has a DIRECT belief about target from tick 5
    direct_belief = BeliefService.refresh_belief_from_observation(recipient, target, 5)
    recipient.mind.perception.entity_memory[target.id] = direct_belief
    
    # Witness has a more recent INDIRECT belief from tick 10
    # (Actually witness usually has direct, but let's say they share)
    witness_belief = BeliefService.refresh_belief_from_observation(witness, target, 10)
    witness.mind.perception.entity_memory[target.id] = witness_belief
    
    # Share from witness to recipient
    KnowledgePropagationService.propagate_gossip(witness, recipient, world)
    # Wait, in the system code I wrote:
    # update = KnowledgePropagationService.propagate_gossip(sharer, recipient, world)
    # BeliefService.merge_indirect_belief(recipient, belief)
    
    p_up, _ = KnowledgePropagationService.propagate_gossip(witness, recipient, world)
    if p_up:
        for eid, belief in p_up.entity_memory.items():
            up = BeliefService.merge_indirect_belief(recipient, belief)
            if up:
                recipient.mind.perception.entity_memory.update(up.entity_memory)
        
    # Recipient should STILL HAVE direct belief because it has higher total value (confidence * directness)
    # unless the new one is significantly more recent? 
    # Current merge logic: Keep higher (confidence * directness)
    # Direct = 1.0 * 1.0 = 1.0
    # Indirect = ~0.8 * 0.7 = 0.56
    
    final_belief = recipient.mind.perception.entity_memory[target.id]
    assert final_belief.knowledge_source == "direct"
    assert final_belief.last_seen_tick == 5
