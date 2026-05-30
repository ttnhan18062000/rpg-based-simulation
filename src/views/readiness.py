"""
src/views/readiness.py
───────────────────────────────────────────────────────────────────────────────
Derived views engine for Phase 17.
"""

from __future__ import annotations
from dataclasses import dataclass
from src.core.state import EntityState

@dataclass(frozen=True, slots=True)
class DerivedReadinessView:
    score: float
    confidence: float
    blocking_factors: tuple[str, ...]
    supporting_factors: tuple[str, ...]
    source_aspects_used: tuple[str, ...]

class DerivedViews:
    """Computes derived readiness views from dynamic aspects on the fly."""

    @staticmethod
    def build_combat_readiness(entity: EntityState) -> DerivedReadinessView:
        hp_ratio = entity.combat.hp / max(1, entity.combat.max_hp)
        score = hp_ratio
        
        blocking = []
        supporting = []
        if hp_ratio < 0.3:
            blocking.append("low_health")
        else:
            supporting.append("healthy")
            
        return DerivedReadinessView(
            score=score,
            confidence=entity.cognition.subjective.emotion.confidence,
            blocking_factors=tuple(blocking),
            supporting_factors=tuple(supporting),
            source_aspects_used=("combat", "emotion")
        )

    @staticmethod
    def build_adventure_readiness(entity: EntityState) -> DerivedReadinessView:
        score = 1.0
        blocking = []
        supporting = []
        
        # Check active blockers in strategic component
        if entity.strategic.blockers:
            score *= 0.5
            blocking.append("has_strategic_blockers")
        else:
            supporting.append("no_strategic_blockers")
            
        return DerivedReadinessView(
            score=score,
            confidence=entity.cognition.subjective.emotion.confidence,
            blocking_factors=tuple(blocking),
            supporting_factors=tuple(supporting),
            source_aspects_used=("strategic", "emotion")
        )

derived_views = DerivedViews()
