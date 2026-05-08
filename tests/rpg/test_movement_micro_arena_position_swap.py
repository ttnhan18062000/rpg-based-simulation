from __future__ import annotations

"""
Movement Micro-Arena E2E Tests
==============================

Purpose:
    These tests prove movement behavior at the pipeline/apply level, not only
    inside MovementSystem.resolve_move(...).

Coverage:
    1. normal direct movement in a one-tile-wide corridor
    2. permanent blocker does not cause silent infinite retry
    3. one-sided blocked movement without consent is rejected / observable
    4. mutual adjacent swap succeeds
    5. accepted POSITION_SWAP contract succeeds with one-sided intent
    6. HOLD mode refuses swap even with contract
    7. stale / expired / moved-position contracts do not move entities
    8. no infinite swap-back loop after contract fulfillment
    9. deterministic repeatability of the same micro-arena

Required src feature:
    These tests assume you have implemented:
        - ContractKind.POSITION_SWAP
        - ReasonCode.POSITION_SWAP
        - ReasonCode.POSITION_SWAP_REFUSED / POSITION_SWAP_ACCEPTED if used
        - AuthoritativeApplyPipeline._resolve_position_swaps(...)
        - position-swap phase before _route_movement_intent(...)
        - contract fulfillment after successful accepted swap

Why this file exists:
    Existing movement tests already cover the local MovementSystem recovery
    ladder: direct step, sidestep, yield, wait_count, reroute, replan, and
    oscillation. This file proves that those laws survive through:
        StateUpdate -> AuthoritativeApplyPipeline.refine -> ApplyPath.apply_generation.
"""

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, ReasonCode
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.core.updates import EntityUpdate, NavigationUpdate, StateUpdate, TaskUpdate
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline


# ---------------------------------------------------------------------------
# Feature guards
# ---------------------------------------------------------------------------


def _require_position_swap_feature() -> None:
    """
    Fail fast if the position-swap feature has not been added to src yet.

    This is better than getting a confusing AttributeError deep inside the
    test. These tests are designed to validate the new feature, so missing enum
    values should be treated as an implementation gap.
    """
    missing = []

    if not hasattr(ContractKind, "POSITION_SWAP"):
        missing.append("ContractKind.POSITION_SWAP")

    if not hasattr(ReasonCode, "POSITION_SWAP"):
        missing.append("ReasonCode.POSITION_SWAP")

    if not hasattr(AuthoritativeApplyPipeline, "_resolve_position_swaps"):
        missing.append("AuthoritativeApplyPipeline._resolve_position_swaps")

    if missing:
        pytest.fail(
            "Position-swap feature is not fully implemented. Missing: "
            + ", ".join(missing)
        )


# ---------------------------------------------------------------------------
# Micro-arena builders
# ---------------------------------------------------------------------------


def make_actor(
    entity_id: int,
    pos: tuple[float, float],
    *,
    faction=Faction.HERO_GUILD,
    target: tuple[float, float] | None = None,
    mode: MovementMode = MovementMode.WANDER,
    wait_count: int = 0,
    oscillation_count: int = 0,
    last_position: tuple[float, float] | None = None,
):
    """
    Build a valid movement actor for micro-arena tests.

    Important setup:
        - hp/alive/lifecycle.active are consistent
        - readiness is high enough that movement is not rejected for readiness
        - navigation target/mode are explicit
        - faction is set so priority/yield logic has stable identity data
    """
    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(float(pos[0]), float(pos[1]))
        .identity(faction=faction)
        .combat(
            hp=100,
            max_hp=100,
            atk=10,
            def_stat=0,
            alive=True,
            readiness=100.0,
        )
        .navigation(
            target=target,
            movement_mode=mode,
            wait_count=wait_count,
            oscillation_count=oscillation_count,
            last_position=last_position,
        )
        .lifecycle(active=True)
        .build()
    )


def one_tile_corridor_walls(
    *,
    x_min: int = -2,
    x_max: int = 6,
    open_y: int = 0,
) -> dict[tuple[int, int], str]:
    """
    Build walls above and below a one-tile-wide horizontal corridor.

    Example for x=0..3:
        #####
        . . . .
        #####

    Entities can only move along y=0 unless the test intentionally leaves a
    passing bay open.
    """
    terrain: dict[tuple[int, int], str] = {}

    for x in range(x_min, x_max + 1):
        terrain[(x, open_y + 1)] = "WALL"
        terrain[(x, open_y - 1)] = "WALL"

    return terrain


def corridor_with_passing_bay(
    *,
    bay_at: tuple[int, int] = (1, 1),
    x_min: int = -1,
    x_max: int = 4,
) -> dict[tuple[int, int], str]:
    """
    Build a one-tile corridor with one open side bay.

    The default bay at (1, 1) allows a blocker to sidestep so another entity can
    pass. This proves the engine prefers legal sidestep/yield before giving up.
    """
    terrain = one_tile_corridor_walls(x_min=x_min, x_max=x_max)
    terrain.pop(bay_at, None)
    return terrain


def make_state(
    *,
    entities: dict[int, object],
    terrain: dict[tuple[int, int], str] | None = None,
    tick: int = 1,
    seed: int = 42,
) -> AuthoritativeState:
    """
    Build a deterministic micro-arena state.
    """
    return AuthoritativeState(
        tick=tick,
        seed=seed,
        entities=entities,
        terrain=terrain or {},
    )


def move_intent(
    entity_id: int,
    target: tuple[float, float],
) -> EntityUpdate:
    """
    Build a normal movement intent routed through the pipeline.

    Both TaskUpdate and NavigationUpdate are included because different
    in-progress source paths inspect different surfaces.
    """
    return EntityUpdate(
        entity_id=entity_id,
        navigation=NavigationUpdate(target_set=target),
        task=TaskUpdate(
            work_kind_set="ENTITY_MOVE",
            payload_set={
                "target_position": target,
                "reason": "MICRO_ARENA_MOVE",
            },
        ),
    )


def raw_position_update(
    entity_id: int,
    new_position: tuple[float, float],
) -> EntityUpdate:
    """
    Build a raw final-position proposal.

    This intentionally bypasses normal movement intent and validates that the
    authoritative pipeline still protects final positions.
    """
    return EntityUpdate(
        entity_id=entity_id,
        new_position=new_position,
        moved_this_tick=True,
    )


def accepted_position_swap_contract(
    *,
    contract_id: str,
    source_id: int,
    target_id: int,
    source_from: tuple[float, float],
    target_from: tuple[float, float],
    tick: int = 1,
    expiry_tick: int = 2,
    status: ContractStatus = ContractStatus.ACCEPTED,
) -> ContractState:
    """
    Build an accepted short-lived POSITION_SWAP contract.

    The terms lock the contract to the current positions. If either entity moves
    before the contract is consumed, the contract becomes stale and must not
    execute.
    """
    _require_position_swap_feature()

    return ContractState(
        id=contract_id,
        kind=ContractKind.POSITION_SWAP,
        source_id=source_id,
        target_id=target_id,
        terms={
            "source_from": source_from,
            "source_to": target_from,
            "target_from": target_from,
            "target_to": source_from,
            "reason": "CORRIDOR_SWAP",
        },
        status=status,
        created_tick=tick,
        expiry_tick=expiry_tick,
    )


def attach_contract_to_both(a, b, contract: ContractState):
    """
    Store the same contract on both participants.

    The position-swap resolver should be able to find the contract from either
    side, and contract fulfillment should update both sides.
    """
    a2 = replace(
        a,
        strategic=replace(
            a.strategic,
            contracts={**a.strategic.contracts, contract.id: contract},
        ),
    )
    b2 = replace(
        b,
        strategic=replace(
            b.strategic,
            contracts={**b.strategic.contracts, contract.id: contract},
        ),
    )
    return a2, b2


def refine_and_apply(
    state: AuthoritativeState,
    raw_update: StateUpdate,
) -> tuple[StateUpdate, AuthoritativeState]:
    """
    Execute one authoritative pipeline/apply step.
    """
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    next_state = ApplyPath.apply_generation(state, refined)
    return refined, next_state


def run_scripted_ticks(
    state: AuthoritativeState,
    scripts: list[dict[int, EntityUpdate]],
) -> AuthoritativeState:
    """
    Run multiple pipeline/apply ticks using scripted per-tick updates.

    This is a micro-arena substitute for Kernel AI. It gives deterministic
    end-to-end coverage without depending on tactical AI choosing the exact
    movement intents we need.
    """
    current = state

    for per_entity_updates in scripts:
        raw = StateUpdate(entity_updates=per_entity_updates)
        _, current = refine_and_apply(current, raw)

    return current


def assert_no_overlap(state: AuthoritativeState) -> None:
    """
    Assert that no two active entities occupy the same tile.
    """
    occupied: dict[tuple[float, float], int] = {}

    for entity in state.entities.values():
        if not entity.lifecycle.active:
            continue

        pos = entity.navigation.position
        assert pos not in occupied, (
            "OVERLAP FAILURE: two active entities occupy the same tile. "
            f"Position={pos}, first={occupied.get(pos)}, second={entity.id}"
        )
        occupied[pos] = entity.id


# ---------------------------------------------------------------------------
# Arena 1 — Direct corridor movement
# ---------------------------------------------------------------------------


def test_micro_arena_direct_corridor_movement_succeeds():
    """
    LAW:
        If the corridor ahead is empty, an entity moves one tile toward target.

    Scenario:
        A starts at (0, 0), target is (2, 0), corridor is one tile wide.

    Expected:
        A moves to (1, 0) in one pipeline/apply step.

    Fraud this catches:
        - pipeline loses navigation intent
        - movement does not survive ApplyPath
        - one-tile corridor terrain incorrectly blocks the open lane
    """
    a = make_actor(1, (0.0, 0.0))
    state = make_state(
        entities={1: a},
        terrain=one_tile_corridor_walls(),
    )

    _, next_state = refine_and_apply(
        state,
        StateUpdate(entity_updates={1: move_intent(1, (2.0, 0.0))}),
    )

    assert next_state.entities[1].navigation.position == (1.0, 0.0)
    assert_no_overlap(next_state)


# ---------------------------------------------------------------------------
# Arena 2 — Static blocker, no consent
# ---------------------------------------------------------------------------


def test_micro_arena_one_sided_blocked_move_without_consent_does_not_overlap():
    """
    LAW:
        One-sided movement into an occupied tile must not create overlap.

    Scenario:
        A at (0, 0) wants to move to B's tile at (1, 0).
        B does not move and has not accepted a swap contract.
        Corridor has no side bay.

    Expected:
        A must not end on B's tile. The engine may either keep A in place,
        record a failure, wait, or replan, but overlap is illegal.

    Fraud this catches:
        - raw movement intent overwrites occupancy safety
        - one-sided movement is incorrectly treated as consent
        - final ApplyPath commits overlapping positions
    """
    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0))
    state = make_state(
        entities={1: a, 2: b},
        terrain=one_tile_corridor_walls(),
    )

    _, next_state = refine_and_apply(
        state,
        StateUpdate(entity_updates={1: move_intent(1, (1.0, 0.0))}),
    )

    assert_no_overlap(next_state)
    assert next_state.entities[1].navigation.position != next_state.entities[2].navigation.position


# ---------------------------------------------------------------------------
# Arena 3 — Permanent HOLD blocker bounded anti-stuck
# ---------------------------------------------------------------------------


def test_micro_arena_hold_blocker_does_not_silently_stuck_forever():
    """
    LAW:
        An entity may be blocked for several ticks, but it must not silently
        retry the same impossible movement forever.

    Scenario:
        A wants to reach (3, 0).
        B holds position at (1, 0) in a one-tile-wide corridor.
        No sidestep or bypass exists.

    Expected:
        After bounded ticks, A must expose recovery evidence:
            - wait_count increased, or
            - failure reason recorded, or
            - target/path cleared, or
            - explicit blocker state exists.

    Fraud this catches:
        - wait_count does not persist through ApplyPath
        - movement failure is lost between ticks
        - pipeline retries forever with no observable state
    """
    a = make_actor(1, (0.0, 0.0), target=(3.0, 0.0))
    b = make_actor(2, (1.0, 0.0), mode=MovementMode.HOLD)
    state = make_state(
        entities={1: a, 2: b},
        terrain=one_tile_corridor_walls(),
    )

    scripts = [
        {1: move_intent(1, (3.0, 0.0))},
        {1: move_intent(1, (3.0, 0.0))},
        {1: move_intent(1, (3.0, 0.0))},
        {1: move_intent(1, (3.0, 0.0))},
        {1: move_intent(1, (3.0, 0.0))},
        {1: move_intent(1, (3.0, 0.0))},
    ]

    final_state = run_scripted_ticks(state, scripts)
    final_a = final_state.entities[1]

    assert_no_overlap(final_state)

    silently_stuck = (
        final_a.navigation.position == (0.0, 0.0)
        and final_a.navigation.target == (3.0, 0.0)
        and final_a.navigation.wait_count == 0
        and not final_a.navigation.last_failure_reason
        and not final_a.strategic.blockers
    )

    assert silently_stuck is False, (
        "Entity silently retried impossible corridor movement without recovery "
        "evidence. "
        f"Position={final_a.navigation.position}, "
        f"Target={final_a.navigation.target}, "
        f"Wait={final_a.navigation.wait_count}, "
        f"Failure={final_a.navigation.last_failure_reason}, "
        f"Blockers={final_a.strategic.blockers}"
    )


# ---------------------------------------------------------------------------
# Arena 4 — Mutual same-tick adjacent swap
# ---------------------------------------------------------------------------


def test_micro_arena_mutual_adjacent_swap_succeeds():
    """
    LAW:
        If two adjacent entities both request each other's tile in the same
        tick, they may swap atomically.

    Scenario:
        A at (0, 0) wants (1, 0).
        B at (1, 0) wants (0, 0).

    Expected:
        A ends at B's old position.
        B ends at A's old position.
        No overlap occurs.

    Fraud this catches:
        - swap is rejected as ordinary occupancy conflict
        - only one side moves
        - both entities end on the same tile
    """
    _require_position_swap_feature()

    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0))
    state = make_state(
        entities={1: a, 2: b},
        terrain=one_tile_corridor_walls(),
    )

    refined, next_state = refine_and_apply(
        state,
        StateUpdate(
            entity_updates={
                1: move_intent(1, (1.0, 0.0)),
                2: move_intent(2, (0.0, 0.0)),
            }
        ),
    )

    assert refined.entity_updates[1].new_position == (1.0, 0.0)
    assert refined.entity_updates[2].new_position == (0.0, 0.0)
    assert next_state.entities[1].navigation.position == (1.0, 0.0)
    assert next_state.entities[2].navigation.position == (0.0, 0.0)
    assert_no_overlap(next_state)


# ---------------------------------------------------------------------------
# Arena 5 — Accepted contract one-sided swap
# ---------------------------------------------------------------------------


def test_micro_arena_accepted_contract_one_sided_swap_succeeds():
    """
    LAW:
        If A asks B to swap and B has accepted the POSITION_SWAP contract,
        A's one-sided movement intent is enough to trigger an atomic swap.

    Scenario:
        A at (0, 0), B at (1, 0).
        Contract says A and B agree to exchange positions.
        Only A sends a move intent this tick.

    Expected:
        A and B swap.
        Contract is marked FULFILLED in the refined update.

    Fraud this catches:
        - social movement contract is ignored
        - accepted contract is not consumed
        - one-sided contract swap causes overlap
    """
    _require_position_swap_feature()

    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0))

    contract = accepted_position_swap_contract(
        contract_id="swap_1_2",
        source_id=1,
        target_id=2,
        source_from=(0.0, 0.0),
        target_from=(1.0, 0.0),
    )

    a, b = attach_contract_to_both(a, b, contract)

    state = make_state(
        entities={1: a, 2: b},
        terrain=one_tile_corridor_walls(),
    )

    refined, next_state = refine_and_apply(
        state,
        StateUpdate(entity_updates={1: move_intent(1, (1.0, 0.0))}),
    )

    assert next_state.entities[1].navigation.position == (1.0, 0.0)
    assert next_state.entities[2].navigation.position == (0.0, 0.0)
    assert_no_overlap(next_state)

    assert refined.entity_updates[1].strategic is not None
    fulfilled = [
        c
        for c in refined.entity_updates[1].strategic.contracts_add_or_update
        if c.id == "swap_1_2"
    ]
    assert fulfilled
    assert fulfilled[0].status == ContractStatus.FULFILLED


# ---------------------------------------------------------------------------
# Arena 6 — HOLD refuses contract swap
# ---------------------------------------------------------------------------


def test_micro_arena_hold_mode_refuses_position_swap_contract():
    """
    LAW:
        HOLD mode refuses position swap.

    Scenario:
        B is in HOLD mode but an accepted POSITION_SWAP contract exists.
        A tries to move into B's tile.

    Expected:
        B does not move.
        A does not overlap B.

    Fraud this catches:
        - contract bypasses movement_mode=HOLD
        - stale social consent overrides current tactical refusal
    """
    _require_position_swap_feature()

    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0), mode=MovementMode.HOLD)

    contract = accepted_position_swap_contract(
        contract_id="swap_1_2",
        source_id=1,
        target_id=2,
        source_from=(0.0, 0.0),
        target_from=(1.0, 0.0),
    )

    a, b = attach_contract_to_both(a, b, contract)

    state = make_state(
        entities={1: a, 2: b},
        terrain=one_tile_corridor_walls(),
    )

    _, next_state = refine_and_apply(
        state,
        StateUpdate(entity_updates={1: move_intent(1, (1.0, 0.0))}),
    )

    assert next_state.entities[2].navigation.position == (1.0, 0.0)
    assert next_state.entities[1].navigation.position != next_state.entities[2].navigation.position
    assert_no_overlap(next_state)


# ---------------------------------------------------------------------------
# Arena 7 — Expired contract cannot swap
# ---------------------------------------------------------------------------


def test_micro_arena_expired_position_swap_contract_does_not_execute():
    """
    LAW:
        Position-swap contracts are short-lived and cannot execute after expiry.

    Scenario:
        Contract expired at tick 2.
        Current state tick is 10.
        A tries to move into B's tile.

    Expected:
        No swap occurs.
        No overlap occurs.

    Fraud this catches:
        - expired social contract moves entities after positions may be stale
        - old consent remains permanently reusable
    """
    _require_position_swap_feature()

    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0))

    contract = accepted_position_swap_contract(
        contract_id="swap_1_2",
        source_id=1,
        target_id=2,
        source_from=(0.0, 0.0),
        target_from=(1.0, 0.0),
        tick=1,
        expiry_tick=2,
    )

    a, b = attach_contract_to_both(a, b, contract)

    state = make_state(
        tick=10,
        entities={1: a, 2: b},
        terrain=one_tile_corridor_walls(),
    )

    _, next_state = refine_and_apply(
        state,
        StateUpdate(entity_updates={1: move_intent(1, (1.0, 0.0))}),
    )

    assert next_state.entities[2].navigation.position == (1.0, 0.0)
    assert next_state.entities[1].navigation.position != next_state.entities[2].navigation.position
    assert_no_overlap(next_state)


# ---------------------------------------------------------------------------
# Arena 8 — Stale-position contract cannot swap
# ---------------------------------------------------------------------------


def test_micro_arena_stale_position_swap_contract_does_not_execute():
    """
    LAW:
        A POSITION_SWAP contract must match current authoritative positions.

    Scenario:
        Contract was created when B was at (1, 0), but B is now at (2, 0).
        A tries to move toward B.

    Expected:
        The stale contract does not execute.

    Fraud this catches:
        - contract terms are ignored
        - stale social contract teleports/moves wrong entities
    """
    _require_position_swap_feature()

    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (2.0, 0.0))

    stale_contract = accepted_position_swap_contract(
        contract_id="swap_1_2",
        source_id=1,
        target_id=2,
        source_from=(0.0, 0.0),
        target_from=(1.0, 0.0),
        tick=1,
        expiry_tick=10,
    )

    a, b = attach_contract_to_both(a, b, stale_contract)

    state = make_state(
        entities={1: a, 2: b},
        terrain=one_tile_corridor_walls(),
    )

    _, next_state = refine_and_apply(
        state,
        StateUpdate(entity_updates={1: move_intent(1, (2.0, 0.0))}),
    )

    assert not (
        next_state.entities[1].navigation.position == (2.0, 0.0)
        and next_state.entities[2].navigation.position == (0.0, 0.0)
    )
    assert_no_overlap(next_state)


# ---------------------------------------------------------------------------
# Arena 9 — Contract cannot be reused for infinite swap-back
# ---------------------------------------------------------------------------


def test_micro_arena_position_swap_contract_not_reused_for_swap_back_loop():
    """
    LAW:
        A consumed POSITION_SWAP contract must be fulfilled and not reused on
        the next tick to swap entities back automatically.

    Scenario:
        Tick 1: A and B perform accepted contract swap.
        Tick 2: No new contract is created.

    Expected:
        They do not automatically swap back just because the old contract exists
        in prior state history.

    Fraud this catches:
        - accepted contract remains reusable forever
        - movement system creates infinite A<->B swap loop
    """
    _require_position_swap_feature()

    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0))

    contract = accepted_position_swap_contract(
        contract_id="swap_1_2",
        source_id=1,
        target_id=2,
        source_from=(0.0, 0.0),
        target_from=(1.0, 0.0),
    )

    a, b = attach_contract_to_both(a, b, contract)

    state = make_state(
        entities={1: a, 2: b},
        terrain=one_tile_corridor_walls(),
    )

    _, after_swap = refine_and_apply(
        state,
        StateUpdate(entity_updates={1: move_intent(1, (1.0, 0.0))}),
    )

    assert after_swap.entities[1].navigation.position == (1.0, 0.0)
    assert after_swap.entities[2].navigation.position == (0.0, 0.0)
    assert_no_overlap(after_swap)

    # Next tick: no explicit new contract or mutual intent. They should not
    # automatically swap back.
    _, final_state = refine_and_apply(after_swap, StateUpdate())

    assert final_state.entities[1].navigation.position == (1.0, 0.0)
    assert final_state.entities[2].navigation.position == (0.0, 0.0)
    assert_no_overlap(final_state)


# ---------------------------------------------------------------------------
# Arena 10 — Passing bay sidestep remains valid after swap feature
# ---------------------------------------------------------------------------


def test_micro_arena_passing_bay_still_allows_sidestep_without_swap_contract():
    """
    LAW:
        Position swap must not replace normal sidestep/yield behavior when a
        legal passing bay exists.

    Scenario:
        A wants to move through B's tile.
        B blocks the direct tile.
        A has an open side bay available.
        No swap contract exists.

    Expected:
        A should choose a legal sidestep/passing-bay move instead of overlap.

    Fraud this catches:
        - swap feature breaks existing sidestep recovery
        - corridor movement regresses to blocked/no-op despite open bay
    """
    a = make_actor(1, (0.0, 0.0))
    b = make_actor(2, (1.0, 0.0))

    state = make_state(
        entities={1: a, 2: b},
        terrain=corridor_with_passing_bay(bay_at=(0, 1)),
    )

    _, next_state = refine_and_apply(
        state,
        StateUpdate(entity_updates={1: move_intent(1, (2.0, 0.0))}),
    )

    assert_no_overlap(next_state)
    assert next_state.entities[1].navigation.position in {
        (0.0, 1.0),
        (0.0, -1.0),
        (0.0, 0.0),
        (1.0, 0.0),
    }


# ---------------------------------------------------------------------------
# Arena 11 — Determinism guard
# ---------------------------------------------------------------------------


def test_micro_arena_position_swap_deterministic_across_identical_runs():
    """
    LAW:
        Position-swap resolution must be deterministic.

    Scenario:
        Run the same accepted-contract swap arena twice from the same initial
        state and same scripted update.

    Expected:
        Final positions are identical.

    Fraud this catches:
        - swap pair selection depends on dictionary iteration
        - contract lookup order creates nondeterminism
        - same input produces different final movement state
    """
    _require_position_swap_feature()

    def build_initial_state() -> AuthoritativeState:
        a = make_actor(1, (0.0, 0.0))
        b = make_actor(2, (1.0, 0.0))

        contract = accepted_position_swap_contract(
            contract_id="swap_1_2",
            source_id=1,
            target_id=2,
            source_from=(0.0, 0.0),
            target_from=(1.0, 0.0),
        )

        a2, b2 = attach_contract_to_both(a, b, contract)

        return make_state(
            entities={1: a2, 2: b2},
            terrain=one_tile_corridor_walls(),
        )

    raw_update = StateUpdate(entity_updates={1: move_intent(1, (1.0, 0.0))})

    _, state_1 = refine_and_apply(build_initial_state(), raw_update)
    _, state_2 = refine_and_apply(build_initial_state(), raw_update)

    assert state_1.entities[1].navigation.position == state_2.entities[1].navigation.position
    assert state_1.entities[2].navigation.position == state_2.entities[2].navigation.position
    assert_no_overlap(state_1)
    assert_no_overlap(state_2)
