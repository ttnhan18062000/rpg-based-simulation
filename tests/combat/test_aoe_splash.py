import pytest
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate, CombatIntent
from src.engine.apply import ApplyPath
from src.engine.combat import CombatResolutionSystem
from src.engine.legality import LegalityServiceV2
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction

def create_mock_entity(eid, pos, faction=Faction.HERO_GUILD):
    return (V2EntityBuilder(eid)
        .kind("HERO")
        .position(pos)
        .readiness(100.0)
        .with_identity(faction=faction)
        .with_attributes(strength=0, vitality=0)
        .with_combat(hp=100, max_hp=100, atk=20, def_stat=5, range=10)
        .build())

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
    success, reason = LegalityServiceV2.verify_aoe_legality(attacker, target1.navigation.position, state)
    assert success is True
    
    # 3. Resolve AoE Attack
    # radius 2, 20 atk -> primary takes damage (atk - def)
    # def=5, atk=20 -> dmg = 20 * (20 / (20 + 5*2 + 1)) = 20 * (20/31) = 12
    aoe_updates = CombatResolutionSystem.resolve_aoe_attack(attacker, target1.navigation.position, radius=2, state=state, defender=target1)
    combat_upd = aoe_updates[2]
    
    # 4. Create StateUpdate
    update = StateUpdate(
        entity_updates={
            eid: EntityUpdate(entity_id=eid, combat=upd)
            for eid, upd in aoe_updates.items()
        }
    )
    
    # 5. Apply Generation
    new_state = ApplyPath.apply_generation(state, update)
    
    # 6. Verify Damage
    # Primary target (2) should take 12 damage
    assert new_state.entities[2].combat.hp == 88 # 100 - 12
    
    # Note: ApplyPath.apply_generation handles splash damage by iterating over simultaneous_intents
    # and applying them to other entities in range.
    # In V2, this is handled by the AuthoritativeApplyPipeline for full updates,
    # but ApplyPath.apply_generation is the lower-level tool.
    
    # Verify splash damage (Splash damage = 50% of atk = 10)
    # target 3 (16,10) is dist 1 from target 1 (15,10) -> in radius 2
    # target 4 (14,10) is dist 1 from target 1 (15,10) -> in radius 2
    assert new_state.entities[3].combat.hp == 90 # 100 - 10
    assert new_state.entities[4].combat.hp == 90 # 100 - 10
    assert new_state.entities[5].combat.hp == 100 # No damage
    
    print("AoE Splash Verification Success: Nearby entities took partial damage.")

if __name__ == "__main__":
    test_aoe_splash_damage()
