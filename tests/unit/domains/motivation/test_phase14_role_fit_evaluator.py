import pytest
from src.domains.motivation.evaluator import RoleFitEvaluator
from src.core.cognition import RoleFitPreference

def test_role_fit_evaluator():
    role_fit = RoleFitPreference(
        weapon_tags={"melee": 0.8, "staff": -0.5},
        armor_tags={"heavy": 0.6},
        skill_tags={"slash": 0.7},
        party_role_tags={"vanguard": 0.9},
        quest_tags={"hunt": 0.5}
    )
    
    # Weapons
    assert RoleFitEvaluator.evaluate_weapon(role_fit, ["melee", "sword"]) == 0.8
    assert RoleFitEvaluator.evaluate_weapon(role_fit, ["staff", "ranged"]) == -0.5
    assert RoleFitEvaluator.evaluate_weapon(role_fit, ["unrelated"]) == 0.0
    
    # Armor
    assert RoleFitEvaluator.evaluate_armor(role_fit, ["heavy", "plate"]) == 0.6
    
    # Skills
    assert RoleFitEvaluator.evaluate_skill(role_fit, ["slash", "physical"]) == 0.7
    
    # Party Role
    assert RoleFitEvaluator.evaluate_party_role(role_fit, "vanguard") == 0.9
    assert RoleFitEvaluator.evaluate_party_role(role_fit, "backline") == 0.0
    
    # Quests
    assert RoleFitEvaluator.evaluate_quest(role_fit, ["hunt", "combat"]) == 0.5
