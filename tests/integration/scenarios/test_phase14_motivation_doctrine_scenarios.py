import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, MotivationModel, IdentityDoctrine, ValuePreferenceProfile, RoleFitPreference
from src.domains.motivation.resolver import DoctrineResolver
from src.domains.motivation.evaluator import RoleFitEvaluator
from src.domains.motivation.service import MotivationBiasService

def test_same_world_classes_choose_different_routes():
    # Setup Warrior
    warrior_doctrine = DoctrineResolver.resolve("warrior")
    warrior_role_fit = RoleFitPreference(
        weapon_tags={"melee": 0.8, "ranged": -0.2},
        armor_tags={"heavy": 0.6}
    )
    warrior_cognition = CognitionModel(
        motivation=MotivationModel(
            doctrine=warrior_doctrine,
            role_fit=warrior_role_fit,
            values=ValuePreferenceProfile(survival=0.6, reward=0.8, pride=0.7)
        )
    )
    warrior = replace(EntityState(id=1, kind="HERO"), cognition=warrior_cognition)

    # Setup Mage
    mage_doctrine = DoctrineResolver.resolve("mage")
    mage_role_fit = RoleFitPreference(
        weapon_tags={"spells": 0.9, "melee": -0.5},
        armor_tags={"heavy": -0.5}
    )
    mage_cognition = CognitionModel(
        motivation=MotivationModel(
            doctrine=mage_doctrine,
            role_fit=mage_role_fit,
            values=ValuePreferenceProfile(survival=0.8, reward=0.4, pride=0.3)
        )
    )
    mage = replace(EntityState(id=2, kind="HERO"), cognition=mage_cognition)

    # Candidate weapons
    greatsword_tags = ["melee", "heavy", "weapon"]
    staff_tags = ["spells", "mana", "weapon"]

    # Evaluate gear fits
    assert RoleFitEvaluator.evaluate_weapon(warrior.cognition.motivation.role_fit, greatsword_tags) == 0.8
    assert RoleFitEvaluator.evaluate_weapon(warrior.cognition.motivation.role_fit, staff_tags) == 0.0
    
    assert RoleFitEvaluator.evaluate_weapon(mage.cognition.motivation.role_fit, greatsword_tags) == -0.5
    assert RoleFitEvaluator.evaluate_weapon(mage.cognition.motivation.role_fit, staff_tags) == 0.9

    # Strategic Route biases
    melee_route = ["melee", "combat"]
    flee_route = ["flee", "caution"]
    coop_route = ["cooperation", "party"]

    # Warrior preferences
    assert MotivationBiasService.compute_bias_multiplier(warrior, melee_route) > 1.0
    assert MotivationBiasService.compute_bias_multiplier(warrior, flee_route) < 1.0

    # Mage preferences
    assert MotivationBiasService.compute_bias_multiplier(mage, melee_route) < 1.0
    assert MotivationBiasService.compute_bias_multiplier(mage, flee_route) > 1.0
    assert MotivationBiasService.compute_bias_multiplier(mage, coop_route) > 1.0 # due to low pride, mage prefers coop more than warrior
