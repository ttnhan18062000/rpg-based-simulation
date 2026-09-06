"""Idea 44 (Settlement Capacity) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS).

CORRECTION, found during Investigate: `settlement_capacity`/`FULL_SETTLEMENT`/`CAMP_ONLY` do not
exist as real identifiers anywhere in `src/` -- confirmed via grep, zero hits. The real,
already-shipped classification mechanism is `PlaceKind` (idea 66,
src/core/state.py:329-337: CITY/CAMP/NEST/LAIR/RUIN/DUNGEON/LANDMARK).

SECOND CORRECTION, found by actually running the real compiler: `WorldCompiler.compile()` DOES
construct a real `Place(kind=CAMP)` for `goblin_camp_conflict`'s region -- refining the epic doc's
own stronger "constructs no Place at all" phrasing. What the doc's caveat gets right: that Place's
`maturity` field (the real CampState-machinery marker, only populated when the underlying content
opts into `creature_kind`) stays `None` -- a CAMP-kind Place classification exists, but no live
`CampState` machinery backs it. The real settlement/non-settlement split this test proves is: a real, named
`Place(kind=CITY)` for `frontier_village_core`'s own settlement, versus `Place(kind=CAMP)` with
`maturity=None` (no live Camp machinery) for `goblin_camp`. `building_ids`/`entity_ids` are
populated later, at spawn/build-assembly time, not by `WorldCompiler.compile()` itself -- not
asserted on here.
"""
from __future__ import annotations

from src.core.state import PlaceKind
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository


def test_frontier_village_core_region_has_a_real_populated_city_place():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("hero_guild_routing")
    state, _ = WorldCompiler.compile(spec, seed=42)

    city_places = [p for p in state.places.values() if p.kind == PlaceKind.CITY]
    assert city_places, "hero_guild_routing must compile at least one real Place(kind=CITY)"
    assert any(p.place_id == "hometown_city" for p in city_places), (
        f"expected frontier_village_core's own hometown_city CITY Place, got "
        f"place_ids={[p.place_id for p in city_places]}"
    )


def test_goblin_camp_region_has_no_live_campstate_machinery():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("hero_guild_routing")
    state, _ = WorldCompiler.compile(spec, seed=42)

    camp_places = [p for p in state.places.values() if p.kind == PlaceKind.CAMP]
    assert camp_places, "hero_guild_routing must compile a real Place(kind=CAMP) for goblin_camp"
    assert all(p.maturity is None for p in camp_places), (
        "goblin_camp_conflict never opts into creature_kind, so its Place(kind=CAMP) must carry no "
        "real CampState-machinery maturity value -- a real, observable non-settlement split from "
        "the fully-populated CITY Place above, without inventing settlement_capacity/"
        "FULL_SETTLEMENT/CAMP_ONLY, which do not exist"
    )
