"""Runtime-evidence program, batch 1 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION).
Does `belief_cycle` -- specifically LEG-RPG-150 lead-staleness decay
(`src/systems/strategic_systems/belief.py::BeliefCycleSystem.decay_stale_leads`) -- actually demote
a stale lead's certainty through the real per-tick pipeline, not just a code trace confirming the
threshold check exists?

Real, unconditional pipeline entry point (no feature-flag gate): `src/engine/pipeline.py:408`,
`run_phase("belief_staleness_decay", update, lambda u: u.merge(BeliefCycleSystem.resolve_lead_staleness(state)))`,
between `strategic_intelligence` and `lead_contradiction` every tick.

World: `data/worlds/mechanic_scenario_combat_judgement_withdrawal/` -- reused as-is (real, compiled,
catalog-driven goblin_scout vs orc_warchief), same world the two prior scenarios in this directory
already use. Only `entity.strategic.leads` is staged here; combat/navigation fields are left at
their compiled defaults since this scenario doesn't dispatch any action.

Differential design, per `docs/plans/mechanic_verification_scenarios_proposal.md` §3.3: same staged
lead (`certainty=APPROXIMATE`, `discovered_tick=0`), same real `Kernel.tick_once()` dispatch, only
`state.tick` differs --
- "mechanism present" (the staleness threshold is cleared): `state.tick=50` (`50 - 0 >= 50`, the
  real `stale_threshold` default) -- the lead must demote to `VAGUE`.
- "mechanism absent" (the threshold is not cleared): `state.tick=10` (`10 - 0 < 50`) -- the lead
  must stay `APPROXIMATE`.
A scenario showing the same outcome in both conditions would not have tested the decay mechanism,
whatever its name claims.
"""
import os
from dataclasses import replace

from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from src.engine.kernel import Kernel
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.core.strategic import LeadState, LeadKind, LeadCertainty

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
GOBLIN_ID = 1
LEAD_ID = "lead_belief_cycle_scenario"
SEED = 42


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _stage_lead_and_tick(state, *, current_tick: int):
    """Stages a single APPROXIMATE lead, discovered at tick 0, on the goblin -- the only varied
    precondition is `current_tick` itself (via `state.tick`, what `resolve_lead_staleness` reads
    for `current_tick`), matching the readiness-gate scenario's own "one precondition varied"
    discipline."""
    goblin = state.entities[GOBLIN_ID]
    lead = LeadState(
        id=LEAD_ID,
        kind=LeadKind.LOCATION,
        subject="test_resource_node",
        discovered_tick=0,
        certainty=LeadCertainty.APPROXIMATE,
    )
    goblin = replace(goblin, strategic=replace(goblin.strategic, leads={LEAD_ID: lead}))

    new_entities = dict(state.entities)
    new_entities[GOBLIN_ID] = goblin
    object.__setattr__(state, "entities", new_entities)
    object.__setattr__(state, "tick", current_tick)
    return state


def _run_one_tick_and_get_lead_certainty(state):
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()

    lead = final_state.entities[GOBLIN_ID].strategic.leads.get(LEAD_ID)
    assert lead is not None, "the staged lead vanished entirely -- a real scenario-staging defect"
    return lead.certainty


def test_lead_demotes_to_vague_once_the_staleness_threshold_is_cleared():
    """Mechanism present: current_tick(50) - discovered_tick(0) = 50 >= stale_threshold(50). The
    decay must fire -- APPROXIMATE -> VAGUE -- through the real, unconditional pipeline phase."""
    state = _compile_world()
    state = _stage_lead_and_tick(state, current_tick=50)

    certainty = _run_one_tick_and_get_lead_certainty(state)

    assert certainty == LeadCertainty.VAGUE, (
        "belief_cycle mechanic: expected the staleness decay "
        "(BeliefCycleSystem.decay_stale_leads, stale_threshold=50) to demote a lead discovered at "
        f"tick 0 once current_tick=50, but certainty was {certainty!r} -- the decay did not fire "
        "through the real per-tick pipeline."
    )


def test_lead_stays_approximate_when_the_staleness_threshold_is_not_cleared():
    """Mechanism absent: current_tick(10) - discovered_tick(0) = 10 < stale_threshold(50). The
    differential half -- without this passing too, the first test could pass for a reason unrelated
    to the staleness check (e.g. every lead getting demoted regardless of age), and the scenario
    would not actually be testing the threshold specifically."""
    state = _compile_world()
    state = _stage_lead_and_tick(state, current_tick=10)

    certainty = _run_one_tick_and_get_lead_certainty(state)

    assert certainty == LeadCertainty.APPROXIMATE, (
        "belief_cycle mechanic: expected a lead discovered at tick 0 to stay APPROXIMATE at "
        f"current_tick=10 (below the 50-tick threshold), but certainty was {certainty!r} -- either "
        "the decay is firing too early (a real defect), or something unrelated to this mechanism "
        "changed the lead."
    )
