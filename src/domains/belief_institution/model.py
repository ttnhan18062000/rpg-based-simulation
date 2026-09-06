"""
src/domains/belief_institution/model.py
───────────────────────────────────────────────────────────────────────────────
BeliefInstitution and BeliefInstitutionCarryForward — a Clan's own organized
reverence around a real, Chronicle-recorded legendary event (idea 63, "Belief
Grows Around Real History").

Design constraints:
  - MUST NOT import from src.engine or src.core.state at module level.
  - All records are frozen (immutable after construction).
  - to_dict() / from_dict() provide JSON-safe round-trip.
  - belief_strength clamped to [0.0, 1.0].
  - Distinct from the per-entity BeliefEntry class -- see
    src/systems/strategic_systems/belief.py, a tactical/near-term decision-
    support record -- and the per-entity KnowledgeFact class -- see
    src/core/self_model.py, structured/queried settled information -- per
    TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION's resolved
    two-track split, this is a genuinely third, population-scale concept.
  - CampaignState stores Dict[str, BeliefInstitutionCarryForward] keyed by
    "{clan_id}:{origin_event_id}" (one entry per clan-per-legend pair, so
    different clans can hold independently-strengthed beliefs about the same
    origin event).

Populated by: BeliefInstitutionDeriver / BeliefInstitutionExporter (end-of-episode hook).
Consumed by:  BeliefInstitutionImporter (no live caller yet -- this is the
              terminal idea in the M5 Fame -> Fidelity -> Belief-Institution
              chain, and the whole chain is "built, not yet visible in play"
              per idea 57's own disclosed precedent).
Stored in:    CampaignState.belief_institutions (Dict[str, BeliefInstitutionCarryForward]).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True, slots=True)
class BeliefInstitution:
    """Immutable snapshot of one Clan's organized belief around a real legend.

    origin_event_id: the NarrativeLedgerEntry.entry_id this belief formed
        around -- the single highest-significance Chronicle entry that
        contributed to the legendary subject's fame (see
        BeliefInstitutionDeriver._select_origin_event_id).
    clan_id: which Clan holds this belief.
    adherent_entity_ids: a snapshot of clan.member_entity_ids at formation
        time -- not a live reference; membership can drift afterward without
        retroactively changing this record.
    belief_strength: float in [0.0, 1.0]. Equal to the legendary subject's own
        fame when the subject is a member of this clan (in-group -- "one of
        our own"); dampened by OUT_GROUP_DAMPENING otherwise (out-group --
        "we've heard of them, but they aren't ours"). This is a disclosed
        simplification: only two distinct values ever occur for a given
        origin event (in-group vs. out-group), not a richer per-clan model.
    """

    origin_event_id: str
    clan_id: str
    adherent_entity_ids: Tuple[int, ...]
    belief_strength: float = 0.0

    def to_dict(self) -> dict:
        return {
            "origin_event_id": self.origin_event_id,
            "clan_id": self.clan_id,
            "adherent_entity_ids": list(self.adherent_entity_ids),
            "belief_strength": self.belief_strength,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BeliefInstitution":
        return cls(
            origin_event_id=d["origin_event_id"],
            clan_id=d["clan_id"],
            adherent_entity_ids=tuple(d.get("adherent_entity_ids", [])),
            belief_strength=d.get("belief_strength", 0.0),
        )


@dataclass(frozen=True, slots=True)
class BeliefInstitutionCarryForward:
    """Durable per-(clan, origin event) belief snapshot carried across episodes.

    Fields
    ------
    key : str
        "{clan_id}:{origin_event_id}" -- the composite identity of this belief.
    institution : BeliefInstitution
        The belief value as of derived_episode.
    derived_episode : int
        0-based index of the episode in which this snapshot was derived.
    """

    key: str
    institution: BeliefInstitution
    derived_episode: int

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "institution": self.institution.to_dict(),
            "derived_episode": self.derived_episode,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BeliefInstitutionCarryForward":
        return cls(
            key=d["key"],
            institution=BeliefInstitution.from_dict(d.get("institution", {})),
            derived_episode=d.get("derived_episode", 0),
        )
