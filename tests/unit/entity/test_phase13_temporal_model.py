import pytest
from src.core.cognition import (
    TemporalModel,
    DeadlineEntry,
    CausalMemory,
    CausalMemoryEntry,
    SpatialMemory,
    RegionVisitMemory
)

def test_temporal_model_defaults_are_empty():
    t = TemporalModel()
    assert len(t.deadlines) == 0
    assert len(t.cooldowns) == 0
    assert len(t.urgency) == 0

def test_deadline_entry_can_be_recorded():
    entry = DeadlineEntry(target_id="quest_1", expiry_tick=500)
    assert entry.target_id == "quest_1"
    assert entry.expiry_tick == 500

def test_causal_memory_entry_records_causes_and_future_advice():
    entry = CausalMemoryEntry(
        event_id="evt_1",
        event_kind="combat_loss",
        interpreted_causes=("low_stamina", "weak_weapon"),
        confidence=0.9,
        future_advice=("repair_weapon",),
        tick=100
    )
    assert "low_stamina" in entry.interpreted_causes
    assert "repair_weapon" in entry.future_advice

def test_causal_memory_is_bounded():
    cm = CausalMemory()
    assert cm.capacity == 30
    assert len(cm.entries) == 0

def test_region_visit_memory_can_be_recorded():
    rv = RegionVisitMemory(region_id="forest", visit_count=3, familiarity=0.6)
    assert rv.region_id == "forest"
    assert rv.visit_count == 3
    assert rv.familiarity == 0.6
