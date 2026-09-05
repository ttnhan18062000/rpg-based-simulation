"""
src/domains/fidelity/model.py
───────────────────────────────────────────────────────────────────────────────
FidelityState and FidelityCarryForward — the data model for Chronicle fidelity
drift (Epic 6.2 / E62, idea 62 "Generations Misremember").

Design constraints:
  - MUST NOT import from src.engine or src.core.state at module level.
  - All records are frozen (immutable after construction).
  - to_dict() / from_dict() provide JSON-safe round-trip.
  - fidelity clamped to [0.0, 1.0]; default 1.0 means fully accurate / just
    recorded (matches "an event you just lived through is fully remembered").
  - CampaignState stores Dict[str, FidelityCarryForward] keyed by
    NarrativeLedgerEntry.entry_id (str).

Populated by: FidelityDeriver / FidelityExporter (end-of-episode hook).
Consumed by:  FidelityImporter (no live caller yet -- idea 63, Belief Grows
              Around Real History, is the intended eventual reader).
Stored in:    CampaignState.historical_drift (Dict[str, FidelityCarryForward]).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FidelityState:
    """Immutable snapshot of one recorded event's remembered-accuracy value.

    fidelity: float in [0.0, 1.0]. 1.0 = fully accurate (just happened / current
    era). Decreases with Era-distance from the current Era (see FidelityDeriver).
    """

    fidelity: float = 1.0

    def to_dict(self) -> dict:
        return {"fidelity": self.fidelity}

    @classmethod
    def from_dict(cls, d: dict) -> "FidelityState":
        return cls(fidelity=d.get("fidelity", 1.0))


@dataclass(frozen=True, slots=True)
class FidelityCarryForward:
    """Durable per-event fidelity snapshot carried across episodes.

    Fields
    ------
    entry_id : str
        The NarrativeLedgerEntry.entry_id this snapshot describes.
    fidelity : FidelityState
        The fidelity value as of derived_episode.
    derived_episode : int
        0-based index of the episode in which this snapshot was derived.
    """

    entry_id: str
    fidelity: FidelityState
    derived_episode: int

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "fidelity": self.fidelity.to_dict(),
            "derived_episode": self.derived_episode,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FidelityCarryForward":
        return cls(
            entry_id=d["entry_id"],
            fidelity=FidelityState.from_dict(d.get("fidelity", {})),
            derived_episode=d.get("derived_episode", 0),
        )
