"""
src/domains/memory/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 13 — MemoryUpdatePhase

Orchestrates temporal calculation updates and causal attribution additions.
"""

from __future__ import annotations
from typing import Sequence, List, Optional
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

    def run(
        self,
        entities: Sequence[EntityState],
        tick: int = 0,
        trigger_event: Optional[dict] = None
    ) -> List[EntityState]:
        updated_entities: List[EntityState] = []

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

            if trigger_event and trigger_event.get("entity_id") == entity.id:
                evt_kind = trigger_event.get("kind")
                evt_id = trigger_event.get("id", "evt_unknown")
                region_id = trigger_event.get("region_id")

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
