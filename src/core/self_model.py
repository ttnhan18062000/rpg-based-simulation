"""
src/core/self_model.py
───────────────────────────────────────────────────────────────────────────────
Phase 2 — Bottom-Up Entity Self Model component schemas.

These are *pure data* records — no behaviour, no mutations, no imports of
service or engine code.  All dataclasses are frozen so they participate in
immutable-update style exactly like every other EntityState component.

Design note:
  - `KnowledgeFact` here is the *entity-owned* persisted record.
    The identically named class in `src/world/providers/information.py` is the
    *provider-side transfer object* (short-lived, not stored on the entity).
    They are intentionally separate.
  - All four components are grouped under `SelfModelBundle` so `EntityState`
    gains exactly one new top-level field instead of four.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Primitive records
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class InterpretedNeed:
    """A single interpreted need with urgency, confidence, and reason."""
    key: str
    urgency: float          # 0.0 (low) … 1.0 (critical)
    confidence: float       # how certain the interpretation is
    reason: str             # short human-readable reason string


@dataclass(frozen=True, slots=True)
class CapabilityEstimate:
    """Subjective capability estimate for a specific action/context key."""
    capability_key: str     # e.g. "combat.enemy_type.rat"
    estimate: float         # 0.0 (impossible) … 1.0 (trivial)
    confidence: float       # how confident the estimate is
    source: str             # what information drove this estimate
    last_updated_tick: int


@dataclass(frozen=True, slots=True)
class KnowledgeFact:
    """
    An entity-owned persisted fact (learned from a provider or observation).

    Distinct from `src.world.providers.information.KnowledgeFact` which is the
    provider-side transfer object used per query.
    """
    subject: str
    fact_type: str          # "resource_source" | "recipe_definition" | "danger_rating" | etc.
    details: Dict[str, Any] = field(default_factory=dict)
    certainty: float = 1.0
    source_id: Optional[str] = None
    recorded_tick: int = 0


@dataclass(frozen=True, slots=True)
class UnknownFact:
    """A gap in the entity's knowledge — something the entity knows it doesn't know."""
    subject: str            # e.g. "material.moon_resin.source"
    reason: str             # why this is unknown ("provider_partial", "never_queried", etc.)
    recorded_tick: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# Component dataclasses (frozen, canonical-serialisable)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SelfAwarenessComponent:
    """
    Subjective self-assessment derived from raw entity state.

    Fields:
        perceived_condition   – named float metrics (health, stamina, load, gear_quality)
        perceived_weaknesses  – ordered tuple of weakness keys
        perceived_strengths   – ordered tuple of strength keys
        confidence_level      – overall self-confidence 0.0–1.0
        stress_level          – composite stress 0.0–1.0 (driven by severity of weaknesses)
        uncertainty_level     – how uncertain the entity is about itself 0.0–1.0
        last_self_check_tick  – tick when this component was last updated
    """
    perceived_condition: Dict[str, float] = field(default_factory=dict)
    perceived_weaknesses: Tuple[str, ...] = ()
    perceived_strengths: Tuple[str, ...] = ()
    confidence_level: float = 0.5
    stress_level: float = 0.0
    uncertainty_level: float = 0.0
    last_self_check_tick: int = 0

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "perceived_condition": dict(sorted(self.perceived_condition.items())),
            "perceived_weaknesses": list(self.perceived_weaknesses),
            "perceived_strengths": list(self.perceived_strengths),
            "confidence_level": round(self.confidence_level, 4),
            "stress_level": round(self.stress_level, 4),
            "uncertainty_level": round(self.uncertainty_level, 4),
            "last_self_check_tick": self.last_self_check_tick,
        }


@dataclass(frozen=True, slots=True)
class NeedInterpretationComponent:
    """
    Interpreted needs derived from self-awareness and raw state.

    Fields:
        active_needs          – mapping from need key to InterpretedNeed
        dominant_need         – the single highest-urgency need key (or None)
        last_interpreted_tick – tick when this component was last updated
    """
    active_needs: Dict[str, InterpretedNeed] = field(default_factory=dict)
    dominant_need: Optional[str] = None
    last_interpreted_tick: int = 0

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "active_needs": {
                k: {
                    "urgency": round(v.urgency, 4),
                    "confidence": round(v.confidence, 4),
                    "reason": v.reason,
                }
                for k, v in sorted(self.active_needs.items())
            },
            "dominant_need": self.dominant_need,
            "last_interpreted_tick": self.last_interpreted_tick,
        }


@dataclass(frozen=True, slots=True)
class CapabilityEstimateComponent:
    """
    Scoped subjective estimates of what the entity can do.

    Keys follow the pattern:
        combat.enemy_type.<enemy>
        travel.region.<region_id>
        gather.resource.<resource_id>
        craft.recipe.<recipe_id>
    """
    estimates: Dict[str, CapabilityEstimate] = field(default_factory=dict)
    last_updated_tick: int = 0

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "estimates": {
                k: {
                    "estimate": round(v.estimate, 4),
                    "confidence": round(v.confidence, 4),
                    "source": v.source,
                    "last_updated_tick": v.last_updated_tick,
                }
                for k, v in sorted(self.estimates.items())
            },
            "last_updated_tick": self.last_updated_tick,
        }


@dataclass(frozen=True, slots=True)
class KnowledgeModelComponent:
    """
    Entity-owned personal knowledge and acknowledged unknowns.

    Distinct from the world truth or provider internal state.
    Only contains what the entity has actually learned or explicitly doesn't know.
    """
    facts: Dict[str, KnowledgeFact] = field(default_factory=dict)
    unknowns: Dict[str, UnknownFact] = field(default_factory=dict)
    last_updated_tick: int = 0

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "facts": {
                k: {
                    "fact_type": v.fact_type,
                    "certainty": round(v.certainty, 4),
                    "source_id": v.source_id,
                    "recorded_tick": v.recorded_tick,
                    "details": dict(sorted(v.details.items())) if v.details else {},
                }
                for k, v in sorted(self.facts.items())
            },
            "unknowns": {
                k: {
                    "reason": v.reason,
                    "recorded_tick": v.recorded_tick,
                }
                for k, v in sorted(self.unknowns.items())
            },
            "last_updated_tick": self.last_updated_tick,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Bundle — single top-level field on EntityState
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SelfModelBundle:
    """
    Groups all four Phase 2 self-model components under one field on EntityState.

    Default: all components at their empty/zero default values.
    Intentionally excluded from authoritative canonical hash (it is derived from
    raw state, not a mutation source).  Include via to_canonical_dict() only in
    inspection/debug exports.
    """
    self_awareness: SelfAwarenessComponent = field(
        default_factory=SelfAwarenessComponent
    )
    needs: NeedInterpretationComponent = field(
        default_factory=NeedInterpretationComponent
    )
    capabilities: CapabilityEstimateComponent = field(
        default_factory=CapabilityEstimateComponent
    )
    knowledge: KnowledgeModelComponent = field(
        default_factory=KnowledgeModelComponent
    )

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "self_awareness": self.self_awareness.to_canonical_dict(),
            "needs": self.needs.to_canonical_dict(),
            "capabilities": self.capabilities.to_canonical_dict(),
            "knowledge": self.knowledge.to_canonical_dict(),
        }

    @classmethod
    def empty(cls) -> "SelfModelBundle":
        """Return a fully default empty self-model bundle."""
        return cls()
