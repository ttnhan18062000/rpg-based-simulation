"""SYNTHETIC worked examples of the shared scenario helper (tests/helpers/scenario.py).

Label: **synthetic**. These are test-only toys: they claim nothing about any gameplay rule and must not be
copied as proof of one. They show the pattern only: stage -> run -> observe, with a control arm.

Declared lane: `perf-cert-arena` (its pytest step lists `tests/mechanic_scenarios`);
tests/unit/tools/test_scenario_examples_lane.py checks that against .github/workflows/test.yml.
"""

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.state import AuthoritativeState
from tests.helpers.scenario import compile_world, run_scenario, run_with_control

LANE = "perf-cert-arena"
LABEL = "synthetic"

pytestmark = [pytest.mark.domain("substrate"), pytest.mark.level("kernel_integration")]


def _hand_built_state() -> AuthoritativeState:
    hero = V2EntityBuilder(1).location(0.0, 0.0).identity(role=EntityRole.HERO).build()
    monster = V2EntityBuilder(2).location(50.0, 50.0).identity(role=EntityRole.MONSTER).build()
    return AuthoritativeState(tick=0, seed=42, world_time=0, entities={1: hero, 2: monster})


def test_example_occurrence_and_effect_with_a_control_arm():
    """Toy claim: running N ticks advances the authoritative tick (occurrence) and changes state (effect);
    the control arm runs 0 ticks from the identical state, so the change cannot be pre-existing."""
    treatment = run_scenario(_hand_built_state(), ticks=3, observe=lambda s: s.tick)
    control = run_scenario(_hand_built_state(), ticks=0, observe=lambda s: s.tick)

    assert treatment.observed == 3
    assert control.observed == 0
    assert treatment.final_hash != control.final_hash


def test_example_run_with_control_stages_only_the_treatment_arm():
    """Toy claim: the treatment stage is applied to one arm only; arms share no state."""
    def stage_treatment(state):
        object.__setattr__(state, "world_time", 999)
        return state

    result = run_with_control(_hand_built_state, ticks=0, observe=lambda s: s.world_time,
                              stage_treatment=stage_treatment)

    assert result.treatment.observed == 999
    assert result.control.observed == 0


def test_example_compiled_world_runs_one_tick():
    """Toy claim: a declared world compiles and the kernel advances it one tick. No gameplay rule is claimed."""
    state = compile_world("mechanic_scenario_combat_judgement_withdrawal")
    ran = run_scenario(state, ticks=1, observe=lambda s: (s.tick, len(s.entities)))

    assert ran.observed[0] == 1
    assert ran.observed[1] > 0
