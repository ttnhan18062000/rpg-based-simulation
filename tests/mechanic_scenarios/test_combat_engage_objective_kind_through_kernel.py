"""A won ``COMBAT_ENGAGE`` goal reaches the project as a ``DEFEAT_ENEMY`` objective, through the real pipeline
(TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND, test_plan.md T3/T4).

World: ``mechanic_scenario_combat_judgement_withdrawal`` -- goblin_warband vs orc_clan, which the content
catalog calls hostile, two tiles apart. Before the fix the same run materialised these objectives as
``reach_location``; the resolver is never consulted on this path, so only a real ``Kernel.tick_once()`` proves
the wiring.

Deliberately NOT asserted here: that a decision-path attack resolves. Measured on this world, 300 ticks: the
two entities are tactically evaluated twice and then chase each other's last position without ever attacking.
That is ``TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES`` (entity id used as
a fixed-point target), which this ticket's plan forbids fixing here.
"""
import os

from src.config.profiles import PROD_SMALL
from src.core.strategic import ObjectiveKind
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
SEED = 42


def _run(ticks: int):
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True, "no_replay": True}, executor=LocalSequentialExecutor())
    objectives = {}
    try:
        for _ in range(ticks):
            kernel.tick_once()
            for entity in kernel._state.entities.values():
                for project in entity.strategic.projects.values():
                    if str(getattr(project.kind, "value", project.kind)) == "combat_engage":
                        for obj in project.objectives:
                            objectives[(entity.id, obj.id)] = (obj.kind, str(obj.target))
    finally:
        kernel.shutdown()
    return objectives


def test_won_combat_engage_materialises_a_defeat_enemy_objective_targeting_the_hostile():
    objectives = _run(40)

    assert objectives, "COMBAT_ENGAGE must win for a catalog-hostile adjacent pair"
    assert {kind for kind, _ in objectives.values()} == {ObjectiveKind.DEFEAT_ENEMY}
    assert {(eid, target) for (eid, _), (_, target) in objectives.items()} == {(1, "2"), (2, "1")}


def test_objective_materialisation_is_deterministic():
    assert _run(40) == _run(40)
