"""
tests/integration/domains/progression/test_phase6_progression_conversion_phase.py

Phase 6 — ProgressionConversionPhase tests.
"""

import pytest
from src.core.state import AuthoritativeState, ItemStack, EquipmentComponent, EquipSlot
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate
from src.domains.progression.phase import ProgressionConversionPhase


def test_phase_skips_when_feature_flag_disabled():
    # If progression_conversion_enabled is False, phase should skip
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True))
    entity = b.build()
    
    # We can create a subclass or subclass mock of AuthoritativeState to bypass slots limits
    class MockState(AuthoritativeState):
        progression_conversion_enabled = False

    state = MockState(entities={1: entity}, tick=1, seed=1)
    
    update = StateUpdate()
    refined = ProgressionConversionPhase.execute(state, update)
    
    # 1 should not be in refined.entity_updates because the phase skipped completely
    assert 1 not in refined.entity_updates


def test_phase_runs_and_outputs_correct_intent():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True))
    entity = b.build()
    
    # Entity is weak (missing weapon)
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    
    update = StateUpdate()
    refined = ProgressionConversionPhase.execute(state, update)
    
    assert 1 in refined.entity_updates
    ent_up = refined.entity_updates[1]
    # Dominant gap is weapon_gap, fallback decision selected should be SAVE_FOR_LATER (no direct action maps to it)
    assert "last_progression_decision" in ent_up.property_updates
    decision = ent_up.property_updates["last_progression_decision"]
    assert decision.selected[0].kind.value == "SAVE_FOR_LATER"
