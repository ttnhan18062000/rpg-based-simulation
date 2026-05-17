# Compliance IDs: PERF-006, STRAT-PERF-001
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, IntentResult, IdentityComponent
from src.core.strategic import BlockerState, BlockerKind, ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus, ContractState, ContractKind, ContractStatus
from src.core.dirty import DirtySet
from src.core.updates import StateUpdate
from src.core.builder import V2EntityBuilder
from src.systems.strategic_systems.work_queue import StrategicWorkQueue


def test_strategic_queue_prioritizes_failed_action_entity():
    # Entity 1: normal
    e1 = V2EntityBuilder(1).navigation(wait_count=0, oscillation_count=0).build()

    # Entity 2: navigation oscillation failure
    e2 = V2EntityBuilder(2).navigation(wait_count=0, oscillation_count=4).build()

    # Entity 3: intent rejection failure
    id_comp = replace(IdentityComponent(), latest_intent_results=[
        IntentResult(transaction_id="t1", accepted=False, reason="INVENTORY_FULL", source_kind="node", source_id=10)
    ])
    e3 = V2EntityBuilder(3).replace_identity(id_comp).build()

    state = AuthoritativeState(tick=10, seed=42)
    state = replace(state, entities={1: e1, 2: e2, 3: e3})
    update = StateUpdate()
    dirty = DirtySet()

    queue = StrategicWorkQueue.build(state, update, dirty, budget=10)
    assert queue == (2, 3, 1)  # T1 (2, 3) followed by T7 (1)


def test_strategic_queue_prioritizes_unresolved_blocker():
    e10 = V2EntityBuilder(10).build()
    
    b = BlockerState(id="b1", kind=BlockerKind.MATERIAL, subject="gold", resolved=False)
    e20 = V2EntityBuilder(20).strategic(blockers={"b1": b}).build()

    state = AuthoritativeState(tick=10, seed=42)
    state = replace(state, entities={10: e10, 20: e20})
    update = StateUpdate()
    dirty = DirtySet()

    queue = StrategicWorkQueue.build(state, update, dirty, budget=10)
    assert queue == (20, 10)  # T2 (20) followed by T7 (10)


def test_strategic_queue_prioritizes_biological_emergency():
    e1 = V2EntityBuilder(100).biological(hunger=10.0).build()
    e2 = V2EntityBuilder(200).biological(hunger=90.0).build()  # Starving

    state = AuthoritativeState(tick=5, seed=42)
    state = replace(state, entities={100: e1, 200: e2})
    update = StateUpdate()
    dirty = DirtySet()

    queue = StrategicWorkQueue.build(state, update, dirty, budget=10)
    assert queue == (200, 100)  # T4 (200) followed by T7 (100)


def test_strategic_queue_includes_dirty_strategic_entities():
    e1 = V2EntityBuilder(5).build()
    e2 = V2EntityBuilder(15).build()

    state = AuthoritativeState(tick=1, seed=42)
    state = replace(state, entities={5: e1, 15: e2})
    update = StateUpdate()
    dirty = DirtySet(strategic_entities={15})

    queue = StrategicWorkQueue.build(state, update, dirty, budget=10)
    assert queue == (15, 5)  # T6 (15) followed by T7 (5)


def test_strategic_queue_respects_budget():
    entities = {i: V2EntityBuilder(i).build() for i in range(1, 21)}
    state = AuthoritativeState(tick=1, seed=42)
    state = replace(state, entities=entities)
    update = StateUpdate()
    dirty = DirtySet()

    queue = StrategicWorkQueue.build(state, update, dirty, budget=5)
    assert len(queue) == 5


def test_strategic_queue_background_sweep_prevents_starvation():
    entities = {i: V2EntityBuilder(i).build() for i in range(1, 11)}
    state1 = AuthoritativeState(tick=0, seed=42)
    state1 = replace(state1, entities=entities)
    update = StateUpdate()
    dirty = DirtySet()

    q_tick0 = StrategicWorkQueue.build(state1, update, dirty, budget=3)

    state2 = replace(state1, tick=1)
    q_tick1 = StrategicWorkQueue.build(state2, update, dirty, budget=3)

    assert q_tick0 != q_tick1  # Deterministic round-robin shift ensures starvation prevention


def test_strategic_queue_force_full_scan_includes_all_strategic_entities():
    entities = {i: V2EntityBuilder(i).build() for i in range(1, 101)}
    state = AuthoritativeState(tick=1, seed=42)
    state = replace(state, entities=entities)
    update = StateUpdate(force_full_scan=True)
    dirty = DirtySet()

    queue = StrategicWorkQueue.build(state, update, dirty, budget=5)
    assert len(queue) == 100  # Bypasses budget/narrowing entirely
