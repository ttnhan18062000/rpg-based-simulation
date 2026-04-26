# tests/combat/test_aoe_splash.py
import pytest
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, TaskComponent
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate, CombatIntent
from src.engine.apply import ApplyPath
from src.engine.combat import CombatResolutionSystem
from src.engine.legality import LegalityServiceV2
from src.core.enums import Faction

def create_mock_entity(eid, pos, faction=Faction.HERO_GUILD):
    return EntityState(
        id=eid,
        kind="HERO",
        position=pos,
        identity=IdentityComponent(faction=faction),
        combat=CombatComponent(hp=100, atk=20, def_stat=5, range=5),
        active=True
    )

@pytest.mark.v2_contract
@pytest.mark.differential
def test_aoe_splash_damage():
    """
    Verifies that an AoE attack deals splash damage to nearby entities.
    """
    # 1. Setup State: Attacker and multiple targets
    attacker = create_mock_entity(1, (10, 10))
    target1 = create_mock_entity(2, (15, 10), faction=Faction.MONSTER_HORDE) # Primary target
    target2 = create_mock_entity(3, (16, 10), faction=Faction.MONSTER_HORDE) # Splash target (dist 1 from primary)
    target3 = create_mock_entity(4, (14, 10), faction=Faction.MONSTER_HORDE) # Splash target (dist 1 from primary)
    target4 = create_mock_entity(5, (20, 20), faction=Faction.MONSTER_HORDE) # Too far
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={e.id: e for e in [attacker, target1, target2, target3, target4]}
    )
    
    # 2. Verify Legality
    success, reason = LegalityServiceV2.verify_aoe_legality(attacker, target1.position, 10, state)
    assert success is True
    
    # 3. Resolve AoE Attack
    # radius 2, 20 atk -> primary takes damage (atk - def)
    # def=5, atk=20 -> dmg = 20 * (20 / (20 + 5*2 + 1)) = 20 * (20/31) = 12
    combat_upd = CombatResolutionSystem.resolve_aoe_attack(attacker, target1.position, radius=2, state=state, defender=target1)
    
    # 4. Create StateUpdate
    update = StateUpdate(
        entity_updates={
            2: EntityUpdate(entity_id=2, combat=combat_upd)
        }
    )
    
    # 5. Apply Generation
    new_state = ApplyPath.apply_generation(state, update)
    
    # 6. Verify Damage
    # Primary target (2) should take 12 damage
    assert new_state.entities[2].combat.hp == 88 # 100 - 12
    
    # Let's check target 3 and 4 (splash)
    # They should take 10 damage each from extra_damage.
    assert new_state.entities[3].combat.hp == 90 # 100 - 10
    assert new_state.entities[4].combat.hp == 90 # 100 - 10
    assert new_state.entities[5].combat.hp == 100 # No damage
    
    print("AoE Splash Verification Success: Nearby entities took partial damage.")

if __name__ == "__main__":
    test_aoe_splash_damage()
