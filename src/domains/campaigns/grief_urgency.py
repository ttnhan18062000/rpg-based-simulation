"""
src/domains/campaigns/grief_urgency.py
───────────────────────────────────────────────────────────────────────────────
GriefUrgencyImporter — episode-start hook that injects grief/rage urgency from
the previous episode's ally deaths into the entity's strategic concern layer.

Implemented by E43F (TCK-20260628-E43F-GRIEF-URGENCY).

Design constraints:
  - Returns a new EntityState (does NOT mutate the original).
  - EntityState accessed via TYPE_CHECKING for static analysis only.
  - ConcernState/ConcernKind imported at runtime from src.core.strategic.
"""
from __future__ import annotations

from dataclasses import replace as dc_replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import EntityState

from src.domains.campaigns.state import GriefUrgencyModifier, NemesisRelation

# Minimum trust score in SocialMemoryRecord.relationship_scores to trigger grief.
ALLY_TRUST_THRESHOLD: float = 0.30

# Minimum number of distinct negative-interaction episodes to form a NemesisRelation.
NEMESIS_EPISODE_COUNT: int = 2
# Interaction kinds (from INTERACTION_KINDS) treated as nemesis-forming events.
NEMESIS_INTERACTION_KINDS: frozenset = frozenset({"betrayed", "conflict"})


class GriefUrgencyImporter:
    """Episode-start hook: injects GriefUrgencyModifier into entity.strategic.concerns.

    Usage (in CampaignOrchestrator._build_initial_state):
        if eid in campaign_state.grief_urgencies:
            entities[eid] = GriefUrgencyImporter.apply(
                entities[eid], campaign_state.grief_urgencies[eid]
            )
    """

    @staticmethod
    def apply(entity: "EntityState", modifier: GriefUrgencyModifier) -> "EntityState":
        """Return a new EntityState with grief urgency injected as a SOCIAL_THREAT concern.

        The concern id is deterministic: "grief_ally_{dead_ally_id}".
        Calling this multiple times for the same dead_ally_id overwrites the concern,
        which is correct (urgency was updated by decay in _advance_state).
        """
        from src.core.strategic import ConcernState, ConcernKind

        concern_id = f"grief_ally_{modifier.dead_ally_id}"
        concern = ConcernState(
            id=concern_id,
            kind=ConcernKind.SOCIAL_THREAT,
            source=f"ally_{modifier.dead_ally_id}_died_ep{modifier.episode}",
            urgency=modifier.urgency,
            created_tick=0,
        )
        new_concerns = {**entity.strategic.concerns, concern_id: concern}
        new_strategic = dc_replace(entity.strategic, concerns=new_concerns)
        return dc_replace(entity, strategic=new_strategic)


class NemesisRelationImporter:
    """Episode-start hook: injects nemesis BlockerState into entity.strategic.blockers.

    For each NemesisRelation where the entity is protagonist, adds a SOCIAL blocker
    keyed by antagonist_id. The FORM_PARTY route generator checks for these blockers
    to block party formation when the antagonist is a candidate.

    Usage (in CampaignOrchestrator._build_initial_state):
        for relation in campaign_state.nemesis_relations.values():
            if relation.protagonist_id == eid:
                entities[eid] = NemesisRelationImporter.apply(entities[eid], relation)
    """

    @staticmethod
    def apply(entity: "EntityState", relation: NemesisRelation) -> "EntityState":
        """Return a new EntityState with nemesis SOCIAL blocker injected."""
        from src.core.strategic import BlockerState, BlockerKind

        blocker_id = f"nemesis_{relation.antagonist_id}"
        blocker = BlockerState(
            id=blocker_id,
            kind=BlockerKind.SOCIAL,
            subject=str(relation.antagonist_id),
            severity=relation.strength,
        )
        new_blockers = {**entity.strategic.blockers, blocker_id: blocker}
        new_strategic = dc_replace(entity.strategic, blockers=new_blockers)
        return dc_replace(entity, strategic=new_strategic)
