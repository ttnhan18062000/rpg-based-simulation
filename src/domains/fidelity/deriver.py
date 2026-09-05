"""
src/domains/fidelity/deriver.py
───────────────────────────────────────────────────────────────────────────────
FidelityDeriver — pure stateless derivation of per-event FidelityState from a
ChronicleHierarchy (idea 62, "Generations Misremember").

Era-distance derivation rule:
  For each chronicle-worthy event, find its containing Era by walking
  hierarchy.eras -> Era.episodes -> Episode.index (NOT episode // ERA_EPISODE_MIN
  arithmetic, which is wrong whenever any episode has zero chronicle-worthy
  events -- Era.episodes batches the already-filtered episode list, not raw
  episode-index values; see ChronicleGrouper._group_eras()).

  era_distance = current_era_ordinal - event_era_ordinal
  fidelity     = max(0.0, 1.0 - era_distance * FIDELITY_DECAY_PER_ERA)

Keying: per-event via NarrativeLedgerEntry.entry_id (deterministic, globally
unique -- avoids collision with any subject_id-keyed sibling deriver output).
Legacy records with entry_id == "" reconstruct the same deterministic format
documented at NarrativeLedgerEntry.entry_id's own docstring.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from src.domains.fidelity.model import FidelityState

if TYPE_CHECKING:
    from src.domains.chronicle.grouper import ChronicleHierarchy

FIDELITY_DECAY_PER_ERA: float = 0.2


class FidelityDeriver:
    """Derive per-event FidelityState from a ChronicleHierarchy.

    Stateless — all logic in the single classmethod derive().
    """

    @classmethod
    def derive(cls, hierarchy: "ChronicleHierarchy") -> Dict[str, FidelityState]:
        """Derive a fidelity value per chronicle-worthy event, keyed by entry_id.

        Walks hierarchy.eras -> Era.episodes -> Episode.index to find each
        event's real era membership. Fidelity decreases linearly with
        era-distance from the current (latest) Era. Same-era events
        (era_distance == 0) get fidelity == 1.0.

        Args:
            hierarchy: Produced by ChronicleGrouper.group().

        Returns:
            Dict[str, FidelityState] keyed by NarrativeLedgerEntry.entry_id.
        """
        if not hierarchy.eras:
            return {}

        episode_to_era: Dict[int, int] = {}
        for era in hierarchy.eras:
            for ep in era.episodes:
                episode_to_era[ep.index] = era.ordinal
        current_era_ordinal = hierarchy.eras[-1].ordinal

        result: Dict[str, FidelityState] = {}
        for entry in hierarchy.events:
            era_ordinal = episode_to_era.get(entry.episode)
            if era_ordinal is None:
                continue  # defensive: entry's episode absent from the eras it came from
            era_distance = current_era_ordinal - era_ordinal
            fidelity_value = max(0.0, 1.0 - era_distance * FIDELITY_DECAY_PER_ERA)
            key = entry.entry_id or f"{entry.episode}:{entry.tick}:{entry.event_type}:{entry.subject_id}"
            result[key] = FidelityState(fidelity=fidelity_value)
        return result
