from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List
from src_v2.core.updates import CombatUpdate

if TYPE_CHECKING:
    from src_v2.core.state import EntityState

class CombatResolutionSystem:
    """
    Authoritative logic for combat interactions and outcomes.
    Matches legacy 'CombatInteractionService'.
    """
    
    @staticmethod
    def calculate_damage(attacker: EntityState, defender: EntityState) -> int:
        """
        Pillar 3: Fractional Armor Mitigation
        Formula: damage = atk * (atk / (atk + def * 2.0 + 1.0))
        """
        atk = float(attacker.combat.atk)
        dfn = float(defender.combat.def_stat)
        raw_damage = int(atk * (atk / (atk + dfn * 2.0 + 1.0)))
        return max(1, raw_damage)

    @staticmethod
    def resolve_attack(
        attacker: EntityState,
        defender: EntityState,
        is_opportunity_attack: bool = False,
        is_lethal: bool = True
    ) -> CombatUpdate:
        """
        Core combat resolution logic.
        """
        # 1. Calculate Damage
        damage = CombatResolutionSystem.calculate_damage(attacker, defender)
        
        # 2. Determine Outcome
        new_hp = defender.combat.hp - damage
        outcome = "SURVIVE"
        alive = True
        
        if new_hp <= 0:
            outcome = "KILL" if is_lethal else "DEFEAT"
            alive = False

        return CombatUpdate(
            damage_taken=damage,
            hp_delta=-damage,
            attacker_id=attacker.id,
            is_opportunity_attack=is_opportunity_attack,
            alive_set=alive,
            outcome_kind=outcome,
            is_lethal=is_lethal
        )

    @staticmethod
    def resolve_opportunity_attack(
        attacker: EntityState,
        defender: EntityState
    ) -> CombatUpdate:
        return CombatResolutionSystem.resolve_attack(
            attacker, defender, is_opportunity_attack=True, is_lethal=False
        )
