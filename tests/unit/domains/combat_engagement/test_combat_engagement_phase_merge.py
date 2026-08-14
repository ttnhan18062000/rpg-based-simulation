"""TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS: the combat_engagement
phase's own real registration in AuthoritativeApplyPipeline.refine() must merge its own output
into the incoming StateUpdate, not replace it wholesale.

CombatEngagementPhase.apply() builds a fresh StateUpdate() with no awareness of prior phases'
own output. Without u.merge(...) in the real run_phase(...) call site
(src/engine/pipeline.py), every real StateUpdate produced by every earlier phase in the same
tick -- including action_routing's own real ATTACK dispatch and movement_routing -- was
silently discarded whenever ENABLE_COMBAT_ENGAGEMENT=ON and the phase actually ran.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate
from src.domains.optimization.feature_flags import FeatureMode
from src.engine.pipeline import AuthoritativeApplyPipeline


def _isolated_entity(entity_id: int, pos=(0.0, 0.0)):
    """An entity with no real neighbors within CombatEngagementPhase's own real radius (10.0),
    so the phase produces no entity_updates entry for it -- isolating whether a PRE-EXISTING
    entry for this entity, injected by this test to simulate an earlier real phase's own
    output, survives the phase's own real chaining."""
    return (
        V2EntityBuilder(entity_id)
        .kind("monster")
        .location(*pos)
        .combat(hp=100, max_hp=100, alive=True, readiness=0.0)
        .lifecycle(active=True)
        .build()
    )


def test_combat_engagement_preserves_prior_phase_updates_when_flag_on():
    entity = _isolated_entity(1, pos=(0.0, 0.0))
    state = AuthoritativeState(
        tick=10, seed=42, entities={1: entity},
        feature_flags={"ENABLE_COMBAT_ENGAGEMENT": FeatureMode.ON},
    )
    # Simulate an earlier real phase (e.g. action_routing) having already produced a real
    # EntityUpdate for entity 1 this tick. property_updates carries an arbitrary, uniquely-named
    # marker key -- no other real phase in the pipeline reads or writes this key, so its survival
    # or loss isolates purely whether combat_engagement's own real chaining preserves prior state
    # (unlike readiness_delta, which a real, unrelated passive-regen phase later in the same
    # chain legitimately recomputes for any entity, making it unsuitable as a probe here).
    incoming = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, property_updates={"__test_prior_phase_marker__": "present"}),
    })

    result = AuthoritativeApplyPipeline.refine(state, incoming)

    upd = result.entity_updates.get(1)
    assert upd is not None, (
        "prior phase's own real EntityUpdate for entity 1 was lost -- combat_engagement's own "
        "run_phase() call is silently discarding accumulated state instead of merging into it"
    )
    assert upd.property_updates.get("__test_prior_phase_marker__") == "present"


def test_combat_engagement_disabled_still_preserves_prior_phase_updates():
    """Regression guard: the flag OFF (real corpus-default) path was never affected -- confirms
    this fix doesn't change behavior for the real, currently-shipped configuration."""
    entity = _isolated_entity(1, pos=(0.0, 0.0))
    state = AuthoritativeState(
        tick=10, seed=42, entities={1: entity},
        feature_flags={"ENABLE_COMBAT_ENGAGEMENT": FeatureMode.OFF},
    )
    incoming = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, property_updates={"__test_prior_phase_marker__": "present"}),
    })

    result = AuthoritativeApplyPipeline.refine(state, incoming)

    upd = result.entity_updates.get(1)
    assert upd is not None
    assert upd.property_updates.get("__test_prior_phase_marker__") == "present"
