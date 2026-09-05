"""
src/domains/belief_institution/deriver.py
───────────────────────────────────────────────────────────────────────────────
BeliefInstitutionDeriver — pure derivation of per-(clan, legend) BeliefInstitution
records from real LegendFacts and real ClanState membership (idea 63, "Belief
Grows Around Real History").

Unlike CultureDeriver/FidelityDeriver/FameDeriver, this Deriver's inputs are not
limited to a ChronicleHierarchy -- it also needs campaign_state (to query
LegendFactService, itself a read over FameCarryForward) and the real Clan
membership map (final_state.clans, confirmed already in scope at
CampaignOrchestrator._advance_state()'s own call site alongside CampaignState,
per direct read of orchestrator.py). This is still a pure function: it reads
its three inputs and returns a fresh dict, mutating nothing.

Formation rule: a BeliefInstitution forms for a (clan, origin_event) pair only
when the origin event's own subject has a real LegendFact (fame crossed
FAME_THRESHOLD, src.domains.fame.legend). One BeliefInstitution per existing
Clan per qualifying legendary subject -- every Clan is assumed to have heard of
a Chronicle-recorded legend (Chronicle is world-visible history, not privately
known), but clans weigh it differently:
  belief_strength = fame                     if the legendary subject is a
                                              member of this clan (in-group)
  belief_strength = fame * OUT_GROUP_DAMPENING otherwise (out-group)

This is a disclosed simplification (see docs/mechanics/05_world_evolution.md
§10): only two distinct belief_strength values ever occur for a given legend
(in-group vs. out-group), not a richer per-clan model -- appropriate for a
P2, zero-live-consumer feature (the whole Fame -> BeliefInstitution chain
remains "built, not yet visible in play").
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

from src.domains.belief_institution.model import BeliefInstitution
from src.domains.fame.legend import FAME_THRESHOLD, LegendFactService

if TYPE_CHECKING:
    from src.core.state import ClanState
    from src.domains.campaigns.state import CampaignState
    from src.domains.chronicle.grouper import ChronicleHierarchy

# A real, if simplified, weighting: an out-group clan has heard of the legend
# (Chronicle is world-visible) but does not own it the way the legend's own
# clan does. Disclosed placeholder, not a full social-simulation model -- see
# module docstring and docs/mechanics/05_world_evolution.md §10.
OUT_GROUP_DAMPENING: float = 0.4

# Mirrors FameDeriver's own Option-B event-type rule exactly, so this Deriver
# never credits an origin event FameDeriver itself would not have counted.
_FAME_CONTRIBUTING_EVENTS = frozenset({"quest_completed"})


class BeliefInstitutionDeriver:
    """Derive BeliefInstitution per (clan, legendary subject) pair.

    Stateless — all logic in the single class method derive().
    """

    @classmethod
    def derive(
        cls,
        hierarchy: "ChronicleHierarchy",
        campaign_state: "CampaignState",
        clans: Dict[str, "ClanState"],
        entity_names: Optional[Dict[int, str]] = None,
    ) -> Dict[str, BeliefInstitution]:
        """Derive BeliefInstitution per (clan_id, origin_event_id) pair.

        Parameters
        ----------
        hierarchy:
            Produced by ChronicleGrouper.group(). Used only to find each
            legendary subject's own origin event (the single highest-
            significance contributing entry) -- FameState itself is an
            aggregate with no single entry_id of its own.
        campaign_state:
            Read-only here; queried via LegendFactService.for_entity() for
            each candidate subject_id found in hierarchy.events.
        clans:
            Read-only real Clan membership (AuthoritativeState.clans from the
            just-completed episode). Never written to.
        entity_names:
            Optional int→str mapping, forwarded to LegendFactService for
            display; not used in the belief_strength computation itself.

        Returns
        -------
        Dict[str, BeliefInstitution]
            "{clan_id}:{origin_event_id}" -> BeliefInstitution.
        """
        origin_events = cls._select_origin_events(hierarchy)

        result: Dict[str, BeliefInstitution] = {}
        for subject_id, origin_event_id in origin_events.items():
            entity_name = (entity_names or {}).get(cls._safe_int(subject_id))
            fact = LegendFactService.for_entity(campaign_state, subject_id, entity_name)
            if fact is None:
                continue  # below FAME_THRESHOLD -- not a legend yet, no belief forms.

            subject_int = cls._safe_int(subject_id)
            for clan_id, clan_state in clans.items():
                in_group = subject_int is not None and subject_int in clan_state.member_entity_ids
                strength = fact.fame if in_group else fact.fame * OUT_GROUP_DAMPENING
                key = f"{clan_id}:{origin_event_id}"
                result[key] = BeliefInstitution(
                    origin_event_id=origin_event_id,
                    clan_id=clan_id,
                    adherent_entity_ids=clan_state.member_entity_ids,
                    belief_strength=min(1.0, max(0.0, strength)),
                )
        return result

    @staticmethod
    def _safe_int(subject_id: str) -> Optional[int]:
        """Cast subject_id to int for Clan-membership comparison, or None.

        subject_id may name a non-entity node (a faction/node id per
        NarrativeLedgerEntry's own docstring) -- a failed cast safely means
        "cannot be a Clan member," never a crash.
        """
        try:
            return int(subject_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _select_origin_events(hierarchy: "ChronicleHierarchy") -> Dict[str, str]:
        """Pick one origin_event_id per subject: the single highest-significance
        fame-contributing entry, preferring a posthumous HERO entity_death
        (the more legend-shaped moment) over a quest_completed entry.

        Mirrors FameDeriver's own event-type rule exactly (quest_completed +
        HERO entity_death) so a subject only gets an origin event here if
        FameDeriver itself would have credited them fame for it.
        """
        best_hero_death: Dict[str, "object"] = {}
        best_quest: Dict[str, "object"] = {}

        for entry in hierarchy.events:
            subject_id = entry.subject_id
            if not subject_id:
                continue
            if entry.event_type == "entity_death" and entry.payload.get("entity_role") == "HERO":
                current = best_hero_death.get(subject_id)
                if current is None or entry.significance > current.significance:
                    best_hero_death[subject_id] = entry
            elif entry.event_type in _FAME_CONTRIBUTING_EVENTS:
                current = best_quest.get(subject_id)
                if current is None or entry.significance > current.significance:
                    best_quest[subject_id] = entry

        origin_events: Dict[str, str] = {}
        # sorted(): a set union's iteration order is not guaranteed stable across
        # process runs (string hash randomization) -- this dict's insertion order
        # must be deterministic since it feeds `result`'s own key order downstream.
        all_subjects = sorted(set(best_hero_death) | set(best_quest))
        for subject_id in all_subjects:
            chosen = best_hero_death.get(subject_id) or best_quest[subject_id]
            origin_events[subject_id] = chosen.entry_id
        return origin_events
