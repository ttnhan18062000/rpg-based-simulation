"""
src/domains/fame/exporter.py
───────────────────────────────────────────────────────────────────────────────
FameExporter and FameImporter — episode-boundary hooks for cross-episode
Chronicle-derived fame persistence (idea 57, "The Living Legend Feedback Loop").

FameExporter.export() is called from CampaignOrchestrator._advance_state()
immediately alongside CultureDriftExporter.export()/FidelityExporter.export(),
consuming the same ChronicleHierarchy local. FameImporter.get_fame() is a thin
lookup helper with no live caller yet -- LegendFactService.for_entity() is the
intended reader (itself lazy/non-durable, no perception/motivation wiring yet).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.domains.fame.model import FameCarryForward

if TYPE_CHECKING:
    from src.domains.campaigns.state import CampaignState
    from src.domains.chronicle.grouper import ChronicleHierarchy
    from src.domains.fame.model import FameState


class FameExporter:
    """Derive fame from ChronicleHierarchy and persist into CampaignState.

    Called at episode end from CampaignOrchestrator._advance_state(), immediately
    alongside CultureDriftExporter.export()/FidelityExporter.export() -- all
    three consume the same _hierarchy local.
    """

    @staticmethod
    def export(
        campaign_state: "CampaignState",
        hierarchy: "ChronicleHierarchy",
        episode_index: int,
        entity_names: Optional[dict] = None,
    ) -> None:
        """Derive FameState per subject and update campaign_state.entity_fame.

        Existing entries for subjects not observed in this episode's hierarchy
        are kept unchanged (fame persists until overwritten by a future
        derivation over a superset of the same narrative_ledger).

        Parameters
        ----------
        campaign_state:
            Mutable CampaignState whose entity_fame dict is updated in-place.
        hierarchy:
            Produced by ChronicleGrouper.group(narrative_ledger).
        episode_index:
            The episode that just completed (stored as derived_episode).
        entity_names:
            Optional id→name map forwarded to FameDeriver (unused currently).
        """
        from src.domains.fame.deriver import FameDeriver

        derived = FameDeriver.derive(hierarchy, entity_names=entity_names)
        for subject_id, fame_state in derived.items():
            campaign_state.entity_fame[subject_id] = FameCarryForward(
                subject_id=subject_id,
                fame=fame_state,
                derived_episode=episode_index,
            )


class FameImporter:
    """Thin lookup helper for a subject's fame (no live consumer yet -- LegendFactService)."""

    @staticmethod
    def get_fame(
        campaign_state: "CampaignState",
        entity_id: str,
    ) -> Optional["FameState"]:
        """Return FameState for a subject, or None if no data exists.

        Does not raise — unknown subject ids return None. `entity_id`'s runtime
        value domain is NarrativeLedgerEntry.subject_id (str), not an int
        entity id.
        """
        cf = campaign_state.entity_fame.get(entity_id)
        if cf is None:
            return None
        return cf.fame
