"""Place Threat Appraisal Service - Strategic evaluation of regional trauma. [PHASE 5]"""

from __future__ import annotations
import uuid
import logging
from typing import TYPE_CHECKING
from src_legacy.core.models.strategy import ConcernRecord, ConcernKind

if TYPE_CHECKING:
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.entities.entity import Entity
    from src_legacy.core.models.life_events import InterpretedLifeEvent
    from src_legacy.actions.base import StrategicUpdate

logger = logging.getLogger(__name__)

class PlaceThreatAppraisalService:
    """Evaluates world events against personal attachments and duties."""

    @classmethod
    def appraise(
        cls, 
        world: WorldState, 
        entity: Entity, 
        event: InterpretedLifeEvent, 
        updates: StrategicUpdate
    ) -> None:
        """Check if an event threatens a location the entity cares about."""
        # 1. Resolve event location's region
        from src_legacy.core.world.regions import find_region_at
        region = find_region_at(event.location, world.regions)
        if not region:
            return
            
        # 2. Check attachments to this region
        # Looking at entity.mind.place_attachments (Phase 3)
        attachment = None
        for a in entity.mind.place_attachments:
            a_region = find_region_at(a.location_pos, world.regions)
            if a_region and a_region.region_id == region.region_id:
                attachment = a
                break
        
        if not attachment:
            return
            
        # 3. Calculate Pressure
        # Manhattan distance to attachment
        dist = attachment.location_pos.manhattan(event.location)
        # Normalize distance (0-20 range for pressure decay)
        dist_factor = max(0.0, 1.0 - (dist / 20.0))
        
        # Base severity of event * attachment importance * distance sensitivity
        pressure = event.severity * attachment.importance * (0.5 + 0.5 * dist_factor)
        
        # [PHASE 4] Home Priority Bias: Significant multiplier for home threats
        from src_legacy.core.models.enums import AttachmentKind
        if attachment.kind == AttachmentKind.HOME:
            pressure *= 1.5
            
        # 4. Generate Concern if sufficiently high
        if pressure > 0.4:
            # We use a deterministic ID based on region to avoid duplicates if multiple events happen
            concern_id = f"concern_threat_{region.region_id}_{entity.id}"
            
            # Check if concern already exists to avoid spamming updates
            existing = next((c for c in entity.mind.strategic.concerns if c.concern_id == concern_id), None)
            if existing:
                # Update priority if existing is lower
                if existing.priority < 4.0 + pressure:
                     updated_c = existing.model_copy(update={"priority": min(10.0, 4.0 + pressure), "urgency": min(1.0, 0.4 + (pressure * 0.1))})
                     updates.concerns_add_or_update.append(updated_c)
                return

            label = f"Threat to {attachment.kind.name.title()} ({region.region_id})"
            
            new_concern = ConcernRecord(
                concern_id=concern_id,
                kind=ConcernKind.THREAT,
                label=label,
            priority=min(10.0, 4.0 + pressure),
                cause_type="environmental",
                source_event_id=event.event_id,
                urgency=min(1.0, 0.5 + (pressure * 0.1)),
                attachment_relevance=attachment.importance,
                visibility="private",
                created_tick=world.tick
            )
            updates.concerns_add_or_update.append(new_concern)
            logger.info("Entity %d generated regional concern for %s: %s (dist: %.1f, pressure: %.2f)", 
                        entity.id, region.region_id, label, dist, pressure)
