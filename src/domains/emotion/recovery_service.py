"""
src/domains/emotion/recovery_service.py
───────────────────────────────────────────────────────────────────────────────
RecoveryReadinessService for Phase 16.
"""

from __future__ import annotations
from dataclasses import replace
from src.core.cognition import RecoveryState

class RecoveryReadinessService:
    """Computes recovery state transitions and retry readiness parameters."""

    @staticmethod
    def is_ready_to_retry(state: RecoveryState, current_tick: int) -> bool:
        if state.recent_near_death:
            if state.recovery_until_tick is not None and current_tick >= state.recovery_until_tick:
                return True
            return state.retry_readiness >= 0.8
        return True

    @staticmethod
    def register_near_death(state: RecoveryState, current_tick: int) -> RecoveryState:
        return replace(
            state,
            recent_near_death=True,
            confidence_loss=min(1.0, state.confidence_loss + 0.4),
            retry_readiness=0.1,
            recovery_until_tick=current_tick + 30, # Forced 30 ticks of recovery
            trauma_tags=state.trauma_tags + ("near_death",)
        )
