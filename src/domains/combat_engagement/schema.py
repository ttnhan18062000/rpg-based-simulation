"""
src/domains/combat_engagement/schema.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — Combat Engagement schemas.
Frozen, immutable dataclasses.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Mapping


class CombatPosture(str, Enum):
    """Subjective pre-combat and tactical combat postures."""
    IGNORE = "ignore"
    WATCH = "watch"
    AVOID = "avoid"
    PROBE = "probe"
    THREATEN = "threaten"
    ENGAGE = "engage"
    SKIRMISH = "skirmish"
    CALL_HELP = "call_help"
    RETREAT = "retreat"
    PANIC_FLEE = "panic_flee"
    GUARD_ALLY = "guard_ally"
    VENGEANCE_ENGAGE = "vengeance_engage"


@dataclass(frozen=True, slots=True)
class PerceivedOpponentEstimate:
    """
    Subjective opponent estimate.
    
    Fields:
        target_id:          The perceived target's ID
        estimated_power:    Subjective target combat power estimate (e.g. 10.0 to 100.0+)
        uncertainty:        Perceived unknown factors percentage (0.0 to 1.0)
        confidence:         Subjective assessment confidence (0.0 to 1.0)
        visible_signals:    Tuple of visible cues (e.g. "better_weapon", "wounded")
        unknown_factors:    Tuple of unknown aspects
        memory_used:        Prior remembered encounters
    """
    target_id: int
    estimated_power: float
    uncertainty: float
    confidence: float
    visible_signals: Tuple[str, ...] = field(default_factory=tuple)
    unknown_factors: Tuple[str, ...] = field(default_factory=tuple)
    memory_used: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SelfCombatEstimate:
    """
    Derived subjective actor combat capability estimate.
    """
    actor_id: int
    estimated_power: float
    confidence: float
    condition_modifiers: Mapping[str, float] = field(default_factory=dict)
    constraints: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class EngagementRiskEvaluation:
    """
    Subjective risk-benefit evaluation profile.
    """
    win_confidence: float
    death_risk: float
    uncertainty_penalty: float
    objective_value: float
    personality_bias: float
    emotional_bias: float
    risk_score: float
    value_score: float
    acceptable: bool
    reasons: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class OpponentModel:
    """
    Persistent model representing remembered combat info for identical subjects.
    """
    subject_key: str  # e.g. "entity.42", "enemy_type.wolf"
    estimated_power: float
    uncertainty: float
    confidence: float
    known_skill_ids: Tuple[str, ...] = field(default_factory=tuple)
    outcomes: Tuple[str, ...] = field(default_factory=tuple)
    last_updated_tick: int = 0


@dataclass(frozen=True, slots=True)
class CombatEngagementDecisionResult:
    """
    Final decision output.
    """
    actor_id: int
    target_id: int
    posture: CombatPosture
    risk_evaluation: EngagementRiskEvaluation
    opponent_estimate: PerceivedOpponentEstimate
    self_estimate: SelfCombatEstimate
    reason: Optional[str] = None
    trace: Dict[str, Any] = field(default_factory=dict)
