"""
tests/unit/domains/combat_engagement/test_phase4_self_combat_estimate.py

Phase 4 — SelfCombatEstimateService unit tests.
Verifies derived actor capability estimates under various HP/durability states.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent, EquipmentComponent, StaminaComponent
from src.core.models.inventory import EquipSlot
from src.domains.combat_engagement.self_estimate import SelfCombatEstimateService


def _entity(hp=100, max_hp=100, stamina=100.0, weapon_slot=None, durability_val=100.0):
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1)
    b.replace_stamina(StaminaComponent(current=stamina, max_stamina=100.0))
    
    if weapon_slot:
        from src.core.state import ReadOnlyDict
        slots = ReadOnlyDict({EquipSlot.MAIN_HAND: "iron_sword"})
        durability = ReadOnlyDict({EquipSlot.MAIN_HAND: durability_val})
        b.replace_equipment(EquipmentComponent(slots=slots, durability=durability))
        
    return b.build()


def test_low_hp_reduces_self_combat_estimate():
    entity_full = _entity(hp=100)
    entity_hurt = _entity(hp=15) # near_death constraint, -0.5 modifier
    
    est_full = SelfCombatEstimateService.estimate(entity_full)
    est_hurt = SelfCombatEstimateService.estimate(entity_hurt)
    
    assert est_hurt.estimated_power < est_full.estimated_power
    assert "near_death" in est_hurt.constraints


def test_low_stamina_reduces_self_combat_estimate():
    entity_fresh = _entity(stamina=100.0)
    entity_tired = _entity(stamina=15.0) # no_stamina constraint, -0.3 modifier
    
    est_fresh = SelfCombatEstimateService.estimate(entity_fresh)
    est_tired = SelfCombatEstimateService.estimate(entity_tired)
    
    assert est_tired.estimated_power < est_fresh.estimated_power
    assert "no_stamina" in est_tired.constraints


def test_better_weapon_increases_self_combat_estimate():
    entity_unarmed = _entity(weapon_slot=None)
    entity_armed = _entity(weapon_slot="iron_sword")
    
    est_unarmed = SelfCombatEstimateService.estimate(entity_unarmed)
    est_armed = SelfCombatEstimateService.estimate(entity_armed)
    
    assert est_armed.estimated_power > est_unarmed.estimated_power
    assert "bare_handed" in est_unarmed.condition_modifiers


def test_damaged_weapon_reduces_self_combat_estimate():
    entity_sharp = _entity(weapon_slot="iron_sword", durability_val=100.0)
    entity_damaged = _entity(weapon_slot="iron_sword", durability_val=10.0) # dull_weapon constraint
    
    est_sharp = SelfCombatEstimateService.estimate(entity_sharp)
    est_damaged = SelfCombatEstimateService.estimate(entity_damaged)
    
    assert est_damaged.estimated_power < est_sharp.estimated_power
    assert "dull_weapon" in est_damaged.constraints
