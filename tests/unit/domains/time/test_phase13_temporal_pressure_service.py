import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, SubjectiveModel, TemporalModel, DeadlineEntry, CooldownEntry, StalenessEntry
from src.domains.time.service import TemporalPressureService

def test_soon_deadline_increases_urgency():
    entity = EntityState(id=1, kind="HERO")
    
    deadlines = {"quest_1": DeadlineEntry("quest_1", expiry_tick=120)}
    time = TemporalModel(deadlines=deadlines)
    entity = replace(entity, cognition=CognitionModel(subjective=SubjectiveModel(time=time)))

    # At tick 100, ticks left is 20 (less than 100) -> Urgency should be high
    urgencies = TemporalPressureService.calculate_urgencies(entity, current_tick=100)
    assert urgencies["quest_1"] > 0.7

def test_active_cooldown_prevents_immediate_retry():
    entity = EntityState(id=1, kind="HERO")
    
    cooldowns = {"skill_1": CooldownEntry("skill_1", ready_tick=150)}
    time = TemporalModel(cooldowns=cooldowns)
    entity = replace(entity, cognition=CognitionModel(subjective=SubjectiveModel(time=time)))

    # At tick 100, ready_tick is 150 (cooldown active) -> Urgency is 0.0
    urgencies = TemporalPressureService.calculate_urgencies(entity, current_tick=100)
    assert urgencies["skill_1"] == 0.0

def test_old_rumor_gets_staleness_penalty():
    entity = EntityState(id=1, kind="HERO")
    
    stale_facts = {"rumor_1": StalenessEntry("rumor_1", last_verified_tick=50)}
    time = TemporalModel(stale_facts=stale_facts)
    entity = replace(entity, cognition=CognitionModel(subjective=SubjectiveModel(time=time)))

    # At tick 100, age is 50 -> Urgency of verifying is 50 * 0.002 = 0.1
    urgencies = TemporalPressureService.calculate_urgencies(entity, current_tick=100)
    assert urgencies["rumor_1"] == 0.1
