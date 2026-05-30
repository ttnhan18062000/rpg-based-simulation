# TDD tests for Phase 10 DirtyWorkScheduler
import pytest
from src.domains.optimization.dirty_scheduler import DirtyWorkScheduler
from src.domains.optimization.budget_manager import PhaseBudget

@pytest.fixture
def dummy_budget():
    return PhaseBudget(
        phase_name="test_phase",
        max_ms_per_tick=50.0,
        max_entities_per_tick=3,
        max_provider_calls_per_tick=5,
        max_results_per_entity=3,
        max_trace_events_per_tick=100,
        max_memory_entries_per_entity=10
    )

def test_dirty_entity_mark_is_recorded():
    scheduler = DirtyWorkScheduler()
    scheduler.mark_entity_dirty(1, "hp_changed")
    assert scheduler.is_entity_dirty(1)

def test_duplicate_dirty_mark_is_coalesced():
    scheduler = DirtyWorkScheduler()
    scheduler.mark_entity_dirty(1, "hp_changed")
    scheduler.mark_entity_dirty(1, "hp_changed")
    assert scheduler.is_entity_dirty(1)
    # The count or processing list should have precisely one entry
    assert len(scheduler.get_dirty_entities()) == 1

def test_scheduler_returns_deterministic_order():
    scheduler = DirtyWorkScheduler()
    scheduler.mark_entity_dirty(5, "stamina_changed")
    scheduler.mark_entity_dirty(2, "hp_changed")
    scheduler.mark_entity_dirty(8, "inventory_changed")
    # Should sort entity IDs deterministically (e.g. ascending numerical order)
    entities = scheduler.next_entities("test_phase", count=3)
    assert entities == (2, 5, 8)

def test_scheduler_respects_entity_budget(dummy_budget):
    scheduler = DirtyWorkScheduler()
    for eid in (10, 5, 2, 8):
        scheduler.mark_entity_dirty(eid, "hp_changed")
    entities = scheduler.next_entities("test_phase", count=dummy_budget.max_entities_per_tick)
    assert len(entities) == 3
    assert entities == (2, 5, 8)

def test_clean_entities_are_not_returned():
    scheduler = DirtyWorkScheduler()
    scheduler.mark_entity_dirty(1, "hp_changed")
    entities = scheduler.next_entities("test_phase", count=5)
    assert 2 not in entities

def test_processed_dirty_entries_are_cleared():
    scheduler = DirtyWorkScheduler()
    scheduler.mark_entity_dirty(1, "hp_changed")
    scheduler.mark_entity_dirty(2, "stamina_changed")
    entities = scheduler.next_entities("test_phase", count=1)
    assert entities == (1,)
    scheduler.clear_processed_entities(entities)
    assert not scheduler.is_entity_dirty(1)
    assert scheduler.is_entity_dirty(2)

def test_dirty_reason_is_preserved_in_report():
    scheduler = DirtyWorkScheduler()
    scheduler.mark_entity_dirty(1, "hp_changed")
    report = scheduler.generate_report()
    assert report[1] == {"hp_changed"}
