"""
src/domains/belief_institution/exporter.py
───────────────────────────────────────────────────────────────────────────────
BeliefInstitutionExporter and BeliefInstitutionImporter — episode-boundary
hooks for cross-episode BeliefInstitution persistence (idea 63, "Belief Grows
Around Real History").

BeliefInstitutionExporter.export() is called from CampaignOrchestrator's
_advance_state(), immediately alongside CultureDriftExporter.export()/
FidelityExporter.export()/FameExporter.export() -- the same established
direct-CampaignState-mutation pattern (CampaignState is confirmed not frozen;
see its own docstring). BeliefInstitutionImporter.get_institution() is a thin
lookup with no live caller yet -- this is the terminal idea in the M5
Fame -> Fidelity -> Belief-Institution chain, and the whole chain remains
"built, not yet visible in play."
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from src.domains.belief_institution.model import BeliefInstitutionCarryForward

if TYPE_CHECKING:
    from src.core.state import ClanState
    from src.domains.belief_institution.model import BeliefInstitution
    from src.domains.campaigns.state import CampaignState
    from src.domains.chronicle.grouper import ChronicleHierarchy


class BeliefInstitutionExporter:
    """Derive BeliefInstitution records and persist into CampaignState.

    Called at episode end from CampaignOrchestrator._advance_state(),
    immediately alongside CultureDriftExporter.export()/FidelityExporter.export()/
    FameExporter.export() -- all four consume the same _hierarchy local; this
    one additionally reads clans (read-only, never written).
    """

    @staticmethod
    def export(
        campaign_state: "CampaignState",
        hierarchy: "ChronicleHierarchy",
        clans: Dict[str, "ClanState"],
        episode_index: int,
        entity_names: Optional[dict] = None,
    ) -> None:
        """Derive BeliefInstitution per (clan, legend) pair and update
        campaign_state.belief_institutions.

        Existing entries for (clan, legend) pairs not re-derived this episode
        are kept unchanged (a belief persists until overwritten by a future
        derivation over a superset of the same narrative_ledger).

        Parameters
        ----------
        campaign_state:
            Mutable CampaignState whose belief_institutions dict is updated
            in-place.
        hierarchy:
            Produced by ChronicleGrouper.group(narrative_ledger).
        clans:
            Real Clan membership (AuthoritativeState.clans), read-only.
        episode_index:
            The episode that just completed (stored as derived_episode).
        entity_names:
            Optional id->name map forwarded to the Deriver (display only).
        """
        from src.domains.belief_institution.deriver import BeliefInstitutionDeriver

        derived = BeliefInstitutionDeriver.derive(
            hierarchy, campaign_state, clans, entity_names=entity_names
        )
        for key, institution in derived.items():
            campaign_state.belief_institutions[key] = BeliefInstitutionCarryForward(
                key=key,
                institution=institution,
                derived_episode=episode_index,
            )


class BeliefInstitutionImporter:
    """Thin lookup helper for a (clan, legend) belief (no live consumer yet)."""

    @staticmethod
    def get_institution(
        campaign_state: "CampaignState",
        clan_id: str,
        origin_event_id: str,
    ) -> Optional["BeliefInstitution"]:
        """Return BeliefInstitution for a (clan_id, origin_event_id) pair, or
        None if no data exists. Does not raise.
        """
        cf = campaign_state.belief_institutions.get(f"{clan_id}:{origin_event_id}")
        if cf is None:
            return None
        return cf.institution
