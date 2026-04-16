from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional

from src.core.models.strategy import StrategicStatus, LeadRecord, CandidateZoneRecord, ObjectiveKind
from src.actions.base import StrategicUpdate

if TYPE_CHECKING:
    from src.ai.states.base import AIContext
    from src.ai.cognition_capacity import CognitionCapacityProfile

logger = logging.getLogger(__name__)

class StrategicUncertaintyService:
    """Handles the resolution of vague spatial information into precise coordinates. [TCK-20260414-SOCIAL-02]
    
    This enforces the 'Anti-Cheating' rule: rumors only provide zones; precise targets 
    require proximity-based evidence resolution or direct intel.
    """

    @staticmethod
    def resolve_uncertainty(ctx: AIContext, profile: CognitionCapacityProfile) -> StrategicUpdate:
        """Inspects the current state and resolves zones to coordinates if evidence is found."""
        # 1. Proximity Resolution (Waveform Collapse)
        up = StrategicUncertaintyService._resolve_proximity(ctx, profile)
        
        # 2. Contradiction Processing (Degradation) [MILESTONE 5]
        contra_up = StrategicUncertaintyService.handle_contradictions(ctx, profile)
        
        # Merge updates
        up.leads_add_or_update.extend(contra_up.leads_add_or_update)
        up.hypotheses_add_or_update.extend(contra_up.hypotheses_add_or_update)
        if contra_up.current_objective_id:
             up.current_objective_id = contra_up.current_objective_id
             
        return up

    @staticmethod
    def handle_contradictions(ctx: AIContext, profile: CognitionCapacityProfile) -> StrategicUpdate:
        """Degrades certainty and handles hypothesis impacts when contradictions appear. [MILESTONE 5]"""
        actor = ctx.actor
        strat = actor.mind.strategic
        up = StrategicUpdate(target_id=actor.id)
        
        sensitivity = getattr(profile, "contradiction_sensitivity", 0.5)
        
        # 1. Lead Degradation
        for lead in strat.leads:
            if lead.contradiction_count > 0:
                # Penalty: 10% per contradiction * sensitivity
                penalty = lead.contradiction_count * 0.1 * sensitivity
                new_certainty = max(0.0, lead.certainty - penalty)
                
                if new_certainty != lead.certainty:
                    up.leads_add_or_update.append(lead.model_copy(update={"certainty": round(new_certainty, 3)}))
        
        # 2. Hypothesis Impact
        for hypo in strat.hypotheses:
            if not hypo.is_active: continue
            
            total_contra = 0
            for lid in hypo.supporting_lead_ids:
                lead = next((l for l in strat.leads if l.lead_id == lid), None)
                if lead:
                    total_contra += lead.contradiction_count
            
            if total_contra > 0:
                # Hypothesis penalty is more aggressive
                penalty = total_contra * 0.15 * sensitivity
                new_conf = max(0.0, hypo.confidence - penalty)
                
                if new_conf != hypo.confidence:
                    up.hypotheses_add_or_update.append(hypo.model_copy(update={"confidence": round(new_conf, 3)}))
                    
                    if new_conf < 0.2:
                        # Deactivate hypothesis if confidence is too low
                         up.hypotheses_add_or_update[-1].is_active = False
                         logger.info("Hypothesis %s deactivated due to low confidence (%s)", hypo.hypothesis_id, new_conf)

        return up

    @staticmethod
    def _resolve_proximity(ctx: AIContext, profile: CognitionCapacityProfile) -> StrategicUpdate:
        """Internal logic for proximity-based resolution."""
        actor = ctx.actor
        strat = actor.mind.strategic
        up = StrategicUpdate(target_id=actor.id)
        
        # 1. Coordinate Resolution through Proximity [Anti-Cheating]
        # If we are investigating a zone and are physically near it, we 'resolve' it.
        curr_obj = ctx.current_objective
        if curr_obj and curr_obj.kind == ObjectiveKind.INVESTIGATE and curr_obj.status == StrategicStatus.ACTIVE:
            # Look for related leads and zones
            for lead_id in curr_obj.evidence_refs:
                lead = next((l for l in strat.leads if l.lead_id == lead_id), None)
                if not lead or lead.target_coords:
                     continue
                
                # Check related zones
                for zone_id in lead.candidate_zone_ids:
                    zone = next((z for z in strat.candidate_zones if z.zone_id == zone_id), None)
                    if not zone:
                         continue
                    
                    # Resolve logic: if we are near the 'hypothesized' center of the zone
                    # In a real sim, we'd check if the entity has PERCEPTION of the target.
                    # For this strategic layer, we use a simple proximity check to 'collapsing' the wave.
                    zone_center = zone.approx_coords if hasattr(zone, "approx_coords") else None
                    if not zone_center and zone.region_id:
                         # Fallback to region center or similar if model supports it
                         pass
                    
                    # Here we simulate the 'Discovery' event
                    # We check if the actor's current position is within the resolution radius
                    # (Usually 5 tiles for rumors)
                    resolution_radius = 5
                    
                    # For testing/demo, we'll use the 'actual' world truth if available in snapshot
                    # anti-cheat: we only look for the target if we are close enough to have 'sensed' it.
                    target_truth = StrategicUncertaintyService._find_world_truth(ctx, lead)
                    if target_truth:
                        dist = actor.spatial.pos.manhattan(target_truth)
                        if dist <= resolution_radius:
                             # RESOLVED!
                             updated_lead = lead.model_copy(update={
                                 "target_coords": target_truth,
                                 "certainty": 1.0,
                                 "source_confidence": 1.0,
                                 "semantic_tags": lead.semantic_tags + ["resolved_evidence"]
                             })
                             up.leads_add_or_update.append(updated_lead)
                             
                             # Also update the objective to point to the real coords
                             updated_obj = curr_obj.model_copy(update={
                                 "target_pos": target_truth,
                                 "label": f"Resolved: {curr_obj.label}"
                             })
                             # We'll need to update the project that owns this objective
                             # The derivation service or a broad update will handle this.
                             up.current_objective_id = updated_obj.objective_id
                             
                             logger.info("StrategicUncertaintyService: Resolved lead %s to %s", lead_id, target_truth)
        
        return up

    @staticmethod
    def _find_world_truth(ctx: AIContext, lead: LeadRecord):
        """Helper to find the 'actual' coordinates of a subject in the world. [INTERNAL]"""
        # This is the only place it's 'allowed' to peek at the reality to collapse the zone.
        # It must ONLY be used when the resolution condition (proximity) is met.
        snapshot = ctx.snapshot
        subject = lead.subject
        
        # 1. Resource Nodes
        for node in snapshot.resource_nodes:
            if node.item_group == subject or (hasattr(node, "item_id") and node.item_id == subject):
                return node.spatial.pos
                
        # 2. Camps
        if "camp" in subject or "hostile" in lead.semantic_tags:
            for cx, cy in snapshot.camps:
                # Return the first camp (simplified)
                from src.core.models.vectors import Vector2
                return Vector2(x=cx, y=cy)
        
        return None
