"""
tests/integration/domains/emotion/test_habit_bias_pipeline_wiring.py

TCK-20260831-HABIT-BIAS-WIRING (Step 3): HabitBiasUpdatePhase must be the first production
caller of HabitBiasService.record_outcome, wired via entity_update.cognition_bundle_set (not a
direct state.entities mutation) -- mirrors
tests/integration/domains/memory/test_memory_update_phase_apply_trigger_events.py's own
assertion shape for a sibling MemoryModel field (causal).
"""
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate
from src.domains.emotion.habit_phase import HabitBiasUpdatePhase
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory


def _combat_loss_trigger_events(state):
    return [
        {"entity_id": int(e.subject), "kind": "combat_loss", "id": f"combat_loss_{e.tick}_{e.subject}", "region_id": e.region_id}
        for e in state.recent_world_events
        if e.category == WorldEventCategory.COMBAT_LOSS and e.subject is not None
    ]


def test_record_outcome_wired_through_authoritative_pipeline():
    entity_x = EntityState(id=7, kind="HERO")
    entity_y = EntityState(id=8, kind="HERO")

    recent_world_events = [
        WorldEvent(category=WorldEventCategory.COMBAT_LOSS, tick=9, region_id="wolf_den", subject="7"),
    ]
    state = AuthoritativeState(
        tick=10, seed=42, entities={7: entity_x, 8: entity_y},
        recent_world_events=recent_world_events,
    )

    trigger_events = _combat_loss_trigger_events(state)
    result = HabitBiasUpdatePhase.apply(state, StateUpdate(), trigger_events)

    x_cognition = result.entity_updates[7].cognition_bundle_set
    assert x_cognition is not None
    assert x_cognition.memory.habit.patterns["combat_engagement"] < 0.5

    # Entity 8 was not the subject of a combat_loss -- no habit write at all.
    assert 8 not in result.entity_updates


def test_habit_bias_update_phase_preserves_prior_cognition_bundle_write():
    """Read-through-then-replace discipline: a same-tick cognition write staged earlier in the
    tick (e.g. by memory_update, which runs immediately before this phase in the pipeline) must
    be preserved, not clobbered -- NearDeathHardeningPhase's pattern, not MemoryUpdatePhase's."""
    from dataclasses import replace
    from src.core.updates import EntityUpdate
    from src.core.cognition import CausalMemoryEntry

    entity = EntityState(id=7, kind="HERO")
    staged_cognition = replace(
        entity.cognition,
        memory=replace(
            entity.cognition.memory,
            causal=replace(entity.cognition.memory.causal, entries=(
                CausalMemoryEntry(
                    event_id="e1", event_kind="combat_loss",
                    interpreted_causes=(), confidence=0.5, future_advice=(), tick=9,
                ),
            )),
        ),
    )
    update = StateUpdate(entity_updates={
        7: EntityUpdate(entity_id=7, cognition_bundle_set=staged_cognition),
    })

    state = AuthoritativeState(tick=10, seed=42, entities={7: entity})
    trigger_events = [{"entity_id": 7, "kind": "combat_loss", "id": "combat_loss_9_7", "region_id": "wolf_den"}]

    result = HabitBiasUpdatePhase.apply(state, update, trigger_events)

    new_cognition = result.entity_updates[7].cognition_bundle_set
    assert len(new_cognition.memory.causal.entries) == 1, "prior memory_update write was clobbered"
    assert new_cognition.memory.habit.patterns["combat_engagement"] < 0.5


def test_habit_bias_action_style_flag_gates_pipeline_phase():
    from src.engine.pipeline import AuthoritativeApplyPipeline

    entity = EntityState(id=7, kind="HERO")
    recent_world_events = [
        WorldEvent(category=WorldEventCategory.COMBAT_LOSS, tick=9, region_id="wolf_den", subject="7"),
    ]

    state_on = AuthoritativeState(
        tick=10, seed=42, entities={7: entity}, recent_world_events=recent_world_events,
        feature_flags={"ENABLE_HABIT_BIAS_ACTION_STYLE": "ON"},
    )
    refined_on = AuthoritativeApplyPipeline.refine(state_on, StateUpdate())
    cognition_on = refined_on.entity_updates[7].cognition_bundle_set
    assert cognition_on is not None
    assert cognition_on.memory.habit.patterns.get("combat_engagement") == 0.4

    state_off = AuthoritativeState(
        tick=10, seed=42, entities={7: entity}, recent_world_events=recent_world_events,
    )
    refined_off = AuthoritativeApplyPipeline.refine(state_off, StateUpdate())
    entity_update_off = refined_off.entity_updates.get(7)
    assert entity_update_off is None or entity_update_off.cognition_bundle_set is None
