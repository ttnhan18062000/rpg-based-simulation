"""
src/domains/emotion/emotion_service.py
───────────────────────────────────────────────────────────────────────────────
EmotionUpdateService for Phase 16.
"""

from __future__ import annotations
from dataclasses import replace
from src.core.cognition import EmotionalModel

class EmotionUpdateService:
    """Updates short-term emotional parameters based on core events."""

    @staticmethod
    def update_on_event(model: EmotionalModel, event_kind: str) -> EmotionalModel:
        fear = model.fear
        confidence = model.confidence
        frustration = model.frustration
        curiosity = model.curiosity
        satisfaction = model.satisfaction
        panic = model.panic
        boredom = model.boredom

        if event_kind == "near_death":
            fear = min(1.0, fear + 0.4)
            panic = min(1.0, panic + 0.5)
            confidence = max(0.0, confidence - 0.3)
        elif event_kind == "easy_win":
            confidence = min(1.0, confidence + 0.1)
            satisfaction = min(1.0, satisfaction + 0.1)
            fear = max(0.0, fear - 0.2)
        elif event_kind == "repeated_failure":
            frustration = min(1.0, frustration + 0.3)
            confidence = max(0.0, confidence - 0.1)
        elif event_kind == "new_unknown":
            curiosity = min(1.0, curiosity + 0.2)
        elif event_kind == "successful_goal":
            satisfaction = min(1.0, satisfaction + 0.2)
            frustration = max(0.0, frustration - 0.3)
        elif event_kind == "stagnation":
            boredom = min(1.0, boredom + 0.1)

        return EmotionalModel(
            fear=fear,
            confidence=confidence,
            frustration=frustration,
            curiosity=curiosity,
            satisfaction=satisfaction,
            panic=panic,
            boredom=boredom
        )
