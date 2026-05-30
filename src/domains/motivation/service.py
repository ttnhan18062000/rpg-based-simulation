"""
src/domains/motivation/service.py
───────────────────────────────────────────────────────────────────────────────
MotivationBiasService for Phase 14.
"""

from __future__ import annotations
from typing import Iterable
from src.core.state import EntityState

class MotivationBiasService:
    """Applies values and doctrine preferences as stable cognitive scoring biases."""

    @staticmethod
    def compute_bias_multiplier(entity: EntityState, tags: Iterable[str]) -> float:
        motivation = entity.cognition.motivation
        multiplier = 1.0

        # 1. Doctrine Preferred & Avoided Route Tags
        preferred = motivation.doctrine.preferred_route_tags
        avoided = motivation.doctrine.avoided_route_tags
        for tag in tags:
            if tag in preferred:
                multiplier += preferred[tag]
            if tag in avoided:
                multiplier -= avoided[tag]

        # 2. Value Preference Profile
        values = motivation.values
        # - High survival increases recovery/flee/caution tags
        # - High pride penalizes cooperation/help/party tags
        # - High curiosity/knowledge increases exploration/research/intel tags
        # - High reward/greed increases gold/chest/loot tags
        for tag in tags:
            if tag in ("recovery", "flee", "caution"):
                multiplier += (values.survival - 0.5) * 0.5
            elif tag in ("cooperation", "help", "party"):
                multiplier -= (values.pride - 0.5) * 0.5
            elif tag in ("exploration", "research", "intel", "knowledge"):
                multiplier += (values.curiosity - 0.5) * 0.5
            elif tag in ("gold", "chest", "loot", "reward"):
                multiplier += (values.reward - 0.5) * 0.5

        return max(0.1, multiplier)
