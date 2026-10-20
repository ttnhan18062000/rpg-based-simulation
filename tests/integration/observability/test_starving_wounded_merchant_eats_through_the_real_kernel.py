"""Merchant 37 (frontier_living_world seed 42, the v1 gate's V3 death) in a forced equivalent, through the real kernel.

Wounded (hp 10/85), gold 0, hunger 100, beside inn 20003 in unclaimed space, with predator_hunter 45 adjacent. With starvation weighed as a present threat
(SURV-07 amendment, row 83) the merchant takes a hunger project and eats; with the old threat gate restored (the control) it does not within the same ticks.
"""
from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

TICKS = 60


def _run_merchant(run_id):
    from tools.test_architecture.rpg_gate_run import build_kernel

    kernel = build_kernel("frontier_living_world", 42, run_id)
    try:
        state = kernel.state
        merchant, hunter = state.entities[37], state.entities[45]
        entities = dict(state.entities)
        entities[37] = replace(merchant, navigation=replace(merchant.navigation, position=(41.0, 31.0)), combat=replace(merchant.combat, hp=10, max_hp=85),
                               biological=replace(merchant.biological, hunger=100.0, sleep_debt=0.0), inventory=replace(merchant.inventory, gold=0, items=[]))
        entities[45] = replace(hunter, navigation=replace(hunter.navigation, position=(41.0, 30.0)))
        object.__setattr__(state, "entities", entities)
        for _ in range(TICKS):
            kernel.tick_once()
            if kernel.state.entities[37].biological.hunger < 90.0:
                break
        return kernel.state.entities[37].biological.hunger
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)


def test_a_starving_wounded_merchant_in_reach_of_an_inn_gets_a_hunger_project_and_eats():
    assert _run_merchant("v3_ii_merchant") < 90.0


def test_the_same_merchant_with_the_old_threat_gate_does_not_eat_in_the_same_ticks(monkeypatch):
    import src.ai.goals.scorers as scorers

    monkeypatch.setattr(scorers, "_hunger_escalated_unless_threatened", scorers._escalated_unless_threatened)
    assert _run_merchant("v3_ii_merchant_control") >= 90.0
