from __future__ import annotations
from typing import TYPE_CHECKING, List

from src.core.models.strategy import (
    ObjectiveRecord, BlockerRecord, BlockerKind, ObjectiveKind
)

if TYPE_CHECKING:
    from src.ai.states.base import AIContext

class BlockerInferenceService:
    """Infers structural blockers for strategic objectives. [phase_3_task_7]"""

    @staticmethod
    def infer_blockers(ctx: AIContext, objective: ObjectiveRecord) -> List[BlockerRecord]:
        """Inspects an objective and its context to identify blockers."""
        blockers = []
        tick = ctx.snapshot.tick
        actor = ctx.actor
        
        # 1. Knowledge Blockers (Missing coordinates)
        if objective.kind in (ObjectiveKind.VISIT, ObjectiveKind.KILL, ObjectiveKind.COLLECT):
            if objective.target_pos is None and objective.target_id is None:
                # We don't know where to go!
                blockers.append(BlockerRecord(
                    blocker_id=f"blocker_kn_{objective.objective_id}_{tick}",
                    kind=BlockerKind.KNOWLEDGE,
                    label=f"Location unknown for '{objective.label}'",
                    subject_ref=objective.objective_id,
                    severity=1.0,
                    confidence=1.0,
                    suggested_detour_types=[ObjectiveKind.INVESTIGATE, ObjectiveKind.SCOUT],
                    discovered_tick=tick
                ))
        
        # 2. Capability Blockers (Health/Stamina stressors)
        if actor.combat.hp < actor.combat.max_hp * 0.3:
             # Too injured to pursue high-risk objectives
             if objective.kind in (ObjectiveKind.KILL, ObjectiveKind.COLLECT, ObjectiveKind.SCOUT):
                  blockers.append(BlockerRecord(
                    blocker_id=f"blocker_cap_injury_{objective.objective_id}",
                    kind=BlockerKind.CAPABILITY,
                    label="Insufficient health for challenge",
                    subject_ref=objective.objective_id,
                    severity=0.8,
                    confidence=1.0,
                    suggested_detour_types=[ObjectiveKind.WAIT, ObjectiveKind.VISIT],
                    discovered_tick=tick
                ))

        # 3. Material/Gold Blockers (already often ingested, but can be inferred)
        if hasattr(objective, "gold_cost") and objective.gold_cost > actor.progression.gold:
             blockers.append(BlockerRecord(
                    blocker_id=f"blocker_mat_gold_{objective.objective_id}",
                    kind=BlockerKind.MATERIAL,
                    label=f"Insufficient gold (need {objective.gold_cost})",
                    subject_ref=objective.objective_id,
                    severity=0.9,
                    confidence=1.0,
                    suggested_detour_types=[ObjectiveKind.COLLECT, ObjectiveKind.KILL], # Loot/rewards
                    discovered_tick=tick
                ))
        
        return blockers
