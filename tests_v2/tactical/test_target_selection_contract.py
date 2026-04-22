import pytest
from src_v2.core.state import EntityState, IdentityComponent, CombatComponent, AuthoritativeState
from src_v2.engine.tactical import TacticalDecisionSystem

def create_mock_entity(eid, faction, hp=100, pos=(0, 0)):
    return EntityState(
        id=eid,
        kind="hero",
        position=pos,
        identity=IdentityComponent(faction=faction),
        combat=CombatComponent(hp=hp, max_hp=100, alive=(hp > 0))
    )

def test_target_selection_priority():
    # Attacker at (0,0)
    attacker = create_mock_entity(1, 1, pos=(0, 0))
    
    # Candidate A: HP 50, Dist 2 (0,2)
    cand_a = create_mock_entity(10, 2, hp=50, pos=(0, 2))
    # Candidate B: HP 50, Dist 1 (0,1)
    cand_b = create_mock_entity(11, 2, hp=50, pos=(0, 1))
    # Candidate C: HP 20, Dist 5 (0,5)
    cand_c = create_mock_entity(12, 2, hp=20, pos=(0, 5))
    
    candidates = [cand_a, cand_b, cand_c]
    
    # Priority 1: Lowest HP => Candidate C (20 HP)
    best = TacticalDecisionSystem.select_best_target(attacker, candidates)
    assert best.id == 12
    
    # Priority 2: Closest if HP is same => Candidate B (Dist 1) vs A (Dist 2)
    candidates = [cand_a, cand_b]
    best = TacticalDecisionSystem.select_best_target(attacker, candidates)
    assert best.id == 11
    
    # Priority 3: Lowest ID if HP and Dist are same
    cand_d = create_mock_entity(13, 2, hp=50, pos=(0, 1)) # Same HP and Dist as B
    candidates = [cand_b, cand_d]
    best = TacticalDecisionSystem.select_best_target(attacker, candidates)
    assert best.id == 11 # 11 < 13
