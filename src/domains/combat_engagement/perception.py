"""
src/domains/combat_engagement/perception.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — OpponentPerceptionService

Formulates subjective opponent power estimates based on visible signals, level,
and memory, deflated by low wisdom/perception or high panic.
"""

from __future__ import annotations
from typing import Optional, Dict, Tuple

from src.core.state import EntityState
from src.domains.combat_engagement.schema import PerceivedOpponentEstimate, OpponentModel


class OpponentPerceptionService:
    """
    Constructs subjective opponent estimates. Strictly protects information opacity
    by avoiding hidden world truth variables.
    """

    @staticmethod
    def estimate(
        actor: EntityState,
        target: EntityState,
        memory: Optional[OpponentModel] = None,
    ) -> PerceivedOpponentEstimate:
        """
        Produce a PerceivedOpponentEstimate based on visible cues, prior memories,
        and actor capability limitations.
        """
        visible_signals: list[str] = []
        unknown_factors: list[str] = []
        memory_used: list[str] = []

        # 1. Base power from level/evolution
        target_lvl = getattr(target.identity, "evolution_level", 1)
        base_power = float(target_lvl * 20.0)

        # 2. Modify based on visible HP status
        target_hp = getattr(target.combat, "hp", 100)
        target_max_hp = getattr(target.combat, "max_hp", 100)
        hp_ratio = target_hp / max(1, target_max_hp)
        
        if hp_ratio < 0.3:
            base_power *= 0.6
            visible_signals.append("critical_health")
        elif hp_ratio < 0.7:
            base_power *= 0.85
            visible_signals.append("wounded")
        else:
            visible_signals.append("healthy")

        # 3. Visible gear signals
        from src.core.models.inventory import EquipSlot
        target_equip = getattr(target, "equipment", None)
        has_weapon = False
        if target_equip and getattr(target_equip, "slots", None):
            slots = getattr(target_equip, "slots")
            if slots.get(EquipSlot.MAIN_HAND):
                base_power += 15.0
                visible_signals.append("armed")
                has_weapon = True
        
        if not has_weapon:
            visible_signals.append("unarmed")

        # 4. Process Memory models
        confidence = 0.5
        uncertainty = 0.4
        
        if memory:
            # Memory reduces uncertainty and adjusts the power estimate toward reality
            confidence = min(0.95, memory.confidence + 0.15)
            uncertainty = max(0.05, memory.uncertainty - 0.15)
            base_power = (base_power * 0.4) + (memory.estimated_power * 0.6)
            memory_used.append(memory.subject_key)
        else:
            unknown_factors.append("unknown_history")

        # 5. Actor limitations: low perception/intelligence increases uncertainty
        attrs = getattr(actor, "attributes", None)
        perception = getattr(attrs, "perception", 5)
        intel = getattr(attrs, "intelligence", 5)
        
        if perception < 4:
            uncertainty = min(0.95, uncertainty + 0.15)
            confidence = max(0.1, confidence - 0.1)
            unknown_factors.append("poor_perception")

        # 6. Biological stress/panic inflation
        bio = getattr(actor, "biological", None)
        rest_pressure = getattr(bio, "rest_pressure", 0.0)
        if rest_pressure > 70.0:
            uncertainty = min(0.95, uncertainty + 0.1)
            unknown_factors.append("fatigued")

        return PerceivedOpponentEstimate(
            target_id=target.id,
            estimated_power=round(base_power, 2),
            uncertainty=round(uncertainty, 2),
            confidence=round(confidence, 2),
            visible_signals=tuple(visible_signals),
            unknown_factors=tuple(unknown_factors),
            memory_used=tuple(memory_used),
        )
