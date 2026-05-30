"""
src/domains/combat_engagement/self_estimate.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — SelfCombatEstimateService

Calculates derived actor combat capability based on current HP, wounds, stamina,
and active equipment.
"""

from __future__ import annotations
from typing import Dict

from src.core.state import EntityState
from src.domains.combat_engagement.schema import SelfCombatEstimate


class SelfCombatEstimateService:
    """
    Computes derived actor capability estimates.
    """

    @staticmethod
    def estimate(actor: EntityState) -> SelfCombatEstimate:
        """
        Evaluate current HP, stamina, and equipment status to calculate a derived
        subjective self combat power estimate.
        """
        condition_modifiers: Dict[str, float] = {}
        constraints: list[str] = []

        # 1. Base power from level and base combat stats
        lvl = getattr(actor.identity, "evolution_level", 1)
        base_power = float(lvl * 20.0)

        comb = getattr(actor, "combat", None)
        if comb:
            atk = getattr(comb, "atk", 10)
            base_power += atk

        # 2. HP condition modifiers
        hp = getattr(comb, "hp", 100)
        max_hp = getattr(comb, "max_hp", 100)
        hp_ratio = hp / max(1, max_hp)

        if hp_ratio < 0.2:
            condition_modifiers["critical_health"] = -0.5
            constraints.append("near_death")
        elif hp_ratio < 0.5:
            condition_modifiers["injured"] = -0.25
            constraints.append("wounded")
        elif hp_ratio < 0.8:
            condition_modifiers["scratched"] = -0.1

        # 3. Stamina modifiers
        stam = getattr(actor, "stamina", None)
        if stam:
            curr_stam = getattr(stam, "current", 100.0)
            max_stam = getattr(stam, "max_stamina", 100.0)
            stam_ratio = curr_stam / max(1.0, max_stam)
            
            if stam_ratio < 0.2:
                condition_modifiers["exhausted"] = -0.3
                constraints.append("no_stamina")
            elif stam_ratio < 0.5:
                condition_modifiers["tired"] = -0.15

        # 4. Equipment modifiers
        from src.core.models.inventory import EquipSlot
        equip = getattr(actor, "equipment", None)
        slots = getattr(equip, "slots", {}) or {}
        if slots.get(EquipSlot.MAIN_HAND):
            condition_modifiers["armed"] = +0.15
        else:
            condition_modifiers["bare_handed"] = -0.2
            constraints.append("unarmed")
                
        # Durability modifiers
        if slots.get(EquipSlot.MAIN_HAND):
            durability = getattr(equip, "durability", {}) or {}
            mh_dur = durability.get(EquipSlot.MAIN_HAND, 100.0)
            if mh_dur < 20.0:
                condition_modifiers["damaged_weapon"] = -0.2
                constraints.append("dull_weapon")

        # 5. Apply modifiers
        final_multiplier = 1.0
        for val in condition_modifiers.values():
            final_multiplier += val
        
        final_multiplier = max(0.1, final_multiplier)
        estimated_power = base_power * final_multiplier

        # Confidence
        confidence = max(0.2, min(1.0, hp_ratio * 0.8 + 0.2))

        return SelfCombatEstimate(
            actor_id=actor.id,
            estimated_power=round(estimated_power, 2),
            confidence=round(confidence, 2),
            condition_modifiers=condition_modifiers,
            constraints=tuple(constraints),
        )
