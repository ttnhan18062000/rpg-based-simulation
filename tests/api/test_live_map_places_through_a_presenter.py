"""D69: the Live Map shows the world's places and real region ids, through a typed presenter read-model, never a raw domain object
(TCK-20261014-THE-LIVE-MAP-SHOWS-PLACES-AND-REGION-IDS-THROUGH-A-PRESENTER-D69, issue #519)."""
from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient

from src.api.presenters.state_presenter import StatePresenter
from src.api.schemas import PlaceReadModel
from src.api.server import create_v2_app
from src.config.profiles import PROD_SMALL
from tests.helpers.scenario import compile_world

KEY = "live-map-places-probe"
SEED = 42
WORLDS = ["sandbox_world", "frontier_living_world"]
PLACE_FIELDS = set(PlaceReadModel.__annotations__)


@pytest.mark.parametrize("world_id", WORLDS)
def test_the_static_read_model_carries_every_compiled_place_under_its_region(world_id):
    state = compile_world(world_id, SEED)
    assert state.places, f"{world_id} authors no places: the test would be vacuous"
    static = StatePresenter.present_static(state)
    presented = {loc["location_id"]: (region["region_id"], loc) for region in static["regions"] for loc in region["locations"]}
    assert set(presented) == set(state.places)
    for place_id, place in state.places.items():
        region_id, loc = presented[place_id]
        assert region_id == place.region_id == loc["region_id"]
        assert loc["location_type"] == place.kind.value.lower()
        assert (loc["x"], loc["y"]) == (int(place.position[0]), int(place.position[1]))
        assert loc["tiles"]["width"] >= 1 and loc["tiles"]["height"] >= 1
        assert loc["name"]


@pytest.mark.parametrize("world_id", WORLDS)
def test_region_ids_come_through_and_no_raw_domain_object_is_exposed(world_id):
    state = compile_world(world_id, SEED)
    static = StatePresenter.present_static(state)
    assert {r["region_id"] for r in static["regions"]} == set(state.regions)
    for region in static["regions"]:
        for loc in region["locations"]:
            assert type(loc) is dict and set(loc) == PLACE_FIELDS
            assert all(isinstance(v, (str, int, float, type(None), dict)) for v in loc.values())  # plain values: no PlaceState, no enum member, no set
            assert type(loc["tiles"]) is dict


def test_a_places_owner_is_its_own_override_else_its_regions_holder():
    from dataclasses import replace

    from src.core.enums import Faction

    state = compile_world("sandbox_world", SEED)
    place = next(iter(state.places.values()))
    region = state.regions[place.region_id]
    held = replace(region, owner_faction_id=int(Faction.HERO_GUILD))
    assert StatePresenter.present_place(replace(place, owner_faction_id=None), held)["owner"] == "hero_guild"
    assert StatePresenter.present_place(replace(place, owner_faction_id=int(Faction.MONSTER_HORDE)), held)["owner"] == "monster_horde"
    assert StatePresenter.present_place(replace(place, owner_faction_id=None), replace(region, owner_faction_id=None))["owner"] is None


def test_a_footprint_is_the_places_tiles_and_a_point_place_is_one_tile():
    from dataclasses import replace

    state = compile_world("sandbox_world", SEED)
    place = next(iter(state.places.values()))
    assert StatePresenter.present_place(replace(place, footprint=None))["tiles"] == {"x": int(place.position[0]), "y": int(place.position[1]), "width": 1, "height": 1}
    assert StatePresenter.present_place(replace(place, footprint=(10, 20, 14, 22)))["tiles"] == {"x": 10, "y": 20, "width": 5, "height": 3}


def test_the_api_static_route_serves_the_places():
    """The route, end to end: /api/v1/static carries the same places the compiled world holds (API schema)."""
    profile = PROD_SMALL.model_copy(update={"api_key_hashes": "probe:" + hashlib.sha256(KEY.encode()).hexdigest()})
    app = create_v2_app(profile, seed=SEED, world_id="sandbox_world")
    compiled = compile_world("sandbox_world", SEED)
    with TestClient(app, headers={"X-API-Key": KEY}) as client:
        static = client.get("/api/v1/static").json()
    served = {loc["location_id"]: loc for region in static["regions"] for loc in region["locations"]}
    assert set(served) == set(compiled.places) and served
    assert all(set(loc) == PLACE_FIELDS for loc in served.values())
    assert all(region["region_id"] for region in static["regions"])
