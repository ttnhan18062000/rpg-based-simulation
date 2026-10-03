"""Global tick-cadence raid spawns at a real settlement, not the world origin.

TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION.

`RaidService.check_for_raid` used to pass `origin=(0, 0), target=(0, 0)` literally, so raiders
landed on the radius-25 ring around the world origin -- outside every region in any world whose
regions do not straddle (0,0), where they sat inert for the rest of the run.
"""
import math

import pytest

from src.core.state import AuthoritativeState, RegionState, PlaceState, PlaceKind
from src.world.raid import RaidService
from src.systems.world_systems.generator import EntityGenerator


def _state_with_far_city(tick, *, with_city=True):
    """A world whose only region and city sit far from (0,0).

    Bounds deliberately exclude the origin, so an origin-anchored spawn is detectable as
    "outside every region" rather than merely "in an odd spot".
    """
    region = RegionState(
        id="hometown", name="Hometown", bounds=(100, 100, 160, 160),
        influence=0.0, owner_faction_id=None,
    )
    places = {}
    if with_city:
        places["city_1"] = PlaceState(
            place_id="city_1", region_id="hometown", kind=PlaceKind.CITY,
            position=(130.0, 130.0),
        )
    return AuthoritativeState(
        tick=tick, seed=42, entities={}, regions={"hometown": region}, places=places,
    )


def _raid_tick():
    return RaidService.RAID_INTERVAL_DAYS * RaidService.TICKS_PER_DAY


def _in_any_region(pos, state):
    for r in state.regions.values():
        x0, y0, x1, y1 = r.bounds
        if x0 <= pos[0] <= x1 and y0 <= pos[1] <= y1:
            return True
    return False


def test_global_raid_spawns_near_a_city_not_at_world_origin():
    """Raiders spawn on the chosen city's outskirts and target it.

    Logic ID: WORLD-032 (Raids)
    """
    state = _state_with_far_city(_raid_tick())
    update = RaidService.check_for_raid(state, EntityGenerator(seed=42))

    assert update.entities_add, "the raid did not fire on its cadence tick"

    city = state.places["city_1"].position
    ring = RaidService.SANCTUARY_RADIUS + 10
    for mob in update.entities_add:
        pos = mob.navigation.position
        # Not anchored to the world origin any more.
        assert math.hypot(pos[0], pos[1]) > ring, (
            f"raider spawned {pos} -- still anchored to the world origin"
        )
        # On the chosen city's outskirts: the ring radius, plus the +/-1 scatter grid.
        d = math.hypot(pos[0] - city[0], pos[1] - city[1])
        assert abs(d - ring) <= 2.0, f"raider at {pos} is {d:.1f} from the city, expected ~{ring}"
        # And it is actually going there.
        assert mob.navigation.target == city


def test_global_raid_raiders_land_inside_a_region():
    """AC-3: a freshly spawned raider is inside the playable world.

    The measured defect was 12 raiders at region_id=None, outside every region, inert for the
    rest of the run.
    """
    state = _state_with_far_city(_raid_tick())
    update = RaidService.check_for_raid(state, EntityGenerator(seed=42))

    assert update.entities_add
    outside = [m.navigation.position for m in update.entities_add
               if not _in_any_region(m.navigation.position, state)]
    assert not outside, f"raiders spawned outside every region: {outside}"


def test_global_raid_falls_back_to_a_region_when_no_city_exists():
    """With no city, the raid still fires and anchors on a region centre.

    Deliberately a placement fix, not a frequency one: requiring a city would suppress raids
    entirely in city-less worlds, which regressed test_phase9_stability::test_1000_tick_stability.
    """
    state = _state_with_far_city(_raid_tick(), with_city=False)
    update = RaidService.check_for_raid(state, EntityGenerator(seed=42))

    assert update.entities_add, "raid frequency changed -- it must still fire without a city"
    centre = state.regions["hometown"].center
    for mob in update.entities_add:
        assert mob.navigation.target == centre


def test_global_raid_does_not_fire_with_nowhere_to_raid():
    """No city and no region means no anchor, so no raid spawns into empty space."""
    state = AuthoritativeState(tick=_raid_tick(), seed=42, entities={}, regions={}, places={})
    update = RaidService.check_for_raid(state, EntityGenerator(seed=42))
    assert not update.entities_add


def test_global_raid_city_choice_is_deterministic():
    """Same seed and tick must choose the same city, twice."""
    a = RaidService.check_for_raid(_state_with_far_city(_raid_tick()), EntityGenerator(seed=42))
    b = RaidService.check_for_raid(_state_with_far_city(_raid_tick()), EntityGenerator(seed=42))
    assert [m.navigation.position for m in a.entities_add] == \
           [m.navigation.position for m in b.entities_add]
    assert [m.navigation.target for m in a.entities_add] == \
           [m.navigation.target for m in b.entities_add]


def test_city_places_is_sorted_and_filters_non_cities():
    """The shared raidable-settlement definition: cities only, stable id order."""
    state = _state_with_far_city(_raid_tick())
    extra = dict(state.places)
    extra["city_0"] = PlaceState(
        place_id="city_0", region_id="hometown", kind=PlaceKind.CITY, position=(110.0, 110.0))
    from dataclasses import replace as _replace
    state = _replace(state, places=extra)

    cities = RaidService.city_places(state)
    assert [c.place_id for c in cities] == ["city_0", "city_1"]
    assert all(c.kind == PlaceKind.CITY for c in cities)


def test_global_raid_still_gated_by_cadence():
    """Unchanged: no raid off the cadence tick, and none at tick 0."""
    assert not RaidService.check_for_raid(
        _state_with_far_city(_raid_tick() + 1), EntityGenerator(seed=42)).entities_add
    assert not RaidService.check_for_raid(
        _state_with_far_city(0), EntityGenerator(seed=42)).entities_add
