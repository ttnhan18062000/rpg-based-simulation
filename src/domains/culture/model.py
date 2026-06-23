"""
src/domains/culture/model.py
───────────────────────────────────────────────────────────────────────────────
CultureState and CultureCarryForward — the data model for regional culture drift
(Epic 6.2 / E62A).

Design constraints:
  - MUST NOT import from src.engine or src.core.state at module level.
  - All records are frozen (immutable after construction).
  - to_dict() / from_dict() provide JSON-safe round-trip.
  - Float axes clamped to [0.0, 1.0]; default 0.0 means no cultural signal yet.
  - CampaignState stores Dict[str, CultureCarryForward] keyed by region_id (str).

Populated by: E62B CultureDeriver / CultureDriftExporter (end-of-episode hook).
Consumed by:  E62B CultureDriftImporter (start-of-episode hook).
Stored in:    CampaignState.region_cultures (Dict[str, CultureCarryForward]).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CultureState:
    """Immutable snapshot of a region's cultural axes.

    All axes are floats in [0.0, 1.0]. Default 0.0 = no cultural signal.

    Axes
    ----
    fatalism
        Derived from calamity events and sustained high-trauma history.
        Raises entity `caution`, lowers `pride`.
    hero_veneration
        Derived from deaths of HERO entities with high narrative significance.
        Raises entity `loyalty` and `pride`.
    resource_scarcity_memory
        Derived from INFLATION_SPIRAL and sustained resource depletion events.
        Raises entity `survival`.
    faction_conflict_exposure
        Derived from war_declared, territory_transferred, faction_destroyed events.
        Raises entity `caution`, lowers `loyalty`.
    """

    fatalism: float = 0.0
    hero_veneration: float = 0.0
    resource_scarcity_memory: float = 0.0
    faction_conflict_exposure: float = 0.0

    def to_dict(self) -> dict:
        return {
            "fatalism": self.fatalism,
            "hero_veneration": self.hero_veneration,
            "resource_scarcity_memory": self.resource_scarcity_memory,
            "faction_conflict_exposure": self.faction_conflict_exposure,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CultureState":
        return cls(
            fatalism=d.get("fatalism", 0.0),
            hero_veneration=d.get("hero_veneration", 0.0),
            resource_scarcity_memory=d.get("resource_scarcity_memory", 0.0),
            faction_conflict_exposure=d.get("faction_conflict_exposure", 0.0),
        )


@dataclass(frozen=True, slots=True)
class CultureCarryForward:
    """Durable per-region cultural snapshot carried across episodes.

    Fields
    ------
    region_id : str
        The region this culture snapshot belongs to.
    culture : CultureState
        The cultural axis values as of `derived_episode`.
    derived_episode : int
        0-based index of the episode in which this snapshot was derived.
        If a region has no events in a later episode, the carry-forward
        persists unchanged until the next derivation.
    """

    region_id: str
    culture: CultureState
    derived_episode: int

    def to_dict(self) -> dict:
        return {
            "region_id": self.region_id,
            "culture": self.culture.to_dict(),
            "derived_episode": self.derived_episode,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CultureCarryForward":
        return cls(
            region_id=d["region_id"],
            culture=CultureState.from_dict(d.get("culture", {})),
            derived_episode=d.get("derived_episode", 0),
        )
