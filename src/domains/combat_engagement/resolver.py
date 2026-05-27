"""
src/domains/combat_engagement/resolver.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — Posture-to-Intent Bridge

Translates subjective CombatPostures into ActionIntents or StrategicUpdates.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Tuple

from src.domains.combat_engagement.schema import CombatPosture, CombatEngagementDecisionResult
from src.engine.intent.action_intent import ActionIntent
from src.core.updates import StrategicUpdate, EntityUpdate
from src.core.strategic import ProjectState, ObjectiveState, ProjectKind, ObjectiveKind


class PostureIntentResolver:
    """
    Translates subjective postures into adapted ActionIntents or StrategicUpdates.
    """

    @staticmethod
    def resolve(
        actor_id: int,
        target_id: int,
        posture: CombatPosture,
        target_pos: Optional[Tuple[float, float]] = None,
    ) -> Tuple[Optional[ActionIntent], Optional[StrategicUpdate]]:
        """
        Produce ActionIntent and StrategicUpdate corresponding to posture.
        """
        intent = None
        strat = None

        if posture in (CombatPosture.ENGAGE, CombatPosture.VENGEANCE_ENGAGE):
            # Attack intent
            payload = {}
            if target_pos:
                payload["position"] = target_pos
            intent = ActionIntent(
                kind="ATTACK_TARGET",
                actor_id=actor_id,
                target_id=target_id,
                payload=payload,
                reason=f"Engaging target {target_id} with posture {posture.value}",
            )

        elif posture in (CombatPosture.RETREAT, CombatPosture.PANIC_FLEE):
            # Retreat movement mode update
            payload = {"retreat": True}
            intent = ActionIntent(
                kind="MOVE_TO",
                actor_id=actor_id,
                target_id=None,
                payload=payload,
                reason=f"Retreating with posture {posture.value}",
            )

        elif posture == CombatPosture.AVOID:
            # strategic detour or blocker
            # Set target coordinate detour to avoid target
            payload = {"detour": True}
            intent = ActionIntent(
                kind="MOVE_TO",
                actor_id=actor_id,
                target_id=None,
                payload=payload,
                reason="Routing detour around stronger threat.",
            )

        elif posture == CombatPosture.CALL_HELP:
            # Strategic need blocker to recruit
            pass

        return intent, strat
