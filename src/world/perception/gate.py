"""
PerceptionGate — data-driven entity perception gating via sense profiles.

Design constraints:
- Read-only: never mutates entity state or catalog state
- Deterministic: same inputs → same result
- Data-driven: all sense strengths come from catalog sense profiles, no race scripts
- Upstream of relation projection: gates raw detection capability only
- Fallback: entities without sense_profile_id use baseline humanoid defaults
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.content.repository import CatalogRepository

# ---------------------------------------------------------------------------
# Level → float mapping (shared with pressure_resolver)
# ---------------------------------------------------------------------------

_LEVEL_TO_FLOAT: Dict[str, float] = {
    "very_high": 1.0,
    "high": 0.9,
    "medium_high": 0.75,
    "medium": 0.6,
    "low_medium": 0.45,
    "low": 0.3,
    "very_low": 0.1,
    "none": 0.0,
}

_PERCEPTION_THRESHOLD = 0.2


def _level(val: Optional[str]) -> float:
    if val is None:
        return 0.0
    return _LEVEL_TO_FLOAT.get(val.lower().replace("-", "_"), 0.0)


# ---------------------------------------------------------------------------
# Channel mapping: sense field → target signal key
# ---------------------------------------------------------------------------

_SENSE_TO_SIGNAL: Dict[str, str] = {
    "vision": "visibility",
    "hearing": "noise",
    "smell": "scent",
    "magic_sense": "magic_signal",
    "life_sense": "life_signal",
    "vibration": "vibration",
    "social_reading": "social_signal",
}

_BASELINE_SENSE: Dict[str, str] = {
    "vision": "medium",
    "hearing": "medium",
    "smell": "low",
    "magic_sense": "none",
    "social_reading": "medium",
}


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

class PerceptionResult(BaseModel):
    """Result of a single perception check."""

    model_config = ConfigDict(frozen=True)

    perceived: bool
    confidence: float = Field(ge=0.0, le=1.0)
    signals_used: List[str]
    profile_source: str  # sense profile id used, or "baseline_humanoid"


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

class PerceptionGate:
    """
    Checks whether a source entity can perceive a target/event given its sense
    profile, distance, terrain context, and the target's emitted signals.

    Usage::

        gate = PerceptionGate(catalog)
        result = gate.can_perceive(source_entity, target_signals, context)
    """

    def __init__(self, catalog: CatalogRepository) -> None:
        self._catalog = catalog

    def can_perceive(
        self,
        source_entity: Any,
        target_signals: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> PerceptionResult:
        """
        Determine whether source_entity detects the target.

        Args:
            source_entity: Entity with optional identity.properties["sense_profile_id"].
            target_signals: Dict or object with signal fields (visibility, noise, scent,
                            magic_signal, life_signal, vibration, social_signal).
                            All fields are optional; absent signals default to "none".
            context: Optional dict with:
                - distance (float, default 1.0): proximity, 0 = adjacent
                - terrain_modifier (float 0–1, default 1.0): environmental penalty
                - alertness (float 0–1, default 0.5): source's current alertness

        Returns:
            PerceptionResult with perceived, confidence, signals_used, profile_source.
        """
        ctx = context or {}
        distance: float = float(ctx.get("distance", 1.0))
        terrain_mod: float = float(ctx.get("terrain_modifier", 1.0))
        alertness: float = float(ctx.get("alertness", 0.5))

        # Clamp modifiers
        distance = max(0.0, distance)
        terrain_mod = max(0.0, min(1.0, terrain_mod))
        alertness = max(0.0, min(1.0, alertness))

        # Distance factor: linear falloff, min 0.05
        distance_factor = max(0.05, 1.0 - distance * 0.02)

        # Load sense profile
        sense_strengths, profile_source = self._load_sense_strengths(source_entity)

        # Extract target signals
        signals = _extract_signals(target_signals)

        # Evaluate each channel
        signals_used: List[str] = []
        max_score = 0.0

        for sense_field, signal_key in _SENSE_TO_SIGNAL.items():
            sense_val = sense_strengths.get(sense_field, "none")
            signal_val = signals.get(signal_key, "none")

            sense_strength = _level(sense_val)
            signal_strength = _level(signal_val)

            if sense_strength == 0.0 or signal_strength == 0.0:
                continue

            score = sense_strength * signal_strength * distance_factor * terrain_mod * (0.5 + alertness * 0.5)
            if score >= _PERCEPTION_THRESHOLD:
                signals_used.append(signal_key)
                if score > max_score:
                    max_score = score

        perceived = len(signals_used) > 0
        confidence = min(1.0, max_score)

        return PerceptionResult(
            perceived=perceived,
            confidence=confidence,
            signals_used=signals_used,
            profile_source=profile_source,
        )

    def _load_sense_strengths(
        self,
        entity: Any,
    ) -> tuple[Dict[str, str], str]:
        """Load sense field values from entity's sense profile or return baseline."""
        sense_profile_id: Optional[str] = None
        if hasattr(entity, "identity") and hasattr(entity.identity, "properties"):
            sense_profile_id = (entity.identity.properties or {}).get("sense_profile_id")

        if sense_profile_id:
            defn = self._catalog.get_sense_profile(sense_profile_id)
            if defn is not None:
                strengths = {
                    field: getattr(defn, field)
                    for field in _SENSE_TO_SIGNAL
                    if getattr(defn, field, None) is not None
                }
                return strengths, sense_profile_id

        return dict(_BASELINE_SENSE), "baseline_humanoid"


# ---------------------------------------------------------------------------
# Signal extraction helper
# ---------------------------------------------------------------------------

def _extract_signals(target: Any) -> Dict[str, str]:
    """Extract signal fields from a dict or attribute-bearing object."""
    signal_keys = set(_SENSE_TO_SIGNAL.values())
    if isinstance(target, dict):
        return {k: v for k, v in target.items() if k in signal_keys}
    result: Dict[str, str] = {}
    for key in signal_keys:
        val = getattr(target, key, None)
        if val is not None:
            result[key] = val
    return result
