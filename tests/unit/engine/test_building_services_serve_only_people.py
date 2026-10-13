"""Owner decision 43 / memo row 43 (EXCH-02): a building service (meal, bed, sale, repair) serves a subject only if its species declares
``keeps_coin_and_trades`` and the place's controlling faction is not hostile to it. One predicate (`engine.serves.serves`), read from the trait and
the relationship, never from a kind name, applied where the building is found (`building_services.service_building`), so every route shares it.

The charge is still clamped at what the subject holds (the free meal): its removal is M0 step 4 (TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-
THAT-CANNOT-PAY-FREE-MEAL), measured alone against baseline v1, so it is not tested here.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, BuildingState, RegionState
from src.engine.building_services import SERVICE_KINDS, service_building, service_delta


def _world(species_id, faction_id=None, region_owner=None, gold=20, kind="inn"):
    props = {"species_id": species_id, **({"faction_id": faction_id} if faction_id else {})}
    ent = V2EntityBuilder(1).kind("worker").properties(props).location(5.0, 5.0).inventory(gold=gold).build()
    buildings = {10: BuildingState(id=10, kind=kind, position=(5.0, 5.0), functional=True)}
    regions = {} if region_owner is None else {"r": RegionState(id="r", name="r", bounds=(0, 0, 20, 20), owner_faction_id=int(region_owner))}
    state = AuthoritativeState(tick=1, seed=1, entities={1: ent}, town_tiles={(5, 5)}, building_tiles={(5, 5): kind}, buildings=buildings, regions=regions)
    return state, ent


@pytest.mark.parametrize("action", ["REST", "EAT"])
def test_a_trading_person_is_served(action):
    state, ent = _world("human")
    assert service_building(state, ent, action) is not None
    assert service_delta(state, ent, action, 1) is not None


@pytest.mark.parametrize("species", ["small_plant_eater", "wolf"])
@pytest.mark.parametrize("action", ["REST", "EAT"])
def test_an_animal_on_an_inn_tile_is_not_served(species, action):
    state, ent = _world(species)
    assert service_building(state, ent, action) is None
    assert service_delta(state, ent, action, 1) is None


@pytest.mark.parametrize("action", sorted(SERVICE_KINDS))
def test_an_animal_is_refused_every_service_route(action):
    kind = sorted(SERVICE_KINDS[action])[0]
    state, ent = _world("small_plant_eater", kind=kind)
    assert service_building(state, ent, action) is None
    person, pent = _world("human", kind=kind)
    assert service_building(person, pent, action) is not None  # the same building serves a person


def test_the_place_relationship_is_not_read_by_rest_or_meal():
    """Trait-only variant: a person in a hostile-owned region is still served rest and meals (the relationship half is its own ticket)."""
    state, ent = _world("human", faction_id="town_council", region_owner=Faction.MONSTER_HORDE)
    assert service_building(state, ent, "REST") is not None
