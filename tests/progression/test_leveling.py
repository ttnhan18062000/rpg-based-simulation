"""
Leveling and evolution tests.
- RPG-0061: evolution_level_determinism
- RPG-0062: evolution_point_accumulation
- RPG-0063: evolution_threshold_scaling
- RPG-0065: stat_recalculation_parity
- RPG-0067: class_based_attribute_bias
"""
import pytest
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent
from src.core.updates import StateUpdate, EntityUpdate, IdentityUpdate, RewardUpdate
from src.engine.evolution import EvolutionSystem
from src.engine.apply import ApplyPath
from src.core.enums import EntityRole

@pytest.mark.v2_contract
def test_automatic_level_up():
    # 1. Setup: Level 1 entity with 0 XP. 
    identity = IdentityComponent(role=EntityRole.MONSTER, evolution_level=1, evolution_points=0)
    combat = CombatComponent(hp=100, max_hp=100, atk=10, def_stat=5)
    entity = EntityState(id=99, kind="hero", position=(0, 0), identity=identity, combat=combat)
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity})
    
    # 2. Grant 150 XP (via RewardUpdate)
    r_upd = RewardUpdate(xp_gain=150)
    ent_upd = EntityUpdate(entity_id=99, reward=r_upd)
    state_upd = StateUpdate(entity_updates={99: ent_upd})
    
    # 3. Call EvolutionSystem directly (bypassing Pipeline sanitizer)
    refined = EvolutionSystem.evaluate(state, state_upd)
    next_state = ApplyPath.apply_generation(state, refined)
    new_ent = next_state.entities[99]
    
    # Level 1 -> 2 (uses 100 XP, 50 remains)
    assert new_ent.identity.evolution_level == 2
    assert new_ent.identity.evolution_points == 50
    
    # V2 Law: Stats are derived from attributes (defaults to all 5).
    # L2 (+5 Vit, +5 Str, +2 End): max_hp = 100 + (10*2) + floor(7*0.5) = 123
    assert new_ent.combat.max_hp == 123
    assert new_ent.combat.atk == 15
    assert new_ent.combat.def_stat == 8
    
    # RPG-0064: HP is refilled to NEW max_hp on level up
    assert new_ent.combat.hp == 123

@pytest.mark.v2_contract
def test_multi_level_up():
    # 1. Setup
    identity = IdentityComponent(role=EntityRole.MONSTER, evolution_level=1, evolution_points=0)
    combat = CombatComponent(hp=100, max_hp=100, atk=10, def_stat=10)
    entity = EntityState(id=99, kind="hero", position=(0, 0), identity=identity, combat=combat)
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity})
    
    # 2. Grant 500 XP
    r_upd = RewardUpdate(xp_gain=500)
    ent_upd = EntityUpdate(entity_id=99, reward=r_upd)
    state_upd = StateUpdate(entity_updates={99: ent_upd})
    
    # 3. Call EvolutionSystem directly
    refined = EvolutionSystem.evaluate(state, state_upd)
    next_state = ApplyPath.apply_generation(state, refined)
    new_ent = next_state.entities[99]
    
    assert new_ent.identity.evolution_level == 3
    assert new_ent.identity.evolution_points == 118
    
    # L3 (+10 Vit, +4 End total): max_hp = 100 + (15*2) + floor(9*0.5) = 134
    assert new_ent.combat.max_hp == 134
    assert new_ent.combat.atk == 17
