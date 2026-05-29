"""
src/domains/perception/service.py
───────────────────────────────────────────────────────────────────────────────
Phase 12 — AttentionFocusService

Computes what the entity is currently biased to notice based on needs,
active projects, and emotional states.
"""

from __future__ import annotations
from typing import List, Tuple
from src.core.state import EntityState

class AttentionFocusService:
    """Computes dynamic attention focus tags biased by active needs and state."""

    @staticmethod
    def get_attention_focus(entity: EntityState) -> Tuple[str, ...]:
        focus_tags: List[str] = []

        # 1. Biased by dominant need
        dominant_need = entity.cognition.subjective.self.needs.dominant_need
        if dominant_need == "healing":
            focus_tags.extend(["healing_resource", "healer", "safe_place"])
        elif dominant_need == "food":
            focus_tags.extend(["food_source", "town_inn"])
        elif dominant_need == "rest":
            focus_tags.extend(["town_inn", "safe_place"])
        elif dominant_need == "gold":
            focus_tags.extend(["gold_opportunity", "shop_merchant", "chest"])
        elif dominant_need == "equipment":
            focus_tags.extend(["blacksmith", "crafting_material", "weapon_upgrade"])
        elif dominant_need == "information":
            focus_tags.extend(["guild_intel", "location_clue", "rumor_source"])

        # 2. Biased by active project
        active_project_id = entity.strategic.current_project_id
        if active_project_id:
            focus_tags.append(f"project_target_{active_project_id}")

        # 3. Biased by emotional state (fear, curiosity)
        fear = entity.cognition.subjective.emotion.fear
        if fear > 0.6:
            focus_tags.extend(["threat", "escape_route", "ally"])
        
        curiosity = entity.cognition.subjective.emotion.curiosity
        if curiosity > 0.6:
            focus_tags.extend(["clue", "unknown_location", "rumor"])

        # Return unique ordered focus tags
        seen = set()
        unique_tags = []
        for tag in focus_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        return tuple(unique_tags)
