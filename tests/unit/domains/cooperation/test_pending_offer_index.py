"""TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK.

`find_pending_incoming_offer` used to scan every entity's contracts once per entity per tick (O(N^2 log N)).
It now reads a per-tick index built once. These tests pin the choice the index must reproduce (the ordering
contract), compare it with the original scan on seeded random worlds, and check the phase builds it once.
"""
from __future__ import annotations

import random
from dataclasses import replace
from unittest import mock

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.domains.cooperation import phase as phase_module
from src.domains.cooperation.phase import CooperationPhase
from src.domains.cooperation.services import CooperationDecisionService, build_pending_offer_index
from src.core.updates import StateUpdate


def _offer(contract_id, source_id, target_id, *, kind=ContractKind.RECRUITMENT, status=ContractStatus.OFFERED,
           expiry_tick=100):
    return ContractState(
        id=contract_id, kind=kind, source_id=source_id, target_id=target_id,
        terms={"daily_pay": 0, "duration": 100}, status=status, created_tick=1, expiry_tick=expiry_tick,
    )


def _entity(entity_id, contracts=(), *, alive=True, active=True, group_id=None):
    builder = V2EntityBuilder(entity_id).kind("HERO").location(float(entity_id), 0.0)
    if group_id is not None:
        builder = builder.identity(group_id=group_id)
    entity = builder.build()
    entity = replace(entity, strategic=replace(entity.strategic, contracts={c.id: c for c in contracts}))
    if not alive:
        entity = replace(entity, combat=replace(entity.combat, alive=False, hp=0))
    if not active:
        entity = replace(entity, lifecycle=replace(entity.lifecycle, active=False))
    return entity


def _state(entities, tick=10):
    return AuthoritativeState(entities={e.id: e for e in entities}, tick=tick, seed=1)


def _reference_scan(entity, state):
    """The pre-index implementation, kept verbatim as the oracle."""
    if entity.identity.group_id is not None:
        return None
    for offerer_id in sorted(state.entities.keys()):
        if offerer_id == entity.id:
            continue
        offerer = state.entities[offerer_id]
        if not offerer.lifecycle.active or not offerer.combat.alive:
            continue
        for c_id in sorted(offerer.strategic.contracts.keys()):
            contract = offerer.strategic.contracts[c_id]
            if (
                contract.kind == ContractKind.RECRUITMENT
                and contract.status == ContractStatus.OFFERED
                and contract.target_id == entity.id
                and (contract.expiry_tick <= 0 or contract.expiry_tick > state.tick)
            ):
                return offerer_id, c_id
    return None


def test_several_offers_to_one_target_resolve_to_lowest_offerer_then_lowest_contract_id():
    target = _entity(2)
    # offerer 9 and 5 are inserted before 3 on purpose: the choice must not depend on insertion order.
    offerer_9 = _entity(9, [_offer("a_9", 9, 2)])
    offerer_5 = _entity(5, [_offer("a_5", 5, 2)])
    offerer_3 = _entity(3, [_offer("b_3", 3, 2), _offer("a_3", 3, 2), _offer("c_3", 3, 2)])
    state = _state([offerer_9, target, offerer_5, offerer_3])

    assert CooperationDecisionService.find_pending_incoming_offer(target, state) == (3, "a_3")
    assert build_pending_offer_index(state)[2] == (3, "a_3")


def test_ordering_falls_through_to_the_next_offerer_when_the_lowest_is_not_live():
    target = _entity(2)
    dead = _entity(1, [_offer("x", 1, 2)], alive=False)
    inactive = _entity(3, [_offer("x", 3, 2)], active=False)
    expired = _entity(4, [_offer("x", 4, 2, expiry_tick=9)])
    accepted = _entity(5, [_offer("x", 5, 2, status=ContractStatus.ACTIVE)])
    other_kind = _entity(6, [_offer("x", 6, 2, kind=ContractKind.LOAN)])
    live = _entity(7, [_offer("x", 7, 2)])
    state = _state([dead, target, inactive, expired, accepted, other_kind, live])

    assert CooperationDecisionService.find_pending_incoming_offer(target, state) == (7, "x")


def test_a_self_addressed_offer_is_never_returned_but_does_not_hide_another_offerer():
    target = _entity(2, [_offer("self", 2, 2)])
    other = _entity(8, [_offer("x", 8, 2)])
    state = _state([target, other])

    assert CooperationDecisionService.find_pending_incoming_offer(target, state) == (8, "x")
    assert build_pending_offer_index(_state([target])).get(2) is None


def test_an_entity_already_in_a_group_gets_no_offer_even_with_an_index():
    target = _entity(2, group_id=99)
    state = _state([_entity(1, [_offer("x", 1, 2)]), target])

    assert CooperationDecisionService.find_pending_incoming_offer(target, state, build_pending_offer_index(state)) is None


def test_a_zero_expiry_offer_never_expires():
    target = _entity(2)
    state = _state([_entity(1, [_offer("x", 1, 2, expiry_tick=0)]), target], tick=10_000)

    assert CooperationDecisionService.find_pending_incoming_offer(target, state) == (1, "x")


@pytest.mark.parametrize("seed", range(40))
def test_index_matches_the_original_scan_on_random_worlds(seed):
    rng = random.Random(seed)
    ids = list(range(1, 25))
    entities = []
    for entity_id in ids:
        contracts = []
        for n in range(rng.randint(0, 3)):
            contracts.append(_offer(
                f"c{rng.randint(0, 5)}_{n}", entity_id, rng.choice(ids),
                kind=rng.choice([ContractKind.RECRUITMENT, ContractKind.RECRUITMENT, ContractKind.LOAN]),
                status=rng.choice([ContractStatus.OFFERED, ContractStatus.OFFERED, ContractStatus.ACTIVE]),
                expiry_tick=rng.choice([0, 5, 10, 11, 50]),
            ))
        entities.append(_entity(
            entity_id, contracts, alive=rng.random() > 0.15, active=rng.random() > 0.15,
            group_id=7 if rng.random() < 0.15 else None,
        ))
    rng.shuffle(entities)
    state = _state(entities, tick=10)
    index = build_pending_offer_index(state)

    for entity in state.entities.values():
        expected = _reference_scan(entity, state)
        assert CooperationDecisionService.find_pending_incoming_offer(entity, state, index) == expected, entity.id
        assert CooperationDecisionService.find_pending_incoming_offer(entity, state) == expected, entity.id


def test_building_the_index_does_not_change_the_state():
    entities = [_entity(1, [_offer("x", 1, 2)]), _entity(2)]
    state = _state(entities)
    before = {eid: e.strategic.contracts for eid, e in state.entities.items()}

    build_pending_offer_index(state)

    assert {eid: e.strategic.contracts for eid, e in state.entities.items()} == before


def test_the_phase_builds_the_index_once_per_tick_not_once_per_entity():
    entities = [_entity(i) for i in range(1, 41)]
    entities[0] = _entity(1, [_offer("x", 1, 2)])
    state = _state(entities)

    with mock.patch.object(phase_module, "build_pending_offer_index", wraps=build_pending_offer_index) as spy:
        CooperationPhase.execute(state, StateUpdate())

    assert spy.call_count == 1
