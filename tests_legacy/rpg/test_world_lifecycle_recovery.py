import pytest
from src_legacy.core.state import AuthoritativeState, ResourceNodeState, CorpseState, EntityState, IdentityComponent, CombatComponent
from src_legacy.systems.world_lifecycle import WorldLifecycleSystem
from src_legacy.core.updates import StateUpdate, ResourceNodeUpdate

def test_resource_regeneration():
    """
    Law: Depleted resources must regenerate after their cooldown expires.
    """
    # 1. Setup: Depleted node with cooldown 1
    node = ResourceNodeState(
        id=1, kind="iron", position=(0,0), yields_item="iron_ore",
        remaining_charges=0, max_charges=5, required_ticks=10,
        respawn_cooldown=100, cooldown_remaining=1
    )
    
    state = AuthoritativeState(tick=100, seed=1, entities={}, resource_nodes={1: node})
    
    # 2. Process world lifecycle (decrements cooldown in HarvestSystem, then recharges here)
    # Actually, WorldLifecycleSystem handles the RECHARGE when cooldown is 0.
    # If cooldown is 1, it won't recharge.
    upd = WorldLifecycleSystem.resolve(state, StateUpdate())
    assert 1 not in upd.node_updates
    
    # 3. Setup: Cooldown is 0
    node_ready = replace(node, cooldown_remaining=0)
    state_ready = AuthoritativeState(tick=101, seed=1, entities={}, resource_nodes={1: node_ready})
    
    upd_ready = WorldLifecycleSystem.resolve(state_ready, StateUpdate())
    
    # Verify recharge
    assert upd_ready.node_updates[1].charges_delta == 5

def test_corpse_decay():
    """
    Law: Corpses must be removed from the world state after their decay tick.
    """
    corpse = CorpseState(
        id=500, original_entity_id=1, position=(0,0), 
        items=[], decay_tick=200
    )
    
    state = AuthoritativeState(tick=200, seed=1, entities={}, corpses={500: corpse})
    
    upd = WorldLifecycleSystem.resolve(state, StateUpdate())
    
    # Verify removal
    assert 500 in upd.corpses_remove

def test_inactive_entity_cleanup():
    """
    Law: Inactive entities must be reaped from the state.
    """
    entity = EntityState(
        id=1, kind="hero", position=(0,0), active=False,
        identity=IdentityComponent(), combat=CombatComponent()
    )
    
    state = AuthoritativeState(tick=300, seed=1, entities={1: entity})
    
    upd = WorldLifecycleSystem.resolve(state, StateUpdate())
    
    # Verify removal
    assert 1 in upd.entities_remove

def replace(obj, **kwargs):
    from dataclasses import replace as dr
    return dr(obj, **kwargs)
