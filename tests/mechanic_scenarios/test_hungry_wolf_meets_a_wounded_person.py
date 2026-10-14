"""Designer check (decisions 44, 47, 49): a HUNGRY wolf that meets a weak or wounded person, with nothing else in reach, attacks. In M0 it does not
(strict xfail below, naming M1's one-appraisal child); the control, a fed wolf, passes.

"Wolves and people avoid each other unless need and advantage meet": the need is a hungry meat-eater, the advantage is a person it believes it
can overcome (here a wounded one). Staged as in LB-S20: a lone wolf and one person, no building, no food node, through the real kernel. The
control is the same person beside a wolf that is not hungry: it does not attack. Nothing names a wolf or a person: the relation is derived.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world

pytestmark = [pytest.mark.domain("combat"), pytest.mark.level("scenario")]

WORLD, SEED, WINDOW = "frontier_living_world", 42, 80
HUNGRY, FED = 85.0, 0.0


def _species(entity):
    return (entity.identity.properties or {}).get("species_id")


def _wolf_attacks_person(*, hunger, person_hp):
    state = compile_world(WORLD, SEED)
    wolf = next(e for e in state.entities.values() if _species(e) == "wolf")
    person = next(e for e in state.entities.values() if _species(e) == "human")
    x, y = wolf.navigation.position
    wolf = replace(wolf, biological=replace(wolf.biological, hunger=hunger))
    person = replace(person, navigation=replace(person.navigation, position=(x + 3.0, y), target=None),
                     combat=replace(person.combat, hp=person_hp, max_hp=max(person.combat.max_hp, person_hp)),
                     inventory=replace(person.inventory, items=()))
    state = replace(state, entities={wolf.id: wolf, person.id: person}, buildings={}, building_tiles={}, resource_nodes={})
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True}, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
    try:
        for _ in range(WINDOW):
            kernel.tick_once()
            w = kernel._state.entities[wolf.id]
            if w.task.payload.get("action") == "ATTACK" and w.task.payload.get("target_id") == person.id:
                return True
    finally:
        kernel.shutdown()
    return False


@pytest.mark.xfail(strict=True, reason="M0 kind-prior limit: a tie in kind bands (wolf medium, human medium) resolves to cannot-overcome and the belief never reads the target's "
                   "visible condition (appraisal.can_overcome, KNOW-04). Milestone 1's one-appraisal child (D44 / D47 / D49) adds it; remove this xfail then.")
def test_a_hungry_wolf_attacks_a_wounded_person_with_nothing_else_in_reach():
    assert _wolf_attacks_person(hunger=HUNGRY, person_hp=5)


def test_control_a_fed_wolf_does_not_attack_the_same_person():
    assert not _wolf_attacks_person(hunger=FED, person_hp=5)
