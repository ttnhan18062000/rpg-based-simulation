"""
MotivationPressureResolver — converts need/drive profile catalog data into normalised
pressure values that downstream goal/target scoring can consume.

Design constraints:
- Read-only: never mutates entity state or catalog state
- Deterministic: same entity + context → same pressures
- No species-specific scripts: resolution is entirely data-driven from catalog profiles
- Pressures are inputs to scoring — they do not directly force actions
- Missing profile → MotivationPressureSet.empty() with source="no_profile", no exception
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.content.repository import CatalogRepository

# ---------------------------------------------------------------------------
# Level → float mapping
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


def _level(val: Optional[str]) -> float:
    if val is None:
        return 0.0
    return _LEVEL_TO_FLOAT.get(val.lower().replace("-", "_"), 0.0)


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

class MotivationPressureSet(BaseModel):
    """Normalised pressure values derived from need/drive profiles. All values 0.0–1.0."""

    model_config = ConfigDict(frozen=True)

    hunger_pressure: float = Field(0.0, ge=0.0, le=1.0)
    safety_pressure: float = Field(0.0, ge=0.0, le=1.0)
    territory_pressure: float = Field(0.0, ge=0.0, le=1.0)
    duty_pressure: float = Field(0.0, ge=0.0, le=1.0)
    wealth_pressure: float = Field(0.0, ge=0.0, le=1.0)
    curiosity_pressure: float = Field(0.0, ge=0.0, le=1.0)
    aggression_pressure: float = Field(0.0, ge=0.0, le=1.0)
    purpose_pressure: float = Field(0.0, ge=0.0, le=1.0)

    source: Literal[
        "need_and_drive_profile",
        "need_profile_only",
        "drive_profile_only",
        "no_profile",
    ] = "no_profile"

    @classmethod
    def empty(cls) -> MotivationPressureSet:
        return cls(source="no_profile")


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

class MotivationPressureResolver:
    """
    Resolves MotivationPressureSet from an entity's need/drive profile IDs.

    Reads profile IDs from entity.identity.properties["need_profile_id"] and
    ["drive_profile_id"], then loads definitions from the CatalogRepository.
    """

    def __init__(self, catalog: CatalogRepository) -> None:
        self._catalog = catalog

    def resolve_pressures(
        self,
        entity: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> MotivationPressureSet:
        """
        Derive normalised pressure values from the entity's need/drive profiles.

        Returns MotivationPressureSet.empty() if neither profile is found.
        Never raises.
        """
        props = {}
        if hasattr(entity, "identity") and hasattr(entity.identity, "properties"):
            props = entity.identity.properties or {}

        need_profile_id: Optional[str] = props.get("need_profile_id")
        drive_profile_id: Optional[str] = props.get("drive_profile_id")

        need_defn = self._catalog.get_need_profile(need_profile_id) if need_profile_id else None
        drive_defn = self._catalog.get_drive_profile(drive_profile_id) if drive_profile_id else None

        if need_defn is None and drive_defn is None:
            return MotivationPressureSet.empty()

        # Build composite pressure: max(need, drive) per dimension
        needs: Dict[str, float] = {
            k: _level(v) for k, v in (need_defn.needs if need_defn else {}).items()
        }
        drives: Dict[str, float] = {
            k: _level(v) for k, v in (drive_defn.drives if drive_defn else {}).items()
        }

        def _merge(key: str) -> float:
            return min(1.0, max(needs.get(key, 0.0), drives.get(key, 0.0)))

        source: Literal["need_and_drive_profile", "need_profile_only", "drive_profile_only", "no_profile"]
        if need_defn and drive_defn:
            source = "need_and_drive_profile"
        elif need_defn:
            source = "need_profile_only"
        else:
            source = "drive_profile_only"

        return MotivationPressureSet(
            hunger_pressure=_merge("hunger"),
            safety_pressure=_merge("safety"),
            territory_pressure=_merge("territory"),
            duty_pressure=_merge("duty"),
            wealth_pressure=_merge("wealth"),
            curiosity_pressure=_merge("curiosity"),
            aggression_pressure=_merge("aggression"),
            purpose_pressure=_merge("purpose_fixation"),
            source=source,
        )
