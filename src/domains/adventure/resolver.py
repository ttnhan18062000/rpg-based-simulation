"""
src/domains/adventure/resolver.py
───────────────────────────────────────────────────────────────────────────────
Phase 3 — ObjectiveIntentResolver

Translates an active objective state into immediate adapted executable ActionIntent targets.
Ensures strategic alignment with the authoritative action vocabulary.
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Tuple

from src.core.strategic import ObjectiveState, ObjectiveKind
from src.engine.intent.action_intent import ActionIntent


class ObjectiveIntentResolver:
    """
    Translates ObjectiveState structures into low-level simulation ActionIntents
    that the ActionIntentAdapter can evaluate and execute.
    """

    @staticmethod
    def resolve(
        entity_id: int,
        objective: ObjectiveState,
        payload: Optional[Dict[str, Any]] = None,
    ) -> ActionIntent:
        """
        Generate the adapted ActionIntent corresponding to the objective state.
        
        Args:
            entity_id: The executing entity's ID
            objective: The active ObjectiveState to resolve
            payload: Optional execution-level payload overrides (e.g. coordinates, item specs)
            
        Returns:
            An ActionIntent matching the objective's strategic intent.
        """
        intent_payload = dict(payload) if payload else {}
        
        # Determine the action kind based on ObjectiveKind
        kind = "DEFER"
        target_id = objective.target
        
        if objective.target_position and "position" not in intent_payload:
            intent_payload["position"] = objective.target_position

        if objective.kind == ObjectiveKind.REACH_SERVICE:
            kind = "MOVE_TO"
            
        elif objective.kind == ObjectiveKind.BUY_ITEM:
            kind = "BUY_ITEM"
            
        elif objective.kind == ObjectiveKind.ACQUIRE_ITEM:
            kind = "REQUEST_CRAFT"
            
        elif objective.kind == ObjectiveKind.REACH_LOCATION:
            kind = "MOVE_TO"
            
        elif objective.kind == ObjectiveKind.ACCEPT_QUEST:
            kind = "ACCEPT_QUEST"
            
        elif objective.kind == ObjectiveKind.DEFEAT_ENEMY:
            kind = "ATTACK_TARGET"
            
        elif objective.kind == ObjectiveKind.REACH_RESOURCE:
            # First reach, then harvest
            kind = "MOVE_TO"
            
        elif objective.kind == ObjectiveKind.HARVEST_RESOURCE:
            kind = "HARVEST_RESOURCE"
            
        elif objective.kind == ObjectiveKind.ASK_INFORMATION:
            kind = "ASK_INFORMATION"
            
        elif objective.kind == ObjectiveKind.RETURN_TOWN:
            kind = "RETURN_TOWN"
            
        else:
            kind = "MOVE_TO"

        return ActionIntent(
            kind=kind,
            actor_id=entity_id,
            target_id=target_id,
            payload=intent_payload,
            source_opportunity_id=objective.id,
            reason=f"Resolving objective {objective.id} of kind {objective.kind.value}",
        )
