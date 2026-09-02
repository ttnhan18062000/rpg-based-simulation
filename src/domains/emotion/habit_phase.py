"""
src/domains/emotion/habit_phase.py
───────────────────────────────────────────────────────────────────────────────
HabitBiasUpdatePhase (TCK-20260831-HABIT-BIAS-WIRING)

Authoritative per-tick writer for HabitBiasService.record_outcome. Mirrors
NearDeathHardeningPhase.apply()'s read-through-then-replace shape (reads
entity_update.cognition_bundle_set, falling back to entity.cognition, before
replacing) rather than MemoryUpdatePhase.run()'s shape (reads state.entities
directly) -- this phase runs strictly after memory_update in the pipeline, so a
same-tick causal/spatial write staged by MemoryUpdatePhase must be preserved,
not clobbered.

record_outcome is called with success=False only: WorldEventCategory currently
provides COMBAT_LOSS but no win/victory category, so a success=True signal
would require inventing new event instrumentation, out of this ticket's scope.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from dataclasses import replace

from src.domains.emotion.habit_service import HabitBiasService, HABIT_PATTERN_COMBAT_ENGAGEMENT

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class HabitBiasUpdatePhase:
    """Applies authoritative habit-bias recording for combat-loss outcomes."""

    @staticmethod
    def apply(
        state: AuthoritativeState,
        update: StateUpdate,
        trigger_events: Optional[List[Dict[str, Any]]] = None,
    ) -> StateUpdate:
        from src.core.updates import EntityUpdate

        entity_updates = dict(update.entity_updates)
        for trigger in (trigger_events or []):
            entity_id = trigger["entity_id"]
            entity = state.entities.get(entity_id)
            if entity is None:
                continue

            entity_update = entity_updates.get(entity_id, EntityUpdate(entity_id=entity_id))
            base_cognition = (
                entity_update.cognition_bundle_set
                if entity_update.cognition_bundle_set is not None
                else entity.cognition
            )
            new_habit = HabitBiasService.record_outcome(
                base_cognition.memory.habit, HABIT_PATTERN_COMBAT_ENGAGEMENT, success=False
            )
            new_memory = replace(base_cognition.memory, habit=new_habit)
            new_cognition = replace(base_cognition, memory=new_memory)
            entity_updates[entity_id] = replace(entity_update, cognition_bundle_set=new_cognition)

        return replace(update, entity_updates=entity_updates)
