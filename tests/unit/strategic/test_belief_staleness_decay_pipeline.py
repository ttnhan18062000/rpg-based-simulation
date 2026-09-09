"""
Real-pipeline evidence for TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP.

`BeliefCycleSystem.decay_stale_leads()` (renamed from `decay_stale_beliefs()`) was already
correct, per-entity decision logic covered by `tests/unit/strategic/test_belief_cycle.py` -- but
had zero callers anywhere, so LEG-RPG-150's documented staleness decay had never executed once in
a real simulation. This module tests the real per-tick wiring
(`BeliefCycleSystem.resolve_lead_staleness()`, called from `src/engine/pipeline.py` between
`strategic_intelligence` and `lead_contradiction`), not the already-covered per-entity logic.
"""
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ResourceNodeState
from src.core.strategic import LeadState, LeadCertainty
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.systems.strategic_systems.belief import BeliefCycleSystem


def _entity_with_lead(entity_id, lead, extra_leads=None):
    leads = {lead.id: lead}
    if extra_leads:
        leads.update({l.id: l for l in extra_leads})
    entity = (
        V2EntityBuilder(entity_id)
        .kind("ACTOR")
        .location(0.0, 0.0)
        .combat(hp=100, atk=10, alive=True)
        .lifecycle(active=True)
        .build()
    )
    return replace(entity, strategic=replace(entity.strategic, leads=leads))


def test_resolve_lead_staleness_demotes_stale_lead_from_real_per_tick_call():
    """The real per-tick orchestrator (not decay_stale_leads() in isolation) demotes a stale lead
    with no contradiction involved."""
    stale_lead = LeadState(
        id="lead_stale", kind="location", subject="gold",
        certainty=LeadCertainty.APPROXIMATE, discovered_tick=10,
    )
    entity = _entity_with_lead(1, stale_lead)
    state = AuthoritativeState(entities={1: entity}, tick=100, seed=1)

    update = BeliefCycleSystem.resolve_lead_staleness(state)

    assert 1 in update.entity_updates
    updated_leads = update.entity_updates[1].strategic.leads_add_or_update
    assert len(updated_leads) == 1
    assert updated_leads[0].id == "lead_stale"
    assert updated_leads[0].certainty == LeadCertainty.VAGUE


def test_resolve_lead_staleness_leaves_precise_lead_untouched():
    precise_lead = LeadState(
        id="lead_precise", kind="location", subject="gold",
        certainty=LeadCertainty.PRECISE, discovered_tick=10,
    )
    entity = _entity_with_lead(1, precise_lead)
    state = AuthoritativeState(entities={1: entity}, tick=100, seed=1)

    update = BeliefCycleSystem.resolve_lead_staleness(state)

    assert 1 not in update.entity_updates


def test_resolve_lead_staleness_skips_dead_entities():
    stale_lead = LeadState(
        id="lead_stale", kind="location", subject="gold",
        certainty=LeadCertainty.APPROXIMATE, discovered_tick=10,
    )
    entity = _entity_with_lead(1, stale_lead)
    entity = replace(entity, combat=replace(entity.combat, alive=False))
    state = AuthoritativeState(entities={1: entity}, tick=100, seed=1)

    update = BeliefCycleSystem.resolve_lead_staleness(state)

    assert 1 not in update.entity_updates


def test_real_pipeline_stale_and_contradicted_lead_ends_exhausted_not_vague():
    """Phase-ordering proof: a lead that is both stale (age > 50 ticks) and contradicted
    (its resource node is depleted) in the same tick must end up EXHAUSTED (lead_contradiction's
    own unconditional write), not VAGUE (belief_staleness_decay's own one-step demotion) --
    verifying this ticket's own investigation.md ordering reasoning empirically, not just
    architecturally."""
    lead = LeadState(
        id="lead_both", kind="resource", subject="moon_resin",
        certainty=LeadCertainty.APPROXIMATE, discovered_tick=10,
    )
    entity = _entity_with_lead(1, lead)
    depleted_node = ResourceNodeState(
        id=99, kind="node", position=(5.0, 5.0), yields_item="moon_resin",
        remaining_charges=0, max_charges=10, required_ticks=5,
    )
    state = AuthoritativeState(
        entities={1: entity}, resource_nodes={99: depleted_node}, tick=100, seed=1,
    )
    raw_update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)}, force_full_scan=True)

    refined = AuthoritativeApplyPipeline.refine(state, raw_update)

    ent_upd = refined.entity_updates[1]
    matching = [l for l in ent_upd.strategic.leads_add_or_update if l.id == "lead_both"]
    assert matching, "expected lead_both to appear in the merged leads_add_or_update"
    # Last-applied wins per StateUpdate.merge_many()'s own per-entity EntityUpdate.merge() ->
    # StrategicUpdate.merge() (list concatenation, dict-overwrite-by-id on apply) -- the final
    # entry in the list is what actually lands in state, so check the LAST match, not just any.
    assert matching[-1].certainty == LeadCertainty.EXHAUSTED, (
        f"expected contradiction's own EXHAUSTED to win over decay's own VAGUE, "
        f"got {matching[-1].certainty}"
    )


def test_capacity_enforcement_prunes_newly_decayed_lead_over_fresh_ones():
    """Once decay is live, a lead demoted this same tick scores lower in
    CapacityEnforcementPhase's own pruning and should be the one removed under capacity
    pressure -- not merely "a different lead gets removed now", but specifically the
    lower-certainty one, per this ticket's own AC.

    Calls the real BeliefCycleSystem.resolve_lead_staleness() (this ticket's own new code) and
    the real CapacityEnforcementPhase.enforce() (pre-existing, unmodified), but not the full
    AuthoritativeApplyPipeline.refine() -- confirmed via direct tracing that
    StrategicIntelligenceSystem.fused_strategic_pass() (an earlier, unrelated phase) has its own
    independent lead-count-management side effect that removes a lead under >max_leads pressure
    before capacity_enforcement itself ever runs, for reasons unrelated to decay or capacity
    scoring -- constructing a state with more leads than max_leads to exercise
    capacity_enforcement's own scoring in isolation would silently test that unrelated mechanism
    instead. Composing the two real, targeted functions this AC actually names avoids that
    interference while keeping both sides of the interaction genuinely real, not mocked."""
    stale_lead = LeadState(
        id="lead_stale", kind="location", subject="stale_subject",
        certainty=LeadCertainty.APPROXIMATE, discovered_tick=10,
    )
    fresh_leads = [
        LeadState(
            id=f"lead_fresh_{i}", kind="location", subject=f"subject_{i}",
            certainty=LeadCertainty.APPROXIMATE, discovered_tick=99,
        )
        for i in range(7)
    ]
    entity = _entity_with_lead(1, stale_lead, extra_leads=fresh_leads)
    assert len(entity.strategic.leads) == 8 == entity.strategic.profile.max_leads

    state = AuthoritativeState(entities={1: entity}, tick=100, seed=1)

    # Real decay output for this tick (lead_stale: APPROXIMATE -> VAGUE), merged with a genuinely
    # NEW lead this same tick -- mirroring a real rumor/observation arriving while already at
    # capacity, the actual real-world trigger for CapacityEnforcementPhase's own pruning branch
    # (its trigger check only fires on a net increase in distinct lead count; decay alone, an
    # update to an already-existing key, never causes one).
    decay_update = BeliefCycleSystem.resolve_lead_staleness(state)
    new_lead = LeadState(
        id="lead_new", kind="location", subject="new_subject",
        certainty=LeadCertainty.APPROXIMATE, discovered_tick=100,
    )
    new_lead_update = StateUpdate(entity_updates={
        1: EntityUpdate(
            entity_id=1,
            strategic=StrategicUpdate(leads_add_or_update=[new_lead]),
        )
    })
    update = new_lead_update.merge(decay_update)

    from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase
    refined = CapacityEnforcementPhase.enforce(state, update)

    ent_upd = refined.entity_updates[1]
    removed_ids = set(ent_upd.strategic.leads_remove)
    assert "lead_stale" in removed_ids, (
        f"expected the newly-decayed (now VAGUE, score 0.3) lead to be pruned over the fresh "
        f"(APPROXIMATE, score 0.7) ones under capacity pressure; removed={removed_ids}"
    )
    assert "lead_new" not in removed_ids
    for fresh in fresh_leads:
        assert fresh.id not in removed_ids
