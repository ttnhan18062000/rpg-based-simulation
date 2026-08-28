# Compliance IDs: SOC-249
"""
Unit tests for CoreActions.execute_trade() (TCK-20260824-AFFECTION-CONTRACT-GATE).

Mirrors test_team_up.py's structure. Confirms ContractKind.MERCHANT is used for the
contract-state kind and is never conflated with InformationProviderArchetype.MERCHANT
(distinct enums, same string value).
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, SocialBond
from src.core.strategic import ContractKind, ContractStatus
from src.domains.information.providers import InformationProviderArchetype
from src.engine.domain.core_actions import CoreActions


def test_execute_trade_accepts_on_fair_price():
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    state = AuthoritativeState(tick=5, seed=42, entities={1: entity, 2: target})

    updates = CoreActions.execute_trade(
        entity, {"target_id": 2, "price": 100, "item_value": 100}, 5, [], state
    )

    entity_contract = updates[1].strategic.contracts_add_or_update[0]
    target_contract = updates[2].strategic.contracts_add_or_update[0]
    assert entity_contract.kind == ContractKind.MERCHANT
    assert entity_contract.status == ContractStatus.ACTIVE
    assert entity_contract is target_contract
    assert not updates[1].resource_transfers
    assert not updates[2].resource_transfers


def test_execute_trade_rejects_on_low_trust_bond():
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    target = V2EntityBuilder(2).kind("hero").location(1.0, 0.0).build()
    target = replace(
        target,
        social=replace(target.social, bonds={1: SocialBond(target_id=1, sentiment=-0.9)}),
    )
    state = AuthoritativeState(tick=5, seed=42, entities={1: entity, 2: target})

    updates = CoreActions.execute_trade(
        entity, {"target_id": 2, "price": 100, "item_value": 100}, 5, [], state
    )

    assert updates[1].strategic is None
    assert updates[2].social.rejection_increment == {1: 1}


def test_execute_trade_target_not_found():
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    state = AuthoritativeState(tick=5, seed=42, entities={1: entity})

    updates = CoreActions.execute_trade(
        entity, {"target_id": 999, "price": 100, "item_value": 100}, 5, [], state
    )

    assert updates[1].navigation.failure_reason == "TARGET_NOT_FOUND"


def test_contract_kind_merchant_is_not_information_provider_archetype_merchant():
    assert ContractKind.MERCHANT is not InformationProviderArchetype.MERCHANT
    assert ContractKind.MERCHANT.__class__ is not InformationProviderArchetype.MERCHANT.__class__
