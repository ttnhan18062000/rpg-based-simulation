import pytest
from src_v2.engine.tactical import TacticalDecisionSystem
from src_v2.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent

def create_mock_entity(eid, faction, pos=(10, 10), hp=100):
    return EntityState(
        id=eid,
        kind="hero",
        position=pos,
        identity=IdentityComponent(faction=faction),
        combat=CombatComponent(hp=hp, max_hp=100, alive=True)
    )

def test_target_selection_parity():
    """
    Law: Target selection follows deterministic priority.
    V2: Lowest HP > Closest > Lowest ID.
    Legacy: Nearest (simple).
    Divergence: V2 is more deterministic/sophisticated for AOA.
    """
    # Target 1: HP 50, Dist 5
    # Target 2: HP 100, Dist 2
    # V2 should pick Target 1 (Lower HP). Legacy would pick Target 2 (Nearest).
    
    attacker = create_mock_entity(1, 1, pos=(0, 0))
    t1 = create_mock_entity(2, 2, pos=(5, 0), hp=50)
    t2 = create_mock_entity(3, 2, pos=(2, 0), hp=100)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: t1, 3: t2})
    
    decision = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert decision.task.payload_set["target_id"] == 2 # Lowest HP wins in V2
    
def test_retreat_threshold_divergence():
    """
    Divergence: V2 retreat at 20%, V1 retreat at 25%.
    """
    attacker = create_mock_entity(1, 1, pos=(0, 0), hp=21) # Just above V2 threshold
    hostile = create_mock_entity(2, 2, pos=(1, 1)) # Need a hostile to trigger intent logic
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: hostile})
    
    decision = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    # At 21 HP (21%), V2 stays in CLOSE mode. V1 would RETREAT.
    assert decision.task.payload_set.get("action") != "RETREAT"
    assert decision.task.payload_set.get("reason") != "RETREAT"
