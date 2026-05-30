import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.domains.memory.phase import MemoryUpdatePhase

def test_lost_to_wolf_then_repairs_before_retry():
    # Simulated Scenario:
    # 1. Entity suffers a combat loss in 'wolf_den' while stamina was low and weapon damaged.
    # 2. Causal attribution marks 'damaged_weapon' and 'low_stamina' as causes.
    # 3. Future advice includes 'repair_weapon' and 'rest_often'.
    # 4. Spatial memory marks 'wolf_den' as dangerous.

    entity = EntityState(id=10, kind="HERO")
    entity = replace(entity, stamina=replace(entity.stamina, current=10.0))
    entity = replace(entity, equipment=replace(entity.equipment, durability={"MAIN_HAND": 0.1}))

    trigger = {
        "entity_id": 10,
        "kind": "combat_loss",
        "id": "loss_wolf",
        "region_id": "wolf_den"
    }

    phase = MemoryUpdatePhase()
    updated = phase.run([entity], tick=150, trigger_event=trigger)
    new_entity = updated[0]

    memory = new_entity.cognition.memory
    assert len(memory.causal.entries) == 1
    
    advice = memory.causal.entries[0].future_advice
    assert "repair_weapon" in advice
    assert "rest_often" in advice

    assert memory.spatial.visited_regions["wolf_den"].is_dangerous is True
