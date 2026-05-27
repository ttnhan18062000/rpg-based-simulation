"""
tests/unit/cognition/test_phase2_need_interpretation_service.py

Phase 2 — NeedInterpretationService unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, StaminaComponent, BiologicalComponent
from src.core.self_model import SelfAwarenessComponent, SelfModelBundle, UnknownFact, KnowledgeModelComponent
from src.cognition.self_assessment import SelfAssessmentService
from src.cognition.need_interpretation import NeedInterpretationService


def _entity_with_awareness(**kwargs):
    """Build entity, run SelfAssessment, return (entity_after, awareness)."""
    hp = kwargs.pop("hp", 100)
    max_hp = kwargs.pop("max_hp", 100)
    stamina = kwargs.pop("stamina", 100)
    max_stamina = kwargs.pop("max_stamina", 100)
    hunger = kwargs.pop("hunger", 0.0)
    sleep_debt = kwargs.pop("sleep_debt", 0.0)
    atk = kwargs.pop("attack", 10)
    level = kwargs.pop("level", 1)
    gold = kwargs.pop("gold", 50)
    unknowns = kwargs.pop("unknowns", {})

    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=atk, def_stat=2))
    b.replace_stamina(StaminaComponent(current=stamina, max_stamina=max_stamina))
    b.replace_biological(BiologicalComponent(hunger=hunger, sleep_debt=sleep_debt))
    b.identity(evolution_level=level)
    b.inventory(gold=gold)

    if unknowns:
        km = KnowledgeModelComponent(unknowns=unknowns)
        from src.core.self_model import SelfModelBundle
        bundle = SelfModelBundle(knowledge=km)
        b.replace_self_model(bundle)

    entity = b.build()
    awareness = SelfAssessmentService.assess(entity)
    return entity, awareness


# ── Healing need ──────────────────────────────────────────────────────────────

class TestNeedHealing:
    def test_phase2_need_low_hp_creates_healing_need(self):
        entity, awareness = _entity_with_awareness(hp=20, max_hp=100)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "healing" in needs.active_needs

    def test_phase2_need_critical_hp_healing_dominates(self):
        entity, awareness = _entity_with_awareness(hp=10, max_hp=100)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert needs.dominant_need == "healing"
        assert needs.active_needs["healing"].urgency >= 0.9

    def test_phase2_need_full_hp_no_healing(self):
        entity, awareness = _entity_with_awareness(hp=100, max_hp=100)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "healing" not in needs.active_needs


# ── Food need ─────────────────────────────────────────────────────────────────

class TestNeedFood:
    def test_phase2_need_high_hunger_creates_food_need(self):
        entity, awareness = _entity_with_awareness(hunger=70.0)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "food" in needs.active_needs

    def test_phase2_need_critical_hunger_high_urgency(self):
        entity, awareness = _entity_with_awareness(hunger=90.0)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert needs.active_needs["food"].urgency >= 0.9

    def test_phase2_need_no_hunger_no_food_need(self):
        entity, awareness = _entity_with_awareness(hunger=5.0)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "food" not in needs.active_needs


# ── Rest need ─────────────────────────────────────────────────────────────────

class TestNeedRest:
    def test_phase2_need_high_sleep_debt_creates_rest_need(self):
        entity, awareness = _entity_with_awareness(sleep_debt=60.0)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "rest" in needs.active_needs

    def test_phase2_need_no_sleep_debt_no_rest(self):
        entity, awareness = _entity_with_awareness(sleep_debt=5.0)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "rest" not in needs.active_needs


# ── Equipment needs ───────────────────────────────────────────────────────────

class TestNeedEquipment:
    def test_phase2_need_weak_weapon_creates_improvement_need(self):
        entity, awareness = _entity_with_awareness(attack=2, level=3)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "equipment_improvement" in needs.active_needs

    def test_phase2_need_critical_hp_makes_improvement_lower_priority_than_healing(self):
        entity, awareness = _entity_with_awareness(hp=10, max_hp=100, attack=2, level=3)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "healing" in needs.active_needs
        assert "equipment_improvement" in needs.active_needs
        assert needs.active_needs["healing"].urgency > needs.active_needs["equipment_improvement"].urgency

    def test_phase2_need_dominant_is_healing_not_equipment_when_critical(self):
        entity, awareness = _entity_with_awareness(hp=10, max_hp=100, attack=2, level=3)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert needs.dominant_need == "healing"


# ── Inventory need ────────────────────────────────────────────────────────────

class TestNeedInventory:
    def test_phase2_need_full_inventory_creates_inventory_space_need(self):
        # Simulate 18 of 20 items loaded — above 85%
        from src.core.models.inventory import ItemStack, InventoryComponent
        items = [ItemStack(item_id="wood", quantity=1) for _ in range(18)]
        b = V2EntityBuilder(1)
        inv = InventoryComponent(items=items, max_slots=20)
        b.replace_inventory(inv)
        entity = b.build()
        awareness = SelfAssessmentService.assess(entity)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "inventory_space" in needs.active_needs


# ── Information need from unknowns ────────────────────────────────────────────

class TestNeedInformation:
    def test_phase2_need_unknown_material_source_creates_information_need(self):
        unknowns = {"material.moon_resin.source": UnknownFact(
            subject="material.moon_resin.source",
            reason="provider_partial",
            recorded_tick=5,
        )}
        entity, awareness = _entity_with_awareness(unknowns=unknowns)
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "information" in needs.active_needs

    def test_phase2_need_no_unknowns_no_information_need(self):
        entity, awareness = _entity_with_awareness()
        needs = NeedInterpretationService.interpret(entity, awareness)
        assert "information" not in needs.active_needs


# ── Priority competition ──────────────────────────────────────────────────────

class TestNeedPriority:
    def test_phase2_need_hunger_vs_upgrade_healing_wins_when_critical_hp(self):
        """Even equipment desire stays below survival."""
        entity, awareness = _entity_with_awareness(hp=10, max_hp=100, hunger=70.0, attack=2, level=3)
        needs = NeedInterpretationService.interpret(entity, awareness)
        healing_u = needs.active_needs.get("healing", None)
        food_u = needs.active_needs.get("food", None)
        improve_u = needs.active_needs.get("equipment_improvement", None)
        assert healing_u is not None
        assert improve_u is not None
        assert healing_u.urgency > improve_u.urgency

    def test_phase2_need_dominant_is_single_highest_urgency(self):
        entity, awareness = _entity_with_awareness(hp=20, max_hp=100, hunger=30.0, attack=2, level=3)
        needs = NeedInterpretationService.interpret(entity, awareness)
        if needs.dominant_need:
            dominant_urgency = needs.active_needs[needs.dominant_need].urgency
            for key, need in needs.active_needs.items():
                assert need.urgency <= dominant_urgency

    def test_phase2_need_output_is_deterministic(self):
        entity, awareness = _entity_with_awareness(hp=40, max_hp=100, hunger=65.0)
        n1 = NeedInterpretationService.interpret(entity, awareness)
        n2 = NeedInterpretationService.interpret(entity, awareness)
        assert n1 == n2
