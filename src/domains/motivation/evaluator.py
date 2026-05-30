"""
src/domains/motivation/evaluator.py
───────────────────────────────────────────────────────────────────────────────
RoleFitEvaluator for Phase 14.
"""

from __future__ import annotations
from typing import Iterable
from src.core.cognition import RoleFitPreference

class RoleFitEvaluator:
    """Evaluates compatibility scores of gear, skills, quests, and roles."""

    @staticmethod
    def evaluate_tags(preference_map: dict[str, float] | dict[str, float], tags: Iterable[str]) -> float:
        score = 0.0
        for tag in tags:
            if tag in preference_map:
                score += preference_map[tag]
        return score

    @classmethod
    def evaluate_weapon(cls, preference: RoleFitPreference, tags: Iterable[str]) -> float:
        return cls.evaluate_tags(preference.weapon_tags, tags)

    @classmethod
    def evaluate_armor(cls, preference: RoleFitPreference, tags: Iterable[str]) -> float:
        return cls.evaluate_tags(preference.armor_tags, tags)

    @classmethod
    def evaluate_skill(cls, preference: RoleFitPreference, tags: Iterable[str]) -> float:
        return cls.evaluate_tags(preference.skill_tags, tags)

    @classmethod
    def evaluate_party_role(cls, preference: RoleFitPreference, role: str) -> float:
        return preference.party_role_tags.get(role, 0.0)

    @classmethod
    def evaluate_quest(cls, preference: RoleFitPreference, tags: Iterable[str]) -> float:
        return cls.evaluate_tags(preference.quest_tags, tags)
