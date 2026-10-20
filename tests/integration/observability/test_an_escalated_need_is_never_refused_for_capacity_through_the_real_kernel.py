"""An escalated need is never refused for project capacity (TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY), through the real kernel.

Blacksmith 13 of crowded_frontier seed 45 holds three SUSPENDED resolve_blocker projects (the cap, `max_active_projects`, is 3; a SUSPENDED project counts as
live, divergence 2.77). In the v1 gate run it reached hunger 100 with no hunger project ever created and starved at tick 2237: the hunger goal won scoring
every brain tick and the capacity check threw it away. A hunger or sleep goal at or past its SURV-07 onset is admitted; below the onset the cap still refuses.
"""
from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _kernel(run_id):
    from tools.test_architecture.rpg_gate_run import build_kernel

    return build_kernel("crowded_frontier", 45, run_id)


def _close(kernel, run_id):
    try:
        kernel.shutdown()
    except Exception:
        pass
    shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)


def _fill_the_cap_and_stage(kernel, *, hunger, sleep_debt):
    """Blacksmith 13 next to inn 20003, three SUSPENDED projects (a full cap), the given needs and some gold."""
    from src.core.strategic import ProjectState, ProjectStatus

    state = kernel.state
    entities = dict(state.entities)
    e = entities[13]
    suspended = {
        f"proj_resolve_blocker_{i}": ProjectState(id=f"proj_resolve_blocker_{i}", kind="resolve_blocker", status=ProjectStatus.SUSPENDED,
                                                  objectives=[], active_objective_id="", created_tick=0, score=1.0)
        for i in (1, 2, 3)
    }
    entities[13] = replace(e, navigation=replace(e.navigation, position=(24.0, 39.0)),
                           biological=replace(e.biological, hunger=hunger, sleep_debt=sleep_debt), inventory=replace(e.inventory, gold=20),
                           strategic=replace(e.strategic, projects=suspended, current_project_id="", current_objective_id=""))
    object.__setattr__(state, "entities", entities)
    assert entities[13].strategic.profile.max_active_projects == 3


def _kinds(kernel):
    return [p.kind for p in kernel.state.entities[13].strategic.projects.values()]


def test_a_hungry_entity_past_the_onset_at_a_full_cap_gets_a_hunger_project_and_eats():
    run_id = "escalated_hunger_admitted"
    kernel = _kernel(run_id)
    try:
        _fill_the_cap_and_stage(kernel, hunger=70.0, sleep_debt=0.0)
        saw_hunger_project = False
        for _ in range(120):
            kernel.tick_once()
            saw_hunger_project = saw_hunger_project or "hunger" in _kinds(kernel)
        assert saw_hunger_project, "the hunger goal won but no hunger project was admitted at a full cap"
        assert kernel.state.entities[13].biological.hunger < 40.0, "the entity never ate"
    finally:
        _close(kernel, run_id)


def test_below_the_onset_the_cap_still_refuses():
    run_id = "escalated_hunger_below_onset"
    kernel = _kernel(run_id)
    try:
        _fill_the_cap_and_stage(kernel, hunger=40.0, sleep_debt=0.0)
        for _ in range(120):
            kernel.tick_once()
            assert "hunger" not in _kinds(kernel)
        assert sorted(_kinds(kernel)) == ["resolve_blocker"] * 3
    finally:
        _close(kernel, run_id)


def test_a_full_cap_is_exceeded_by_at_most_one_project_per_need():
    run_id = "escalated_one_per_need"
    kernel = _kernel(run_id)
    try:
        _fill_the_cap_and_stage(kernel, hunger=70.0, sleep_debt=70.0)
        for _ in range(150):
            kernel.tick_once()
            kinds = _kinds(kernel)
            assert kinds.count("hunger") <= 1 and kinds.count("fatigue") <= 1
            assert kinds.count("resolve_blocker") == 3, "nothing is evicted, abandoned or resumed"
            assert len(kinds) <= 5
    finally:
        _close(kernel, run_id)


def test_an_admitted_hunger_project_that_is_not_current_survives_the_bandwidth_trim_and_the_suspended_projects_are_untouched():
    """The trim (Law 194-197) works on the other projects only: a live hunger project is outside it, keyed on its kind, even when something else is current."""
    from src.core.strategic import ProjectStatus

    run_id = "escalated_hunger_not_current"
    kernel = _kernel(run_id)
    try:
        _fill_the_cap_and_stage(kernel, hunger=70.0, sleep_debt=0.0)
        for _ in range(200):
            kernel.tick_once()
            if "hunger" in _kinds(kernel):
                break
        assert "hunger" in _kinds(kernel), "no hunger project was admitted"
        # Something else becomes current (a suspended project resumes): the hunger project is SUSPENDED and not current, the other three stay at the cap.
        entities = dict(kernel.state.entities)
        e = entities[13]
        projects = {pid: (replace(p, status=ProjectStatus.SUSPENDED) if p.kind == "hunger" else p) for pid, p in e.strategic.projects.items()}
        resumed = "proj_resolve_blocker_1"
        projects[resumed] = replace(projects[resumed], status=ProjectStatus.ACTIVE, lock_until_tick=kernel.state.tick + 500)
        entities[13] = replace(e, strategic=replace(e.strategic, projects=projects, current_project_id=resumed, current_objective_id=""))
        object.__setattr__(kernel.state, "entities", entities)
        for _ in range(60):  # three brain ticks: the bandwidth law runs on each
            kernel.tick_once()
            kinds = _kinds(kernel)
            assert "hunger" in kinds, "the bandwidth trim removed the live hunger project"
            assert kinds.count("resolve_blocker") == 3, "a suspended project was evicted for the need project"
    finally:
        _close(kernel, run_id)


def test_the_gate_run_blacksmith_gets_a_hunger_project_by_about_hunger_95_and_eats_before_100__pins_current_scoring_not_the_rule():
    """The bs13 case itself, no staging. PINS CURRENT SCORING, NOT THE RULE: the hunger goal only beats town_return (about 139) near hunger 95, so the
    project appears around tick 1900; this tightens when the town_return outbid is fixed (TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95)."""
    run_id = "escalated_bs13_replay"
    kernel = _kernel(run_id)
    try:
        peak = 0.0
        project_at_hunger = None
        for _ in range(2100):
            kernel.tick_once()
            e = kernel.state.entities[13]
            peak = max(peak, e.biological.hunger)
            if project_at_hunger is None and "hunger" in _kinds(kernel):
                project_at_hunger = e.biological.hunger
        assert project_at_hunger is not None, "blacksmith 13 never got a hunger project"
        assert project_at_hunger <= 96.0, f"the hunger project came late, at hunger {project_at_hunger}"
        assert peak < 100.0, "blacksmith 13 reached hunger 100: it did not eat in time"
    finally:
        _close(kernel, run_id)
