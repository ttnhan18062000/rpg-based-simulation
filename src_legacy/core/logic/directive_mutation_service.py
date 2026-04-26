"""Directive Mutation Service - Logic for identity shifts from turning points. [PHASE 5]"""

from __future__ import annotations
import uuid
import logging
from typing import TYPE_CHECKING
from src_legacy.core.models.strategy import DirectiveRecord, DirectiveKind
from src_legacy.core.models.enums import TurningPointKind, Domain

if TYPE_CHECKING:
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.entities.entity import Entity
    from src_legacy.core.models.life_events import TurningPointRecord
    from src_legacy.actions.base import StrategicUpdate
    from src_legacy.systems.rng import DeterministicRNG
    from src_legacy.ai.cognition_capacity import CognitionCapacityProfile

logger = logging.getLogger(__name__)

class DirectiveMutationService:
    """Rules for shifting long-term orientations based on salient memories."""

    @classmethod
    def evaluate_mutation(
        cls, 
        world: WorldState, 
        entity: Entity, 
        tp: TurningPointRecord, 
        updates: StrategicUpdate,
        rng: DeterministicRNG | None = None,
        profile: CognitionCapacityProfile | None = None
    ) -> None:
        """Analyze turning point and mutate directives if salience thresholds are met. [phase_2_intel_capacity]"""
        
        # Resolve profile if missing
        if profile is None:
            from src_legacy.ai.cognition_capacity import CognitionCapacityBuilder
            profile = CognitionCapacityBuilder.build(entity)

        # High salience requirement for identity shift
        # Bounded by judgment stability (higher stability = higher threshold for identity drift)
        # range: 0.8 (unstable) to 1.2 (stable)
        base_threshold = 0.8
        effective_threshold = base_threshold * (0.5 + 0.7 * profile.judgment_stability)
        
        if tp.salience_score < effective_threshold: 
            return

        # [TCK-20260414-SOCIAL-04] Count event history for persistence thresholds
        history = entity.mind.narrative.turning_points
        def get_count(kind):
            return len([prev for prev in history if prev.kind == kind])

        # 1. Map Turning Point Kind to Directive Shift
        if tp.kind == TurningPointKind.NEAR_DEATH:
            # Requires at least 2 salient Near Deaths to shift to a Safety directive
            if get_count(TurningPointKind.NEAR_DEATH) >= 2:
                cls._ensure_directive(entity, updates, "Safety & Self-Preservation", DirectiveKind.PERSONAL, 3.5, "trauma", world.tick, rng)
            
        elif tp.kind == TurningPointKind.BETRAYAL:
            # Betrayal is uniquely high-impact (Threshold: 1)
            cls._ensure_directive(entity, updates, "Avenge Betrayal/Loss", DirectiveKind.PERSONAL, 3.0, "trauma", world.tick, rng)

        elif tp.kind == TurningPointKind.ALLY_DIED:
            # Requires at least 2 salient Ally Deaths to trigger vengeful focus
            if get_count(TurningPointKind.ALLY_DIED) >= 2:
                 cls._ensure_directive(entity, updates, "Avenge Betrayal/Loss", DirectiveKind.PERSONAL, 3.0, "trauma", world.tick, rng)
            
        elif tp.kind == TurningPointKind.BOSS_ENCOUNTER:
            if tp.emotional_impact < 0:
                # Failed boss encounter
                cls._ensure_directive(entity, updates, "Legendary Ambition", DirectiveKind.PROFESSIONAL, 4.0, "glory", world.tick, rng)

        elif tp.kind == TurningPointKind.AVENGED_ALLY:
            cls._ensure_directive(entity, updates, "Guardian of the Guild", DirectiveKind.FACTIONAL, 3.5, "loyalty", world.tick, rng)

        elif tp.kind == TurningPointKind.RESCUE:
            cls._ensure_directive(entity, updates, "Heroic Altruism", DirectiveKind.IDEOLOGICAL, 3.2, "social", world.tick, rng)

        elif tp.kind == TurningPointKind.FIRST_KILL:
            cls._ensure_directive(entity, updates, "Lethal Resolve", DirectiveKind.PERSONAL, 2.5, "bloodshed", world.tick, rng)

    @staticmethod
    def _ensure_directive(
        entity: Entity, 
        updates: StrategicUpdate, 
        label: str, 
        kind: DirectiveKind, 
        priority: float,
        source: str,
        tick: int = 0,
        rng: DeterministicRNG | None = None
    ) -> None:
        """Check for existing directive by label or add a new one."""
        existing = next((d for d in entity.mind.strategic.directives if d.label == label), None)
        
        if existing:
            # Strengthen priority if already exists
            new_priority = min(5.0, existing.priority + 0.5)
            if new_priority > existing.priority:
                # We update by adding it again to the update list (ActionSystem handles replacement by ID)
                updated_d = existing.model_copy(update={"priority": new_priority})
                updates.directives_add.append(updated_d)
        else:
            # Add new directive
            new_d = DirectiveRecord(
                directive_id=f"dir_{label.lower().replace(' ', '_')}_{rng.next_hex(Domain.SOCIAL, entity.id, tick, sub_id=30)}" if rng else f"dir_{label.lower().replace(' ', '_')}_{uuid.uuid4().hex[:4]}",
                kind=kind,
                label=label,
                priority=priority,
                source=source,
                created_tick=0 # Will be populated by system if needed, or stick to 0 for default
            )
            updates.directives_add.append(new_d)
            logger.info("Entity %d acquired new directive: %s", entity.id, label)
