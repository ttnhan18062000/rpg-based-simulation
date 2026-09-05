"""
src/domains/fame/legend.py
───────────────────────────────────────────────────────────────────────────────
LegendFact and LegendFactService — a lazily-computed, non-durable read-model
over FameCarryForward (idea 57, "The Living Legend Feedback Loop").

LegendFact is deliberately NOT a CampaignState field. It is fully and
deterministically reconstructible from FameCarryForward (the actual durable,
typed record, with its own defined lifecycle: derive -> export -> carry-forward),
so per the Durable State Rule it does not need a second persisted record of its
own. LegendFactService.for_entity() constructs it lazily at query time.

FAME_THRESHOLD reuses CHRONICLE_THRESHOLD (src/domains/chronicle/significance.py,
CHRONICLE_THRESHOLD = 0.5) as its anchor -- both operate on the same normalized
[0.0, 1.0] scale and express the same underlying concept: "has this crossed the
bar to be considered narratively significant enough to be noticed."

LegendFact must never be confused with the pre-existing, unrelated
LEGENDARY_ARRIVAL faction-reputation consequence event
(src/systems/social_systems/consequence_events.py) -- that mechanism reads
CampaignState.social_memories[...].faction_reputation, never Chronicle-derived
fame. LegendFact's only real input is FameImporter.get_fame().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Tuple

from src.domains.fame.exporter import FameImporter

if TYPE_CHECKING:
    from src.domains.campaigns.state import CampaignState
    from src.domains.perception.salience import WorldSignal

# Anchor: src/domains/chronicle/significance.py's CHRONICLE_THRESHOLD (0.5), the
# existing authoritative significance cutoff on the same normalized scale.
FAME_THRESHOLD: float = 0.5


@dataclass(frozen=True, slots=True)
class LegendFact:
    """A plain, immutable snapshot of a subject's fame at the moment it was
    queried above FAME_THRESHOLD -- not a live reference to FameState, so the
    fact can't silently change after construction.
    """

    subject_id: str
    fame: float
    entity_name: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "subject_id": self.subject_id,
            "fame": self.fame,
            "entity_name": self.entity_name,
        }


class LegendFactService:
    """Lazy, query-time construction of LegendFact from FameCarryForward."""

    @staticmethod
    def for_entity(
        campaign_state: "CampaignState",
        subject_id: str,
        entity_name: Optional[str] = None,
    ) -> Optional[LegendFact]:
        """Return a LegendFact if subject_id's fame crosses FAME_THRESHOLD, else None."""
        fame_state = FameImporter.get_fame(campaign_state, subject_id)
        if fame_state is None or fame_state.fame < FAME_THRESHOLD:
            return None
        return LegendFact(subject_id=subject_id, fame=fame_state.fame, entity_name=entity_name)

    @staticmethod
    def to_world_signal(
        fact: LegendFact,
        position: Tuple[float, float] = (0.0, 0.0),
    ) -> "WorldSignal":
        """Wrap a LegendFact as a WorldSignal for perception discoverability.

        `position` must be explicit (default (0.0, 0.0)) -- LegendFact/FameState
        have no location concept of their own (a hero's fame isn't location-bound).
        """
        from src.domains.perception.salience import WorldSignal

        return WorldSignal(
            signal_id=f"legend:{fact.subject_id}",
            kind="legend_fact",
            position=position,
            base_relevance=fact.fame,
            danger_level=0.0,
            is_novel=False,
        )
