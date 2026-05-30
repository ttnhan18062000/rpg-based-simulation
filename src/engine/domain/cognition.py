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

    SYSTEM BOUNDARIES:
    - 1. Strategic Planning (Authoritative): Strategic project and goal choice occurs exclusively
      inside the pipeline-level `StrategicIntelligenceSystem.fused_strategic_pass()`.
    - 2. Emotional Appraisal: Handled by `AppraisalSystem` to evaluate emotional state based on
      tactical context, regional trauma, and sensory filters.
    - 3. Tactical Decision: Handled by `TacticalDecisionSystem` to evaluate tactical intent/actions
      based on current active strategic project/objective.
    - 4. Action Execution: Sequential action execution in the main loop schedules movements and acts.
    """

    @staticmethod
    def execute_brain(
        state: AuthoritativeState,
        entity: EntityState,
        force: bool = False
    ) -> Dict[int, EntityUpdate]:
        """
        RPG TACTICAL COGNITION.
        Determines tactical intent and emotional appraisals.
        Optimized v2.4: early-exit for idle/isolated entities and reduced object pressure.
        """
        from src.engine.cognition import SensoryFilter, AppraisalSystem
        from src.engine.tactical import TacticalDecisionSystem
        
        is_idle = entity.task.work_kind == "IDLE"
        has_project = bool(entity.strategic.current_project_id)
        
        from src.engine.cadence import should_run, SystemCadence
        cad_val = SystemCadence().strategic_intelligence
        is_cadence_tick = should_run(state.tick, entity.id, cad_val)

        if not has_project and is_idle and not is_cadence_tick and not force:
             return {entity.id: EntityUpdate(entity_id=entity.id)}

        pos = entity.navigation.position
        readonly_state = state.to_readonly()
        from src.engine.domain.view import DomainView
        neighbors = DomainView.get_neighbor_view(readonly_state, entity, radius=10.0)
        
        if not neighbors and not has_project and is_idle and not force and not is_cadence_tick:
             return {entity.id: EntityUpdate(entity_id=entity.id)}

        salient_neighbors = SensoryFilter.filter_saliency(entity, neighbors)
        trauma = DomainView.get_region_trauma(readonly_state, pos)
        
        # 1. Emotional Appraisal
        emotion = AppraisalSystem.evaluate_emotional_state(
            entity, 
            salient_neighbors, 
            region_trauma=trauma,
            social_context=entity.social
        )
             
        # 2. Tactical Intent
        tactical_up = TacticalDecisionSystem.evaluate_entity_intent(readonly_state, entity, salient_neighbors, trauma)
        
        return {entity.id: replace(tactical_up, 
            strategic=None, 
            readiness_delta=0.0
        )}
