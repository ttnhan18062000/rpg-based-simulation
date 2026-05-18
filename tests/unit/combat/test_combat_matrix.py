import pytest
from dataclasses import replace
from src.engine.combat import CombatResolutionSystem
from src.core.state import AuthoritativeState, EntityState, CombatComponent, BiologicalComponent, IdentityComponent, ItemStack
from src.core.enums import EntityRole, Faction, ReasonCode
from src.core.builder import V2EntityBuilder

@pytest.fixture
def base_state():
    attacker = (V2EntityBuilder(1)
                .kind("hero")
                .location(5.0, 5.0)
                .identity(faction=Faction.HERO_GUILD, role=EntityRole.HERO)
                .combat(readiness=100.0, atk=20, def_stat=10, hp=100, attack_range=1)
                .build())
                
    defender = (V2EntityBuilder(2)
                .kind("mob")
                .location(6.0, 5.0)
                .identity(faction=Faction.MONSTER_HORDE, role=EntityRole.MONSTER)
                .combat(readiness=100.0, atk=10, def_stat=5, hp=50, attack_range=1)
                .build())
                
    ally = (V2EntityBuilder(3)
            .kind("hero")
            .location(5.0, 6.0)
            .identity(faction=Faction.HERO_GUILD, role=EntityRole.HERO)
            .combat(readiness=100.0, atk=10, def_stat=5, hp=50, attack_range=1)
            .build())
    
    return AuthoritativeState(
        tick=1, seed=123, 
        entities={1: attacker, 2: defender, 3: ally},
        terrain={}
    )

def test_melee_range_violation(base_state):
    # Move defender 2 tiles away
    defender = base_state.entities[2]
    new_entities = dict(base_state.entities)
    new_entities[2] = replace(defender, navigation=replace(defender.navigation, position=(7.0, 5.0)))
    base_state = replace(base_state, entities=new_entities)
    
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
        base_state.entities[1], (6.0, 5.0), radius=2.0, state=base_state, defender=base_state.entities[2]
    )
    
    # Monster should be hit
    assert 2 in res_map
    assert res_map[2].outcome_kind != "REJECTED"
    
    # Ally should NOT be hit (friendly fire safety)
    assert 3 not in res_map

def test_atomic_rewards_on_kill(base_state):
    # Set monster HP very low
    defender = base_state.entities[2]
    new_entities = dict(base_state.entities)
    new_entities[2] = replace(defender, combat=replace(defender.combat, hp=1))
    base_state = replace(base_state, entities=new_entities)
    
    res = CombatResolutionSystem.resolve_attack(base_state.entities[1], base_state.entities[2], base_state)
    assert res.outcome_kind == "KILL"
    assert not res.alive_set
    
    # Should have multiple ResourceTransferIntents (split by group vs individual)
    assert len(res.resource_transfers) >= 1
    total_xp = sum(intent.xp_reward for intent in res.resource_transfers)
    total_gold = sum(intent.gold_delta for intent in res.resource_transfers)
    assert total_xp > 0
    assert total_gold > 0

def test_multi_attacker_kill_rewards(base_state):
    # Two attackers hit one monster
    attacker1 = base_state.entities[1]
    attacker2 = base_state.entities[3] # ally
    defender = base_state.entities[2]
    
    # Set monster HP low
    new_entities = dict(base_state.entities)
    new_entities[2] = replace(defender, combat=replace(defender.combat, hp=5))
    base_state = replace(base_state, entities=new_entities)
    
    res = CombatResolutionSystem.resolve_multi_attack([attacker1, attacker2], base_state.entities[2], base_state)
    assert res.outcome_kind == "KILL"
    assert not res.alive_set
    
    # Should have ResourceTransferIntent
    assert len(res.resource_transfers) >= 1
    total_xp = sum(intent.xp_reward for intent in res.resource_transfers)
    assert total_xp > 0

def test_xp_rejected_when_inventory_full(base_state):
    # Set monster HP low
    defender = base_state.entities[2]
    attacker = base_state.entities[1]
    
    new_entities = dict(base_state.entities)
    new_entities[2] = replace(defender, combat=replace(defender.combat, hp=1))
    new_entities[1] = replace(attacker, inventory=replace(attacker.inventory, max_slots=0))
    base_state = replace(base_state, entities=new_entities)
    
    # Resolve attack - should still be a KILL
    res = CombatResolutionSystem.resolve_attack(base_state.entities[1], base_state.entities[2], base_state)
    assert res.outcome_kind == "KILL"
    
    # Find an intent to inject an item into
    intent = res.resource_transfers[0]
    intent = replace(intent, items_add=[ItemStack("IRON_ORE", 1)])
    
    # Now verify ResourceTransactionResolver behavior - it should be atomic REJECTED
    from src.core.conservation import ResourceTransactionResolver
    tx_res = ResourceTransactionResolver.resolve(base_state, base_state.entities[1], intent)
    
    assert tx_res.accepted is False
    assert tx_res.reason == ReasonCode.INVENTORY_FULL

def test_no_double_kill_rewards(base_state):
    # we can verify that resolve_attack only returns rewards if the target WAS alive.
    defender = base_state.entities[2]
    new_entities = dict(base_state.entities)
    new_entities[2] = replace(defender, combat=replace(defender.combat, hp=0, alive=False))
    base_state = replace(base_state, entities=new_entities)
    
    res = CombatResolutionSystem.resolve_attack(base_state.entities[1], base_state.entities[2], base_state)
    assert res.outcome_kind == "REJECTED"
    assert res.failure_reason == "TARGET_INCAPACITATED"
    assert len(res.resource_transfers) == 0
