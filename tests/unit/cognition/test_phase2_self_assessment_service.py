"""
tests/unit/cognition/test_phase2_self_assessment_service.py

Phase 2 — SelfAssessmentService unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, StaminaComponent, BiologicalComponent
from src.cognition.self_assessment import SelfAssessmentService


def _entity(
    hp=100, max_hp=100,
    stamina=100, max_stamina=100,
    hunger=0.0, sleep_debt=0.0,
    items=None, max_slots=20,
    atk=10, level=1,
    gear_slots=None,
):
    """Helper to build a test entity with controlled state."""
    from dataclasses import replace
    b = V2EntityBuilder(1)
    # Combat
    combat = CombatComponent(hp=hp, max_hp=max_hp, atk=atk, def_stat=2)
    b.replace_combat(combat)
    # Stamina
    stam = StaminaComponent(current=stamina, max_stamina=max_stamina)
    b.replace_stamina(stam)
    # Biological
    bio = BiologicalComponent(hunger=hunger, sleep_debt=sleep_debt)
    b.replace_biological(bio)
    # Level via identity
    b.identity(evolution_level=level)
    return b.build()


# ── Low health ────────────────────────────────────────────────────────────────

class TestSelfAssessmentLowHealth:
    def test_phase2_assessment_low_hp_creates_low_health_weakness(self):
        entity = _entity(hp=20, max_hp=100)
        sa = SelfAssessmentService.assess(entity)
        assert "low_health" in sa.perceived_weaknesses

    def test_phase2_assessment_low_hp_increases_stress(self):
        healthy = _entity(hp=100, max_hp=100)
        wounded = _entity(hp=15, max_hp=100)
        sa_h = SelfAssessmentService.assess(healthy)
        sa_w = SelfAssessmentService.assess(wounded)
        assert sa_w.stress_level > sa_h.stress_level

    def test_phase2_assessment_low_hp_lowers_confidence(self):
        healthy = _entity(hp=100, max_hp=100)
        wounded = _entity(hp=20, max_hp=100)
        sa_h = SelfAssessmentService.assess(healthy)
        sa_w = SelfAssessmentService.assess(wounded)
        assert sa_w.confidence_level < sa_h.confidence_level

    def test_phase2_assessment_critical_hp_not_low_health_above_threshold(self):
        entity = _entity(hp=90, max_hp=100)
        sa = SelfAssessmentService.assess(entity)
        assert "low_health" not in sa.perceived_weaknesses

    def test_phase2_assessment_health_condition_recorded(self):
        entity = _entity(hp=30, max_hp=100)
        sa = SelfAssessmentService.assess(entity)
        assert "health" in sa.perceived_condition
        assert abs(sa.perceived_condition["health"] - 0.3) < 0.01


# ── Low stamina ───────────────────────────────────────────────────────────────

class TestSelfAssessmentLowStamina:
    def test_phase2_assessment_low_stamina_creates_weakness(self):
        entity = _entity(stamina=10, max_stamina=100)
        sa = SelfAssessmentService.assess(entity)
        assert "low_stamina" in sa.perceived_weaknesses

    def test_phase2_assessment_full_stamina_no_weakness(self):
        entity = _entity(stamina=100, max_stamina=100)
        sa = SelfAssessmentService.assess(entity)
        assert "low_stamina" not in sa.perceived_weaknesses

    def test_phase2_assessment_stamina_condition_recorded(self):
        entity = _entity(stamina=20, max_stamina=100)
        sa = SelfAssessmentService.assess(entity)
        assert "stamina" in sa.perceived_condition
        assert abs(sa.perceived_condition["stamina"] - 0.2) < 0.01


# ── Biological needs ──────────────────────────────────────────────────────────

class TestSelfAssessmentBiological:
    def test_phase2_assessment_high_hunger_creates_weakness(self):
        entity = _entity(hunger=75.0)
        sa = SelfAssessmentService.assess(entity)
        assert "hunger_pressure" in sa.perceived_weaknesses

    def test_phase2_assessment_low_hunger_no_weakness(self):
        entity = _entity(hunger=10.0)
        sa = SelfAssessmentService.assess(entity)
        assert "hunger_pressure" not in sa.perceived_weaknesses

    def test_phase2_assessment_high_sleep_debt_creates_weakness(self):
        entity = _entity(sleep_debt=65.0)
        sa = SelfAssessmentService.assess(entity)
        assert "sleep_debt_pressure" in sa.perceived_weaknesses


# ── Weak weapon ───────────────────────────────────────────────────────────────

class TestSelfAssessmentWeapon:
    def test_phase2_assessment_weak_weapon_for_level(self):
        # Level 5 expects atk >= 25, but entity only has 3
        entity = _entity(atk=3, level=5)
        sa = SelfAssessmentService.assess(entity)
        assert "weak_weapon" in sa.perceived_weaknesses

    def test_phase2_assessment_adequate_weapon_no_weakness(self):
        entity = _entity(atk=30, level=5)
        sa = SelfAssessmentService.assess(entity)
        assert "weak_weapon" not in sa.perceived_weaknesses


# ── Multiple weaknesses ───────────────────────────────────────────────────────

class TestSelfAssessmentMixed:
    def test_phase2_assessment_multiple_weaknesses_high_stress(self):
        entity = _entity(hp=15, max_hp=100, stamina=10, max_stamina=100, hunger=70.0)
        sa = SelfAssessmentService.assess(entity)
        assert sa.stress_level > 0.4
        assert len(sa.perceived_weaknesses) >= 3

    def test_phase2_assessment_output_is_deterministic(self):
        entity = _entity(hp=50, max_hp=100, atk=10, level=3)
        sa1 = SelfAssessmentService.assess(entity)
        sa2 = SelfAssessmentService.assess(entity)
        assert sa1 == sa2

    def test_phase2_assessment_does_not_mutate_entity(self):
        entity = _entity(hp=30, max_hp=100)
        hp_before = entity.combat.hp
        SelfAssessmentService.assess(entity)
        assert entity.combat.hp == hp_before

    def test_phase2_assessment_strengths_on_good_condition(self):
        entity = _entity(hp=100, max_hp=100, stamina=100, max_stamina=100, atk=30, level=1)
        sa = SelfAssessmentService.assess(entity)
        assert len(sa.perceived_strengths) > 0
