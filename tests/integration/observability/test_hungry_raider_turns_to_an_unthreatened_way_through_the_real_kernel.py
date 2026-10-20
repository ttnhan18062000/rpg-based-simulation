"""Raider 27 (crowded_frontier seed 45, the v1 gate's V3 death) in a forced equivalent, through the real kernel.

Hp 2/70, hunger 80, gold 10, at (54,40) with its hunger project aimed at inn 20003 in the west; a guard and two workers hold the walk at x 44-46 (pinned
there, alive, every tick; the two wild hunters nearby are removed so the east is quiet). With the re-choice (SURV-07, memo row 84) the project turns to the
forage node at (72,20) and the raider eats; with the re-choice off (the control) it shuttles on y 40 as in the gate run and does not eat in the same ticks.
"""
from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

TICKS = 120
FORAGE_AT = (72.0, 20.0)
PINNED = {11: (45.0, 41.0), 3: (46.0, 40.0), 2: (44.0, 40.0)}
REMOVED = (15, 18)


def _run_raider(run_id):
    from tools.test_architecture.rpg_gate_run import build_kernel

    kernel = build_kernel("crowded_frontier", 45, run_id)
    targets = []
    try:
        state = kernel.state
        entities = dict(state.entities)
        raider = entities[27]
        entities[27] = replace(raider, navigation=replace(raider.navigation, position=(54.0, 40.0)), combat=replace(raider.combat, hp=2, max_hp=70),
                               biological=replace(raider.biological, hunger=80.0, sleep_debt=0.0), inventory=replace(raider.inventory, gold=10))
        object.__setattr__(state, "entities", entities)
        for _ in range(TICKS):
            held = dict(kernel.state.entities)
            for eid, pos in PINNED.items():
                e = held[eid]
                held[eid] = replace(e, navigation=replace(e.navigation, position=pos), combat=replace(e.combat, hp=e.combat.max_hp, alive=True),
                                    lifecycle=replace(e.lifecycle, active=True, death_record=None))
            for eid in REMOVED:
                e = held[eid]
                held[eid] = replace(e, combat=replace(e.combat, hp=0, alive=False), lifecycle=replace(e.lifecycle, active=False))
            object.__setattr__(kernel.state, "entities", held)
            kernel.tick_once()
            raider = kernel.state.entities[27]
            project = raider.strategic.projects.get(raider.strategic.current_project_id) if raider.strategic.current_project_id else None
            if project is not None and project.kind == "hunger":
                targets.append(next(o for o in project.objectives if o.id == project.active_objective_id).target_position)
            if raider.biological.hunger < 70.0 or not raider.combat.alive:
                break
        return kernel.state.entities[27].biological.hunger, targets
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)


def test_a_hungry_raider_whose_route_to_the_inn_is_held_by_townsfolk_turns_to_the_forage_node_and_eats():
    hunger, targets = _run_raider("hunger_route_raider_fix")
    assert FORAGE_AT in targets, "the hunger project never turned to the forage node"
    assert hunger < 70.0


def test_the_same_raider_without_the_re_choice_shuttles_and_does_not_eat_in_the_same_ticks(monkeypatch):
    import src.systems.strategic_systems.intelligence as intelligence

    monkeypatch.setattr(intelligence, "retarget_if_threatened", lambda entity, state, project: None)
    hunger, targets = _run_raider("hunger_route_raider_control")
    assert FORAGE_AT not in targets
    assert hunger >= 80.0
