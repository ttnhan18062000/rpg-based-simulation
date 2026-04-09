
import pytest
from src.core.entities.entity_builder import EntityBuilder
from src.platform.rng import DeterministicRNG
from src.core.models.enums import Archetype, Faction, ActionType
from src.systems.gameplay.action_system import ActionSystem
from src.core.models.world_state import WorldState
from src.platform.spatial_hash import SpatialHash
from src.core.world.grid import Grid
from src.actions.base import ActionProposal
from src.config import SimulationConfig

def test_authoritative_gossip():
    rng = DeterministicRNG(123)
    world = WorldState(seed=123, grid=Grid(10, 10), spatial_index=SpatialHash(2))
    config = SimulationConfig()
    
    # Entity A (Actor)
    eid_a = world.allocate_entity_id()
    entity_a = (EntityBuilder(rng, eid_a)
                .kind("hero")
                .at((5, 5))
                .faction(Faction.HERO_GUILD)
                .with_archetype(Archetype.GLORY_SEEKER)
                .build())
    world.add_entity(entity_a)
    
    # Entity B (Listener)
    eid_b = world.allocate_entity_id()
    entity_b = (EntityBuilder(rng, eid_b)
                .kind("hero")
                .at((5, 6)) # Proximity (dist=1)
                .faction(Faction.HERO_GUILD)
                .with_archetype(Archetype.BALANCED)
                .build())
    world.add_entity(entity_b)
    
    # Give A some knowledge to gossip
    from src.core.aspects.mind import BeliefRecord
    from src.core.models.vectors import Vector2
    entity_a.mind.perception.entity_memory[999] = BeliefRecord(entity_id=999, pos=Vector2(0,0))
    
    # Proposal for A (does nothing important, but triggers the loop)
    proposal = ActionProposal(actor_id=eid_a, verb=ActionType.REST, target=None)
    
    # Apply updates through ActionSystem
    # This should trigger _process_proximity_gossip for entity_a,
    # which should add a KnowledgeUpdate to all_updates,
    # and then _apply_updates should apply it to ALL entities in the world (or targeted ones).
    # Wait, _apply_updates takes 'entity' as an argument. 
    # If the gossip update is for entity_b, will it work?
    # Let's check ActionSystem._apply_updates.
    
    ActionSystem.apply_action_state_transitions(world, config, [proposal], rng)
    
    # Verify B has the knowledge from A
    assert 999 in entity_b.mind.perception.entity_memory
