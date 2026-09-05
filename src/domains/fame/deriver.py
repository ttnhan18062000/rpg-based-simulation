"""
src/domains/fame/deriver.py
───────────────────────────────────────────────────────────────────────────────
FameDeriver — pure stateless derivation of per-subject FameState from a
ChronicleHierarchy (idea 57, "The Living Legend Feedback Loop").

Event rule (Option B, per docs/brainstorm/2026-09-04-idea57-entity-scale-fame-
aggregation-design.md):
  fame += entry.significance for quest_completed entries (subject-attributed)
  fame += entry.significance for entity_death entries where
          payload["entity_role"] == "HERO" (posthumous fame)
  No other event types contribute -- deliberately narrower than
  CultureDeriver's own frozensets (no faction/diplomatic/calamity events).

Keying: entry.subject_id. Entries with a falsy subject_id are skipped -- fame
is per-entity and an unattributed event has no entity to credit (unlike
CultureDeriver's own "__global__" region fallback).

Normalisation: fame = min(1.0, raw_sum / NORMALISE_DENOMINATOR)
NORMALISE_DENOMINATOR = 3.0 -- a fresh module-local constant, independent of
CultureDeriver's own identically-valued constant (never imported/aliased).

Disclosed characteristic: orchestrator.py's _SIGNIFICANCE_MAP maps QUEST_FAILED
to event_type="quest_completed" (significance=0.3, vs. 0.7 for a real success).
Since ChronicleGrouper's chronicle-worthiness gate scores by event_type alone,
both real quest successes and failures reach hierarchy.events and both match
this deriver's event_type == "quest_completed" check -- a real, accepted
characteristic of the existing NarrativeLedgerEntry taxonomy, not special-cased
here (see docs/mechanics/05_world_evolution.md §9).
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Optional

from src.domains.fame.model import FameState

if TYPE_CHECKING:
    from src.domains.chronicle.grouper import ChronicleHierarchy

NORMALISE_DENOMINATOR: float = 3.0

_FAME_EVENTS = frozenset({"quest_completed"})


class FameDeriver:
    """Derive FameState per subject from a ChronicleHierarchy.

    Stateless — all logic in the single class method derive().
    """

    @classmethod
    def derive(
        cls,
        hierarchy: "ChronicleHierarchy",
        entity_names: Optional[Dict[int, str]] = None,
    ) -> Dict[str, FameState]:
        """Derive FameState per subject from all chronicle-worthy events.

        Parameters
        ----------
        hierarchy:
            Produced by ChronicleGrouper.group(). Uses hierarchy.events
            (all chronicle-worthy NarrativeLedgerEntry objects).
        entity_names:
            Optional int→str mapping for future entity resolution.
            Not used in current derivation; kept for API forward-compat.

        Returns
        -------
        Dict[str, FameState]
            subject_id → FameState. Entries with a falsy subject_id do not
            accumulate fame and are excluded from the result.
        """
        fame: "defaultdict[str, float]" = defaultdict(float)

        for entry in hierarchy.events:
            subject_id = entry.subject_id
            if not subject_id:
                continue
            sig = entry.significance
            etype = entry.event_type

            if etype in _FAME_EVENTS:
                fame[subject_id] += sig
            elif etype == "entity_death" and entry.payload.get("entity_role") == "HERO":
                fame[subject_id] += sig

        result: Dict[str, FameState] = {}
        for subject_id, raw in fame.items():
            result[subject_id] = FameState(fame=cls._normalise(raw))
        return result

    @staticmethod
    def _normalise(raw: float) -> float:
        return min(1.0, raw / NORMALISE_DENOMINATOR)
