"""The maintenance-shift counter on a building (EXCH-02, ruling 61: upkeep in work, TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN).

Shape only: the content declaration, the two typed fields on ``BuildingState``, the ``BuildingUpdate`` delta and set, the apply order
(set first, then the delta) and the period reset at the upkeep tick. Counting a paid shift, the derived upkeep and ``nearest_work`` are
later parts of the same ticket.
"""
from __future__ import annotations

import pytest

from src.content.schema import BuildingDefinition
from src.core.enums import Faction
from src.core.state import AuthoritativeState, BuildingState, RegionState
from src.core.treasury import treasury_key
from src.core.updates import BuildingUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence
from src.engine.town_resolution import TownResolutionSystem

HERO = int(Faction.HERO_GUILD)


def _state(done=0, needed=2, tick=40, functional=True):
    region = RegionState(id="town", name="Town", bounds=(0, 0, 20, 20), kind="TOWN", owner_faction_id=HERO, tax_share=0.1)
    inn = BuildingState(id=1, kind="inn", position=(5, 5), functional=functional, maintenance_shifts_needed=needed, maintenance_shifts_done=done)
    return AuthoritativeState(tick=tick, seed=1, regions={"town": region}, buildings={1: inn}, global_resources={treasury_key(HERO): 1000.0})


def test_content_declares_the_shifts_and_an_ordinary_building_needs_one():
    assert BuildingDefinition(id="x", display_name="X").maintenance_shifts == 1
    assert BuildingDefinition(id="x", display_name="X", maintenance_shifts=0).maintenance_shifts == 0
    with pytest.raises(ValueError):
        BuildingDefinition(id="x", display_name="X", maintenance_shifts=-1)


def test_the_catalog_buildings_carry_a_declaration():
    from src.content.paths import ContentPathConfig
    from src.content.repository import CatalogRepository
    repo = CatalogRepository(ContentPathConfig().content_root)
    repo.load_all()
    assert repo.buildings and all(b.maintenance_shifts >= 0 for b in repo.buildings.values())


def test_the_state_fields_default_to_zero_and_are_in_the_canonical_dict_and_the_hash_basis():
    fresh = BuildingState(id=1, kind="inn", position=(5, 5))
    assert (fresh.maintenance_shifts_needed, fresh.maintenance_shifts_done) == (0, 0)
    assert fresh.to_canonical_dict()["maintenance_shifts_needed"] == 0 and fresh.to_canonical_dict()["maintenance_shifts_done"] == 0
    a, b = _state(done=0).buildings[1], _state(done=1).buildings[1]
    assert a.to_canonical_dict() != b.to_canonical_dict()
    assert _state(done=2).buildings[1].to_canonical_dict()["maintenance_shifts_done"] == 2  # round trip: what is stored is what is read


def test_updates_merge_deltas_add_and_the_later_set_wins():
    first = BuildingUpdate(building_id=1, maintenance_shifts_done_delta=1)
    second = BuildingUpdate(building_id=1, maintenance_shifts_done_delta=2, maintenance_shifts_done_set=0)
    merged = first.merge(second)
    assert merged.maintenance_shifts_done_delta == 3 and merged.maintenance_shifts_done_set == 0
    assert second.merge(first).maintenance_shifts_done_set == 0   # a missing set keeps the other's


@pytest.mark.parametrize("done,delta,set_to,expect", [(1, 1, None, 2), (2, 0, 0, 0), (2, 1, 0, 1), (0, 0, None, 0)])
def test_apply_sets_first_then_adds_the_delta(done, delta, set_to, expect):
    state = _state(done=done)
    upd = StateUpdate(building_updates={1: BuildingUpdate(building_id=1, maintenance_shifts_done_delta=delta, maintenance_shifts_done_set=set_to)})
    assert ApplyPath.apply_generation(state, upd).buildings[1].maintenance_shifts_done == expect


def test_the_counter_resets_at_the_upkeep_tick_and_not_on_other_ticks():
    cadence = SystemCadence()
    period = cadence.town_resolution * 2
    at = TownResolutionSystem.resolve(_state(done=2, tick=period * 3), StateUpdate(), cadence=cadence)
    assert at.building_updates[1].maintenance_shifts_done_set == 0
    off = TownResolutionSystem.resolve(_state(done=2, tick=period * 3 + 1), StateUpdate(), cadence=cadence)
    assert 1 not in off.building_updates or off.building_updates[1].maintenance_shifts_done_set is None


def test_the_reset_covers_a_closed_building_and_skips_one_already_at_zero():
    cadence = SystemCadence()
    tick = cadence.town_resolution * 2 * 3
    closed = TownResolutionSystem.resolve(_state(done=1, tick=tick, functional=False), StateUpdate(), cadence=cadence)
    assert closed.building_updates[1].maintenance_shifts_done_set == 0
    zero = TownResolutionSystem.resolve(_state(done=0, tick=tick), StateUpdate(), cadence=cadence)
    assert 1 not in zero.building_updates or zero.building_updates[1].maintenance_shifts_done_set is None


def test_the_compiler_copies_the_declaration_to_the_building():
    from tests.helpers.scenario import compile_world, DEFAULT_SEED
    state = compile_world("urban_political", DEFAULT_SEED) if callable(compile_world) else None
    assert state is not None and state.buildings
    assert all(b.maintenance_shifts_needed >= 0 for b in state.buildings.values())
    assert any(b.maintenance_shifts_needed >= 1 for b in state.buildings.values())
