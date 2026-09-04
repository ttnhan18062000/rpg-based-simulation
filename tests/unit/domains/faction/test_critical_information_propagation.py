"""
Tests for TCK-20260903-INFORMATION-HUB-ACCUMULATION Step 6:
InformationPropagationService.compute_propagation_events().

City-to-City: a critical WorldEvent (severity >= 0.8) at a City owned by a faction propagates
to every sibling City in that same faction's territory.

City-to-Country: the same event also propagates to every City in an ALLIED faction's territory,
but NOT to a faction with no explicit diplomatic relation (defaults to NEUTRAL, per the
fs.diplomatic_relations.get(other_id, DiplomaticState.NEUTRAL) idiom) -- "unrelated Country B"
in the ticket's own AC #4 wording.
"""
from __future__ import annotations

from src.core.enums import DiplomaticState
from src.core.state import AuthoritativeState, FactionState
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.engine.faction_decision import FactionAwarenessService, InformationPropagationService


def _state_with_factions(**factions: FactionState) -> AuthoritativeState:
    return AuthoritativeState(tick=100, seed=1, factions=dict(factions))


def test_critical_information_propagates_within_faction_territory():
    country_a = FactionState(faction_id="country_a", territory=("city_1", "city_2", "city_3"))
    state = _state_with_factions(country_a=country_a)
    events = [WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=99, region_id="city_1", severity=0.9)]

    propagated = InformationPropagationService.compute_propagation_events(state, events)

    dest_regions = {e.region_id for e in propagated}
    assert dest_regions == {"city_2", "city_3"}
    assert all(e.category == WorldEventCategory.CRITICAL_INFORMATION_PROPAGATED for e in propagated)


def test_critical_information_reaches_allied_country_not_unrelated_country():
    country_a = FactionState(
        faction_id="country_a", territory=("city_1",),
        diplomatic_relations={"country_b": DiplomaticState.ALLIED},
    )
    country_b = FactionState(faction_id="country_b", territory=("city_b1", "city_b2"))
    # country_c has no explicit relation entry with country_a -> defaults to NEUTRAL and must
    # NOT receive the propagation (this is the AC #4 "unrelated Country B" case).
    country_c = FactionState(faction_id="country_c", territory=("city_c1",))
    state = _state_with_factions(country_a=country_a, country_b=country_b, country_c=country_c)
    events = [WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=99, region_id="city_1", severity=1.0)]

    propagated = InformationPropagationService.compute_propagation_events(state, events)

    dest_regions = {e.region_id for e in propagated}
    assert "city_b1" in dest_regions
    assert "city_b2" in dest_regions
    assert "city_c1" not in dest_regions


def test_non_critical_severity_event_does_not_propagate():
    country_a = FactionState(faction_id="country_a", territory=("city_1", "city_2"))
    state = _state_with_factions(country_a=country_a)
    events = [WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=99, region_id="city_1", severity=0.5)]

    propagated = InformationPropagationService.compute_propagation_events(state, events)
    assert propagated == []


def test_propagation_does_not_interfere_with_faction_awareness_tension_output():
    country_a = FactionState(faction_id="country_a", territory=("city_1", "city_2"))
    state = _state_with_factions(country_a=country_a)
    events = [
        WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, tick=99, region_id="city_1", severity=1.0),
    ]

    tension_updates = FactionAwarenessService.compute_tension_updates(state, events)
    propagated = InformationPropagationService.compute_propagation_events(state, events)

    assert len(tension_updates) == 1
    assert tension_updates[0].faction_id == "country_a"
    assert tension_updates[0].tension_delta == 0.1
    # Both services independently read the same recent_events window without interfering.
    assert any(e.region_id == "city_2" for e in propagated)
