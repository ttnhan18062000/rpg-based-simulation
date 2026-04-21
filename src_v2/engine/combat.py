from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List
from src_v2.core.updates import CombatUpdate

if TYPE_CHECKING:
    from src_v2.core.state import EntityState

class CombatReactionSystem:
    """
    Authoritative logic for reaction attacks and combat outcomes.
    Matches legacy 'CombatInteractionService'.
    """

    @staticmethod
    def resolve_opportunity_attack(
        attacker: EntityState,
        defender: EntityState
    ) -> CombatUpdate:
        """
        Resolution logic for a single Opportunity Attack (OA).
        Parity Note: In legacy, OAs deal standard melee damage but can be dodged.
        """
        # P0 Implementation: For now, we deal a fixed 5 damage for simplicity
        # and to prove the plumbing works.
        return CombatUpdate(
            damage_taken=5.0,
            attacker_id=attacker.id,
            is_opportunity_attack=True
        )
