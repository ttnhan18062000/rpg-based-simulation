import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent
from src_legacy.engine.movement import MovementSystem
from src_legacy.engine.apply import ApplyPath
from src_legacy.core.updates import StateUpdate

@pytest.mark.v2_contract
def test_oa_triggered_on_disengagement_hardened():
    """
    Parity Test: LEG-RPG-099 / test_oa_triggered_on_disengagement
    Verify that moving while adjacent to a hostile entity triggers an Opportunity Attack
    with legacy-parity damage calculation.
    """
    # 1. Setup Initial State
    # Hero (ATK 10, DEF 5, HP 100) at (0,0)
    # Enemy (ATK 20, DEF 10, HP 100) at (1,0)
    hero = EntityState(
        id=1, kind="hero", position=(0.0, 0.0),
        identity=IdentityComponent(faction=1),
        combat=CombatComponent(hp=100, max_hp=100, atk=10, def_stat=5)
    )
    enemy = EntityState(
        id=2, kind="enemy", position=(1.0, 0.0),
        identity=IdentityComponent(faction=2),
        combat=CombatComponent(hp=100, max_hp=100, atk=20, def_stat=10)
    )
    
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: hero, 2: enemy}
    )
    
    # 2. Hero moves to (0,1)
    target_pos = (0.0, 1.0)
    
    # 3. Resolve the move
    # Attacker is Entity 2 (Enemy), Defender is Entity 1 (Hero)
    # Formula: atk_final = 20, def_final = 5
    # raw_damage = 20 * (20 / (20 + 5*2 + 1)) = 20 * (20 / 31) = 20 * 0.645 = 12.9 -> 12
    # damage = max(1, 12) = 12
    move_upds = MovementSystem.resolve_move(state, hero, target_pos)
    hero_update = move_upds[1]
    
    # 4. Verify OA trigger
    assert hero_update.combat is not None
    assert hero_update.combat.is_opportunity_attack is True
    assert hero_update.combat.attacker_id == 2
    assert hero_update.combat.damage_taken == 12
    
    # 5. Apply the update and verify HP reduction
    new_hero_state = ApplyPath._apply_entity_update(hero, hero_update)
    assert new_hero_state.combat.hp == 88 # 100 - 12
    assert "total_damage_taken" not in new_hero_state.properties

@pytest.mark.v2_contract
def test_no_oa_if_no_hostiles():
    """
    Verify that moving while NOT engaged does NOT trigger an OA.
    """
    hero = EntityState(
        id=1, kind="hero", position=(0.0, 0.0),
        identity=IdentityComponent(faction=1),
        combat=CombatComponent()
    )
    # Friend is adjacent but in same faction
    friend = EntityState(
        id=2, kind="hero", position=(1.0, 0.0),
        identity=IdentityComponent(faction=1),
        combat=CombatComponent()
    )
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: friend})
    move_upds = MovementSystem.resolve_move(state, hero, (0.0, 1.0))
    hero_update = move_upds[1]
    
    assert hero_update.combat is None
