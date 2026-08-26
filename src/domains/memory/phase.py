"""
src/domains/memory/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 13 — MemoryUpdatePhase

Orchestrates temporal calculation updates and causal attribution additions.
"""

from __future__ import annotations
from typing import Sequence, List, Optional, Any
from dataclasses import replace

from src.core.state import EntityState
from src.core.cognition import (
    CausalMemoryEntry,
    CausalMemory,
    SpatialMemory,
    TemporalModel
)
from src.domains.time.service import TemporalPressureService
from src.domains.memory.attribution import CausalAttributionService
from src.domains.memory.spatial_update import SpatialMemoryUpdateService

class MemoryUpdatePhase:
    """Orchestrates temporal recalculations, causal attributions, and spatial updates."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def apply(
        state: Any,  # AuthoritativeState
        update: Any,  # StateUpdate
        trigger_events: Optional[List[dict]] = None,
    ) -> Any:  # StateUpdate
        """
        Routes MemoryUpdatePhase.run()'s output through the typed EntityUpdate/CognitionPatch
        apply path, mirroring SelfModelUpdatePhase.apply() -- never mutates state.entities.
        """
        from src.core.updates import EntityUpdate

        active_entities = [
            e for e in state.entities.values()
            if e.lifecycle.active and e.combat.alive
        ]
        updated = MemoryUpdatePhase().run(active_entities, tick=state.tick, trigger_events=trigger_events)

        new_entity_updates = dict(update.entity_updates)
        for new_entity in updated:
            entity_up = new_entity_updates.get(new_entity.id, EntityUpdate(entity_id=new_entity.id))
            new_entity_updates[new_entity.id] = replace(entity_up, cognition_bundle_set=new_entity.cognition)

        return replace(update, entity_updates=new_entity_updates)

    def run(
        self,
        entities: Sequence[EntityState],
        tick: int = 0,
        trigger_events: Optional[List[dict]] = None
    ) -> List[EntityState]:
        updated_entities: List[EntityState] = []
        trigger_by_entity = {t["entity_id"]: t for t in (trigger_events or [])}

        for entity in entities:
            # Skip inactive/dead
            if not entity.lifecycle.active or not entity.combat.alive:
                updated_entities.append(entity)
                continue

            cognition = entity.cognition
            subjective = cognition.subjective
            memory = cognition.memory

            # 1. Update Temporal Model Urgencies
            new_urgencies = TemporalPressureService.calculate_urgencies(entity, tick)
            new_time = replace(subjective.time, urgency=new_urgencies)
            subjective = replace(subjective, time=new_time)

            # 2. Handle Trigger Event (Causal Memory attribution + Spatial marking)
            new_causal_entries = list(memory.causal.entries)
            new_spatial = memory.spatial

            trigger = trigger_by_entity.get(entity.id)
            if trigger:
                evt_kind = trigger.get("kind")
                evt_id = trigger.get("id", "evt_unknown")
                region_id = trigger.get("region_id")

                # Process Causal Attribution
                entry = CausalAttributionService.attribute(
                    entity=entity,
                    event_id=evt_id,
                    event_kind=evt_kind,
                    tick=tick,
                    region_id=region_id
                )

                # Append to bounded Causal Memory capacity
                if len(new_causal_entries) >= memory.causal.capacity:
                    new_causal_entries.pop(0)  # Evict oldest
                new_causal_entries.append(entry)

                # Process Spatial danger tagging if it was near death or combat loss
                if evt_kind in ("combat_loss", "near_death") and region_id:
                    new_spatial = SpatialMemoryUpdateService.mark_region_danger(
                        spatial=new_spatial,
                        region_id=region_id,
                        is_dangerous=True
                    )

            # 3. Regular Spatial Visited region updating based on current position
            curr_region = entity.navigation.region_id
            if curr_region:
                new_spatial = SpatialMemoryUpdateService.update_region_visit(
                    spatial=new_spatial,
                    region_id=curr_region
                )

            # Pack all modifications back into EntityState
            new_causal = replace(memory.causal, entries=tuple(new_causal_entries))
            new_memory = replace(memory, causal=new_causal, spatial=new_spatial)
            new_cognition = replace(cognition, subjective=subjective, memory=new_memory)
            new_entity = replace(entity, cognition=new_cognition)

            updated_entities.append(new_entity)

        return updated_entities
