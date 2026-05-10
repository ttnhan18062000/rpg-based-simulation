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
        """
        from src.engine.cognition import SensoryFilter, AppraisalSystem
        from src.systems.strategic import StrategicIntelligenceSystem
        from src.engine.tactical import TacticalDecisionSystem
        from src.engine.domain.view import DomainView
        
        # Phase E5.3: Read-Only Guard (Hardening)
        readonly_state = state if getattr(state, "_readonly_cache", None) is state else state.to_readonly()
        
        # 1. Sensory Perception
        neighbors = DomainView.get_neighbor_view(readonly_state, entity, radius=10.0)
        salient_neighbors = SensoryFilter.filter_saliency(entity, neighbors)
        
        # 2. Regional Awareness
        trauma = DomainView.get_region_trauma(readonly_state, entity.navigation.position)
        
        # 3. Emotional Appraisal
        emotion = AppraisalSystem.evaluate_emotional_state(
            entity, 
            salient_neighbors, 
            region_trauma=trauma,
            social_context=entity.social
        )
        
        # 4. Blocker Inference
        current_proj = entity.strategic.projects.get(entity.strategic.current_project_id or "")
        inferred_up = StrategicIntelligenceSystem.infer_blockers(
            entity,
            entity.task.work_kind,
            entity.task.payload,
            navigation_failure=entity.navigation.last_failure_reason,
            current_project=current_proj
        )
        
        temp_entity = entity
        if inferred_up.blockers_add_or_update:
             from src.engine.apply import ApplyPath
             temp_strat = entity.strategic
             for b in inferred_up.blockers_add_or_update:
                  temp_strat = replace(temp_strat, blockers={**temp_strat.blockers, b.id: b})
             temp_entity = replace(entity, strategic=temp_strat)
             
        # 5. Strategic Intent
        strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(readonly_state, temp_entity, force=force)
        
        # Merge inferred blockers into strat_up
        if inferred_up.blockers_add_or_update:
            strat_up = replace(
                strat_up,
                blockers_add_or_update=list(set(strat_up.blockers_add_or_update + inferred_up.blockers_add_or_update))
            )
        
        temp_entity = entity
        if strat_up.current_project_id_set is not None:
             from src.engine.apply import ApplyPath
             temp_projects = dict(entity.strategic.projects)
             for p in strat_up.projects_add_or_update:
                 temp_projects[p.id] = p
                 
             temp_strat = replace(
                 entity.strategic,
                 projects=temp_projects,
                 current_project_id=strat_up.current_project_id_set,
                 current_objective_id=strat_up.current_objective_id_set
             )
             temp_entity = replace(entity, strategic=temp_strat)
             
        # 6. Tactical Intent
        tactical_up = TacticalDecisionSystem.evaluate_entity_intent(readonly_state, temp_entity)
        
        # 7. Bandwidth Enforcement
        from src.systems.detour import DetourSuggestionSystem
        bandwidth_up = DetourSuggestionSystem.enforce_bandwidth(temp_entity, state.tick)
        
        final_strat = strat_up
        if (strat_up.current_project_id_set is None and 
            not strat_up.projects_add_or_update and 
            tactical_up.strategic is not None):
             final_strat = tactical_up.strategic
             
        from src.core.updates import StrategicUpdate
        if final_strat is None:
             final_strat = StrategicUpdate()
             
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
