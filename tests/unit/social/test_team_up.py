# Compliance IDs: SOC-250
"""
Unit tests for CoreActions.execute_team_up() (TCK-20260824-AFFECTION-CONTRACT-GATE).

Mirrors test_recruitment.py's style for the closest existing precedent
(CoreActions.execute_recruit()) -- routes a temp ContractState through
SocialAppraisalSystem.appraise_contract() and asserts on the resulting
EntityUpdate bundle.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, SocialBond
from src.core.strategic import ContractKind, ContractStatus
from src.engine.domain.core_actions import CoreActions
from dataclasses import replace


def test_execute_team_up_accepts_on_high_trust_bond():
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    target = replace(
        target,
        social=replace(target.social, bonds={1: SocialBond(target_id=1, sentiment=0.8)}),
    )
    state = AuthoritativeState(tick=5, seed=42, entities={1: entity, 2: target})

    updates = CoreActions.execute_team_up(
        entity, {"target_id": 2, "risk_level": "NORMAL"}, 5, [], state
    )

    assert updates[1].strategic is not None
    assert updates[2].strategic is not None
    entity_contract = updates[1].strategic.contracts_add_or_update[0]
    target_contract = updates[2].strategic.contracts_add_or_update[0]
    assert entity_contract.kind == ContractKind.TEAM_UP
    assert entity_contract.status == ContractStatus.ACTIVE
    assert entity_contract is target_contract
    assert not updates[1].resource_transfers
    assert not updates[2].resource_transfers


def test_execute_team_up_rejects_on_low_trust_bond():
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    target = replace(
        target,
        social=replace(target.social, bonds={1: SocialBond(target_id=1, sentiment=-0.9)}),
    )
    state = AuthoritativeState(tick=5, seed=42, entities={1: entity, 2: target})

    updates = CoreActions.execute_team_up(
        entity, {"target_id": 2, "risk_level": "NORMAL"}, 5, [], state
    )

    assert updates[1].strategic is None
    assert updates[2].social.rejection_increment == {1: 1}


def test_execute_team_up_target_not_found():
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    state = AuthoritativeState(tick=5, seed=42, entities={1: entity})

    updates = CoreActions.execute_team_up(
        entity, {"target_id": 999, "risk_level": "NORMAL"}, 5, [], state
    )

    assert updates[1].navigation.failure_reason == "TARGET_NOT_FOUND"
