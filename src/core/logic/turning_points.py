"""Turning-point salience and lifecycle management. [PHASE 2]

Turning points are rare, high-impact memories that define an entity's life arc.
This service manages insertion (with cap enforcement), salience scoring
(weighted by emotional impact, motive relevance, entity importance, and recency),
pruning (evict lowest-salience entries), and resolution marking.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from src.core.models.life_events import TurningPointRecord
from src.core.models.enums import TurningPointKind, PersonalMotiveType

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

logger = logging.getLogger(__name__)

MAX_TURNING_POINTS = 20
SALIENCE_FLOOR = 0.1
SALIENCE_DECAY_PER_TICK = 0.0005


class TurningPointService:
    """Manages turning-point lifecycle: insertion, salience scoring, pruning, resolution."""

    @staticmethod
    def calculate_salience(
        turning_point: TurningPointRecord,
        current_tick: int,
        actor_motives: list | None = None,
        important_entity_ids: set[int] | None = None,
    ) -> float:
        """Calculate weighted salience for a turning point.

        Factors:
        - Emotional impact (absolute value, primary driver)
        - Motive relevance (does this TP affect an active motive?)
        - Entity importance (are involved entities still relevant?)
        - Recency (linear decay with floor)
        """
        base = abs(turning_point.emotional_impact)

        # Motive relevance bonus
        motive_bonus = 0.0
        if actor_motives and turning_point.motive_effects:
            for motive in actor_motives:
                motive_kind = getattr(motive, 'kind', None)
                if motive_kind is not None:
                    kind_name = motive_kind.name if hasattr(motive_kind, 'name') else str(motive_kind)
                    if kind_name in turning_point.motive_effects:
                        motive_bonus += abs(turning_point.motive_effects[kind_name]) * 0.3

        # Entity importance bonus
        entity_bonus = 0.0
        if important_entity_ids and turning_point.involved_entity_ids:
            overlap = set(turning_point.involved_entity_ids) & important_entity_ids
            entity_bonus = len(overlap) * 0.2

        # Recency multiplier (linear decay with floor)
        age = max(0, current_tick - turning_point.tick)
        recency_mult = max(SALIENCE_FLOOR, 1.0 - (age * SALIENCE_DECAY_PER_TICK))

        # Unresolved events retain higher salience
        resolution_mult = 1.0 if turning_point.still_salient else 0.5

        return (base + motive_bonus + entity_bonus) * recency_mult * resolution_mult

    @classmethod
    def prepare_insertion(cls, entity: "Entity", turning_point: TurningPointRecord, current_tick: int) -> PerceptionUpdate | None:
        """Evaluates a turning point for insertion. Returns PerceptionUpdate if it should be added.
        
        AOA Pillar 2: Services return intent. Mutation is handled authoritatively.
        """
        from src.actions.base import PerceptionUpdate
        
        # 1. Deduplication
        if any(tp.event_id == turning_point.event_id for tp in entity.mind.narrative.turning_points):
            return None

        # 2. Score the candidate
        motives = getattr(entity.mind.decision, 'motives', [])
        candidate_salience = cls.calculate_salience(turning_point, current_tick, motives)
        
        # Score the turning point
        turning_point = turning_point.model_copy(update={
            "salience_score": candidate_salience,
            "event_id": turning_point.event_id or f"tp-{uuid.uuid4().hex[:8]}"
        })

        # 3. Decision to insert
        tp_list = entity.mind.narrative.turning_points
        if len(tp_list) < MAX_TURNING_POINTS:
            return PerceptionUpdate(turning_points_add=[turning_point])

        # At capacity — find weakest existing entry
        weakest_salience = candidate_salience
        for tp in tp_list:
            s = cls.calculate_salience(tp, current_tick, motives)
            if s < weakest_salience:
                weakest_salience = s

        if candidate_salience > weakest_salience:
             return PerceptionUpdate(turning_points_add=[turning_point])

        return None

    @classmethod
    def prune(cls, entity: "Entity", current_tick: int) -> None:
        """Re-score all turning points and evict entries below the salience floor."""
        tp_list = entity.mind.narrative.turning_points
        if not tp_list:
            return

        motives = getattr(entity.mind.decision, 'motives', [])
        scored = [
            (i, cls.calculate_salience(tp, current_tick, motives))
            for i, tp in enumerate(tp_list)
        ]

        # Update stored salience scores
        for i, score in scored:
            tp_list[i].salience_score = score

        # Evict entries below absolute floor (only if unresolved and very old)
        min_threshold = SALIENCE_FLOOR * 2  # 0.2 — very generous
        to_remove = [i for i, score in scored if score < min_threshold and not tp_list[i].still_salient]
        for idx in reversed(sorted(to_remove)):
            evicted = tp_list.pop(idx)
            logger.debug("Pruned resolved TP %s (salience=%.2f) for entity %d.", evicted.event_id, evicted.salience_score, entity.id)

    @staticmethod
    def mark_resolved(entity: "Entity", event_id: str) -> None:
        """Mark a turning point as resolved (e.g., revenge completed)."""
        for tp in entity.mind.narrative.turning_points:
            if tp.event_id == event_id:
                tp.still_salient = False
                logger.debug("Marked TP %s as resolved for entity %d.", event_id, entity.id)
                return
