"""
src/domains/culture/deriver.py
───────────────────────────────────────────────────────────────────────────────
CultureDeriver — pure stateless derivation of CultureState from ChronicleHierarchy.

Implemented by E62B (TCK-20260619-E62B-CULTURE-DERIVER).

Axis derivation rules (all additive, then normalised to [0.0, 1.0]):
  fatalism                += significance for calamity events and entity_death
                             caused by calamity (payload["cause"] == "calamity")
  hero_veneration         += significance for entity_death where
                             payload["entity_role"] == "HERO"
  resource_scarcity_memory += significance for INFLATION_SPIRAL events
  faction_conflict_exposure += significance for war_declared, territory_transferred,
                              faction_destroyed events

Normalisation: axis = min(1.0, raw_sum / NORMALISE_DENOMINATOR)
NORMALISE_DENOMINATOR = 3.0 — three high-significance events saturate an axis.

Region attribution: entry.payload.get("region_id") → key in result dict.
Fallback: entries without region_id accumulate into "__global__".
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Optional

from src.domains.culture.model import CultureState

if TYPE_CHECKING:
    from src.domains.chronicle.grouper import ChronicleHierarchy
    from src.domains.campaigns.state import NarrativeLedgerEntry

NORMALISE_DENOMINATOR: float = 3.0

_FATALISM_EVENTS = frozenset({"calamity"})
_CONFLICT_EVENTS = frozenset({"war_declared", "territory_transferred", "faction_destroyed"})
_SCARCITY_EVENTS = frozenset({"INFLATION_SPIRAL"})


class CultureDeriver:
    """Derive CultureState per region from a ChronicleHierarchy.

    Stateless — all logic in the single class method derive().
    """

    @classmethod
    def derive(
        cls,
        hierarchy: "ChronicleHierarchy",
        entity_names: Optional[Dict[int, str]] = None,
    ) -> Dict[str, CultureState]:
        """Derive CultureState per region from all chronicle-worthy events.

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
        Dict[str, CultureState]
            region_id → CultureState. Keys are taken from entry.payload["region_id"]
            when present, otherwise "__global__".
        """
        # Raw additive accumulators per region
        fatalism: defaultdict[str, float] = defaultdict(float)
        hero_veneration: defaultdict[str, float] = defaultdict(float)
        scarcity: defaultdict[str, float] = defaultdict(float)
        conflict: defaultdict[str, float] = defaultdict(float)

        for entry in hierarchy.events:
            region_id: str = entry.payload.get("region_id", "__global__") or "__global__"
            sig = entry.significance
            etype = entry.event_type

            if etype in _FATALISM_EVENTS:
                fatalism[region_id] += sig
            elif etype == "entity_death":
                cause = entry.payload.get("cause", "")
                role = entry.payload.get("entity_role", "")
                if cause == "calamity" or "trauma" in cause:
                    fatalism[region_id] += sig
                if role == "HERO":
                    hero_veneration[region_id] += sig
            elif etype in _SCARCITY_EVENTS:
                scarcity[region_id] += sig
            elif etype in _CONFLICT_EVENTS:
                conflict[region_id] += sig

        all_regions = (
            set(fatalism)
            | set(hero_veneration)
            | set(scarcity)
            | set(conflict)
        )

        result: Dict[str, CultureState] = {}
        for rid in all_regions:
            result[rid] = CultureState(
                fatalism=cls._normalise(fatalism[rid]),
                hero_veneration=cls._normalise(hero_veneration[rid]),
                resource_scarcity_memory=cls._normalise(scarcity[rid]),
                faction_conflict_exposure=cls._normalise(conflict[rid]),
            )
        return result

    @staticmethod
    def _normalise(raw: float) -> float:
        return min(1.0, raw / NORMALISE_DENOMINATOR)
