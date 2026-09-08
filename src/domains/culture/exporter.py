"""
src/domains/culture/exporter.py
───────────────────────────────────────────────────────────────────────────────
CultureDriftExporter and CultureDriftImporter — episode-boundary hooks for
cross-episode culture persistence (Epic 6.2B).

CultureDriftExporter.export() is called from CampaignOrchestrator._advance_state()
after social memories are updated. CultureDriftImporter.get_culture() is a thin
lookup helper used by E62C, now wired into AdventureRouteScorer.score()'s
personality_bias mechanism (TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE) — the
original MotivationBiasService this docstring referred to was confirmed dead and
deleted (TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.domains.culture.model import CultureCarryForward

if TYPE_CHECKING:
    from src.domains.campaigns.state import CampaignState
    from src.domains.chronicle.grouper import ChronicleHierarchy
    from src.domains.culture.model import CultureState


class CultureDriftExporter:
    """Derive culture from ChronicleHierarchy and persist into CampaignState.

    Called at episode end from CampaignOrchestrator._advance_state().
    """

    @staticmethod
    def export(
        campaign_state: "CampaignState",
        hierarchy: "ChronicleHierarchy",
        episode_index: int,
        entity_names: Optional[dict] = None,
    ) -> None:
        """Derive CultureState per region and update campaign_state.region_cultures.

        Existing entries for regions not observed in this episode are kept
        unchanged (culture persists until overwritten by a future derivation).

        Parameters
        ----------
        campaign_state:
            Mutable CampaignState whose region_cultures dict is updated in-place.
        hierarchy:
            Produced by ChronicleGrouper.group(narrative_ledger).
        episode_index:
            The episode that just completed (stored as derived_episode).
        entity_names:
            Optional id→name map forwarded to CultureDeriver (unused currently).
        """
        from src.domains.culture.deriver import CultureDeriver

        derived = CultureDeriver.derive(hierarchy, entity_names=entity_names)
        for region_id, culture in derived.items():
            campaign_state.region_cultures[region_id] = CultureCarryForward(
                region_id=region_id,
                culture=culture,
                derived_episode=episode_index,
            )


class CultureDriftImporter:
    """Thin lookup helper for regional culture at episode start."""

    @staticmethod
    def get_culture(
        campaign_state: "CampaignState",
        region_id: str,
    ) -> Optional["CultureState"]:
        """Return CultureState for a region, or None if no data exists.

        Does not raise — unknown regions return None.
        """
        ccf = campaign_state.region_cultures.get(region_id)
        if ccf is None:
            return None
        return ccf.culture
