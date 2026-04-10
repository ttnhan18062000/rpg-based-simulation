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
        """Maps a blocker to one or more resolution objectives using Lead Matching."""
        detours = []
        tick = ctx.snapshot.tick
        
        # Priority boost based on severity (le 5.0 constraint)
        base_priority = min(5.0, 3.0 + (blocker.severity * 2.0))
        
        if blocker.kind == BlockerKind.KNOWLEDGE:
            # Match Knowledge blocker with a relevant lead
            # 1. Look for a lead that matches the subject_ref and is NOT exhausted
            lead = next((l for l in ctx.active_leads if l.subject == blocker.subject_ref and not l.is_exhausted), None)
            
            # 2. Prefer untested leads if multiple exist (Lifecycle Awareness)
            untested = [l for l in ctx.active_leads if l.subject == blocker.subject_ref and not l.is_exhausted and not l.tested]
            if untested:
                lead = untested[0]
            
            # 3. Fallback to the freshest 'investigation' lead
            if not lead:
                lead = next((l for l in ctx.active_leads if not l.is_exhausted), None)
            
            target_pos = lead.target_coords if lead else None
            
            detours.append(ObjectiveRecord(
                objective_id=f"detour_investigate_{blocker.blocker_id}",
                project_id=project_id,
                kind=ObjectiveKind.INVESTIGATE,
                label=f"Investigate: {blocker.label}",
                priority=min(5.0, base_priority + 0.5),
                target_pos=target_pos,
                created_tick=tick,
                spawned_from_id=blocker.blocker_id,
                evidence_refs=[lead.lead_id] if lead else []
            ))
            
        elif blocker.kind == BlockerKind.MATERIAL:
            # Match Material blocker with a lead that reports that material
            # Lifecycle Awareness: Filter out exhausted sources
            matches = [l for l in ctx.active_leads if not l.is_exhausted and (l.subject == blocker.subject_ref or blocker.subject_ref in l.semantic_tags)]
            
            # Prioritize untested/high-certainty
            matches.sort(key=lambda x: (not x.tested, x.certainty), reverse=True)
            lead = matches[0] if matches else None
            
            target_pos = lead.target_coords if lead else None
            
            detours.append(ObjectiveRecord(
                objective_id=f"detour_resources_{blocker.blocker_id}",
                project_id=project_id,
                kind=ObjectiveKind.COLLECT,
                label=f"Gather resources for: {blocker.label}",
                priority=min(5.0, base_priority),
                target_pos=target_pos,
                created_tick=tick,
                spawned_from_id=blocker.blocker_id,
                evidence_refs=[lead.lead_id] if lead else []
            ))

        elif blocker.kind == BlockerKind.CAPABILITY:
            # Match Capability (skill) blocker with a lead for that skill (e.g. trainer location)
            lead = next((l for l in ctx.active_leads if l.subject == blocker.subject_ref and not l.is_exhausted), None)
            
            target_pos = lead.target_coords if lead else None
            
            detours.append(ObjectiveRecord(
                objective_id=f"detour_training_{blocker.blocker_id}",
                project_id=project_id,
                kind=ObjectiveKind.TRAIN,
                label=f"Build capability for: {blocker.label}",
                priority=min(5.0, base_priority),
                target_pos=target_pos,
                created_tick=tick,
                spawned_from_id=blocker.blocker_id,
                evidence_refs=[lead.lead_id] if lead else []
            ))

        elif blocker.kind == BlockerKind.ACCESS:
            # Handle Access blockers (e.g. Home rebuilding)
            # These usually require visiting a specific location or person
            from src.core.models.enums import AttachmentKind
            target_pos = ctx.actor.spatial.home_pos
            if not target_pos:
                attachment = next((a for a in ctx.actor.mind.place_attachments if a.kind == AttachmentKind.HOME), None)
                if attachment:
                    target_pos = attachment.location_pos

            detours.append(ObjectiveRecord(
                objective_id=f"detour_access_{blocker.blocker_id}",
                project_id=project_id,
                kind=ObjectiveKind.COLLECT, # Rebuilding home counts as a collection/visit task
                label=f"Resolve access issue: {blocker.label}",
                priority=base_priority,
                target_pos=target_pos,
                created_tick=tick,
                spawned_from_id=blocker.blocker_id
            ))
            
        return detours
