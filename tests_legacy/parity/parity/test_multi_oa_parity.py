# tests/parity/test_multi_oa_parity.py
import pytest
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent
from src.engine.movement import MovementSystem
from src.engine.legality import LegalityServiceV2
from src.core.enums import Faction

def create_mock_entity(eid, pos, faction=Faction.HERO_GUILD):
    return EntityState(
        id=eid,
        kind="HERO",
        position=pos,
        identity=IdentityComponent(faction=faction),
        combat=CombatComponent(hp=100, atk=10, def_stat=5, range=1),
        active=True
    )

@pytest.mark.v2_contract
@pytest.mark.differential
def test_multi_attacker_opportunity_attacks():
    """
    Verifies that a moving entity triggers OAs from ALL adjacent hostiles.
    """
    # 1. Setup State: Hero surrounded by 3 Monsters
    hero = create_mock_entity(1, (10, 10), faction=Faction.HERO_GUILD)
    m1 = create_mock_entity(2, (9, 10), faction=Faction.MONSTER_HORDE)
    m2 = create_mock_entity(3, (11, 10), faction=Faction.MONSTER_HORDE)
    m3 = create_mock_entity(4, (10, 9), faction=Faction.MONSTER_HORDE)
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={e.id: e for e in [hero, m1, m2, m3]}
    )
    
    # 2. Hero moves to (10, 11) - egresses from 3 hostiles
    # LegalityService should return [2, 3, 4]
    engaged = LegalityServiceV2.get_engaged_hostiles(hero, state)
    assert len(engaged) == 3
    assert engaged == [2, 3, 4] # Sorted
    
    # 3. Resolve move
    move_upds = MovementSystem.resolve_move(state, hero, (10, 11))
    update = move_upds[1]
    
    # 4. Verify CombatUpdate
    assert update.combat is not None
    assert update.combat.is_opportunity_attack is True
    assert len(update.combat.simultaneous_intents) == 3
    
    # Damage calculation:
    # atk=10, def=5
    # dmg = 10 * (10 / (10 + 5*2 + 1)) = 10 * (10/21) = 10 * 0.476 = 4
    # Total damage = 4 * 3 = 12
    assert update.combat.damage_taken == 12
    assert update.combat.hp_delta == -12
    
    print("Multi-OA Verification Success: Hero took damage from all 3 hostiles.")

if __name__ == "__main__":
    test_multi_attacker_opportunity_attacks()
