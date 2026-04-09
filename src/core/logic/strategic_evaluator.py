"""Strategic Evaluator Service — Phase 1 Stage 7 logic for project and objective selection.

This service implements the high-level 'Strategic Pass' that converts 
durable directives and immediate concerns into active commitments.
"""

import logging
from typing import TYPE_CHECKING
from src.core.models.strategy import (
    StrategicState, StrategicStatus, ProjectRecord, ObjectiveRecord, 
    ConcernRecord, ConcernKind, ProjectKind, ObjectiveKind,
    BlockerRecord, BlockerKind
)
from src.actions.base import StrategicUpdate

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class StrategicEvaluatorService:
    """Evaluates an entity's strategic state and proposes updates to active commitments."""

    @classmethod
    def evaluate(cls, entity: 'Entity', world: 'WorldState', current_tick: int) -> StrategicUpdate | None:
        """Run the strategic appraisal pass for the entity.
        
        Args:
            entity: The entity to evaluate.
            world: The authoritative world state snapshot.
            current_tick: The current simulation tick.
            
        Returns:
            A StrategicUpdate if changes are needed, else None.
        """
        strat = entity.mind.strategic
        routine = entity.mind.routine
        decision = entity.mind.decision
        
        updates = StrategicUpdate()
        has_changes = False

        # --- 0. Objective Resolution ---
        # If we have a current objective, check if it's done.
        current_obj = None
        if strat.current_objective_id and strat.current_project_id:
            project = next((p for p in strat.projects if p.project_id == strat.current_project_id), None)
            if project:
                current_obj = next((o for o in project.objectives if o.objective_id == strat.current_objective_id), None)
        
        if current_obj and current_obj.status == StrategicStatus.ACTIVE:
            is_resolved = False
            # Resolve by kind
            if current_obj.kind == ObjectiveKind.VISIT and current_obj.target_pos:
                dist = entity.spatial.pos.manhattan(current_obj.target_pos)
                if dist < 2:
                    is_resolved = True
            elif current_obj.kind == ObjectiveKind.KILL and current_obj.target_id:
                # Check perception memory for target status
                target_belief = entity.mind.perception.entity_memory.get(current_obj.target_id)
                # If target is missing or known dead, resolve
                if not target_belief or target_belief.stale_ticks > 50:
                     is_resolved = True # Consider it 'gone' or 'fixed'
            
            if is_resolved:
                # Propose resolution
                updated_obj = current_obj.model_copy()
                updated_obj.status = StrategicStatus.RESOLVED
                updated_obj.resolved_tick = current_tick
                
                # We need to update the project's objective list too
                if project:
                    updated_prj = project.model_copy()
                    # Replace the objective in the list
                    for i, obj in enumerate(updated_prj.objectives):
                        if obj.objective_id == current_obj.objective_id:
                            updated_prj.objectives[i] = updated_obj
                            break
                    
                    # Clear current markers
                    updates.current_objective_id = "" # Clear to trigger next selection
                    updates.projects_add_or_update.append(updated_prj)
                    has_changes = True
                    current_obj = None # No longer active

        # --- 1. Biological Concerns ---
        needs_attention = routine.hunger_level > 0.8 or routine.sleep_debt > 0.8
        survival_concern_id = "concern_survival"
        existing_survival = next((c for c in strat.concerns if c.concern_id == survival_concern_id), None)
        
        if needs_attention:
            if not existing_survival:
                update_c = ConcernRecord(
                    concern_id=survival_concern_id,
                    kind=ConcernKind.THREAT,
                    label="Critical Biological Need",
                    priority=4.5,
                    created_tick=current_tick
                )
                updates.concerns_add_or_update.append(update_c)
                has_changes = True
        elif existing_survival:
            updates.concerns_remove.append(survival_concern_id)
            has_changes = True
            
        # --- 1.1 Regional & Spatial Concerns (Stage 15) ---
        from src.core.world.regions import find_region_at
        current_region = find_region_at(entity.spatial.pos, world.regions)
        region_threat_id = "concern_regional_threat"
        existing_threat = next((c for c in strat.concerns if c.concern_id == region_threat_id), None)
        
        if current_region:
            registry = getattr(world, 'region_consequence_registry', {})
            record = registry.get(current_region.region_id)
            if record:
                # Danger Threshold (Hysteresis)
                is_dangerous = record.danger_level > 0.6 or record.stability < 0.4
                # Recovery Threshold
                is_safe = record.danger_level < 0.3 and record.stability > 0.7
                
                if is_dangerous and not existing_threat:
                    # High salience threat
                    update_c = ConcernRecord(
                        concern_id=region_threat_id,
                        kind=ConcernKind.THREAT,
                        label=f"Instability in {current_region.name}",
                        priority=6.0, # Higher than biological usually
                        created_tick=current_tick
                    )
                    updates.concerns_add_or_update.append(update_c)
                    has_changes = True
                elif is_safe and existing_threat:
                    updates.concerns_remove.append(region_threat_id)
                    has_changes = True

        # Nearby Scar Detection
        scar_concern_id = "concern_nearby_scar"
        existing_scar_c = next((c for c in strat.concerns if c.concern_id == scar_concern_id), None)
        
        # Look for scars within 10 units
        nearby_scars = [s for s in getattr(world, 'scar_registry', []) 
                       if s.location_pos.manhattan(entity.spatial.pos) < 10]
        
        if nearby_scars and not existing_scar_c:
            closest = min(nearby_scars, key=lambda s: s.location_pos.manhattan(entity.spatial.pos))
            update_c = ConcernRecord(
                concern_id=scar_concern_id,
                kind=ConcernKind.OPPORTUNITY,
                label=f"Trauma Site: {closest.kind.value}",
                priority=3.5,
                created_tick=current_tick,
                source_event_id=closest.source_event_id
            )
            updates.concerns_add_or_update.append(update_c)
            has_changes = True
        elif not nearby_scars and existing_scar_c:
             updates.concerns_remove.append(scar_concern_id)
             has_changes = True

        # --- 2. Blocker Detection (Phase 3) ---
        # If we have an active objective but are 'stuck' (idle for too long)
        is_stuck = decision.consecutive_idle_ticks > 50
        if current_obj and is_stuck and not any(b.kind == BlockerKind.KNOWLEDGE for b in current_obj.blockers):
            # If we don't know the exact location or can't reach it, it's likely a knowledge blocker
            if current_obj.kind == ObjectiveKind.VISIT and not current_obj.target_pos:
                new_blocker = BlockerRecord(
                    blocker_id=f"blocker_loc_{current_obj.objective_id}",
                    kind=BlockerKind.KNOWLEDGE,
                    label="Unknown Location",
                    description=f"No known coordinates for {current_obj.label}",
                    discovered_tick=current_tick
                )
                
                updated_prj = project.model_copy()
                for i, obj in enumerate(updated_prj.objectives):
                    if obj.objective_id == current_obj.objective_id:
                        updated_prj.objectives[i].blockers.append(new_blocker)
                        break
                
                updates.projects_add_or_update.append(updated_prj)
                has_changes = True
                current_obj = updated_prj.objectives[i] # Refresh local ref

        # --- 3. Project Selection & Detours ---
        # Consolidate concerns: existing ones not being removed + newly added/updated ones
        concerns_to_consider = {c.concern_id: c for c in strat.concerns if c.concern_id not in updates.concerns_remove}
        for c in updates.concerns_add_or_update:
            concerns_to_consider[c.concern_id] = c
            
        highest_concern = max(concerns_to_consider.values(), key=lambda c: c.priority) if concerns_to_consider else None

        if highest_concern and highest_concern.priority > 4.0:
            if highest_concern.concern_id == survival_concern_id:
                if strat.current_project_id != "project_survival":
                    if strat.current_project_id:
                        updates.interrupted_project_id = strat.current_project_id
                    
                    updates.current_project_id = "project_survival"
                    updates.current_objective_id = "obj_satisfy_needs"
                    has_changes = True
                    
                    survival_prj = ProjectRecord(
                        project_id="project_survival",
                        kind=ProjectKind.SOCIAL,
                        label="Ensure Survival",
                        priority=5.0,
                        urgency=1.0,
                        created_tick=current_tick,
                        metadata={"reason": highest_concern.label if highest_concern else "Biological Need"}
                    )
                    survival_obj = ObjectiveRecord(
                        objective_id="obj_satisfy_needs",
                        project_id="project_survival",
                        kind=ObjectiveKind.INTERACT,
                        label="Find food or rest",
                        priority=5.0,
                        created_tick=current_tick
                    )
                    survival_prj.objectives.append(survival_obj)
                    survival_prj.active_objective_id = "obj_satisfy_needs"
                    updates.projects_add_or_update.append(survival_prj)
                    
            # --- 3.1 Regional Threat Intervention (Stage 15) ---
            elif highest_concern.concern_id == region_threat_id:
                if strat.current_project_id != "project_stabilization":
                    if strat.current_project_id:
                        updates.interrupted_project_id = strat.current_project_id
                    
                    updates.current_project_id = "project_stabilization"
                    updates.current_objective_id = "obj_stabilize_region"
                    has_changes = True
                    
                    stabilize_prj = ProjectRecord(
                        project_id="project_stabilization",
                        kind=ProjectKind.SOCIAL,
                        label="Restore Regional Order",
                        priority=5.0,
                        urgency=0.9,
                        created_tick=current_tick,
                        metadata={"reason": highest_concern.label}
                    )
                    stabilize_obj = ObjectiveRecord(
                        objective_id="obj_stabilize_region",
                        project_id="project_stabilization",
                        kind=ObjectiveKind.INTERACT,
                        label=f"Address Crisis in {current_region.name if current_region else 'Region'}",
                        priority=5.0,
                        created_tick=current_tick
                    )
                    stabilize_prj.objectives.append(stabilize_obj)
                    stabilize_prj.active_objective_id = "obj_stabilize_region"
                    updates.projects_add_or_update.append(stabilize_prj)

            # --- 3.2 Trauma Site Investigation (Stage 15) ---
            elif highest_concern.concern_id == scar_concern_id:
                # If we aren't already investigating, add an objective to the current project or a new one
                invest_prj_id = "project_trauma_investigation"
                if strat.current_project_id != invest_prj_id:
                    # Add an investigation project or objective
                    if not any(p.project_id == invest_prj_id for p in strat.projects):
                         new_prj = ProjectRecord(
                             project_id=invest_prj_id,
                             kind=ProjectKind.INVESTIGATION,
                             label="World Trauma Investigation",
                             priority=4.0,
                             created_tick=current_tick
                         )
                         updates.projects_add_or_update.append(new_prj)
                    
                    updates.current_project_id = invest_prj_id
                    updates.current_objective_id = f"obj_investigate_{highest_concern.source_event_id}"
                    has_changes = True
                    
                    # Fetch closest scar to get location
                    closest = min(nearby_scars, key=lambda s: s.location_pos.manhattan(entity.spatial.pos))
                    invest_obj = ObjectiveRecord(
                        objective_id=updates.current_objective_id,
                        project_id=invest_prj_id,
                        kind=ObjectiveKind.VISIT,
                        label=f"Analyze {closest.kind.value}",
                        priority=4.5,
                        created_tick=current_tick,
                        target_pos=closest.location_pos
                    )
                    updates.projects_add_or_update[-1].objectives.append(invest_obj)

        # --- 4. Strategic Detours (Phase 3 Inquiry) ---
        elif current_obj and any(b.kind == BlockerKind.KNOWLEDGE for b in current_obj.blockers):
            # We are blocked by knowledge. Can we find a lead?
            # (Heuristic: Look for leads matching the objective label or kind)
            matching_lead = next((l for l in strat.leads if not l.is_exhausted), None)
            
            if matching_lead:
                # Detour: Investigation
                detour_obj_id = f"detour_investigate_{matching_lead.lead_id}"
                if current_obj.objective_id != detour_obj_id:
                    new_detour = ObjectiveRecord(
                        objective_id=detour_obj_id,
                        project_id=current_obj.project_id,
                        kind=ObjectiveKind.INVESTIGATE,
                        label=f"Investigate {matching_lead.label}",
                        priority=current_obj.priority + 0.5,
                        created_tick=current_tick,
                        target_pos=matching_lead.target_coords # Bias toward lead coords
                    )
                    
                    updated_prj = project.model_copy()
                    updated_prj.objectives.append(new_detour)
                    updated_prj.active_objective_id = detour_obj_id
                    
                    updates.projects_add_or_update.append(updated_prj)
                    updates.current_objective_id = detour_obj_id
                    has_changes = True
            else:
                # Detour: Gossip/Social
                detour_obj_id = f"detour_gossip_{current_obj.objective_id}"
                if current_obj.objective_id != detour_obj_id:
                    new_detour = ObjectiveRecord(
                        objective_id=detour_obj_id,
                        project_id=current_obj.project_id,
                        kind=ObjectiveKind.INTERACT,
                        label=f"Gather rumors about {current_obj.label}",
                        priority=current_obj.priority + 0.3,
                        created_tick=current_tick
                    )
                    updated_prj = project.model_copy()
                    updated_prj.objectives.append(new_detour)
                    updated_prj.active_objective_id = detour_obj_id
                    
                    updates.projects_add_or_update.append(updated_prj)
                    updates.current_objective_id = detour_obj_id
                    has_changes = True

        # --- 5. Default Project Selection ---
        elif not strat.current_project_id and strat.directives:
            top_directive = max(strat.directives, key=lambda d: d.priority)
            project_id = f"project_{top_directive.directive_id}"
            existing_prj = next((p for p in strat.projects if p.project_id == project_id), None)
            
            if not existing_prj:
                new_prj = ProjectRecord(
                    project_id=project_id,
                    kind=ProjectKind.DEVELOPMENT,
                    label=f"Pursue {top_directive.label}",
                    priority=top_directive.priority,
                    created_tick=current_tick,
                    metadata={"reason": f"Inspired by Directive: {top_directive.label}"}
                )
                init_obj = ObjectiveRecord(
                    objective_id=f"obj_init_{project_id}",
                    project_id=project_id,
                    kind=ObjectiveKind.VISIT,
                    label="Explore surroundings",
                    priority=1.0,
                    created_tick=current_tick
                )
                new_prj.objectives.append(init_obj)
                new_prj.active_objective_id = init_obj.objective_id
                
                updates.projects_add_or_update.append(new_prj)
                updates.current_project_id = project_id
                updates.current_objective_id = init_obj.objective_id
                has_changes = True
            else:
                updates.current_project_id = project_id
                updates.current_objective_id = existing_prj.active_objective_id
                has_changes = True

        if has_changes:
            return updates
        return None

        if has_changes:
            return updates
        return None
