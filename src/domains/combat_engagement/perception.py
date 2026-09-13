"""
src/domains/combat_engagement/perception.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — OpponentPerceptionService

Formulates subjective opponent power estimates based on visible signals, level,
and memory, deflated by low wisdom/perception or high panic.
"""

from __future__ import annotations
from typing import Optional, Dict, Tuple

from src.core.state import AuthoritativeState, EntityState
from src.domains.combat_engagement.schema import PerceivedOpponentEstimate, OpponentModel
from src.domains.combat_engagement.power import (
    true_power,
    apparent_power,
    deterministic_observation_noise,
    gap_uncertainty,
    NOISE_MAGNITUDE_AT_MAX_UNCERTAINTY,
)


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
        state: Optional[AuthoritativeState] = None,
    ) -> PerceivedOpponentEstimate:
        """
        Produce a PerceivedOpponentEstimate based on visible cues, prior memories,
        and actor capability limitations.

        `state` is optional (defaults produce deterministic-but-unseeded-looking output only when
        omitted, e.g. in isolated unit tests that don't need the noise term itself under test) --
        every real per-tick caller has a real `state` and must pass it, per Sec 13.9's determinism
        law: the noise term is a pure function of (seed, tick, observer_id, observed_id).
        """
        visible_signals: list[str] = []
        unknown_factors: list[str] = []
        memory_used: list[str] = []

        # 1. Apparent power: true_power(target) adjusted for its current condition (Sec 13.2).
        # true_power() deliberately excludes evolution_level -- levelling's own strength gain is
        # already fully present in atk/def_stat/max_hp via Attribute Points, so a level term here
        # would double-count it (see docs/mechanics/04_strategic_cognition.md Sec 13.2, and
        # docs/plans/deferred_tuning_decisions_register.md D-11's own 214-entity evidence that a
        # level-only term does not discriminate at all in real compiled worlds).
        base_power = apparent_power(target)

        target_hp = target.combat.hp
        target_max_hp = max(1, target.combat.max_hp)
        hp_ratio = target_hp / target_max_hp
        if hp_ratio < 0.3:
            visible_signals.append("critical_health")
        elif hp_ratio < 0.7:
            visible_signals.append("wounded")
        else:
            visible_signals.append("healthy")

        # 2. Visible gear signals
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

        # 3. Power-gap-driven observation error (Sec 13.3). The observer's own side of the gap is
        # true_power(actor), never an estimate -- a stated law (Sec 13.2): an entity knows its own
        # strength exactly, and only judges others poorly. Confident at extremes, maximally
        # uncertain exactly at parity -- the point of the design, not a side effect to smooth away.
        attrs = getattr(actor, "attributes", None)
        perception = getattr(attrs, "perception", 5)

        gap = abs(true_power(actor) - base_power)
        uncertainty = gap_uncertainty(gap, perception)
        confidence = round(max(0.05, 1.0 - uncertainty), 2)

        # Deterministic observation noise (Sec 13.9): a pure function of stable inputs, scaled by
        # how uncertain this observation already is -- more uncertain estimates carry more noise.
        # No unseeded RNG call anywhere in this pipeline.
        if state is not None:
            noise_unit = deterministic_observation_noise(state.seed, state.tick, actor.id, target.id)
            base_power *= (1.0 + noise_unit * uncertainty * NOISE_MAGNITUDE_AT_MAX_UNCERTAINTY)

        # 4. Process Memory models
        if memory:
            # Memory reduces uncertainty and adjusts the power estimate toward reality
            confidence = min(0.95, memory.confidence + 0.15)
            uncertainty = max(0.05, uncertainty - 0.15)
            base_power = (base_power * 0.4) + (memory.estimated_power * 0.6)
            memory_used.append(memory.subject_key)
        else:
            unknown_factors.append("unknown_history")

        if perception < 4:
            unknown_factors.append("poor_perception")

        # 5. Biological stress/panic inflation
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
