"""Reputation Service — manages updates to public reputation profiles. [PHASE 2]

Reputation is the public-facing social memory of an entity. This service
applies ReputationUpdate intents to an entity's ReputationProfile.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src_legacy.core.entities.entity import Entity
    from src_legacy.actions.base import ReputationUpdate

logger = logging.getLogger(__name__)

class ReputationService:
    """Manages an entity's public reputation mapping."""

    @classmethod
    def apply_update(cls, entity: Entity, update: ReputationUpdate) -> None:
        """Apply a ReputationUpdate intent to an entity's reputation profile."""
        rep = entity.identity.reputation
        
        # Apply score deltas with clamping
        rep.defender_score = max(-10.0, min(10.0, rep.defender_score + update.defender_delta))
        rep.cowardice_score = max(-10.0, min(10.0, rep.cowardice_score + update.cowardice_delta))
        rep.greed_score = max(-10.0, min(10.0, rep.greed_score + update.greed_delta))
        rep.heroism_score = max(-10.0, min(10.0, rep.heroism_score + update.heroism_delta))
        rep.threat_notoriety = max(-10.0, min(10.0, rep.threat_notoriety + update.threat_notoriety_delta))
        rep.trustworthiness = max(-10.0, min(10.0, rep.trustworthiness + update.trustworthiness_delta))

        # Manage tags
        for tag in update.tags_add:
            if tag not in rep.reputation_tags:
                rep.reputation_tags.append(tag)
        
        for tag in update.tags_remove:
            if tag in rep.reputation_tags:
                rep.reputation_tags.remove(tag)

        # 3. Dynamic Title/Tag Refresh [PHASE 2]
        cls._refresh_dynamic_tags(entity)

        logger.debug(
            "Updated reputation for entity %d: Df=%.1f, Cw=%.1f, Gr=%.1f, Hr=%.1f",
            entity.id, rep.defender_score, rep.cowardice_score, 
            rep.greed_score, rep.heroism_score
        )

    @classmethod
    def _refresh_dynamic_tags(cls, entity: Entity) -> None:
        """Internal title management based on score thresholds."""
        rep = entity.identity.reputation
        tags = set(rep.reputation_tags)

        # Heroism thresholds
        if rep.heroism_score >= 2.0: tags.add("Hero")
        elif rep.heroism_score >= 5.0: tags.add("Saviour")
        elif rep.heroism_score < 1.0: tags.discard("Hero"); tags.discard("Saviour")
        
        # Cowardice thresholds
        if rep.cowardice_score >= 1.0: tags.add("Craven")
        elif rep.cowardice_score < 0.5: tags.discard("Craven")

        # Threat thresholds
        if rep.threat_notoriety >= 3.0: tags.add("Menace")
        elif rep.threat_notoriety >= 7.0: tags.add("Calamity")

        rep.reputation_tags = list(tags)

