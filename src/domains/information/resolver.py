"""
src/domains/information/resolver.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — InformationIntentResolver

Translates subjective query options or search parameters into executable ActionIntents.
"""

from __future__ import annotations
from typing import Optional, Tuple, Dict, Any

from src.core.state import EntityState, AuthoritativeState
from src.engine.intent.action_intent import ActionIntent
from src.domains.information.schema import InformationSourceCandidate, InformationQuery


class InformationIntentResolver:
    """
    Translates chosen candidates and query parameters into executable ActionIntents.
    """

    @staticmethod
    def resolve(
        entity: EntityState,
        candidate: InformationSourceCandidate,
        query: InformationQuery,
        state: AuthoritativeState,
    ) -> Optional[ActionIntent]:
        """
        Produce ActionIntent to ask information or move to the source if far away.
        """
        source_id = candidate.source_id
        source_npc = state.entities.get(source_id)

        # Proximity checks
        actor_pos = entity.navigation.position or (0.0, 0.0)
        
        # Proximity threshold of 2 units
        dist = 999.0
        target_pos = None
        if source_npc:
            target_pos = source_npc.navigation.position
            if target_pos:
                dx = target_pos[0] - actor_pos[0]
                dy = target_pos[1] - actor_pos[1]
                dist = (dx * dx + dy * dy) ** 0.5

        # 1. Resolve to MOVE_TO if source is far (>2.0 units)
        if dist > 2.0 and target_pos is not None:
            return ActionIntent(
                kind="MOVE_TO",
                actor_id=entity.id,
                target_id=source_id,
                payload={"position": target_pos},
                reason=f"Moving close to source {source_id} to query {query.subject}.",
            )

        # 2. Resolve to ASK_INFORMATION if close
        payload = {
            "subject": query.subject,
            "query_kind": query.kind,
            "cost_paid": candidate.cost_gold,
        }

        # 3. Affordability check
        actor_gold = getattr(entity.inventory, "gold", 0) or 0
        if actor_gold < candidate.cost_gold:
            # Gold blocker details
            return None

        return ActionIntent(
            kind="ASK_INFORMATION",
            actor_id=entity.id,
            target_id=source_id,
            payload=payload,
            reason=f"Querying {source_id} for information on {query.subject}.",
        )
