"""Strategic Consequence Service - translating semantic events into strategic shifts. [PHASE 5]

This service is the bridge between interpreted life events (social) and 
durable strategic reprioritization (directives, projects, concerns).
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional

from src.actions.base import StrategicUpdate

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.core.entities.entity import Entity
    from src.core.models.life_events import InterpretedLifeEvent, TurningPointRecord

logger = logging.getLogger(__name__)

class StrategicConsequenceService:
    """Orchestrates strategic shifts derived from narrated consequences."""

    @classmethod
    def process_consequences(
        cls, 
        world: WorldState, 
        entity: Entity, 
        event: InterpretedLifeEvent, 
        tp: Optional[TurningPointRecord] = None
    ) -> StrategicUpdate:
        """Analyze an event/turning point and generate strategic updates.
        
        This is called after social/reputation updates have been applied.
        """
        updates = StrategicUpdate(target_id=entity.id)
        
        # 1. Concern Generation (Task 2)
        from src.core.logic.concern_generation import ConcernGenerationService
        ConcernGenerationService.generate(world, entity, event, updates)
        
        # 2. Directive Mutation (Task 3)
        if tp:
            from src.core.logic.directive_mutation_service import DirectiveMutationService
            DirectiveMutationService.evaluate_mutation(world, entity, tp, updates)
            
        # 3. Place Appraisal (Task 4)
        from src.core.logic.place_threat_appraisal import PlaceThreatAppraisalService
        PlaceThreatAppraisalService.appraise(world, entity, event, updates)
        
        # 4. Project Mutation & Interruption (Task 5)
        from src.core.logic.project_mutation_service import ProjectMutationService
        ProjectMutationService.process_interruption(world, entity, event, tp, updates)
        
        return updates
