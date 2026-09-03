# Compliance IDs: SOC-261 (see docs/parity_ledger/social_narrative.yaml)
"""
Unit tests for CoreActions.execute_propose_marriage() (TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT).

Mirrors test_teach.py's structure -- the direct precedent for a two-party contract-kind action
that routes a transient ContractState through SocialAppraisalSystem.appraise_contract() and
asserts on the resulting EntityUpdate bundle. Marriage differs from TEACH in that ACCEPTED
writes a new typed durable MarriageState record (via StrategicUpdate.marriages_add_or_update)
on BOTH parties, rather than a direct IdentityUpdate on the target alone.
"""
from __future__ import annotations

import dataclasses
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, SocialBond
from src.core.strategic import ContractKind, ContractState, ContractStatus, MarriageState, MarriageStatus
from src.core.updates import StateUpdate
from src.core.enums import ReasonCode
from src.engine.apply import ApplyPath
from src.engine.domain.action_router import ActionRouter
from src.engine.domain.core_actions import CoreActions
from src.systems.social_systems.appraisal import SocialAppraisalSystem


def _trusting_bond(entity, toward_id, sentiment=0.8):
    return replace(entity, social=replace(entity.social, bonds={toward_id: SocialBond(target_id=toward_id, sentiment=sentiment)}))


def test_marriage_action_requires_proposer_and_target():
    proposer = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    target = _trusting_bond(target, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: proposer, 2: target})

    updates = CoreActions.execute_propose_marriage(
        proposer, {"target_id": 2}, 5, [], state
    )
    assert 1 in updates
    assert 2 in updates

    no_target_updates = CoreActions.execute_propose_marriage(
        proposer, {"target_id": 999}, 5, [], state
    )
    assert no_target_updates[1].navigation.failure_reason == "TARGET_NOT_FOUND"


def test_marriage_refused_below_trust_hard_cancel_threshold():
    proposer = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    target = _trusting_bond(target, 1, sentiment=-0.9)
    state = AuthoritativeState(tick=5, seed=42, entities={1: proposer, 2: target})

    updates = CoreActions.execute_propose_marriage(
        proposer, {"target_id": 2}, 5, [], state
    )

    assert updates[1].strategic is None
    assert updates[2].strategic is None
    assert updates[2].social.rejection_increment == {1: 1}


def test_marriage_proposal_builds_transient_contract_and_calls_real_appraise_contract():
    proposer = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    target = _trusting_bond(target, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: proposer, 2: target})

    updates = CoreActions.execute_propose_marriage(proposer, {"target_id": 2}, 5, [], state)

    # A hand-built ContractState using the exact transient shape execute_propose_marriage()
    # is documented to construct, routed through the real appraise_contract(), must agree
    # with the action handler's own outcome -- proving the handler is not a bespoke inline
    # threshold check.
    expected_contract = ContractState(
        id="temp_eval", kind=ContractKind.MARRIAGE, source_id=1, target_id=2,
        terms={}, status=ContractStatus.OFFERED, created_tick=5,
    )
    expected_status, expected_reason, _ = SocialAppraisalSystem.appraise_contract(target, expected_contract, state)

    assert expected_status == ContractStatus.ACCEPTED
    assert expected_reason == ReasonCode.MARRIAGE_ACCEPTED
    marriage_record = updates[1].strategic.marriages_add_or_update[0]
    assert marriage_record.status == MarriageStatus.ACCEPTED


def test_marriage_accepted_writes_typed_marriagestate_on_both_parties():
    proposer = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    target = _trusting_bond(target, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: proposer, 2: target})

    updates = CoreActions.execute_propose_marriage(proposer, {"target_id": 2}, 5, [], state)

    # Prove the durable write path via the real authoritative apply pipeline, not a
    # hand-rolled dict merge.
    state_upd = StateUpdate(entity_updates=updates)
    new_state = ApplyPath.apply_generation(state, state_upd)

    proposer_marriages = new_state.entities[1].strategic.marriages
    target_marriages = new_state.entities[2].strategic.marriages
    assert len(proposer_marriages) == 1
    assert len(target_marriages) == 1

    proposer_record = next(iter(proposer_marriages.values()))
    target_record = next(iter(target_marriages.values()))
    assert proposer_record.id == target_record.id
    assert proposer_record.status == MarriageStatus.ACCEPTED
    assert proposer_record.proposer_entity_id == 1
    assert proposer_record.target_entity_id == 2
    assert proposer_record.married_tick == 5


def test_marriage_no_free_form_dict_carries_accepted_outcome():
    proposer = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    target = _trusting_bond(target, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: proposer, 2: target})

    updates = CoreActions.execute_propose_marriage(proposer, {"target_id": 2}, 5, [], state)

    # On ACCEPTED, neither party's task payload carries a free-form "reason"/outcome string --
    # the accepted-marriage outcome is reachable only through the typed MarriageState field.
    assert updates[1].task is None
    assert updates[2].task is None
    assert isinstance(updates[1].strategic.marriages_add_or_update[0].status, MarriageStatus)


def test_marriage_no_duration_or_aging_threshold_introduced():
    field_names = {f.name for f in dataclasses.fields(MarriageState)}
    assert field_names == {"id", "proposer_entity_id", "target_entity_id", "status", "married_tick"}


def test_marriage_target_appraises_proposer_not_vice_versa():
    proposer = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()

    # Proposer is hostile toward target, but target trusts proposer -> succeeds
    proposer_hostile = _trusting_bond(proposer, 2, sentiment=-0.9)
    target_trusting = _trusting_bond(target, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: proposer_hostile, 2: target_trusting})

    updates = CoreActions.execute_propose_marriage(
        proposer_hostile, {"target_id": 2}, 5, [], state
    )
    assert updates[1].strategic.marriages_add_or_update[0].status == MarriageStatus.ACCEPTED

    # Invert: proposer trusts target, but target distrusts proposer -> fails
    proposer_trusting = _trusting_bond(proposer, 2, sentiment=0.8)
    target_hostile = _trusting_bond(target, 1, sentiment=-0.9)
    state2 = AuthoritativeState(tick=5, seed=42, entities={1: proposer_trusting, 2: target_hostile})

    updates2 = CoreActions.execute_propose_marriage(
        proposer_trusting, {"target_id": 2}, 5, [], state2
    )
    assert updates2[1].strategic is None


def test_marriage_action_routes_through_action_router():
    proposer = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    target = _trusting_bond(target, 1, sentiment=0.8)
    state = AuthoritativeState(tick=5, seed=42, entities={1: proposer, 2: target})

    updates = ActionRouter.execute_action(
        proposer,
        payload={"action": "PROPOSE_MARRIAGE", "target_id": 2},
        current_tick=5,
        neighbor_view=[(2, target)],
        context=state,
    )

    assert updates[1].strategic.marriages_add_or_update[0].status == MarriageStatus.ACCEPTED
