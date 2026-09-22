"""Runtime-evidence program, value-differential axis (TCK-20260921-MECHANISM-PROGRESSION-VALUE-
DIFFERENTIAL-INSTRUMENT), wave 2: applies the instrument to `entity_role`
(`src/core/enums.py::EntityRole`) via the real branch it gates inside
`EvolutionSystem.evaluate()` (`src/engine/evolution.py:112-132`): on a level-up, a HERO-role
entity gets `unspent_ap_delta`/`learned_skills` (the AP/skill-tree branch); any other role gets
real attribute deltas scaled by the entity's own aptitude (`vitality_delta`/`strength_delta`/
`endurance_delta`, the non-hero stat-growth branch). Both branches are real, unconditional code in
the same method -- this differential confirms `entity.identity.role`'s own value genuinely
selects between them, not merely that a level-up happens.

Immediate/deterministic, same-tick outcome (no §5.1 horizon concern): the branch is selected and
applied within `EvolutionSystem.evaluate()`, which runs inside the same real Kernel tick as the
kill that triggers the level-up -- reuses the exact forced-kill staging this program's own
`evolution`/`xp_leveling` value-differential already established (goblin attacks a staged-HP=1
orc), with the attacker's own `evolution_points` staged at 95 (one level-1 kill's 10 XP crosses
the real 100-XP threshold -- the same real positive control `evolution`'s own registry entry
already cites) and only the attacker's `identity.role` varied between arms.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.core.state import TaskComponent
from src.core.enums import EntityRole

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
ORC_ID = 2
SEED = 42


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _run_arm(*, attacker_role: EntityRole):
    state = _compile_world()
    goblin = state.entities[GOBLIN_ID]
    orc = state.entities[ORC_ID]

    goblin = replace(
        goblin,
        navigation=replace(goblin.navigation, position=(0.0, 0.0)),
        identity=replace(goblin.identity, role=attacker_role, evolution_points=95),
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": ORC_ID}),
    )
    orc = replace(
        orc,
        navigation=replace(orc.navigation, position=(1.0, 0.0)),
        combat=replace(orc.combat, hp=1),
    )

    new_entities = dict(state.entities)
    new_entities[GOBLIN_ID] = goblin
    new_entities[ORC_ID] = orc
    object.__setattr__(state, "entities", new_entities)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
    return final_state.entities[GOBLIN_ID]


def test_hero_role_takes_the_ap_and_skills_branch_on_level_up():
    """Positive control: role=HERO must produce unspent_ap on level-up (this branch's own real
    output), and the level-up itself must actually have happened (evolution_level moved), proving
    the scenario window is long enough for the outcome to be computed."""
    goblin_after = _run_arm(attacker_role=EntityRole.HERO)

    assert goblin_after.identity.evolution_level == 2, (
        "scenario reach check: expected the staged kill (95 + 10 XP) to cross the level-2 "
        f"threshold, got evolution_level={goblin_after.identity.evolution_level}."
    )
    assert goblin_after.identity.unspent_ap > 0, (
        f"entity_role mechanic: expected HERO role to grant unspent_ap on level-up, got "
        f"unspent_ap={goblin_after.identity.unspent_ap}."
    )


def test_non_hero_role_takes_the_attribute_growth_branch_on_level_up_instead():
    """Negative control (same real level-up, only role varied): a non-HERO role (GUARD, this
    world's own compiled role for the goblin) must NOT grant unspent_ap -- it takes the other real
    branch (attribute deltas) instead. Proves role's own value, not just the level-up itself,
    selects the outcome."""
    goblin_after = _run_arm(attacker_role=EntityRole.GUARD)

    assert goblin_after.identity.evolution_level == 2, (
        "scenario reach check: expected the staged kill (95 + 10 XP) to cross the level-2 "
        f"threshold, got evolution_level={goblin_after.identity.evolution_level}."
    )
    assert goblin_after.identity.unspent_ap == 0, (
        "entity_role mechanic negative control: expected non-HERO role to NOT grant unspent_ap on "
        f"level-up, got unspent_ap={goblin_after.identity.unspent_ap}."
    )
