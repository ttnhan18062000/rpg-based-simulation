import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, BuildingState, TaskComponent
from src.engine.legality import LegalityServiceV2
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate

def create_mock_entity(eid, faction, pos=(10, 10), hp=100):
    return EntityState(
        id=eid,
        kind="hero",
        position=pos,
        identity=IdentityComponent(faction=faction),
        combat=CombatComponent(hp=hp, max_hp=100, alive=True),
        readiness=100.0,
        task=TaskComponent()
    )

def test_terrain_movement_blockage():
    # Target at (10,11), WALL at (10,11)
    state = AuthoritativeState(tick=1, seed=42, terrain={(10, 11): "WALL"})
    
    # Verify occupancy at (10,11) is illegal
    is_legal, reason = LegalityServiceV2.verify_occupancy((10, 11), state)
    assert not is_legal
    assert reason == "PATH_NOT_FOUND"

def test_building_movement_blockage():
    # Target at (10,11), Building at (10,11)
    build = BuildingState(id=1, kind="shop", position=(10, 11))
    state = AuthoritativeState(tick=1, seed=42, buildings={1: build})
    
    is_legal, reason = LegalityServiceV2.verify_occupancy((10, 11), state)
    assert not is_legal
    assert reason == "BUILDING_OBSTRUCTION"

def test_combat_line_of_sight():
    attacker = create_mock_entity(1, 1, pos=(10, 10))
    attacker = replace(attacker, combat=replace(attacker.combat, range=2))
    target = create_mock_entity(2, 2, pos=(10, 12)) # 2 distance
    
    # 1. Clear LoS
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert is_legal
    
    # 2. Obstructed by WALL at (10,11)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target}, terrain={(10, 11): "WALL"})
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert not is_legal
    assert reason == "LOS_OBSTRUCTED"

def test_high_ground_bonus():
    from src.engine.pipeline import AuthoritativeApplyPipeline
    
    attacker = create_mock_entity(1, 1, pos=(10, 10))
    attacker = replace(attacker, combat=replace(attacker.combat, atk=10))
    target = create_mock_entity(2, 2, pos=(10, 11))
    target = replace(target, combat=replace(target.combat, def_stat=0)) # No defense for simple math
    
    # Attacker on HILL
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target}, terrain={(10, 10): "HILL"})
    
    # Propose ATTACK
    raw_update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 2}))
    })
    
    # Refine (Attack resolution)
    update = AuthoritativeApplyPipeline._route_combat_intent(state, raw_update)
    
    # Damage should be 10 (base) + 5 (HILL) = 15
    # Wait, damage formula is: atk * (atk / (atk + def*2 + 1))
    # If def=0, damage = 10 * (10 / 11) = ~9
    # With +5 bonus, it should be higher.
    
    combat_upd = update.entity_updates[2].combat
    assert combat_upd.damage_taken > 9 # Verified bonus added
