"""V4 reads CONSUMPTION through the real pipeline, up to the emitted gate row (TCK-20261019-V4-COUNTS-CONSUMPTION-NOT-ACQUISITION).

The ledger observes an update whose resource intents are already consumed (`economy.py` clears `resource_transfers` after resolution), so it reads the eaten
item from what left the eater's inventory. A real ``build_kernel`` run, the real events file and the real ``rpg_gate_metrics.compute`` are used; a meat-only body
is given a plant food and a hunger need. With the diet gate forced open the V4 row fires; with the gate in place (the control) it does not.
"""
from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

pytestmark = pytest.mark.integration

WORLD, SEED = "frontier_living_world", 42


def _seed_hungry_meat_eater_with_berries(kernel) -> int:
    from src.ai.goals.kind_group import kind_group
    from src.core.state import ItemStack

    state = kernel.state
    wolf = next(e for e in state.entities.values() if kind_group(e) == "meat" and e.combat.alive)
    entities = dict(state.entities)
    entities[wolf.id] = replace(wolf, biological=replace(wolf.biological, hunger=95.0),
                                inventory=replace(wolf.inventory, items=[ItemStack(item_id="wild_berries", quantity=2)]))
    object.__setattr__(state, "entities", entities)
    return wolf.id


def _v4_row(run_id: str, ticks: int = 25, eater: Optional[List[int]] = None) -> Dict[str, Any]:
    from src.observability import rpg_gate_metrics
    from tools.test_architecture.rpg_gate_run import RunArtifacts, build_kernel

    run_dir = Path("data") / "runs" / run_id
    kernel = build_kernel(WORLD, SEED, run_id)
    try:
        seeded = _seed_hungry_meat_eater_with_berries(kernel)
        if eater is not None:
            eater.append(seeded)
        for _ in range(ticks):
            kernel.tick_once()
    finally:
        kernel.shutdown()  # flushes the recorded event stream before the metrics read it
    try:
        result = rpg_gate_metrics.compute(RunArtifacts(WORLD, SEED, ticks, "test", kernel.state, run_dir, seeds=(SEED,)))
        rows: List[Dict[str, Any]] = list(result["metrics"] if isinstance(result, dict) else result)
        return next(r for r in rows if r["id"] == "V4" and r.get("group") == "*")
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_a_meat_only_body_that_eats_plant_food_in_a_real_run_fires_the_v4_row(monkeypatch):
    import src.engine.domain.core_actions as core_actions
    import src.engine.tactical_rest as tactical_rest
    from src.observability.run_ledger import MAX_EXAMPLES, RunLedger

    monkeypatch.setattr(tactical_rest, "can_eat_item", lambda *a, **k: True)  # the observer is under test, so the diet gate that normally refuses is opened
    monkeypatch.setattr(core_actions, "can_eat_item", lambda *a, **k: True)
    eater: List[int] = []
    row = _v4_row("v4_real_pipeline_forbidden_meal", eater=eater)
    assert row["violations"] > 0, row
    assert any(e.get("consumption") == "meat|CARRIED_FOOD|wild_berries" and e.get("group") == "meat" and e.get("source") == "CARRIED_FOOD"
               and e.get("item") == "wild_berries" for e in row["examples"]), row["examples"]
    named = [e for e in row["examples"] if "entity_id" in e]
    assert named and all(e["entity_id"] == eater[0] and e["source"] == "CARRIED_FOOD" and e["item"] == "wild_berries" and e["kind_group"] == "meat"
                         and isinstance(e["tick"], int) for e in named), row["examples"]  # the example names the forced meat-only body and its tick
    assert len(named) == min(RunLedger._diet_breaches["meat|CARRIED_FOOD|wild_berries"], MAX_EXAMPLES)
    assert RunLedger._diet_breaches.get("meat|CARRIED_FOOD|wild_berries", 0) >= 1  # the counter behind the row (no longer the proof)


def test_the_same_setup_with_the_diet_gate_in_place_gives_no_v4_violation():
    row = _v4_row("v4_real_pipeline_control")
    assert row["violations"] == 0, row
