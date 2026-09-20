"""Runtime-evidence program, batch 2 (TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION,
Bucket C, closing the one honest gap this program's own close-out surfaced: `cognition_capacity_fatigue`
was reachable and unconditional (`CapacityEnforcementPhase.enforce()`,
`run_phase("capacity_enforcement", ...)` with no flag argument, `must_run_every_tick=True` in
`phase_graph.py`) but never got a scenario built or a disposition recorded across 4 waves.

The real staging difficulty that caused it to keep falling through: `enforce()` only considers an
entity that already has a real `StrategicUpdate` staged THIS TICK by an EARLIER phase
(`ent_upd = refined_entity_updates.get(e_id); if not ent_upd or not ent_upd.strategic: continue`,
`capacity_enforcement.py`) -- an entity that is genuinely over its own `profile.max_leads` cap in
raw compiled state, with nothing else proposing anything for it that tick, is silently skipped
entirely, not trimmed. A scenario staging only "9 leads on the entity" and nothing else would test
nothing.

**Resolved by chaining two already-validated real mechanisms, not by forcing a route**: this
program's own `belief_cycle` scenario already established that a stale lead
(`discovered_tick=0`, `state.tick=50`) produces a real, non-empty `StrategicUpdate` through
`BeliefCycleSystem.resolve_lead_staleness()` -- the real, unconditional `belief_staleness_decay`
phase (`pipeline.py:408`), which runs BEFORE `capacity_enforcement` (`pipeline.py:427`) in the same
tick. Staging one stale lead alongside the others gives `capacity_enforcement` a real, non-synthetic
`ent_upd.strategic` to work from, the same way a real corpus entity would if any other phase had
proposed anything for it that tick -- not a monkeypatch, not a hand-built `update.entity_updates`,
just two real mechanisms' own real preconditions staged together.

Differential design: 8 real "keeper" leads (`certainty=PRECISE`, the highest `_score_lead()` score,
safe from trimming) plus one real stale lead (`certainty=APPROXIMATE`, `discovered_tick=0` --
decays to `VAGUE`, the lowest score among survivors, via the real staleness-decay phase), only the
keeper COUNT differs --
- "mechanism present" (9 leads total, exceeds `profile.max_leads=8`): the stale lead -- now the
  real lowest-scored one after its own real decay -- must be trimmed by
  `CapacityService.trim_dict()`, leaving exactly the 8 keepers.
- "mechanism absent" (8 leads total, exactly at the cap): nothing exceeds `max_leads`, so nothing
  is trimmed -- the stale lead survives, still real and still decayed to `VAGUE`.
Per §5 item 5: the negative arm's reach is confirmed directly, not inferred from the outcome alone
-- the stale lead's own certainty is checked as `VAGUE` in BOTH conditions, proving
`belief_staleness_decay` genuinely produced a real `ent_upd.strategic` in the at-cap case too, so
`capacity_enforcement`'s own "nothing trimmed" result is a genuine reached-and-declined evaluation
(`len(leads) + len(leads_add_or_update) <= max_leads`), not the entity being skipped before ever
being considered.
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
STALE_LEAD_ID = "stale_lead"
SEED = 42


def _compile_world():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _stage_leads(state, *, n_keepers: int):
    goblin = state.entities[GOBLIN_ID]
    leads = {
        f"keeper_{i}": LeadState(
            id=f"keeper_{i}", kind=LeadKind.LOCATION, subject=f"subj_{i}",
            discovered_tick=0, certainty=LeadCertainty.PRECISE,
        )
        for i in range(n_keepers)
    }
    leads[STALE_LEAD_ID] = LeadState(
        id=STALE_LEAD_ID, kind=LeadKind.LOCATION, subject="stale_subj",
        discovered_tick=0, certainty=LeadCertainty.APPROXIMATE,
    )
    goblin = replace(goblin, strategic=replace(goblin.strategic, leads=leads))

    new_entities = dict(state.entities)
    new_entities[GOBLIN_ID] = goblin
    object.__setattr__(state, "entities", new_entities)
    object.__setattr__(state, "tick", 50)  # cadence-free for belief_cycle; clears its own stale_threshold=50
    return state


def _run_one_tick_and_get_leads(state):
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
        final_state = kernel._state
    finally:
        kernel.shutdown()
    return final_state.entities[GOBLIN_ID].strategic.leads


def test_lowest_scored_lead_is_trimmed_when_over_the_real_cap():
    """Mechanism present: 9 real leads (max_leads=8, confirmed the compiled default). The stale
    lead, decayed to VAGUE by the real staleness-decay phase this same tick, is the lowest-scored
    survivor and must be the one CapacityService.trim_dict() removes through a real
    Kernel.tick_once()."""
    state = _compile_world()
    assert state.entities[GOBLIN_ID].strategic.profile.max_leads == 8, (
        "scenario staging assumption: max_leads changed from the compiled default -- re-check "
        "n_keepers below"
    )
    state = _stage_leads(state, n_keepers=8)

    leads = _run_one_tick_and_get_leads(state)

    assert len(leads) == 8, (
        f"cognition_capacity_fatigue mechanic: expected exactly 8 leads to survive trimming down "
        f"to max_leads, got {len(leads)}: {sorted(leads.keys())!r}."
    )
    assert STALE_LEAD_ID not in leads, (
        "cognition_capacity_fatigue mechanic: expected the lowest-scored (decayed-to-VAGUE) lead "
        f"to be the one trimmed, but it survived: {sorted(leads.keys())!r}."
    )


def test_nothing_is_trimmed_when_exactly_at_the_real_cap():
    """Mechanism absent: 8 real leads total (at, not over, max_leads=8). The differential half --
    without this passing too, the first test could pass for a reason unrelated to the cap check
    (e.g. the stale lead always getting removed regardless of count). Reach confirmed directly,
    per §5 item 5: the stale lead's own certainty is checked as VAGUE here too, proving the
    staleness-decay phase (and therefore a real ent_upd.strategic for capacity_enforcement to
    evaluate) genuinely ran in this condition -- "not trimmed" means reached-and-declined, not
    skipped-before-being-considered."""
    state = _compile_world()
    state = _stage_leads(state, n_keepers=7)

    leads = _run_one_tick_and_get_leads(state)

    assert len(leads) == 8, (
        f"cognition_capacity_fatigue mechanic: expected all 8 leads (at the cap, not over) to "
        f"survive, got {len(leads)}: {sorted(leads.keys())!r}."
    )
    assert STALE_LEAD_ID in leads, (
        "cognition_capacity_fatigue mechanic: expected the stale lead to survive when at (not "
        f"over) the cap, but it was removed: {sorted(leads.keys())!r}."
    )
    assert leads[STALE_LEAD_ID].certainty == LeadCertainty.VAGUE, (
        "scenario reach check (proposal doc §5 item 5): expected the stale lead to have genuinely "
        "decayed to VAGUE this tick (proving belief_staleness_decay produced a real "
        "ent_upd.strategic for capacity_enforcement to evaluate, not that the entity was skipped "
        f"before ever being considered), but got {leads[STALE_LEAD_ID].certainty!r}."
    )


def test_trim_dict_itself_works_when_called_directly():
    """Positive control: the trimming logic itself is not broken -- calling
    CapacityService.trim_dict() directly against a real over-cap dict produces the same real
    lowest-score-first removal the gated-present scenario above observes through the real
    pipeline."""
    from src.strategy.capacity import CapacityService
    from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase

    leads = {
        f"keeper_{i}": LeadState(id=f"keeper_{i}", kind=LeadKind.LOCATION, subject=f"subj_{i}", certainty=LeadCertainty.PRECISE)
        for i in range(8)
    }
    leads[STALE_LEAD_ID] = LeadState(id=STALE_LEAD_ID, kind=LeadKind.LOCATION, subject="stale_subj", certainty=LeadCertainty.VAGUE)

    removals = CapacityService.trim_dict(leads, max_size=8, score_func=CapacityEnforcementPhase._score_lead)

    assert removals == [STALE_LEAD_ID]
