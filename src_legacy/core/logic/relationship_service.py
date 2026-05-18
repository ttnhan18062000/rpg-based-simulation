"""Relationship Service — manages systemic social bond state transitions. [PHASE 2]

This service provides an authoritative bridge to the SocialRegistry, applying
SocialUpdate intents to directed relationships between entities.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src_legacy.core.models.social import SocialRegistry
    from src_legacy.actions.base import SocialUpdate

logger = logging.getLogger(__name__)

class RelationshipService:
    """Manages the systemic social bond layer (SocialRegistry)."""

    @staticmethod
    def apply_update(registry: SocialRegistry, update: SocialUpdate, tick: int) -> None:
        """Apply a SocialUpdate intent to the global social registry."""
        old_vals, new_vals = registry.update_bond(
            source_id=update.source_id,
            target_id=update.target_id,
            trust_delta=update.trust_delta,
            fear_delta=update.fear_delta,
            rivalry_delta=update.rivalry_delta,
            familiarity_delta=update.familiarity_delta,
            loyalty_delta=update.loyalty_delta,
            resentment_delta=update.resentment_delta,
            admiration_delta=update.admiration_delta,
            debt_delta=update.debt_delta,
            tick=tick
        )
        
        logger.debug(
            "Bond update (%d -> %d): trust %.2f->%.2f, loyalty %.2f->%.2f",
            update.source_id, update.target_id, 
            old_vals["trust"], new_vals["trust"],
            old_vals["loyalty"], new_vals["loyalty"]
        )
