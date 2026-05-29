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
    updated = phase.run([entity], tick=10, trigger_event=trigger)
    
    assert len(updated) == 1
    new_entity = updated[0]
    causal_mem = new_entity.cognition.memory.causal
    assert len(causal_mem.entries) == 1
    assert causal_mem.entries[0].event_id == "loss_evt_1"
    assert causal_mem.entries[0].region_id == "wolf_den"
    assert new_entity.cognition.memory.spatial.visited_regions["wolf_den"].is_dangerous is True

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
