"""
src/domains/combat_engagement/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — CombatEngagementPhase

Integrates sensor candidate targets with subjective postures.
Bounded overhead per tick via spatial filtering.
"""

from __future__ import annotations
from typing import Dict, List, Optional

from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate
from src.domains.combat_engagement.service import CombatEngagementDecisionService
from src.domains.combat_engagement.resolver import PostureIntentResolver


class CombatEngagementPhase:
    """
    Evaluates dynamic pre-combat engagement postures at strategic cadence.
    """

    @staticmethod
    def apply(
        state: AuthoritativeState,
        context: Optional[dict] = None,
    ) -> StateUpdate:
        """
        Evaluate eligible actors on hostiles entering sensory visibility.
        """
        update = StateUpdate()
        entity_updates: Dict[int, EntityUpdate] = {}

        # 1. Filter actors (alive, active, hero class, etc.)
        actors = [e for e in state.entities.values() if e.combat.alive and e.lifecycle.active]
        if not actors:
            return update

        # To avoid pairwise NxN comparison, let's only compare actors against nearby candidates
        # Retrieve sensory visibility or nearby hostiles
        for actor in actors:
            # Check if actor is stunned/frozen
            # Retrieve nearby target options (e.g. within 10 units)
            targets = [
                e for e in state.entities.values()
                if e.id != actor.id and e.combat.alive and e.lifecycle.active
                # Simple distance proxy sensory check
                and ((e.navigation.position[0] - actor.navigation.position[0]) ** 2 +
                     (e.navigation.position[1] - actor.navigation.position[1]) ** 2) <= 100.0  # within range 10
            ]
            
            if not targets:
                continue

            # Limit candidates evaluated per entity (cap = 3) to strictly stay within strategic budget
            targets_to_evaluate = targets[:3]

            for target in targets_to_evaluate:
                # 2. Subjective Pre-combat evaluation
                result = CombatEngagementDecisionService.evaluate(actor, target, state)
                
                # Apply bridge mappings
                intent, strat_upd = PostureIntentResolver.resolve(
                    actor_id=actor.id,
                    target_id=target.id,
                    posture=result.posture,
                    target_pos=target.navigation.position,
                )
                
                # Update properties with chosen posture
                prop_updates = {
                    "last_combat_posture": result.posture.value,
                    "last_combat_posture_target": target.id,
                }
                
                entity_updates[actor.id] = EntityUpdate(
                    entity_id=actor.id,
                    intent_results=[],
                    property_updates=prop_updates,
                    strategic=strat_upd,
                )
                break # evaluate first target only


        if entity_updates:
            update = StateUpdate(entity_updates=entity_updates)

        return update
