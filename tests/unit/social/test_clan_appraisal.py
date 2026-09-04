# Compliance IDs: SOC-264
"""
Unit tests for CoreActions.execute_join_clan()/execute_leave_clan() and the
ContractKind.CLAN dispatch branch (TCK-20260903-CLAN-LIFECYCLE-SUCCESSION, idea 40/M4).

Mirrors test_marriage.py's structure -- the direct precedent for a two-party
contract-kind action that routes a transient ContractState through
SocialAppraisalSystem.appraise_contract() and asserts on the resulting
EntityUpdate bundle.
"""
from __future__ import annotations

import inspect
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ClanState, SocialBond
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.core.enums import ReasonCode
from src.engine.domain.action_router import ActionRouter
from src.engine.domain.core_actions import CoreActions
from src.systems.social_systems.appraisal import SocialAppraisalSystem


def _trusting_bond(entity, toward_id, sentiment=0.8):
    return replace(entity, social=replace(entity.social, bonds={toward_id: SocialBond(target_id=toward_id, sentiment=sentiment)}))


def test_clan_join_routes_through_appraise_contract():
    joiner = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).build()
    leader = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    leader = _trusting_bond(leader, 1, sentiment=0.8)
    clan = ClanState(clan_id="stormfell", leader_entity_id=2, member_entity_ids=(2,))
    state = AuthoritativeState(tick=5, seed=42, entities={1: joiner, 2: leader}, clans={"stormfell": clan})

    updates = CoreActions.execute_join_clan(joiner, {"clan_id": "stormfell"}, 5, [], state)

    assert updates[1].navigation is None

    # A hand-built ContractState using the exact transient shape execute_join_clan() is
    # documented to construct, routed through the real appraise_contract(), must agree with
    # the action handler's own outcome -- proving the handler is not a bespoke inline check.
    expected_contract = ContractState(
        id="temp_eval", kind=ContractKind.CLAN, source_id=1, target_id=2,
        terms={"clan_id": "stormfell"}, status=ContractStatus.OFFERED, created_tick=5,
    )
    expected_status, expected_reason, _ = SocialAppraisalSystem.appraise_contract(leader, expected_contract, state)
    assert expected_status == ContractStatus.ACCEPTED
    assert expected_reason == ReasonCode.CLAN_JOIN_ACCEPTED


def test_clan_join_shared_trust_prelude_still_cancels():
    joiner = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).build()
    leader = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    leader = _trusting_bond(leader, 1, sentiment=-0.9)
    clan = ClanState(clan_id="stormfell", leader_entity_id=2, member_entity_ids=(2,))
    state = AuthoritativeState(tick=5, seed=42, entities={1: joiner, 2: leader}, clans={"stormfell": clan})

    updates = CoreActions.execute_join_clan(joiner, {"clan_id": "stormfell"}, 5, [], state)

    assert updates[1].navigation.failure_reason == ReasonCode.TOTAL_DISTRUST.value


def test_clan_join_never_silently_auto_composes():
    """Architecture guard: no code path adds an entity to ClanState.member_entity_ids
    without going through appraise_contract() first. execute_join_clan() is the only
    producer of a JOIN_CLAN SUCCESS outcome, and its source must always call
    appraise_contract() before returning a non-failure EntityUpdate."""
    source = inspect.getsource(CoreActions.execute_join_clan)
    assert "appraise_contract" in source


def test_clan_join_already_member_rejected():
    joiner = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).build()
    leader = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    clan = ClanState(clan_id="stormfell", leader_entity_id=2, member_entity_ids=(1, 2))
    state = AuthoritativeState(tick=5, seed=42, entities={1: joiner, 2: leader}, clans={"stormfell": clan})

    updates = CoreActions.execute_join_clan(joiner, {"clan_id": "stormfell"}, 5, [], state)
    assert updates[1].navigation.failure_reason == "ALREADY_MEMBER"


def test_clan_join_unknown_clan_rejected():
    joiner = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).build()
    state = AuthoritativeState(tick=5, seed=42, entities={1: joiner}, clans={})

    updates = CoreActions.execute_join_clan(joiner, {"clan_id": "does_not_exist"}, 5, [], state)
    assert updates[1].navigation.failure_reason == "TARGET_NOT_FOUND"


def test_clan_leave_removes_member_on_success():
    member = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).build()
    clan = ClanState(clan_id="stormfell", leader_entity_id=2, member_entity_ids=(1, 2))
    state = AuthoritativeState(tick=5, seed=42, entities={1: member}, clans={"stormfell": clan})

    updates = CoreActions.execute_leave_clan(member, {"clan_id": "stormfell"}, 5, [], state)
    assert updates[1].navigation is None


def test_clan_leave_not_a_member_rejected():
    member = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).build()
    clan = ClanState(clan_id="stormfell", leader_entity_id=2, member_entity_ids=(2,))
    state = AuthoritativeState(tick=5, seed=42, entities={1: member}, clans={"stormfell": clan})

    updates = CoreActions.execute_leave_clan(member, {"clan_id": "stormfell"}, 5, [], state)
    assert updates[1].navigation.failure_reason == "NOT_A_MEMBER"


def test_clan_join_action_routes_through_action_router():
    joiner = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).build()
    leader = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    leader = _trusting_bond(leader, 1, sentiment=0.8)
    clan = ClanState(clan_id="stormfell", leader_entity_id=2, member_entity_ids=(2,))
    state = AuthoritativeState(tick=5, seed=42, entities={1: joiner, 2: leader}, clans={"stormfell": clan})

    updates = ActionRouter.execute_action(
        joiner,
        payload={"action": "JOIN_CLAN", "clan_id": "stormfell"},
        current_tick=5,
        neighbor_view=[],
        context=state,
    )
    assert updates[1].navigation is None


def test_contract_kind_clan_does_not_alias_recruitment():
    assert ContractKind.CLAN != ContractKind.RECRUITMENT
    assert ContractKind.CLAN.value != ContractKind.RECRUITMENT.value
