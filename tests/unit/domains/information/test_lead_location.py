"""
tests/unit/domains/information/test_lead_location.py

TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING

Unit tests for resolve_location_lead_region_id() -- the single, sanctioned way
to read a real region out of a kind="location" lead's own `detail`.
"""

import logging

import pytest

from src.core.state import AuthoritativeState, RegionState
from src.core.strategic import LeadState, LeadCertainty
from src.domains.information.lead_location import resolve_location_lead_region_id


def _state(regions=None) -> AuthoritativeState:
    return AuthoritativeState(
        tick=1, seed=1, world_time=100, entities={},
        groups={}, regions=regions or {}, resource_nodes={}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=(),
        building_tiles=(), terrain=(), home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=(), town_entity_ids=(),
    )


def _lead(detail):
    return LeadState(
        id="lead_1", kind="location", subject="moon_resin", detail=detail,
        certainty=LeadCertainty.VAGUE,
    )


def test_resolves_coordinate_detail_to_containing_region():
    region = RegionState(id="north_ruin", name="North Ruin", bounds=(0, 0, 100, 100))
    state = _state(regions={"north_ruin": region})

    result = resolve_location_lead_region_id(_lead("45,12"), state)

    assert result == "north_ruin"


def test_returns_none_for_coordinate_outside_every_region():
    region = RegionState(id="north_ruin", name="North Ruin", bounds=(0, 0, 100, 100))
    state = _state(regions={"north_ruin": region})

    result = resolve_location_lead_region_id(_lead("500,500"), state)

    assert result is None


def test_returns_none_and_warns_for_non_coordinate_detail(caplog):
    state = _state()

    with caplog.at_level(logging.WARNING):
        result = resolve_location_lead_region_id(_lead("bandit_road"), state)

    assert result is None
    assert any("non-coordinate detail" in r.message for r in caplog.records)


def test_returns_none_for_empty_detail():
    state = _state()

    result = resolve_location_lead_region_id(_lead(""), state)

    assert result is None
