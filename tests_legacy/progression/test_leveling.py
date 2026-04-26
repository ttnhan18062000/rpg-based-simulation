import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent
from src_legacy.core.updates import StateUpdate, EntityUpdate, IdentityUpdate, RewardUpdate
from src_legacy.engine.apply import ApplyPath
from src_legacy.core.enums import EntityRole

@pytest.mark.v2_contract
def test_automatic_level_up():
    # 1. Setup: Level 1 entity with 0 XP. 
    # Level 1 requires 100 XP (100 * 1^1.5) to reach Level 2.
    identity = IdentityComponent(role=EntityRole.MONSTER, evolution_level=1, evolution_points=0)
    combat = CombatComponent(hp=100, max_hp=100, atk=10, def_stat=5)
    entity = EntityState(id=99, kind="hero", position=(0, 0), identity=identity, combat=combat)
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity})
    
    # 2. Grant 150 XP (via RewardUpdate)
    r_upd = RewardUpdate(xp_gain=150)
    ent_upd = EntityUpdate(entity_id=99, reward=r_upd)
    state_upd = StateUpdate(entity_updates={99: ent_upd})
    
    # 3. Apply
    next_state = ApplyPath.apply_generation(state, state_upd)
    new_ent = next_state.entities[99]
    
    # Level 1 -> 2 (uses 100 XP, 50 remains)
    assert new_ent.identity.evolution_level == 2
    assert new_ent.identity.evolution_points == 50
    
    # Stats grow by 10%
    assert new_ent.combat.max_hp == 110
    assert new_ent.combat.atk == 11
    assert new_ent.combat.def_stat == 5 # int(5 * 1.1) = 5
    
    # Healing Surge check: (100/100) + 0.2 = 1.2 -> capped at 1.0 -> 110 HP
    assert new_ent.combat.hp == 110

@pytest.mark.v2_contract
def test_multi_level_up():
    # 1. Setup
    identity = IdentityComponent(role=EntityRole.MONSTER, evolution_level=1, evolution_points=0)
    combat = CombatComponent(hp=100, max_hp=100, atk=10, def_stat=10)
    entity = EntityState(id=99, kind="hero", position=(0, 0), identity=identity, combat=combat)
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity})
    
    # 2. Grant 500 XP
    # L1->L2: 100 XP
    # L2->L3: 100 * 2^1.5 = 282 XP
    # Total needed for L3: 382
    r_upd = RewardUpdate(xp_gain=500)
    ent_upd = EntityUpdate(entity_id=99, reward=r_upd)
    state_upd = StateUpdate(entity_updates={99: ent_upd})
    
    # 3. Apply
    next_state = ApplyPath.apply_generation(state, state_upd)
    new_ent = next_state.entities[99]
    
    assert new_ent.identity.evolution_level == 3
    assert new_ent.identity.evolution_points == (500 - 100 - 282) # 118
    
    # L2 max_hp: 100 * 1.1 = 110
    # L3 max_hp: 110 * 1.1 = 121
    assert new_ent.combat.max_hp == 121
    # L2 atk: 10 * 1.1 = 11
    # L3 atk: 11 * 1.1 = 12
    assert new_ent.combat.atk == 12
