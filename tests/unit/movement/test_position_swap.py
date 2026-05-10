from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.core.updates import EntityUpdate, NavigationUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline


def make_actor(
    entity_id: int,
    pos: tuple[float, float],
):
    """
    Build a valid active movement actor for position-swap tests.
    """
    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(*pos)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )


def test_mutual_adjacent_position_swap_succeeds():
    """
    LAW:
        If two adjacent entities both try to move into each other's current
        position in the same tick, the pipeline resolves it as an atomic swap.

    Fraud this catches:
        - one-tile corridor passing is impossible even with mutual intent
        - entities overlap
        - deterministic swap is rejected as ordinary occupancy conflict
    """
    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0))

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            1: a,
            2: b,
        },
    )

    raw_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                navigation=NavigationUpdate(target_set=(1.0, 0.0)),
            ),
            2: EntityUpdate(
                entity_id=2,
                navigation=NavigationUpdate(target_set=(0.0, 0.0)),
            ),
        }
    )

    refined = AuthoritativeApplyPipeline.refine(state, raw_update)

    assert refined.entity_updates[1].new_position == (1.0, 0.0)
    assert refined.entity_updates[2].new_position == (0.0, 0.0)

    assert refined.entity_updates[1].navigation.failure_reason == ReasonCode.POSITION_SWAP
    assert refined.entity_updates[2].navigation.failure_reason == ReasonCode.POSITION_SWAP

    new_state = ApplyPath.apply_generation(state, refined)

    assert new_state.entities[1].navigation.position == (1.0, 0.0)
    assert new_state.entities[2].navigation.position == (0.0, 0.0)
    assert new_state.entities[1].navigation.position != new_state.entities[2].navigation.position


def test_accepted_position_swap_contract_succeeds_with_one_sided_intent():
    """
    LAW:
        If A asks B to swap and B has accepted the POSITION_SWAP contract,
        A does not need B to independently generate a movement intent in the
        same tick. The contract supplies B's consent.

    Fraud this catches:
        - accepted movement contracts are ignored
        - one-sided request still gets treated as ordinary occupancy violation
        - contract is not consumed after fulfillment
    """
    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0))

    contract = ContractState(
        id="swap_1_2",
        kind=ContractKind.POSITION_SWAP,
        source_id=1,
        target_id=2,
        terms={
            "source_from": (0.0, 0.0),
            "source_to": (1.0, 0.0),
            "target_from": (1.0, 0.0),
            "target_to": (0.0, 0.0),
        },
        status=ContractStatus.ACCEPTED,
        created_tick=1,
        expiry_tick=2,
    )

    a = replace(
        a,
        strategic=replace(
            a.strategic,
            contracts={contract.id: contract},
        ),
    )

    b = replace(
        b,
        strategic=replace(
            b.strategic,
            contracts={contract.id: contract},
        ),
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            1: a,
            2: b,
        },
    )

    raw_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                navigation=NavigationUpdate(target_set=(1.0, 0.0)),
            )
        }
    )

    refined = AuthoritativeApplyPipeline.refine(state, raw_update)

    assert refined.entity_updates[1].new_position == (1.0, 0.0)
    assert refined.entity_updates[2].new_position == (0.0, 0.0)

    assert refined.entity_updates[1].strategic is not None
    assert refined.entity_updates[2].strategic is not None

    fulfilled_statuses = [
        c.status
        for c in refined.entity_updates[1].strategic.contracts_add_or_update
        if c.id == "swap_1_2"
    ]

    assert fulfilled_statuses == [ContractStatus.FULFILLED]


def test_position_swap_contract_does_not_override_hold_mode():
    """
    LAW:
        HOLD mode refuses position swap. Consent cannot be assumed when the
        responder is explicitly holding position.

    Fraud this catches:
        - POSITION_SWAP bypasses HOLD semantics
        - accepted stale contract moves an entity that currently refuses movement
    """
    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0))
    b = replace(
        b,
        navigation=replace(
            b.navigation,
            movement_mode=MovementMode.HOLD,
        ),
    )

    contract = ContractState(
        id="swap_1_2",
        kind=ContractKind.POSITION_SWAP,
        source_id=1,
        target_id=2,
        terms={
            "source_from": (0.0, 0.0),
            "source_to": (1.0, 0.0),
            "target_from": (1.0, 0.0),
            "target_to": (0.0, 0.0),
        },
        status=ContractStatus.ACCEPTED,
        created_tick=1,
        expiry_tick=2,
    )

    a = replace(
        a,
        strategic=replace(
            a.strategic,
            contracts={contract.id: contract},
        ),
    )

    b = replace(
        b,
        strategic=replace(
            b.strategic,
            contracts={contract.id: contract},
        ),
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            1: a,
            2: b,
        },
    )

    raw_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                navigation=NavigationUpdate(target_set=(1.0, 0.0)),
            )
        }
    )

    refined = AuthoritativeApplyPipeline.refine(state, raw_update)

    assert refined.entity_updates.get(2) is None or refined.entity_updates[2].new_position is None
    assert refined.entity_updates[1].new_position != (1.0, 0.0)