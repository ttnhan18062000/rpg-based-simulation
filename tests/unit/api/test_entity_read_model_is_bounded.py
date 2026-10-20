"""The entity read model does not grow with an entity's age (TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL).

An entity piles up finished records for its whole life: terminal quests, resolved blockers, closed contracts. The list model carries counts only; the detail model carries
the live records and the newest few finished ones; the full quest history is a paged sub-resource. These tests pin the payload CEILINGS an aged entity must stay under,
measured on the serialised bytes (the unit the platform SLO measures), and that nothing is lost: the counts and the paged history are exact.
"""
from __future__ import annotations

import json

import pytest

from src.api.presenters.state_presenter import (
    DETAIL_CLOSED_CONTRACTS,
    DETAIL_TERMINAL_QUESTS,
    MAX_ENTITY_PAGE,
    StatePresenter,
    present_entity_quests,
)
from src.api.read_model_cache import ReadModelCache
from tests.helpers.aged_entity import aged_entity

SUMMARY_CEILING_BYTES = 1_024  # one list row, however old the entity
DETAIL_CEILING_BYTES = 8_192  # one detail model: live records plus the capped tail, however old the entity
AGES = (0, 10, 500)


def _size(dto) -> int:
    return len(json.dumps(dto))


@pytest.mark.parametrize("age", AGES)
def test_the_summary_is_under_its_ceiling_at_every_age_and_does_not_grow_with_it(age):
    young = _size(StatePresenter.present_entity_summary(aged_entity()))
    aged = _size(StatePresenter.present_entity_summary(aged_entity(terminal_quests=age, resolved_blockers=age, closed_contracts=age)))
    assert aged <= SUMMARY_CEILING_BYTES
    assert aged - young <= 16, f"only a few count digits may differ between a young and a {age}-record entity, not {aged - young} bytes"


@pytest.mark.parametrize("age", AGES)
def test_the_detail_is_under_its_ceiling_at_every_age(age):
    detail = StatePresenter.present_entity(aged_entity(terminal_quests=age, resolved_blockers=age, closed_contracts=age, item_properties=0))
    assert _size(detail) <= DETAIL_CEILING_BYTES


def test_the_detail_keeps_every_live_record_and_the_newest_finished_ones_and_counts_the_rest():
    entity = aged_entity(terminal_quests=500, resolved_blockers=500, closed_contracts=500, live_quests=2, unresolved_blockers=2, open_contracts=1)
    detail = StatePresenter.present_entity(entity)
    quests = detail["quests"]
    assert detail["quests_total"] == 502
    assert [q["id"] for q in quests if q["live"]] == ["q_live_1", "q_live_0"]  # every live quest, newest first
    finished = [q for q in quests if not q["live"]]
    assert len(finished) == DETAIL_TERMINAL_QUESTS
    assert [q["created_tick"] for q in finished] == sorted((q["created_tick"] for q in finished), reverse=True)
    assert finished[0]["id"] == "q_done_499"  # the newest finished quest
    strategic = detail["strategic"]
    assert len(strategic["blockers"]) == 2 and strategic["blockers_resolved_count"] == 500  # unresolved in full, the rest counted
    assert strategic["contracts_total"] == 501 and len(strategic["contracts"]) == 1 + DETAIL_CLOSED_CONTRACTS


def test_the_summary_counts_are_exact():
    counts = StatePresenter.present_entity_summary(aged_entity(terminal_quests=40, resolved_blockers=30, closed_contracts=20, live_quests=3, unresolved_blockers=2, open_contracts=1))["counts"]
    assert counts == {"quests_live": 3, "quests_total": 43, "projects": 43, "blockers_open": 2, "contracts_open": 1}


def test_the_paged_quest_history_returns_everything_newest_first_and_filters_by_status():
    entity = aged_entity(terminal_quests=60, live_quests=2)
    everything = []
    offset = 0
    while True:
        page = present_entity_quests(entity, "all", offset, 25)
        assert page["total"] == 62 and page["offset"] == offset
        everything += page["quests"]
        offset += 25
        if offset >= page["total"]:
            break
    assert len(everything) == 62 and len({q["id"] for q in everything}) == 62
    ticks = [q["created_tick"] for q in everything]
    assert ticks == sorted(ticks, reverse=True)
    assert present_entity_quests(entity, "live")["total"] == 2 and present_entity_quests(entity, "terminal")["total"] == 60
    assert all(q["live"] for q in present_entity_quests(entity, "live")["quests"])


def test_a_page_never_returns_more_than_the_page_ceiling_whatever_limit_asks_for():
    entity = aged_entity(terminal_quests=MAX_ENTITY_PAGE + 100)
    assert len(present_entity_quests(entity, "all", 0, 10 * MAX_ENTITY_PAGE)["quests"]) == MAX_ENTITY_PAGE
    assert present_entity_quests(entity, "all", -5, -1)["limit"] == 0 and present_entity_quests(entity, "all", -5, 1)["offset"] == 0


def test_the_list_builds_summaries_and_the_detail_cache_is_separate():
    from types import SimpleNamespace

    entities = {i: aged_entity(entity_id=i, terminal_quests=50) for i in (1, 2, 3)}
    state = SimpleNamespace(entities=entities)
    cache = ReadModelCache()
    page = cache.get_entities_paged(state, 0, 10)
    assert [e["id"] for e in page["entities"]] == [1, 2, 3] and page["total"] == 3
    assert all("quests" not in e and "counts" in e for e in page["entities"]), "the list carries the summary model"
    assert not cache._entity_dtos, "building a page must not build or cache the heavy detail"
    detail = cache.get_entity_dto(entities[1])
    assert "quests" in detail and 1 in cache._entity_dtos and 1 in cache._entity_summaries
    cache.get_entities_paged(state, 0, 10)
    assert cache._hits >= 3, "a second page is served from the summary cache"
    cache.clear()
    assert not cache._entity_dtos and not cache._entity_summaries
