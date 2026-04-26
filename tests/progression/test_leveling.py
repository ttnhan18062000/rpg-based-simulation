import pytest
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent
from src.core.updates import StateUpdate, EntityUpdate, IdentityUpdate, RewardUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.core.enums import EntityRole

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
    
    # 3. Refine & Apply
    refined = AuthoritativeApplyPipeline.refine(state, state_upd)
    next_state = ApplyPath.apply_generation(state, refined)
    new_ent = next_state.entities[99]
    
    # Level 1 -> 2 (uses 100 XP, 50 remains)
    assert new_ent.identity.evolution_level == 2
    assert new_ent.identity.evolution_points == 50
    
    # Stats grow by aptitude (Vit=20, Str=5, End=2)
    # Default aptitude is 1.0 in V2
    assert new_ent.combat.max_hp == 120
    assert new_ent.combat.atk == 15
    assert new_ent.combat.def_stat == 7 # 5 + 2
    
    # Healing Surge check: restoration is capped at new max_hp
    assert new_ent.combat.hp == 120

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
    
    # 3. Refine & Apply
    refined = AuthoritativeApplyPipeline.refine(state, state_upd)
    next_state = ApplyPath.apply_generation(state, refined)
    new_ent = next_state.entities[99]
    
    assert new_ent.identity.evolution_level == 3
    assert new_ent.identity.evolution_points == (500 - 100 - 282) # 118
    
    # L2 max_hp: 100 + 20 = 120
    # L3 max_hp: 120 + 20 = 140
    assert new_ent.combat.max_hp == 140
    # L2 atk: 10 + 5 = 15
    # L3 atk: 15 + 5 = 20
    assert new_ent.combat.atk == 20
