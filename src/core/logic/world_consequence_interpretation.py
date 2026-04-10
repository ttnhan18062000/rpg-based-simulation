"""World Consequence Interpretation Service - strategic meaning for world scars. [PHASE 5]"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.core.models.strategy import ConcernRecord, ConcernKind

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.entities.entity import Entity
    from src.actions.base import StrategicUpdate

logger = logging.getLogger(__name__)

class WorldConsequenceInterpretationService:
    """Interprets long-term world trauma into individual strategic concerns."""

    @classmethod
    def appraise_environment(
        cls, 
        world: WorldState, 
        entity: Entity, 
        updates: StrategicUpdate
    ) -> None:
        """Scan local region and scars to generate durable concerns."""
        # 1. Regional Danger
        rid = entity.spatial.current_region_id
        if not rid: return
        
        region_consequence = world.region_consequence_registry.get(rid)
        if region_consequence and region_consequence.danger_level > 0.5:
            # Dangerous Homeland Concern
            # Only if entity has Home attachment here
            attachment = next((a for a in entity.mind.routine.place_attachments if a.region_id == rid), None)
            if attachment and attachment.kind.name == "HOME":
                cls._ensure_regional_concern(entity, updates, rid, region_consequence.danger_level, world.tick)

        # 2. Local Scars Awareness
        # Standing near a persistent scar (Battlefield)
        from src.ai.brain import Perception
        visible_scars = Perception.visible_scars(entity, world, scan_range=10)
        if visible_scars:
            max_severity = max(s.severity for s in visible_scars)
            if max_severity > 0.7:
                # Haunted Battlefield / Recent Slaughter Concern
                cls._ensure_scar_concern(entity, updates, visible_scars[0], world.tick)

    @staticmethod
    def _ensure_regional_concern(entity: Entity, updates: StrategicUpdate, region_id: str, danger_level: float, tick: int) -> None:
        concern_id = f"concern_unstable_region_{region_id}"
        if any(c.concern_id == concern_id for c in entity.mind.strategic.concerns):
            return
            
        new_c = ConcernRecord(
            concern_id=concern_id,
            kind=ConcernKind.THREAT,
            label=f"Unstable Homeland: {region_id}",
            priority=2.0 + (danger_level * 3.0),
            cause_type="scar",
            urgency=danger_level,
            attachment_relevance=1.0,
            visibility="private",
            created_tick=tick
        )
        updates.concerns_add_or_update.append(new_c)

    @staticmethod
    def _ensure_scar_concern(entity: Entity, updates: StrategicUpdate, scar: LocalScarRecord, tick: int) -> None:
        # Scars are small enough that we might just have a generic 'Trauma Zone' concern
        concern_id = f"concern_trauma_zone"
        if any(c.concern_id == concern_id for c in entity.mind.strategic.concerns):
            return
            
        new_c = ConcernRecord(
            concern_id=concern_id,
            kind=ConcernKind.THREAT,
            label="Trauma zone awareness",
            priority=2.5,
            cause_type="scar",
            linked_scar_ids=[scar.source_event_id or "unknown"],
            urgency=0.6,
            visibility="private",
            created_tick=tick
        )
        updates.concerns_add_or_update.append(new_c)
