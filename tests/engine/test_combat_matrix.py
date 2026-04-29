import pytest
from src.engine.combat import CombatResolutionSystem
from src.core.state import AuthoritativeState, EntityState, CombatComponent, BiologicalComponent, IdentityComponent, ItemStack
from src.core.enums import EntityRole

@pytest.fixture
def base_state():
    attacker = EntityState(
        id=1, kind="hero", position=(5, 5), readiness=100,
        identity=IdentityComponent(faction="heroes", role=EntityRole.HERO),
        combat=CombatComponent(atk=20, def_stat=10, hp=100, max_hp=100, range=1, alive=True)
    )
    defender = EntityState(
        id=2, kind="mob", position=(6, 5), readiness=100,
        identity=IdentityComponent(faction="monsters", role=EntityRole.MONSTER),
        combat=CombatComponent(atk=10, def_stat=5, hp=50, max_hp=50, range=1, alive=True)
    )
    ally = EntityState(
        id=3, kind="hero", position=(5, 6), readiness=100,
        identity=IdentityComponent(faction="heroes", role=EntityRole.HERO),
        combat=CombatComponent(atk=10, def_stat=5, hp=50, max_hp=50, range=1, alive=True)
    )
    
    return AuthoritativeState(
        tick=1, seed=123, 
        entities={1: attacker, 2: defender, 3: ally},
        terrain={}
    )

from dataclasses import replace

def test_melee_range_violation(base_state):
    # Move defender 2 tiles away
    defender = base_state.entities[2]
    base_state.entities[2] = replace(defender, position=(7, 5))
    
    res = CombatResolutionSystem.resolve_attack(base_state.entities[1], base_state.entities[2], base_state)
    assert res.outcome_kind == "REJECTED"
    assert res.failure_reason == "OUT_OF_RANGE"

def test_friendly_fire_single_attack(base_state):
    # Try to attack ally
    res = CombatResolutionSystem.resolve_attack(base_state.entities[1], base_state.entities[3], base_state)
    assert res.outcome_kind == "REJECTED"
    assert res.failure_reason == "FRIENDLY_FIRE_ILLEGAL"

def test_aoe_friendly_fire_safety(base_state):
    # AoE centered on monster (2), ally (3) is also in radius
    # Attacker (1) is at (5,5), Monster (2) at (6,5), Ally (3) at (5,6)
    # Distance (6,5) to (5,6) is 2 (Manhattan)
    
    res_map = CombatResolutionSystem.resolve_aoe_attack(
        base_state.entities[1], (6, 5), radius=2, state=base_state, defender=base_state.entities[2]
    )
    
    # Monster should be hit
    assert 2 in res_map
    assert res_map[2].outcome_kind != "REJECTED"
    
    # Ally should NOT be hit (friendly fire safety)
    assert 3 not in res_map

def test_atomic_rewards_on_kill(base_state):
    # Set monster HP very low
    defender = base_state.entities[2]
    base_state.entities[2] = replace(defender, combat=replace(defender.combat, hp=1))
    
    res = CombatResolutionSystem.resolve_attack(base_state.entities[1], base_state.entities[2], base_state)
    assert res.outcome_kind == "KILL"
    assert not res.alive_set
    
    # Should have ResourceTransferIntent
    assert len(res.resource_transfers) == 1
    intent = res.resource_transfers[0]
    assert intent.source_id == 2
    assert intent.reward_upd.xp_gain > 0
    assert intent.gold_delta > 0

def test_multi_attacker_kill_rewards(base_state):
    # Two attackers hit one monster
    attacker1 = base_state.entities[1]
    attacker2 = base_state.entities[3] # ally
    defender = base_state.entities[2]
    
    # Set monster HP low
    base_state.entities[2] = replace(defender, combat=replace(defender.combat, hp=5))
    
    res = CombatResolutionSystem.resolve_multi_attack([attacker1, attacker2], base_state.entities[2], base_state)
    assert res.outcome_kind == "KILL"
    assert not res.alive_set
    
    # Should have ResourceTransferIntent
    assert len(res.resource_transfers) == 1
    intent = res.resource_transfers[0]
    assert intent.source_id == 2
    assert intent.reward_upd.xp_gain > 0

def test_xp_granted_when_inventory_full(base_state):
    # Set monster HP low
    defender = base_state.entities[2]
    base_state.entities[2] = replace(defender, combat=replace(defender.combat, hp=1))
    
    # Set attacker inventory full
    attacker = base_state.entities[1]
    base_state.entities[1] = replace(attacker, inventory=replace(attacker.inventory, max_slots=0))
    
    # Modify resolve_attack to include an item for this test
    res = CombatResolutionSystem.resolve_attack(base_state.entities[1], base_state.entities[2], base_state)
    assert res.outcome_kind == "KILL"
    
    # Manually add an item to the intent to trigger capacity failure
    intent = res.resource_transfers[0]
    intent = replace(intent, items_add=[ItemStack("IRON_ORE", 1)])
    
    # Now verify ResourceTransactionResolver behavior
    from src.core.conservation import ResourceTransactionResolver
    tx_res = ResourceTransactionResolver.resolve(base_state, base_state.entities[1], intent)
    
    assert tx_res.accepted
    assert tx_res.reward_update.xp_gain > 0
    assert tx_res.inventory_update is None # Both items AND gold dropped because inv is full
    assert tx_res.reason == "INVENTORY_FULL_GOLD_ITEMS_DROPPED"
    
    assert tx_res.accepted
    assert tx_res.reward_update.xp_gain > 0
    assert tx_res.inventory_update is None # Items/gold dropped
    assert tx_res.reason == "INVENTORY_FULL_GOLD_ITEMS_DROPPED"

def test_no_double_kill_rewards(base_state):
    # we can verify that resolve_attack only returns rewards if the target WAS alive.
    defender = base_state.entities[2]
    base_state.entities[2] = replace(defender, combat=replace(defender.combat, hp=0, alive=False))
    
    res = CombatResolutionSystem.resolve_attack(base_state.entities[1], base_state.entities[2], base_state)
    assert res.outcome_kind == "REJECTED"
    assert res.failure_reason == "TARGET_INCAPACITATED"
    assert len(res.resource_transfers) == 0
