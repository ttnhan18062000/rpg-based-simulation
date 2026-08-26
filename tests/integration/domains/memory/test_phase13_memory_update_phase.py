import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, SubjectiveModel, TemporalModel, StalenessEntry
from src.domains.memory.phase import MemoryUpdatePhase

def test_phase_updates_causal_memory_after_combat_loss():
    entity = EntityState(id=42, kind="HERO")
    
    trigger = {
        "entity_id": 42,
        "kind": "combat_loss",
        "id": "loss_evt_1",
        "region_id": "wolf_den"
    }

    phase = MemoryUpdatePhase()
    updated = phase.run([entity], tick=10, trigger_events=[trigger])
    
    assert len(updated) == 1
    new_entity = updated[0]
    causal_mem = new_entity.cognition.memory.causal
    assert len(causal_mem.entries) == 1
    assert causal_mem.entries[0].event_id == "loss_evt_1"
    assert causal_mem.entries[0].region_id == "wolf_den"
    assert new_entity.cognition.memory.spatial.visited_regions["wolf_den"].is_dangerous is True

def test_run_updates_multiple_entities_with_distinct_trigger_events_same_tick():
    entity_a = EntityState(id=1, kind="HERO")
    entity_b = EntityState(id=2, kind="HERO")
    entity_c = EntityState(id=3, kind="HERO")

    trigger_a = {"entity_id": 1, "kind": "combat_loss", "id": "loss_a", "region_id": "wolf_den"}
    trigger_b = {"entity_id": 2, "kind": "failed_search", "id": "search_b", "region_id": "old_ruins"}

    phase = MemoryUpdatePhase()
    updated = phase.run([entity_a, entity_b, entity_c], tick=20, trigger_events=[trigger_a, trigger_b])

    by_id = {e.id: e for e in updated}
    assert len(by_id) == 3

    causal_a = by_id[1].cognition.memory.causal.entries
    assert len(causal_a) == 1
    assert causal_a[0].event_id == "loss_a"
    assert causal_a[0].event_kind == "combat_loss"

    causal_b = by_id[2].cognition.memory.causal.entries
    assert len(causal_b) == 1
    assert causal_b[0].event_id == "search_b"
    assert causal_b[0].event_kind == "failed_search"

    assert len(by_id[3].cognition.memory.causal.entries) == 0


def test_phase_updates_temporal_staleness_after_old_fact():
    entity = EntityState(id=1, kind="HERO")
    stale_facts = {"rumor_1": StalenessEntry("rumor_1", last_verified_tick=50)}
    time = TemporalModel(stale_facts=stale_facts)
    entity = replace(entity, cognition=CognitionModel(subjective=SubjectiveModel(time=time)))

    phase = MemoryUpdatePhase()
    # At tick 150, age is 100 -> Urgency should update to 0.2
    updated = phase.run([entity], tick=150)
    
    assert len(updated) == 1
    assert updated[0].cognition.subjective.time.urgency["rumor_1"] == 0.2
