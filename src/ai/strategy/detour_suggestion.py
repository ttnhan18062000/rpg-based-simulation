from __future__ import annotations
from typing import TYPE_CHECKING, List

from src.core.models.strategy import (
    ObjectiveRecord, BlockerRecord, BlockerKind, ObjectiveKind, StrategicStatus
)
from src.ai.cognition_capacity import CognitionCapacityProfile

if TYPE_CHECKING:
    from src.ai.states.base import AIContext

class DetourSuggestionService:
    """Suggests remediation objectives (detours) to resolve blockers. [phase_3_task_7]"""

    @staticmethod
    def suggest_detours(ctx: AIContext, blocker: BlockerRecord, project_id: str, profile: CognitionCapacityProfile) -> List[ObjectiveRecord]:
        """Maps a blocker to one or more resolution objectives using Lead Matching."""
        detours = []
        tick = ctx.snapshot.tick
        
        # [PHASE 3 INTEL CAPACITY] 
        # Check recursion depth limit
        parent_obj = next((o for p in ctx.strategic.projects if p.project_id == project_id for o in p.objectives if o.objective_id == blocker.spawned_from_id), None)
        depth = (parent_obj.detour_depth + 1) if parent_obj else 1
        
        if depth > profile.detour_depth_limit:
             from src.core.aspects.mind import DecisionDriver
             # Note: We return empty and let the derivation service handle the fallback project mutation
             return []
        
        # Priority boost based on severity (le 5.0 constraint)
        base_priority = min(5.0, 3.0 + (blocker.severity * 2.0))
        
        target_pos = None
        if blocker.kind == BlockerKind.KNOWLEDGE:
            # Match Knowledge blocker with a relevant lead
            # 1. Look for a lead that matches the subject_ref and is NOT exhausted
            # [PHASE 3 INTEL CAPACITY] Skip tested leads unless wisdom is extremely low (0.1 threshold)
            wisdom = profile.judgment_stability # Proxy for wisdom-based persistence
            can_retry = wisdom < 0.1
            
            leads = [l for l in ctx.active_leads if l.subject == blocker.subject_ref and not l.is_exhausted]
            if not can_retry:
                 leads = [l for l in leads if l.lead_id not in ctx.strategic.tested_lead_ids]
            
            lead = leads[0] if leads else None
            
            # 2. Prefer untested leads if multiple exist (Lifecycle Awareness)
            if leads:
                untested = [l for l in leads if not l.tested]
                if untested:
                    lead = untested[0]
            
            # 3. Fallback to the freshest 'investigation' lead
            if not lead:
                all_leads = [l for l in ctx.active_leads if not l.is_exhausted]
                if not can_retry:
                     all_leads = [l for l in all_leads if l.lead_id not in ctx.strategic.tested_lead_ids]
                lead = all_leads[0] if all_leads else None
            
            target_pos = lead.target_coords if lead else None
            
            # [TCK-20260414-SOCIAL-02] Use CandidateZone center for scouting if lead is vague
            if lead and not target_pos and lead.candidate_zone_ids:
                 zone_id = lead.candidate_zone_ids[0]
                 zone = next((z for z in ctx.strategic.candidate_zones if z.zone_id == zone_id), None)
                 if zone:
                      target_pos = zone.approx_coords
            
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
                spawned_from_id=blocker.blocker_id,
                detour_depth=depth # [PHASE 3 INTEL CAPACITY]
            ))
            
        elif blocker.kind == BlockerKind.SOCIAL:
            # Match Social blocker with a recruitment detour
            # Default to the Inn if it exists
            from src.ai.states.town import find_building
            inn = find_building(ctx.snapshot, "inn")
            target_pos = inn.spatial.pos if inn else None
            
            detours.append(ObjectiveRecord(
                objective_id=f"detour_recruit_{blocker.blocker_id}",
                project_id=project_id,
                kind=ObjectiveKind.INTERACT, # Recruitment
                label=f"Find allies for: {blocker.label}",
                priority=min(5.0, base_priority + 0.2), # High priority to find help
                target_pos=target_pos,
                created_tick=tick,
                spawned_from_id=blocker.blocker_id,
                detour_depth=depth
            ))
            
        # [PHASE 3 INTEL CAPACITY] Breadth Limit
        if len(detours) > profile.active_slice_limit:
             detours = detours[:profile.active_slice_limit]
             
        return detours
