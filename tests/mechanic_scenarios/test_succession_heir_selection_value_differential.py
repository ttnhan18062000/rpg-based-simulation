"""Runtime-evidence program, value-differential axis (TCK-20260921-MECHANISM-PROGRESSION-VALUE-
DIFFERENTIAL-INSTRUMENT), wave 3: applies the instrument to `succession`
(`LifecycleSystem._select_default_heir`, `src/systems/lifecycle_systems/lifecycle.py:121-134`) --
the real bond-strength-scored heir fallback: `score = 0.6 * bond.familiarity + 0.4 *
((bond.sentiment + 1.0) / 2.0)`, highest score wins (ties broken by `last_interaction_tick` then
`target_id`).

Pure, deterministic, no RNG -- same shape as `readiness_speed_scaling`'s own calibration
(structurally immune to the determinism trap) -- and the outcome (who is selected as heir) is
fully computed within the same tick the deceased entity dies, reusing `aging_death`'s own
guaranteed-death staging (`age_ticks >= max_age_ticks`). No §5.1 horizon concern.

World: `crowded_frontier` (a real, multi-entity corpus world already used elsewhere in this arc's
own corpus instrumentation, e.g. `xp_leveling`'s own registry note) -- reused for its real entity
count (38, all real content-spawned, all with empty `social.bonds` at compile time, since bonds
accumulate through play rather than being authored at spawn). Three real entities used: one staged
to die of old age (reusing `aging_death`'s own technique), two staged as real bond candidates.
Only the deceased entity's own `social.bonds` component is touched -- the two candidates
themselves are untouched, real, content-spawned entities.

Two real arms:
- Positive control: candidate A's bond scores clearly higher than candidate B's in one arm, and
  the reverse in a second run -- confirms the WINNER tracks the higher score, not a fixed
  candidate or iteration-order artifact.
- Negative control: `last_interaction_tick` is documented as a tie-break field, read only when
  scores are equal (`candidates.sort(key=lambda c: (-c[0], -c[1], c[2]))` -- the score dominates
  the sort key). Varying it while the score gap stays decisive must not change the winner --
  proving this instrument does not report a difference whenever any field on the bond is
  perturbed, only when the actual scoring input changes the outcome.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.core.models.social import SocialBond

WORLD_ID = "crowded_frontier"
SEED = 42
DECEASED_ID = 1
CANDIDATE_A_ID = 2
CANDIDATE_B_ID = 3


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _run_arm(*, bond_a: SocialBond, bond_b: SocialBond):
    state = _compile_world()
    deceased = state.entities[DECEASED_ID]
    deceased = replace(
        deceased,
        lifecycle=replace(deceased.lifecycle, age_ticks=1000, max_age_ticks=999),
        social=replace(deceased.social, bonds={CANDIDATE_A_ID: bond_a, CANDIDATE_B_ID: bond_b}),
    )
    new_entities = dict(state.entities)
    new_entities[DECEASED_ID] = deceased
    object.__setattr__(state, "entities", new_entities)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
    return final_state.entities[DECEASED_ID]


def test_higher_scored_candidate_becomes_heir_in_either_direction():
    """Positive control: run twice, swapping which candidate has the higher bond score, and
    confirm the heir selection swaps with it -- proving familiarity/sentiment's own value, not a
    fixed candidate or iteration order, decides the outcome."""
    high = SocialBond(target_id=0, familiarity=0.9, sentiment=0.9, last_interaction_tick=10)
    low = SocialBond(target_id=0, familiarity=0.1, sentiment=-0.5, last_interaction_tick=10)

    deceased_after_a_wins = _run_arm(bond_a=high, bond_b=low)
    deceased_after_b_wins = _run_arm(bond_a=low, bond_b=high)

    assert deceased_after_a_wins.lifecycle.active is False, (
        "scenario reach check: the deceased entity must actually have died this tick for heir "
        "selection to have run at all."
    )
    assert deceased_after_a_wins.lifecycle.heir_entity_id == CANDIDATE_A_ID, (
        f"succession mechanic: expected the higher-scored candidate A to be selected heir, got "
        f"heir_entity_id={deceased_after_a_wins.lifecycle.heir_entity_id}."
    )
    assert deceased_after_b_wins.lifecycle.heir_entity_id == CANDIDATE_B_ID, (
        f"succession mechanic: expected the selection to swap to candidate B when B has the "
        f"higher score, got heir_entity_id={deceased_after_b_wins.lifecycle.heir_entity_id}."
    )


def test_last_interaction_tick_does_not_override_a_decisive_score_gap():
    """Negative control: last_interaction_tick is a tie-break field only (read after score in the
    sort key) -- with a decisive score gap already in place, varying it (giving the LOWER-scored
    candidate the more recent interaction) must not flip the outcome."""
    winner_bond = SocialBond(target_id=0, familiarity=0.9, sentiment=0.9, last_interaction_tick=1)
    loser_bond_with_more_recent_interaction = SocialBond(
        target_id=0, familiarity=0.1, sentiment=-0.5, last_interaction_tick=9999
    )

    deceased_after = _run_arm(bond_a=winner_bond, bond_b=loser_bond_with_more_recent_interaction)

    assert deceased_after.lifecycle.heir_entity_id == CANDIDATE_A_ID, (
        "succession mechanic negative control: expected the decisive score gap to still pick "
        f"candidate A despite candidate B's more recent last_interaction_tick, got "
        f"heir_entity_id={deceased_after.lifecycle.heir_entity_id}."
    )
