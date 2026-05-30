import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.domains.memory.attribution import CausalAttributionService

def test_combat_loss_attributes_low_stamina_and_damaged_weapon():
    entity = EntityState(id=1, kind="HERO")
    # Set low stamina
    entity = replace(entity, stamina=replace(entity.stamina, current=15.0))
    # Equip a damaged weapon
    entity = replace(entity, equipment=replace(entity.equipment, durability={"MAIN_HAND": 0.1}))

    entry = CausalAttributionService.attribute(
        entity=entity,
        event_id="loss_1",
        event_kind="combat_loss",
        tick=100
    )

    assert "low_stamina" in entry.interpreted_causes
    assert "damaged_weapon" in entry.interpreted_causes
    assert "rest_often" in entry.future_advice
    assert "repair_weapon" in entry.future_advice

def test_failed_search_attributes_wrong_location_or_bad_rumor():
    entity = EntityState(id=1, kind="HERO")

    entry = CausalAttributionService.attribute(
        entity=entity,
        event_id="search_1",
        event_kind="failed_search",
        tick=100
    )

    assert "wrong_location" in entry.interpreted_causes
    assert "seek_trusted_guide" in entry.future_advice
