"""
tests/unit/engine/test_near_death_hardening_emotion.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260824-WIRE-ORPHANED-MECHANISMS Step 4 — verifies EmotionUpdateService is
wired into NearDeathHardeningPhase.apply() for the "near_death" event_kind, and
that it correctly handles a same-tick collision with an earlier phase (e.g.
MemoryUpdatePhase) that already set cognition_bundle_set for the same entity.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.engine.pipeline_phases.hardening import NearDeathHardeningPhase


def _near_death_entity(entity_id: int = 1):
    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )


def test_near_death_hardening_updates_emotional_model():
    """
    A near-death survival (projected HP <= 10% of max HP) produces a
    cognition_bundle_set whose subjective.emotion has fear/panic increased and
    confidence decreased, while combat.max_hp_delta=5 from the existing
    hardening logic is preserved alongside it.
    """
    entity = _near_death_entity()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})

    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-95)),
        }
    )

    refined = NearDeathHardeningPhase.apply(state, update)
    upd = refined.entity_updates[1]

    assert upd.combat.max_hp_delta == 5

    assert upd.cognition_bundle_set is not None
    new_emotion = upd.cognition_bundle_set.subjective.emotion
    base_emotion = entity.cognition.subjective.emotion
    assert new_emotion.fear > base_emotion.fear
    assert new_emotion.panic > base_emotion.panic
    assert new_emotion.confidence < base_emotion.confidence


def test_near_death_hardening_only_changes_emotion_subfield():
    """
    cognition_bundle_set-shape guard: only subjective.emotion differs from the
    entity's prior CognitionModel — no other sub-field (self-model, knowledge,
    commitments, memory) is clobbered by the whole-bundle replace.
    """
    entity = _near_death_entity()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})

    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-95)),
        }
    )

    refined = NearDeathHardeningPhase.apply(state, update)
    new_cognition = refined.entity_updates[1].cognition_bundle_set

    expected = replace(
        entity.cognition,
        subjective=replace(entity.cognition.subjective, emotion=new_cognition.subjective.emotion),
    )
    assert new_cognition == expected


def test_near_death_hardening_preserves_same_tick_cognition_bundle_set():
    """
    Same-tick collision: if an earlier phase (e.g. MemoryUpdatePhase) already set
    cognition_bundle_set on this entity_update this tick, NearDeathHardeningPhase
    must build on top of it (entity_update.cognition_bundle_set), not the stale
    pre-tick entity.cognition — otherwise it would silently discard the earlier
    phase's same-tick changes to unrelated cognition sub-fields.
    """
    entity = _near_death_entity()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})

    prior_phase_cognition = replace(
        entity.cognition,
        subjective=replace(
            entity.cognition.subjective,
            knowledge=replace(entity.cognition.subjective.knowledge, last_updated_tick=777),
        ),
    )

    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                combat=CombatUpdate(hp_delta=-95),
                cognition_bundle_set=prior_phase_cognition,
            ),
        }
    )

    refined = NearDeathHardeningPhase.apply(state, update)
    new_cognition = refined.entity_updates[1].cognition_bundle_set

    # Earlier phase's change survives...
    assert new_cognition.subjective.knowledge.last_updated_tick == 777
    # ...alongside this phase's own emotion change.
    assert new_cognition.subjective.emotion.fear > entity.cognition.subjective.emotion.fear
