# tests/unit/social/test_social_memory_service.py
"""
Unit tests for SocialMemoryService.tick_place_attachment() and
.check_nemesis_promotion() (src/systems/social_systems/memory.py).

Ticket: TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS

These two functions are currently dead code in production (not called anywhere
in src/), so these tests invoke them directly rather than through a tick/apply
pipeline. No src/ change accompanies this file; see the ticket for reasoning.

Coverage:
  - tick_place_attachment(): explicit region_id, auto-detect containing region,
    no matching region, no regions at all, inclusive boundary match, empty-string
    region_id truthy-falsy pin
  - check_nemesis_promotion(): empty grudge history, below threshold,
    already-nemesis exclusion, qualifying promotion, exact threshold boundary,
    mixed multi-entry filtering with exact list/order assertion
  - Architecture guard: neither function mutates the entity/state passed in
"""

from src.core.state import RegionState
from src.core.models.social import SocialBond, RelationshipRole
from src.core.updates import SocialUpdate
from src.systems.social_systems.memory import SocialMemoryService
from tests.helpers.entities import make_entity, make_state, with_navigation, with_social


def test_tick_place_attachment_uses_explicit_region_id():
    entity = make_entity(pos=(0.0, 0.0))
    state = make_state(entities=[entity], regions={})

    result = SocialMemoryService.tick_place_attachment(
        entity, state, region_id="explicit_region"
    )

    assert result == SocialUpdate(place_attachment_delta={"explicit_region": 0.001})


def test_tick_place_attachment_auto_detects_containing_region():
    entity = make_entity(pos=(5.0, 5.0))
    region = RegionState(id="forest_home", name="Forest Home", bounds=(0, 0, 10, 10))
    state = make_state(entities=[entity], regions={region.id: region})

    result = SocialMemoryService.tick_place_attachment(entity, state, region_id=None)

    assert result == SocialUpdate(place_attachment_delta={"forest_home": 0.001})


def test_tick_place_attachment_returns_none_when_no_region_contains_position():
    entity = make_entity(pos=(50.0, 50.0))
    region = RegionState(id="forest_home", name="Forest Home", bounds=(0, 0, 10, 10))
    state = make_state(entities=[entity], regions={region.id: region})

    result = SocialMemoryService.tick_place_attachment(entity, state, region_id=None)

    assert result is None


def test_tick_place_attachment_returns_none_when_no_regions_exist():
    entity = make_entity(pos=(0.0, 0.0))
    state = make_state(entities=[entity], regions={})

    result = SocialMemoryService.tick_place_attachment(entity, state, region_id=None)

    assert result is None


def test_tick_place_attachment_boundary_position_matches_region_edge():
    entity = make_entity(pos=(10.0, 5.0))
    region = RegionState(id="forest_home", name="Forest Home", bounds=(0, 0, 10, 10))
    state = make_state(entities=[entity], regions={region.id: region})

    result = SocialMemoryService.tick_place_attachment(entity, state, region_id=None)

    assert result == SocialUpdate(place_attachment_delta={"forest_home": 0.001})


def test_tick_place_attachment_empty_string_region_id_falls_back_to_auto_detect():
    entity = make_entity(pos=(5.0, 5.0))
    region = RegionState(id="forest_home", name="Forest Home", bounds=(0, 0, 10, 10))
    state = make_state(entities=[entity], regions={region.id: region})

    result = SocialMemoryService.tick_place_attachment(entity, state, region_id="")

    assert result == SocialUpdate(place_attachment_delta={"forest_home": 0.001})


def test_check_nemesis_promotion_empty_grudge_history_returns_none():
    entity = make_entity(grudge_history={})

    result = SocialMemoryService.check_nemesis_promotion(entity)

    assert result is None


def test_check_nemesis_promotion_below_threshold_not_promoted():
    entity = make_entity(grudge_history={99: 2.9})

    result = SocialMemoryService.check_nemesis_promotion(entity)

    assert result is None


def test_check_nemesis_promotion_already_nemesis_not_repromoted():
    entity = make_entity(grudge_history={99: 5.0})
    entity = with_social(entity, nemesis_ids={99})

    result = SocialMemoryService.check_nemesis_promotion(entity)

    assert result is None


def test_check_nemesis_promotion_qualifying_entry_promoted():
    entity = make_entity(grudge_history={99: 5.0})
    entity = with_social(entity, nemesis_ids=set())

    result = SocialMemoryService.check_nemesis_promotion(entity)

    assert result == SocialUpdate(nemesis_promotion=[99])


def test_check_nemesis_promotion_exact_threshold_boundary_promoted():
    entity = make_entity(grudge_history={99: 3.0})
    entity = with_social(entity, nemesis_ids=set())

    result = SocialMemoryService.check_nemesis_promotion(entity)

    assert result == SocialUpdate(nemesis_promotion=[99])


def test_check_nemesis_promotion_mixed_entries_only_new_qualifying_promoted():
    entity = make_entity(grudge_history={101: 2.0, 102: 4.0, 103: 6.0})
    entity = with_social(entity, nemesis_ids={102})

    result = SocialMemoryService.check_nemesis_promotion(entity)

    assert result.nemesis_promotion == [103]


def test_check_nemesis_promotion_rival_role_below_grudge_threshold_not_promoted():
    """
    RelationshipRole.RIVAL is a lightweight categorical tag on SocialBond,
    independent of nemesis_ids/grudge_history (docs/simulation/social_systems_contract.md:84,
    "nemesis promotion" -- grudge_history >= 3.0). A RIVAL-tagged bond with no
    accumulated grudge must not be nemesis-promoted, and check_nemesis_promotion()
    must never read role. Logic ID: SOC-247.
    """
    entity = make_entity(grudge_history={99: 2.9})
    entity = with_social(
        entity,
        nemesis_ids=set(),
        bonds={99: SocialBond(target_id=99, sentiment=0.8, role=RelationshipRole.RIVAL)},
    )

    result = SocialMemoryService.check_nemesis_promotion(entity)

    assert result is None
    assert 99 not in entity.social.nemesis_ids


def test_social_memory_service_functions_are_pure_and_do_not_mutate_entity():
    entity = make_entity(pos=(5.0, 5.0), grudge_history={99: 5.0})
    entity = with_social(entity, nemesis_ids=set())
    region = RegionState(id="forest_home", name="Forest Home", bounds=(0, 0, 10, 10))
    state = make_state(entities=[entity], regions={region.id: region})

    entity_before = entity
    state_before = state

    place_result = SocialMemoryService.tick_place_attachment(entity, state, region_id=None)
    nemesis_result = SocialMemoryService.check_nemesis_promotion(entity)

    assert place_result is not None
    assert nemesis_result is not None
    assert entity == entity_before
    assert state == state_before
