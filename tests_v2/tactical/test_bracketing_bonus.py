import pytest
from dataclasses import replace
from src_v2.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, TaskComponent
from src_v2.engine.pipeline import AuthoritativeApplyPipeline
from src_v2.core.updates import StateUpdate, EntityUpdate, TaskUpdate

def create_mock_entity(eid, faction, pos=(10, 10), hp=100):
    return EntityState(
        id=eid,
        kind="hero",
        position=pos,
        identity=IdentityComponent(faction=faction),
        combat=CombatComponent(hp=hp, max_hp=100, atk=10, def_stat=0, alive=True),
        task=TaskComponent()
    )

def test_bracketing_bonus_application():
    # Target at (10,10)
    target = create_mock_entity(1, 2, pos=(10, 10))
    # Attacker A at (11,10)
    attacker_a = create_mock_entity(2, 1, pos=(11, 10))
    # Attacker B at (9,10) (Opposite side of A)
    attacker_b = create_mock_entity(3, 1, pos=(9, 10))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: target, 2: attacker_a, 3: attacker_b})
    
    # Attacker A proposes attack
    raw_update = StateUpdate(entity_updates={
        2: EntityUpdate(entity_id=2, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 1}))
    })
    
    # Resolve
    update = AuthoritativeApplyPipeline._route_combat_intent(state, raw_update)
    
    # Base damage ~9. Bracketing bonus is +3. Total ~12.
    combat_upd = update.entity_updates[1].combat
    assert combat_upd.damage_taken > 11
