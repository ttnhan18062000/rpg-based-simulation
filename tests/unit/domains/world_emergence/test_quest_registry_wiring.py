# tests/unit/domains/world_emergence/test_quest_registry_wiring.py
"""AC-4: WorldEmergencePhase populates quest_registry via the authoritative apply path."""
import pytest
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath
from src.domains.world_emergence.phase import WorldEmergencePhase
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.core.models.quests import QuestOpportunityStatus


def test_world_emergence_populates_quest_registry():
    depleted_event = WorldEvent(
        category=WorldEventCategory.RESOURCE_DEPLETED,
        tick=5,
        region_id="north",
        subject="iron_ore",
        severity=0.8,
    )
    state = AuthoritativeState(tick=5, seed=1)
    update = StateUpdate()

    new_update, result = WorldEmergencePhase.execute(state, update, recent_events=[depleted_event])

    assert len(new_update.quest_registry_add) >= 1
    opp = new_update.quest_registry_add[0]
    assert opp.kind == "resource_crisis"
    assert opp.status == QuestOpportunityStatus.OFFERED

    applied_state = ApplyPath.apply_generation(state, new_update)
    assert len(applied_state.quest_registry) >= 1
    entry = next(iter(applied_state.quest_registry.values()))
    assert entry.status == QuestOpportunityStatus.OFFERED
