"""
src/domains/fidelity/exporter.py
───────────────────────────────────────────────────────────────────────────────
FidelityExporter and FidelityImporter — episode-boundary hooks for cross-episode
Chronicle fidelity persistence (idea 62, "Generations Misremember").

FidelityExporter.export() is called from CampaignOrchestrator._advance_state()
immediately alongside CultureDriftExporter.export(), consuming the same
ChronicleHierarchy local. FidelityImporter.get_fidelity() is a thin lookup
helper with no live caller yet -- idea 63 (Belief Grows Around Real History)
is the intended eventual consumer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.domains.fidelity.model import FidelityCarryForward

if TYPE_CHECKING:
    from src.domains.campaigns.state import CampaignState
    from src.domains.chronicle.grouper import ChronicleHierarchy
    from src.domains.fidelity.model import FidelityState


class FidelityExporter:
    """Derive fidelity from ChronicleHierarchy and persist into CampaignState.

    Called at episode end from CampaignOrchestrator._advance_state(), immediately
    alongside CultureDriftExporter.export() -- both consume the same _hierarchy
    local.
    """

    @staticmethod
    def export(
        campaign_state: "CampaignState",
        hierarchy: "ChronicleHierarchy",
        episode_index: int,
    ) -> None:
        """Derive FidelityState per event and update campaign_state.historical_drift.

        Existing entries for events not observed in this episode's hierarchy
        are kept unchanged (fidelity persists until overwritten by a future
        derivation over a superset of the same narrative_ledger).

        Parameters
        ----------
        campaign_state:
            Mutable CampaignState whose historical_drift dict is updated in-place.
        hierarchy:
            Produced by ChronicleGrouper.group(narrative_ledger).
        episode_index:
            The episode that just completed (stored as derived_episode).
        """
        from src.domains.fidelity.deriver import FidelityDeriver

        derived = FidelityDeriver.derive(hierarchy)
        for entry_id, fidelity_state in derived.items():
            campaign_state.historical_drift[entry_id] = FidelityCarryForward(
                entry_id=entry_id,
                fidelity=fidelity_state,
                derived_episode=episode_index,
            )


class FidelityImporter:
    """Thin lookup helper for an event's fidelity (no live consumer yet -- idea 63)."""

    @staticmethod
    def get_fidelity(
        campaign_state: "CampaignState",
        entry_id: str,
    ) -> Optional["FidelityState"]:
        """Return FidelityState for an event, or None if no data exists.

        Does not raise — unknown entry_ids return None.
        """
        cf = campaign_state.historical_drift.get(entry_id)
        if cf is None:
            return None
        return cf.fidelity
