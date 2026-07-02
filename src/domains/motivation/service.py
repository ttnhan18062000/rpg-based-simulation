"""
src/domains/motivation/service.py
───────────────────────────────────────────────────────────────────────────────
MotivationBiasService for Phase 14.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Iterable, Optional
from src.core.state import EntityState

if TYPE_CHECKING:
    from src.domains.culture.model import CultureState

class MotivationBiasService:
    """Applies values and doctrine preferences as stable cognitive scoring biases."""

    @staticmethod
    def compute_bias_multiplier(
        entity: EntityState,
        tags: Iterable[str],
        culture_values: Optional["CultureState"] = None,
    ) -> float:
        """Compute motivation bias multiplier for a route given its tags.

        Parameters
        ----------
        entity:
            Entity being scored.
        tags:
            Route tags to evaluate against doctrine and value preferences.
        culture_values:
            Optional CultureState for the entity's current region. When provided,
            an additive cultural bias delta (from CulturalBiasApplicator) is added
            to the base multiplier. When None, behaviour is identical to pre-E62C.
        """
        tags_list = list(tags)
        motivation = entity.cognition.motivation
        multiplier = 1.0

        # 1. Doctrine Preferred & Avoided Route Tags
        preferred = motivation.doctrine.preferred_route_tags
        avoided = motivation.doctrine.avoided_route_tags
        for tag in tags_list:
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
        for tag in tags_list:
            if tag in ("recovery", "flee", "caution"):
                multiplier += (values.survival - 0.5) * 0.5
            elif tag in ("cooperation", "help", "party"):
                multiplier -= (values.pride - 0.5) * 0.5
            elif tag in ("exploration", "research", "intel", "knowledge"):
                multiplier += (values.curiosity - 0.5) * 0.5
            elif tag in ("gold", "chest", "loot", "reward"):
                multiplier += (values.reward - 0.5) * 0.5

        # 3. Cultural bias overlay (E62C) — transient, not stored in entity state
        if culture_values is not None:
            from src.domains.culture.applicator import CulturalBiasApplicator
            multiplier += CulturalBiasApplicator.compute_culture_delta(
                culture_values, tags_list
            )

        return max(0.1, multiplier)
