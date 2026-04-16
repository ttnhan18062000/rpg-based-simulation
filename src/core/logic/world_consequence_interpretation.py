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
        # 1. Localized Scars (Independent of Region)
        from src.ai.perception import Perception
        visible_scars = Perception.visible_scars(entity, world, scan_range=10)
        if visible_scars:
             max_severity = max(s.severity for s in visible_scars)
             if max_severity > 0.4:
                 # Haunted Battlefield / Recent Slaughter Concern
                 cls._ensure_scar_concern(entity, updates, visible_scars[0], world.tick)

        # 2. Regional Danger
        rid = getattr(entity.spatial, 'current_region_id', None) or getattr(entity.spatial, 'region_id', None)
        if not rid: return
        
        region_consequence = world.region_consequence_registry.get(rid)
        
        # Robust handling for Mock objects in integration tests
        danger = 0.0
        if region_consequence:
             danger_val = getattr(region_consequence, 'danger_level', 0.0)
             if isinstance(danger_val, (int, float)):
                 danger = float(danger_val)
             else:
                 danger = 0.0
             
        if danger > 0.6:
            # Regional Awareness
            attachment = next((a for a in entity.mind.place_attachments if a.region_id == rid), None)
            cls._ensure_regional_concern(entity, updates, rid, danger, world.tick, has_attachment=bool(attachment))

    @staticmethod
    def _ensure_regional_concern(entity: Entity, updates: StrategicUpdate, region_id: str, danger_level: float, tick: int, has_attachment: bool = False) -> None:
        concern_id = f"concern_unstable_region_{region_id}"
        if any(c.concern_id == concern_id for c in entity.mind.strategic.concerns):
            return
            
        base_p = 4.0 if has_attachment else 2.5
        new_c = ConcernRecord(
            concern_id=concern_id,
            kind=ConcernKind.THREAT,
            label=f"Unstable region: {region_id}",
            priority=base_p + (danger_level * 4.0),
            cause_type="environmental",
            urgency=danger_level,
            attachment_relevance=1.0 if has_attachment else 0.2,
            visibility="private",
            created_tick=tick
        )
        updates.concerns_add_or_update.append(new_c)

    @staticmethod
    def _ensure_scar_concern(entity: Entity, updates: StrategicUpdate, scar: LocalScarRecord, tick: int) -> None:
        # Scars are small enough that we might just have a generic 'Trauma Zone' concern
        concern_id = f"concern_nearby_scar"
        if any(c.concern_id == concern_id for c in entity.mind.strategic.concerns):
            return
            
        new_c = ConcernRecord(
            concern_id=concern_id,
            kind=ConcernKind.THREAT,
            label="Nearby world trauma sensed",
            priority=2.5,
            cause_type="scar",
            source_event_id=scar.source_event_id,
            linked_scar_ids=[scar.source_event_id or "unknown"],
            urgency=0.6,
            visibility="private",
            created_tick=tick
        )
        updates.concerns_add_or_update.append(new_c)
