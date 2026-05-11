# src/engine/domain/cognition.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Dict, Any, Optional, List
from dataclasses import replace

from src.core.updates import EntityUpdate, StrategicUpdate
from src.core.enums import ReasonCode

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState

class CognitionDomain:
    """
    Handles RPG Tactical Cognition and Sensory/Appraisal orchestration.
    """

    @staticmethod
    def execute_brain(
        state: AuthoritativeState,
        entity: EntityState,
        force: bool = False
    ) -> Dict[int, EntityUpdate]:
        """
        RPG TACTICAL COGNITION.
        Determines intent, appraisals, and strategic updates.
        Optimized v2.4: early-exit for idle/isolated entities and reduced object pressure.
        """
        from src.engine.cognition import SensoryFilter, AppraisalSystem
        from src.systems.strategic import StrategicIntelligenceSystem
        from src.engine.tactical import TacticalDecisionSystem
        # --- EARLY EXIT CASE (PHASE 2.1: Optimized) ---
        # Logic: If idle, has no project, and it's not the strategic cadence tick,
        # we can skip the expensive neighbor check and early-exit.
        is_idle = entity.task.work_kind == "IDLE"
        has_project = bool(entity.strategic.current_project_id)
        
        from src.engine.cadence import should_run, SystemCadence
        cad_val = SystemCadence().strategic_intelligence
        is_cadence_tick = should_run(state.tick, entity.id, cad_val)

        if not has_project and is_idle and not is_cadence_tick and not force:
             return {entity.id: EntityUpdate(entity_id=entity.id)}

        pos = entity.navigation.position
        # 1. Sensory Perception (Optimized O(1) grid query)
        readonly_state = state.to_readonly()
        from src.engine.domain.view import DomainView
        neighbors = DomainView.get_neighbor_view(readonly_state, entity, radius=10.0)
        
        if not neighbors and not has_project and is_idle and not force and not is_cadence_tick:
             return {entity.id: EntityUpdate(entity_id=entity.id)}

        salient_neighbors = SensoryFilter.filter_saliency(entity, neighbors)
        
        # 2. Regional Awareness (Optimized O(1) cache lookup)
        trauma = DomainView.get_region_trauma(readonly_state, pos)
        
        # 3. Emotional Appraisal
        emotion = AppraisalSystem.evaluate_emotional_state(
            entity, 
            salient_neighbors, 
            region_trauma=trauma,
            social_context=entity.social
        )
        
        # 4. Blocker Inference
        current_proj_id = entity.strategic.current_project_id
        current_proj = entity.strategic.projects.get(current_proj_id) if current_proj_id else None
        
        inferred_up = StrategicIntelligenceSystem.infer_blockers(
            entity,
            entity.task.work_kind,
            entity.task.payload,
            navigation_failure=entity.navigation.last_failure_reason,
            current_project=current_proj
        )
        
        temp_entity = entity
        if inferred_up.blockers_add_or_update:
             new_blockers = {**entity.strategic.blockers}
             for b in inferred_up.blockers_add_or_update:
                  new_blockers[b.id] = b
             temp_entity = replace(entity, strategic=replace(entity.strategic, blockers=new_blockers))
             
        # 5. Strategic Intent
        strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(readonly_state, temp_entity, force=force)
        
        # Merge inferred blockers into strat_up
        if inferred_up.blockers_add_or_update:
            strat_up = replace(
                strat_up,
                blockers_add_or_update=list(set(strat_up.blockers_add_or_update + inferred_up.blockers_add_or_update))
            )
        
        # 6. Tactical Intent
        # We must use the updated strategic context for tactical decisions.
        if strat_up.current_project_id_set is not None or strat_up.projects_add_or_update:
             new_projects = dict(temp_entity.strategic.projects)
             for p in strat_up.projects_add_or_update:
                 new_projects[p.id] = p
             
             temp_entity = replace(temp_entity, strategic=replace(temp_entity.strategic,
                 projects=new_projects,
                 current_project_id=strat_up.current_project_id_set if strat_up.current_project_id_set is not None else temp_entity.strategic.current_project_id,
                 current_objective_id=strat_up.current_objective_id_set if strat_up.current_objective_id_set is not None else temp_entity.strategic.current_objective_id
             ))
             
        tactical_up = TacticalDecisionSystem.evaluate_entity_intent(readonly_state, temp_entity, salient_neighbors, trauma)
        
        # 7. Bandwidth Enforcement
        from src.systems.strategic_systems.detour import DetourSuggestionSystem
        bandwidth_up = DetourSuggestionSystem.enforce_bandwidth(temp_entity, state.tick)
        
        final_strat = strat_up
        if (strat_up.current_project_id_set is None and 
            not strat_up.projects_add_or_update and 
            tactical_up.strategic is not None):
             final_strat = tactical_up.strategic
             
        if final_strat is None:
             from src.core.updates import StrategicUpdate
             final_strat = StrategicUpdate()
             
        # Merge bandwidth removals
        if bandwidth_up.leads_remove or bandwidth_up.concerns_remove:
            final_strat = replace(
                final_strat,
                leads_remove=list(set(final_strat.leads_remove + bandwidth_up.leads_remove)),
                concerns_remove=list(set(final_strat.concerns_remove + bandwidth_up.concerns_remove)),
                overload_source_set=bandwidth_up.overload_source_set or final_strat.overload_source_set,
                overload_tick_set=bandwidth_up.overload_tick_set or final_strat.overload_tick_set
            )
        
        return {entity.id: replace(tactical_up, 
            strategic=final_strat, 
            readiness_delta=0.0
        )}
