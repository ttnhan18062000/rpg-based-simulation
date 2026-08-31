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
    from src.core.strategic import ConcernState, BlockerState
    from src.core.updates import StrategicUpdate

from src.core.social_constants import ALLY_TRUST_THRESHOLD
from src.domains.campaigns.state import GriefUrgencyModifier, NemesisRelation

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
    def _build_grief_concern(modifier: GriefUrgencyModifier) -> "ConcernState":
        """Build the SOCIAL_THREAT ConcernState for a grief modifier.

        The concern id is deterministic: "grief_ally_{dead_ally_id}". Shared by
        both apply() (episode-boundary, direct EntityState return) and
        build_strategic_update() (mid-episode, StrategicUpdate return) so the two
        paths cannot drift.
        """
        from src.core.strategic import ConcernState, ConcernKind

        concern_id = f"grief_ally_{modifier.dead_ally_id}"
        return ConcernState(
            id=concern_id,
            kind=ConcernKind.SOCIAL_THREAT,
            source=f"ally_{modifier.dead_ally_id}_died_ep{modifier.episode}",
            urgency=modifier.urgency,
            created_tick=0,
        )

    @staticmethod
    def apply(entity: "EntityState", modifier: GriefUrgencyModifier) -> "EntityState":
        """Return a new EntityState with grief urgency injected as a SOCIAL_THREAT concern.

        Calling this multiple times for the same dead_ally_id overwrites the concern,
        which is correct (urgency was updated by decay in _advance_state).

        Only safe pre-Kernel, while _build_initial_state() is constructing a brand-new
        AuthoritativeState from scratch — there is no live ApplyPath to go through at
        that point. A mid-episode caller must use build_strategic_update() instead.
        """
        concern = GriefUrgencyImporter._build_grief_concern(modifier)
        new_concerns = {**entity.strategic.concerns, concern.id: concern}
        new_strategic = dc_replace(entity.strategic, concerns=new_concerns)
        return dc_replace(entity, strategic=new_strategic)

    @staticmethod
    def build_strategic_update(modifier: GriefUrgencyModifier) -> "StrategicUpdate":
        """Return a StrategicUpdate carrying the grief concern, for the mid-episode
        (live Kernel tick) caller — applied through ApplyPath/StrategicPatch rather
        than by direct EntityState replacement.
        """
        from src.core.updates import StrategicUpdate

        return StrategicUpdate(
            concerns_add_or_update=[GriefUrgencyImporter._build_grief_concern(modifier)]
        )


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
    def _build_nemesis_blocker(relation: NemesisRelation) -> "BlockerState":
        """Build the SOCIAL BlockerState for a nemesis relation.

        The blocker id is deterministic: "nemesis_{antagonist_id}". Shared by
        both apply() and build_strategic_update() so the two paths cannot drift.
        """
        from src.core.strategic import BlockerState, BlockerKind

        blocker_id = f"nemesis_{relation.antagonist_id}"
        return BlockerState(
            id=blocker_id,
            kind=BlockerKind.SOCIAL,
            subject=str(relation.antagonist_id),
            severity=relation.strength,
        )

    @staticmethod
    def apply(entity: "EntityState", relation: NemesisRelation) -> "EntityState":
        """Return a new EntityState with nemesis SOCIAL blocker injected.

        Only safe pre-Kernel, same constraint as GriefUrgencyImporter.apply().
        """
        blocker = NemesisRelationImporter._build_nemesis_blocker(relation)
        new_blockers = {**entity.strategic.blockers, blocker.id: blocker}
        new_strategic = dc_replace(entity.strategic, blockers=new_blockers)
        return dc_replace(entity, strategic=new_strategic)

    @staticmethod
    def build_strategic_update(relation: NemesisRelation) -> "StrategicUpdate":
        """Return a StrategicUpdate carrying the nemesis blocker.

        Added for architectural symmetry with GriefUrgencyImporter.build_strategic_update()
        (ticket TCK-20260824-GRIEF-NEMESIS-REACHABILITY Scope). NOT wired to any live
        mid-episode call site: nemesis-relation formation requires
        NEMESIS_EPISODE_COUNT>=2 distinct *episodes* of antagonism history, which cannot
        be evaluated from a single live episode — there is no natural mid-episode trigger
        for it.
        """
        from src.core.updates import StrategicUpdate

        return StrategicUpdate(
            blockers_add_or_update=[NemesisRelationImporter._build_nemesis_blocker(relation)]
        )
