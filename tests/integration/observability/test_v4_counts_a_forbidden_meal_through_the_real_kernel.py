"""V4 reads CONSUMPTION through the real pipeline (TCK-20261019-V4-COUNTS-CONSUMPTION-NOT-ACQUISITION).

The ledger observes an update whose resource intents are already consumed (`economy.py` clears `resource_transfers` after resolution), so it reads the eaten
item from what left the eater's inventory. A meat-only body is given a plant food and a hunger need, and the diet gate that normally keeps it from eating
is forced open for the test; the real kernel, apply path and ledger then count the meal.
"""
from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_a_meat_only_body_that_eats_plant_food_in_a_real_run_is_counted(monkeypatch):
    import src.engine.domain.core_actions as core_actions
    import src.engine.tactical_rest as tactical_rest
    from src.ai.goals.kind_group import kind_group
    from src.core.state import ItemStack
    from src.observability.run_ledger import RunLedger
    from tools.test_architecture.rpg_gate_run import build_kernel

    monkeypatch.setattr(tactical_rest, "can_eat_item", lambda *a, **k: True)  # the gate under test is the OBSERVER, not the diet gate
    monkeypatch.setattr(core_actions, "can_eat_item", lambda *a, **k: True)
    run_id = "v4_real_pipeline_forbidden_meal"
    kernel = build_kernel("frontier_living_world", 42, run_id)
    try:
        state = kernel.state
        wolf = next(e for e in state.entities.values() if kind_group(e) == "meat" and e.combat.alive)
        entities = dict(state.entities)
        entities[wolf.id] = replace(wolf, biological=replace(wolf.biological, hunger=95.0),
                                    inventory=replace(wolf.inventory, items=[ItemStack(item_id="wild_berries", quantity=2)]))
        object.__setattr__(state, "entities", entities)
        for _ in range(40):
            kernel.tick_once()
            if RunLedger._diet_breaches:
                break
        assert RunLedger._diet_breaches == {"meat|CARRIED_FOOD|wild_berries": 1}
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
