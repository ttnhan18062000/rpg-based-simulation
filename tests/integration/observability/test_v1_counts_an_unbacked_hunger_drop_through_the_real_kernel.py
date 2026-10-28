"""V1 through the real pipeline (TCK-20261019-V1-COUNTS-A-HUNGER-DROP-AS-BACKED-ONLY-WHEN-AN-ACCEPTED-TRANSFER-MOVED-SOMETHING).

A real ``build_kernel`` run, the real events file and the real ``compute``. A hungry worker with no coin eats in the world's meal path: its hunger falls and
nothing moves (no coin, no item), so V1 must fire. The V1 row names a kind group, not an entity, so the forced eater is pinned through its own state: it is
the only entity seeded broke and hungry, and the test records the tick its hunger fell with its purse still empty. The control gives the same worker coin:
its meal is charged (the purse falls), the drop is backed, and the worker adds nothing to the V1 row.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from tests.integration.observability.test_gate_validity_checks_fire_through_the_real_kernel import _set_entities, run_gate_metrics, validity_rows

pytestmark = pytest.mark.integration

TICKS = 80


def _forced_worker(gold: int):
    """Returns (prepare, watch, seen): `prepare` seeds the worker, `watch` records after each tick whether its hunger fell and whether its purse moved."""
    seen = {"id": None, "group": None, "hunger_fell": 0, "purse_fell": 0, "unbacked": 0, "last": None}

    def prepare(kernel) -> None:
        from src.ai.goals.kind_group import kind_group

        state = kernel.state
        inn = next(b for b in state.buildings.values() if b.kind == "inn")
        worker = next(e for e in state.entities.values() if e.kind == "worker" and e.combat.alive)
        entities = dict(state.entities)
        entities[worker.id] = replace(
            worker, navigation=replace(worker.navigation, position=(inn.position[0] + 1.0, inn.position[1])),
            biological=replace(worker.biological, hunger=100.0), inventory=replace(worker.inventory, items=[], gold=gold))
        _set_entities(kernel, entities)
        seen.update(id=worker.id, group=kind_group(entities[worker.id]), last=(100.0, gold))

    def watch(kernel, n: int) -> None:
        entity = kernel.state.entities[seen["id"]]
        hunger, purse = entity.biological.hunger, entity.inventory.gold
        before_hunger, before_purse = seen["last"]
        if hunger < before_hunger:
            seen["hunger_fell"] += 1
            if purse < before_purse:
                seen["purse_fell"] += 1
            elif purse == before_purse:
                seen["unbacked"] += 1
        seen["last"] = (hunger, purse)

    return prepare, watch, seen


def _v1(run_id: str, gold: int):
    prepare, watch, seen = _forced_worker(gold)
    row = validity_rows(run_gate_metrics(run_id, TICKS, prepare=prepare, after_tick=watch))["V1"]
    return row, seen


def test_a_broke_eater_beside_the_inn_is_not_fed_so_v1_has_nothing_to_count():
    """Decision 73 (TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1): the broke worker that this test once pinned as V1's positive case is now
    refused the meal. Its hunger does not fall for nothing, so its group adds no `without_transfer` tick. (V1's detector itself is pinned by its unit tests.)"""
    row, seen = _v1("gate_pos_v1", gold=0)
    assert seen["unbacked"] == 0, seen  # no hunger fell with nothing moved
    keys = {e["group_key"]: e["ticks"] for e in row.get("examples", [])}
    assert keys.get(f"{seen['group']}|without_transfer", 0) == 0, (keys, seen)


def test_v1_does_not_count_the_same_worker_when_it_pays_for_the_meal():
    row, paid = _v1("gate_pos_v1_control", gold=200)
    assert paid["purse_fell"] >= 1 and paid["unbacked"] == 0, paid  # its meal was charged, so the drop is backed
    keys = {e["group_key"]: e["ticks"] for e in row.get("examples", [])}
    assert keys.get(f"{paid['group']}|without_transfer", 0) == 0, (keys, paid)
