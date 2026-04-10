from __future__ import annotations
from typing import TYPE_CHECKING, List

from src.core.models.strategy import (
    ObjectiveRecord, BlockerRecord, BlockerKind, ObjectiveKind, StrategicStatus
)

if TYPE_CHECKING:
    from src.ai.states.base import AIContext

class DetourSuggestionService:
    """Suggests remediation objectives (detours) to resolve blockers. [phase_3_task_7]"""

    @staticmethod
    def suggest_detours(ctx: AIContext, blocker: BlockerRecord, project_id: str) -> List[ObjectiveRecord]:
        """Maps a blocker to one or more resolution objectives."""
        detours = []
        tick = ctx.snapshot.tick
        
        if blocker.kind == BlockerKind.KNOWLEDGE:
            # Map knowledge blocker to INVESTIGATE detour
            # Look for a relevant lead that might help resolve this [phase_3_task_10]
            lead = next((l for l in ctx.active_leads if not l.is_exhausted), None)
            target_pos = lead.target_coords if lead else None
            
            detours.append(ObjectiveRecord(
                objective_id=f"detour_investigate_{blocker.blocker_id}",
                project_id=project_id,
                kind=ObjectiveKind.INVESTIGATE,
                label=f"Investigate: {blocker.label}",
                priority=3.5,
                target_pos=target_pos,
                created_tick=tick,
                spawned_from_id=blocker.blocker_id,
                evidence_refs=[lead.lead_id] if lead else []
            ))
            
        elif blocker.kind == BlockerKind.MATERIAL:
            # For material, if it's quest-related, we might need to hunt/collect
            detours.append(ObjectiveRecord(
                objective_id=f"detour_resources_{blocker.blocker_id}",
                project_id=project_id,
                kind=ObjectiveKind.COLLECT,
                label=f"Gather resources/gold for: {blocker.label}",
                priority=3.0,
                created_tick=tick,
                spawned_from_id=blocker.blocker_id
            ))

        elif blocker.kind == BlockerKind.CAPABILITY:
            # If injured or weak, suggest training or rest
            detours.append(ObjectiveRecord(
                objective_id=f"detour_training_{blocker.blocker_id}",
                project_id=project_id,
                kind=ObjectiveKind.TRAIN,
                label=f"Build capability for: {blocker.label}",
                priority=3.0,
                created_tick=tick,
                spawned_from_id=blocker.blocker_id
            ))
            
        return detours
