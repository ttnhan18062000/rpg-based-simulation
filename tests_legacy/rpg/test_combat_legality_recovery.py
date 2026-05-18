import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, CombatComponent, IdentityComponent
from src_legacy.engine.domain_logic import SimulationDomainLogic
from src_legacy.engine.legality import LegalityServiceV2
from src_legacy.core.enums import Faction, EntityRole

def test_melee_adjacency_enforcement():
    """
    Law: Melee attacks (range 1) must be adjacent.
    """
    # Attacker at (0,0), range 1
    attacker = EntityState(
        id=1, kind="HERO", position=(0,0),
        combat=CombatComponent(hp=100, atk=10, range=1, alive=True),
        identity=IdentityComponent(faction=Faction.HERO_GUILD)
    )
    # Target at (2,0), range 2 (Not adjacent)
    target = EntityState(
        id=2, kind="MONSTER", position=(2,0),
        combat=CombatComponent(hp=10, atk=5, alive=True),
        identity=IdentityComponent(faction=Faction.MONSTER_HORDE)
    )
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})
    
    # 1. Verify LegalityService directly
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert not legal
    assert reason == "OUT_OF_RANGE"
    
    # 2. Verify SimulationDomainLogic enforcement
    # If the logic is hardened, it should return a fallback update (just readiness cost) or error
    updates = SimulationDomainLogic.execute_action(attacker, {"action": "ATTACK", "target_id": 2}, current_tick=1, context=state)
    
    # Current behavior (Buggy): It proceeds with the attack.
    # Expected behavior: It should reject or just consume readiness without damage.
    if 2 in updates:
        assert updates[2].combat is None or updates[2].combat.damage_taken == 0

def test_ranged_los_enforcement():
    """
    Law: Ranged attacks require clear Line of Sight.
    """
    # Attacker at (0,0), range 5
    attacker = EntityState(
        id=1, kind="HERO", position=(0,0),
        combat=CombatComponent(hp=100, atk=10, range=5, alive=True),
        identity=IdentityComponent(faction=Faction.HERO_GUILD)
    )
    # Target at (4,0), range 4
    target = EntityState(
        id=2, kind="MONSTER", position=(4,0),
        combat=CombatComponent(hp=10, atk=5, alive=True),
        identity=IdentityComponent(faction=Faction.MONSTER_HORDE)
    )
    
    # Wall at (2,0)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target}, terrain={(2,0): "WALL"})
    
    # 1. Verify LoS
    assert not LegalityServiceV2.has_line_of_sight(attacker.position, target.position, state)
    
    # 2. Verify LegalityService
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert not legal
    assert reason == "LOS_OBSTRUCTED"
    
    # 3. Verify Domain Logic enforcement
    updates = SimulationDomainLogic.execute_action(attacker, {"action": "ATTACK", "target_id": 2}, current_tick=1, context=state)
    if 2 in updates:
        assert updates[2].combat is None or updates[2].combat.damage_taken == 0

def test_aoe_splash_los_and_faction():
    """
    Law: AoE splash damage respects Line of Sight and (optionally) Faction logic.
    """
    from src_legacy.core.updates import StateUpdate, EntityUpdate, CombatUpdate, CombatIntent
    from src_legacy.engine.apply import ApplyPath
    
    # Attacker at (0,0)
    attacker = EntityState(
        id=1, kind="HERO", position=(0,0),
        combat=CombatComponent(hp=100, atk=10, range=10, alive=True),
        identity=IdentityComponent(faction=Faction.HERO_GUILD)
    )
    # Target at (2,0) (Direct hit)
    target = EntityState(
        id=2, kind="MONSTER", position=(2,0),
        combat=CombatComponent(hp=100, atk=5, alive=True),
        identity=IdentityComponent(faction=Faction.MONSTER_HORDE)
    )
    # Ally at (3,0) (In splash radius 1, but same faction)
    ally = EntityState(
        id=3, kind="HERO", position=(3,0),
        combat=CombatComponent(hp=100, atk=10, alive=True),
        identity=IdentityComponent(faction=Faction.HERO_GUILD)
    )
    # Monster behind Wall at (1,0)? No, let's put wall between 2 and 4.
    # Splash center is (2,0). Target 4 is at (2,1). Wall at (2, 0.5)
    monster_hidden = EntityState(
        id=4, kind="MONSTER", position=(2,2),
        combat=CombatComponent(hp=100, atk=5, alive=True),
        identity=IdentityComponent(faction=Faction.MONSTER_HORDE)
    )
    
    state = AuthoritativeState(
        tick=1, seed=42, 
        entities={1: attacker, 2: target, 3: ally, 4: monster_hidden},
        terrain={(2,1): "WALL"} # Wall between splash center (2,0) and target (2,2)
    )
    
    # Simulate AoE Attack Update
    # Attacker hits Target 2 with splash radius 2
    intent = CombatIntent(attacker_id=1, damage=10, splash_radius=2, splash_damage=5)
    upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, readiness_delta=-100),
        2: EntityUpdate(entity_id=2, combat=CombatUpdate(damage_taken=10, hp_delta=-10, simultaneous_intents=[intent]))
    })
    
    new_state = ApplyPath.apply_generation(state, upd)
    
    # 1. Target 2 should take direct damage (10)
    assert new_state.entities[2].combat.hp == 90
    
    # 2. Target 4 should NOT take splash damage (Blocked by WALL at 2,1)
    # Current behavior (Buggy): It probably takes damage because ApplyPath doesn't check LoS.
    assert new_state.entities[4].combat.hp == 100
    
    # 3. Ally 3 might take damage depending on Faction Safety law. 
    # If "Fireball hits everyone", then 3 takes damage.
    # If "Player Skills are safe", then 3 is 100 HP.
    # Let's assume Faction Safety is NOT enforced yet for "Hard AoE".
    # assert new_state.entities[3].combat.hp < 100
