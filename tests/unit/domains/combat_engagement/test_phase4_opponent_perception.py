"""
tests/unit/domains/combat_engagement/test_phase4_opponent_perception.py

Phase 4 — OpponentPerceptionService unit tests.
Verifies subjective opponent estimation and uncertainty propagation.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, EquipmentComponent
from src.core.models.inventory import ItemStack, EquipSlot
from src.domains.combat_engagement.perception import OpponentPerceptionService
from src.domains.combat_engagement.schema import OpponentModel


def _entity(e_id, level=1, perception=5, hp=100, weapon_slot=None):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=level)
    b.attributes(perception=perception)
    
    if weapon_slot:
        # Equip weapon
        from src.core.models.inventory import EquipSlot
        from src.core.state import ReadOnlyDict
        slots = ReadOnlyDict({EquipSlot.MAIN_HAND: "iron_sword"})
        durability = ReadOnlyDict({EquipSlot.MAIN_HAND: 100.0})
        b.replace_equipment(EquipmentComponent(slots=slots, durability=durability))
        
    return b.build()


def test_unknown_enemy_has_high_uncertainty():
    actor = _entity(1, perception=5)
    target = _entity(2, level=2) # level 2 base power = 40
    
    est = OpponentPerceptionService.estimate(actor, target, memory=None)
    
    assert est.estimated_power == 40.0
    assert est.uncertainty >= 0.35
    assert est.confidence <= 0.6


def test_known_enemy_memory_reduces_uncertainty():
    actor = _entity(1, perception=5)
    target = _entity(2, level=2)
    
    mem = OpponentModel(
        subject_key="entity.2",
        estimated_power=42.0,
        uncertainty=0.1,
        confidence=0.9,
    )
    
    est = OpponentPerceptionService.estimate(actor, target, memory=mem)
    
    # Uncertainty is reduced, confidence is increased
    assert est.uncertainty < 0.3
    assert est.confidence > 0.6
    # Estimated power moves toward memory value
    assert abs(est.estimated_power - 41.2) < 0.1  # weighted blend 40*0.4 + 42*0.6 = 41.2


def test_visible_better_equipment_increases_estimate():
    actor = _entity(1, perception=5)
    target_unarmed = _entity(2, level=1)
    target_armed = _entity(3, level=1, weapon_slot="iron_sword")
    
    est_unarmed = OpponentPerceptionService.estimate(actor, target_unarmed)
    est_armed = OpponentPerceptionService.estimate(actor, target_armed)
    
    assert est_armed.estimated_power > est_unarmed.estimated_power
    assert "armed" in est_armed.visible_signals


def test_low_perception_increases_uncertainty():
    actor_blind = _entity(1, perception=2) # poor perception
    actor_sharp = _entity(2, perception=8)
    target = _entity(3, level=1)
    
    est_blind = OpponentPerceptionService.estimate(actor_blind, target)
    est_sharp = OpponentPerceptionService.estimate(actor_sharp, target)
    
    assert est_blind.uncertainty > est_sharp.uncertainty
    assert "poor_perception" in est_blind.unknown_factors
