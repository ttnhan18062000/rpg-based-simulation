# Compliance IDs: STRAT-264
"""
src/strategy/role_model_imitation.py
───────────────────────────────────────────────────────────────────────────────
RoleModelImitationService (TCK-20260831-ROLE-MODEL-IMITATION)

Deliberately kept separate from CapacityService.derive_profile (src/strategy/
cognition_capacity.py) rather than folded into it -- derive_profile is a pure
function of entity.attributes/identity.personality/biological only, with zero
content-catalog coupling today; adding a CatalogRepository dependency there
would be the first such coupling, for a concept unrelated to any of
CognitionProfile's 11 existing fields. See plan.md's "Fork justification"
(design decision 3) for the full trace.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import EntityState


class RoleModelImitationService:
    """
    Purely deterministic; does not mutate entity state.
    Resolves an entity's intelligence_tier-modulated imitation-fidelity multiplier.
    """

    HIGH_TIER_FIDELITY = 1.0
    LOW_TIER_FIDELITY = 0.5
    DEFAULT_FIDELITY = 0.5  # fallback when race/tier cannot be resolved

    @staticmethod
    def compute_imitation_fidelity(entity: "EntityState") -> float:
        race_id = entity.identity.properties.get("race_id")
        if not race_id:
            return RoleModelImitationService.DEFAULT_FIDELITY

        from src.content_semantics.faction import get_faction_semantics_service
        race_def = get_faction_semantics_service().repo.get_race(race_id)
        if race_def is None:
            return RoleModelImitationService.DEFAULT_FIDELITY

        tier = getattr(race_def, "intelligence_tier", None)
        if tier == "high":
            return RoleModelImitationService.HIGH_TIER_FIDELITY
        return RoleModelImitationService.LOW_TIER_FIDELITY
