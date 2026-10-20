"""Each gate validity check fires through the real kernel (designer ruling after the v1 gate: a green that cannot go red is not evidence).

A real ``build_kernel`` run of a few ticks, the real events file and the real ``compute`` (the ``run_gate_metrics`` helper below); each test forces ONE violation
by seeding state or opening a path and asserts ``violations > 0`` on the emitted row. V1 and V4 have theirs elsewhere (V1: Lane B's tests, V4:
test_v4_counts_a_forbidden_meal_through_the_real_kernel.py); V2, V3, V5, V6, V7 and V8 are here.
"""
from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest

pytestmark = pytest.mark.integration


WORLD, SEED = "frontier_living_world", 42


def run_gate_metrics(run_id: str, ticks: int, prepare: Optional[Callable[[Any], None]] = None, after_tick: Optional[Callable[[Any, int], None]] = None,
                     world: str = WORLD, seed: int = SEED) -> List[Dict[str, Any]]:
    """Run ``ticks`` real ticks of ``world`` and return every row the real ``compute`` emits. ``prepare(kernel)`` seeds state before tick 1;
    ``after_tick(kernel, tick_number)`` may seed state between ticks."""
    from src.observability import rpg_gate_metrics
    from tools.test_architecture.rpg_gate_run import RunArtifacts, build_kernel

    run_dir = Path("data") / "runs" / run_id
    kernel = build_kernel(world, seed, run_id)
    try:
        if prepare is not None:
            prepare(kernel)
        for n in range(1, ticks + 1):
            kernel.tick_once()
            if after_tick is not None:
                after_tick(kernel, n)
    finally:
        kernel.shutdown()  # flushes the recorded event stream before the metrics read it
    try:
        result = rpg_gate_metrics.compute(RunArtifacts(world, seed, ticks, "test", kernel.state, run_dir))
        return list(result["metrics"] if isinstance(result, dict) else result)
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def validity_rows(metrics: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """The per-run validity rows by id (``V1``..``V8``; V7 is pooled and absent here)."""
    return {r["id"]: r for r in metrics if str(r.get("id", "")).startswith("V") and r.get("group") == "*"}


def run_gate_row_set(run_id: str, ticks: int, prepare: Optional[Callable[[Any], None]] = None, after_tick: Optional[Callable[[Any, int], None]] = None,
                     world: str = WORLD, seed: int = SEED) -> Dict[str, Dict[str, Any]]:
    return validity_rows(run_gate_metrics(run_id, ticks, prepare, after_tick, world, seed))


def _set_entities(kernel, entities) -> None:
    object.__setattr__(kernel.state, "entities", entities)


# ------------------------------------------------------------------------------------------------------------------------------ V2
def _seed_decaying_body(kernel) -> None:
    from src.core.state import CorpseState, ItemStack

    state = kernel.state
    body = CorpseState(id=1000900, original_entity_id=900, position=(30.0, 30.0), items=[ItemStack(item_id="raw_meat", quantity=4)], decay_tick=state.tick + 4)
    object.__setattr__(state, "corpses", {**(state.corpses or {}), body.id: body})


def test_v2_fires_when_a_body_with_meat_decays_and_the_decay_sink_is_silent(monkeypatch):
    import src.engine.world_dynamics as world_dynamics

    monkeypatch.setattr(world_dynamics, "_meat_decayed_events", lambda state: [])  # the sink under test is silenced; the body still decays
    row = run_gate_row_set("gate_pos_v2", 8, prepare=_seed_decaying_body)["V2"]
    assert row["violations"] > 0
    assert any("meat_decayed_events" in example for example in row["examples"]), row["examples"]


def test_v2_sink_example_is_absent_when_the_decay_sink_writes_its_record():
    row = run_gate_row_set("gate_pos_v2_control", 8, prepare=_seed_decaying_body)["V2"]
    assert not any("meat_decayed_events" in example for example in row["examples"]), row["examples"]


# ------------------------------------------------------------------------------------------------------------------------------ V3
def _seed_hungry_worker_beside_an_inn(kernel) -> int:
    state = kernel.state
    inn = next(b for b in state.buildings.values() if b.kind == "inn")
    worker = next(e for e in state.entities.values() if e.kind == "worker" and e.combat.alive)
    entities = dict(state.entities)
    entities[worker.id] = replace(
        worker, navigation=replace(worker.navigation, position=(inn.position[0] + 1.0, inn.position[1])),
        biological=replace(worker.biological, hunger=100.0), combat=replace(worker.combat, hp=2), inventory=replace(worker.inventory, items=[], gold=0))
    _set_entities(kernel, entities)
    return worker.id


def test_v3_fires_for_a_starvation_death_beside_an_open_way_even_when_the_dying_entity_had_no_update(monkeypatch):
    import src.engine.apply as apply

    monkeypatch.setattr(apply, "hp_loss", lambda *a, **k: 40)  # the starvation drain is made large so the death falls in the first ticks
    row = run_gate_row_set("gate_pos_v3", 6, prepare=_seed_hungry_worker_beside_an_inn)["V3"]
    assert row["violations"] > 0
    assert row["examples"][0]["untried"], row["examples"]


def test_v3_records_one_death_once_and_does_not_rerecord_an_entity_that_starved_earlier(monkeypatch):
    import src.engine.apply as apply

    monkeypatch.setattr(apply, "hp_loss", lambda *a, **k: 40)
    metrics = run_gate_metrics("gate_pos_v3_once", 25, prepare=_seed_hungry_worker_beside_an_inn)
    row = validity_rows(metrics)["V3"]
    assert row["violations"] == 1, row  # one death, recorded once, though the body stays in the state for the remaining ticks
    deaths = [r for r in metrics if r["id"] == "O2.deaths" and r.get("key") == "STARVATION"]
    assert sum(r["value"] for r in deaths) == 1


# ------------------------------------------------------------------------------------------------------------------------------ V5
def test_v5_fires_for_an_alive_entity_that_acts_outside_the_world_extent():
    def prepare(kernel) -> None:
        entities = dict(kernel.state.entities)
        for entity in list(entities.values())[:6]:
            if entity.combat.alive:
                entities[entity.id] = replace(entity, navigation=replace(entity.navigation, position=(5000.0, 5000.0)))
        _set_entities(kernel, entities)

    row = run_gate_row_set("gate_pos_v5", 30, prepare=prepare)["V5"]
    assert row["violations"] > 0
    assert row["examples"][0]["position"] == [5000.0, 5000.0]


# ------------------------------------------------------------------------------------------------------------------------------ V6
def test_v6_fires_when_an_entity_holds_more_coin_than_the_world_ever_declared():
    def after_tick(kernel, n: int) -> None:
        if n == 1:
            state = kernel.state
            entity = next(e for e in state.entities.values() if e.combat.alive)
            entities = dict(state.entities)
            entities[entity.id] = replace(entity, inventory=replace(entity.inventory, gold=entity.inventory.gold + 500))
            _set_entities(kernel, entities)

    row = run_gate_row_set("gate_pos_v6", 4, after_tick=after_tick)["V6"]
    assert row["violations"] > 0


# ------------------------------------------------------------------------------------------------------------------------------ V7 (pooled)
def test_v7_fires_in_the_pooled_rows_of_real_runs_where_people_never_use_a_declared_way():
    from src.observability import rpg_gate_metrics

    documents = []
    for seed in (42, 43):
        metrics = run_gate_metrics(f"gate_pos_v7_{seed}", 12, seed=seed)  # people exist, and in 12 ticks nobody has eaten at an inn or a node
        documents.append({"world": "frontier_living_world", "metrics": metrics})
    (row,) = [r for r in rpg_gate_metrics.pool(documents) if r["id"] == "V7"]
    assert row["scope"] == "pooled" and row["violations"] > 0, row
    assert {example["way"] for example in row["examples"]} & {"TOWN_SERVICE", "NODE"}


# ------------------------------------------------------------------------------------------------------------------------------ V8
def test_v8_fires_for_an_entity_added_mid_run_with_no_declared_source(monkeypatch):
    from src.core.builder import V2EntityBuilder
    from src.engine.world_dynamics import WorldDynamicsSystem

    real = WorldDynamicsSystem.resolve_dynamics
    added = []

    def with_an_unsourced_add(state, update, *args, **kwargs):
        refined = real(state, update, *args, **kwargs)
        if state.tick == 2 and not added:
            newcomer = V2EntityBuilder(state.next_entity_id).location(30.0, 30.0).build()
            added.append(newcomer.id)
            refined = replace(refined, entities_add=[*refined.entities_add, newcomer])  # no entity_spawn_sources entry: an undeclared add
        return refined

    monkeypatch.setattr(WorldDynamicsSystem, "resolve_dynamics", staticmethod(with_an_unsourced_add))
    row = run_gate_row_set("gate_pos_v8", 5)["V8"]
    assert added and row["violations"] > 0, row
