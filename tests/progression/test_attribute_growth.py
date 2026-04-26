import pytest
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, AttributeComponent, AptitudeComponent
from src.core.updates import StateUpdate, EntityUpdate, RewardUpdate
from src.engine.apply import ApplyPath
from src.actions.attributes import AllocateAttributeAction
from src.core.enums import EntityRole

@pytest.mark.v2_contract
def test_hero_ap_grant_on_level_up():
    # 1. Setup: Level 1 Hero with 0 XP. 
    identity = IdentityComponent(role=EntityRole.HERO, evolution_level=1, evolution_points=0, unspent_ap=0)
    combat = CombatComponent(hp=100, max_hp=100, atk=10, def_stat=5)
    attributes = AttributeComponent(strength=5, vitality=5)
    entity = EntityState(id=1, kind="hero", position=(0, 0), identity=identity, combat=combat, attributes=attributes)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # 2. Grant 100 XP (Level 1 -> 2)
    r_upd = RewardUpdate(xp_gain=100)
    ent_upd = EntityUpdate(entity_id=1, reward=r_upd)
    state_upd = StateUpdate(entity_updates={1: ent_upd})
    
    # 3. Apply
    next_state = ApplyPath.apply_generation(state, state_upd)
    new_ent = next_state.entities[1]
    
    assert new_ent.identity.evolution_level == 2
    assert new_ent.identity.unspent_ap == 5 # Granted 5 AP
    
    # 4. Hybrid check: Hero combat stats should NOT have scaled by 1.1x
    # (Except for HP healing surge logic)
    assert new_ent.combat.max_hp == 100
    assert new_ent.combat.atk == 10

@pytest.mark.v2_contract
def test_monster_no_ap_auto_scale():
    # 1. Setup: Level 1 Monster
    identity = IdentityComponent(role=EntityRole.MONSTER, evolution_level=1, evolution_points=0)
    combat = CombatComponent(hp=100, max_hp=100, atk=10, def_stat=10)
    entity = EntityState(id=2, kind="monster", position=(0, 0), identity=identity, combat=combat)
    state = AuthoritativeState(tick=1, seed=42, entities={2: entity})
    
    # 2. Grant 100 XP
    r_upd = RewardUpdate(xp_gain=100)
    ent_upd = EntityUpdate(entity_id=2, reward=r_upd)
    state_upd = StateUpdate(entity_updates={2: ent_upd})
    
    # 3. Apply
    next_state = ApplyPath.apply_generation(state, state_upd)
    new_ent = next_state.entities[2]
    
    assert new_ent.identity.evolution_level == 2
    assert new_ent.identity.unspent_ap == 0 # No AP for monsters
    
    # 4. Auto-scale check: Monster stats SHOULD scale by 1.1x
    assert new_ent.combat.max_hp == 110
    assert new_ent.combat.atk == 11

@pytest.mark.v2_contract
def test_attribute_allocation_and_recalc():
    # 1. Setup: Level 2 Hero with 5 AP
    identity = IdentityComponent(role=EntityRole.HERO, evolution_level=2, unspent_ap=5)
    # base stats: hp=100, atk=10, def=5
    # recalc with str=5, vit=5, end=5:
    # max_hp = 100 + 5*2 + 5*0.5 = 112
    # atk = 10 + 5*0.5 = 12
    # def = 5 + 5*0.3 = 6
    attributes = AttributeComponent(strength=5, vitality=5, endurance=5)
    combat = CombatComponent(hp=112, max_hp=112, atk=12, def_stat=6)
    entity = EntityState(id=1, kind="hero", position=(0, 0), identity=identity, combat=combat, attributes=attributes)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # 2. Action: Allocate 1 point to Strength
    action = AllocateAttributeAction(attribute_name="strength")
    ent_upd = action.execute(entity, state)
    state_upd = StateUpdate(entity_updates={1: ent_upd})
    
    # 3. Apply
    next_state = ApplyPath.apply_generation(state, state_upd)
    new_ent = next_state.entities[1]
    
    # 4. Verify
    assert new_ent.identity.unspent_ap == 4
    assert new_ent.attributes.strength == 6
    # atk should increase: 10 + 6*0.5 = 13
    assert new_ent.combat.atk == 13

@pytest.mark.v2_contract
def test_aptitude_multiplier_PROG_015():
    # 1. Setup: Hero with str_apt = 2.0
    aptitude = AptitudeComponent(str_apt=2.0)
    identity = IdentityComponent(role=EntityRole.HERO, unspent_ap=1)
    attributes = AttributeComponent(strength=5)
    entity = EntityState(id=1, kind="hero", position=(0, 0), identity=identity, attributes=attributes, aptitude=aptitude)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # 2. Action: Allocate 1 point to Strength
    action = AllocateAttributeAction(attribute_name="strength")
    ent_upd = action.execute(entity, state)
    state_upd = StateUpdate(entity_updates={1: ent_upd})
    
    # 3. Apply
    next_state = ApplyPath.apply_generation(state, state_upd)
    new_ent = next_state.entities[1]
    
    # 4. Verify: strength increased by 2 (1 * 2.0)
    assert new_ent.attributes.strength == 7

@pytest.mark.v2_contract
def test_attribute_cap_PROG_046():
    # 1. Setup: Attribute at 99
    identity = IdentityComponent(role=EntityRole.HERO, unspent_ap=10)
    attributes = AttributeComponent(strength=99)
    entity = EntityState(id=1, kind="hero", position=(0, 0), identity=identity, attributes=attributes)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # 2. Action: Allocate (would go to 100)
    action = AllocateAttributeAction(attribute_name="strength")
    ent_upd = action.execute(entity, state)
    state_upd = StateUpdate(entity_updates={1: ent_upd})
    
    next_state = ApplyPath.apply_generation(state, state_upd)
    new_ent = next_state.entities[1]
    assert new_ent.attributes.strength == 100
    
    # 3. Action: Allocate again (should stay at 100)
    action2 = AllocateAttributeAction(attribute_name="strength")
    ent_upd2 = action2.execute(new_ent, next_state)
    state_upd2 = StateUpdate(entity_updates={1: ent_upd2})
    
    final_state = ApplyPath.apply_generation(next_state, state_upd2)
    final_ent = final_state.entities[1]
    assert final_ent.attributes.strength == 100
    # AP is still consumed? 
    # Current implementation consumes AP but apply path caps the value.
    # We should probably check if it was capped in AllocateAttributeAction too,
    # but for now this verifies the ApplyPath safety.
    assert final_ent.identity.unspent_ap == 8
