"""
Attribute growth and AP allocation tests.
- RPG-0066: attribute_growth_bandwidth
"""
import pytest
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, AttributeComponent, AptitudeComponent
from src.core.updates import StateUpdate, EntityUpdate, RewardUpdate
from src.engine.evolution import EvolutionSystem
from src.engine.apply import ApplyPath
from src.actions.attributes import AllocateAttributeAction
from src.core.enums import EntityRole, Faction
from src.core.builder import V2EntityBuilder

@pytest.mark.v2_contract
def test_hero_ap_grant_on_level_up():
    # 1. Setup: Level 1 Hero with 0 XP. 
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .at((0, 0))
              .with_identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD, evolution_level=1)
              .with_combat(hp=100, max_hp=100, atk=10, def_stat=5)
              .with_attributes(strength=5, vitality=5)
              .build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # 2. Grant 100 XP (Level 1 -> 2)
    r_upd = RewardUpdate(xp_gain=100)
    ent_upd = EntityUpdate(entity_id=1, reward=r_upd)
    state_upd = StateUpdate(entity_updates={1: ent_upd})
    
    # 3. Call EvolutionSystem directly (bypassing Pipeline sanitizer)
    refined = EvolutionSystem.evaluate(state, state_upd)
    next_state = ApplyPath.apply_generation(state, refined)
    new_ent = next_state.entities[1]
    
    assert new_ent.identity.evolution_level == 2
    assert new_ent.identity.unspent_ap == 5 # Granted 5 AP
    
    # Hero stats are recalculated on level up
    # recalc: max_hp = 100 + 5*2 + floor(5*0.5) = 112
    # atk = 10 + floor(5*0.5) = 12
    assert new_ent.combat.max_hp == 112
    assert new_ent.combat.atk == 12

@pytest.mark.v2_contract
def test_monster_no_ap_auto_scale():
    # 1. Setup: Level 1 Monster
    entity = (V2EntityBuilder(2)
              .kind("monster")
              .at((0, 0))
              .with_identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, evolution_level=1)
              .with_combat(hp=100, max_hp=100, atk=10, def_stat=10)
              .build())
    state = AuthoritativeState(tick=1, seed=42, entities={2: entity})
    
    # 2. Grant 100 XP
    r_upd = RewardUpdate(xp_gain=100)
    ent_upd = EntityUpdate(entity_id=2, reward=r_upd)
    state_upd = StateUpdate(entity_updates={2: ent_upd})
    
    # 3. Call EvolutionSystem directly
    refined = EvolutionSystem.evaluate(state, state_upd)
    next_state = ApplyPath.apply_generation(state, refined)
    new_ent = next_state.entities[2]
    
    assert new_ent.identity.evolution_level == 2
    assert new_ent.identity.unspent_ap == 0
    
    # L2 (+5 Vit, +5 Str, +2 End): 100 + (10*2) + floor(7*0.5) = 123
    assert new_ent.combat.max_hp == 123
    assert new_ent.combat.atk == 15
    assert new_ent.combat.def_stat == 8 # (5 base + floor(10*0.3))

@pytest.mark.v2_contract
def test_attribute_allocation_and_recalc():
    # 1. Setup: Level 2 Hero with 5 AP
    # Note: V2EntityBuilder doesn't have unspent_ap setter, we use replace
    from dataclasses import replace
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .at((0, 0))
              .with_identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD, evolution_level=2)
              .with_attributes(strength=5, vitality=5, endurance=5)
              .build())
    entity = replace(entity, identity=replace(entity.identity, unspent_ap=5))
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
    # atk should increase: 10 + floor(6*0.5) = 13
    assert new_ent.combat.atk == 13

@pytest.mark.v2_contract
def test_aptitude_multiplier_PROG_015():
    from dataclasses import replace
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .at((0, 0))
              .with_aptitude(str_apt=2.0)
              .with_attributes(strength=5)
              .build())
    entity = replace(entity, identity=replace(entity.identity, unspent_ap=1))
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    action = AllocateAttributeAction(attribute_name="strength")
    ent_upd = action.execute(entity, state)
    state_upd = StateUpdate(entity_updates={1: ent_upd})
    
    next_state = ApplyPath.apply_generation(state, state_upd)
    new_ent = next_state.entities[1]
    assert new_ent.attributes.strength == 7

@pytest.mark.v2_contract
def test_attribute_cap_PROG_046():
    from dataclasses import replace
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .at((0, 0))
              .with_attributes(strength=99)
              .build())
    entity = replace(entity, identity=replace(entity.identity, unspent_ap=10))
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    action = AllocateAttributeAction(attribute_name="strength")
    ent_upd = action.execute(entity, state)
    state_upd = StateUpdate(entity_updates={1: ent_upd})
    
    next_state = ApplyPath.apply_generation(state, state_upd)
    new_ent = next_state.entities[1]
    assert new_ent.attributes.strength == 100
    
    action2 = AllocateAttributeAction(attribute_name="strength")
    ent_upd2 = action2.execute(new_ent, next_state)
    state_upd2 = StateUpdate(entity_updates={1: ent_upd2})
    
    final_state = ApplyPath.apply_generation(next_state, state_upd2)
    final_ent = final_state.entities[1]
    assert final_ent.attributes.strength == 100
    assert final_ent.identity.unspent_ap == 8
