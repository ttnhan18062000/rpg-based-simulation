"""
src/cognition/need_interpretation.py
───────────────────────────────────────────────────────────────────────────────
Phase 2 — NeedInterpretationService

Converts raw state + SelfAwarenessComponent into NeedInterpretationComponent.
Stateless, deterministic, read-only.

Rules:
  - Does not mutate state.
  - Does not choose actions.
  - Survival needs outrank growth needs.
  - Information needs are generated when knowledge gaps exist.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from src.core.self_model import (
    InterpretedNeed,
    NeedInterpretationComponent,
    SelfAwarenessComponent,
)

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState


# ── Urgency constants ─────────────────────────────────────────────────────────
_URGENCY_CRITICAL = 0.95
_URGENCY_HIGH     = 0.75
_URGENCY_MEDIUM   = 0.50
_URGENCY_LOW      = 0.25

# ── Gold floor — below this, gold is a moderate need ─────────────────────────
_GOLD_LOW = 30
_GOLD_VERY_LOW = 10


class NeedInterpretationService:
    """
    Interprets raw state + self-awareness into structured needs.

    Survival needs (healing, food, rest, safety) outrank growth needs
    (equipment improvement, gold, information) when critical.
    """

    @staticmethod
    def interpret(
        entity: "EntityState",
        self_awareness: SelfAwarenessComponent,
        state: Optional["AuthoritativeState"] = None,
    ) -> NeedInterpretationComponent:
        """
        Produce NeedInterpretationComponent.

        Args:
            entity:         The entity whose needs are being interpreted.
            self_awareness: Already-computed SelfAwarenessComponent.
            state:          World state (optional; used for knowledge gap checks).
        Returns:
            A frozen NeedInterpretationComponent.
        """
        needs: Dict[str, InterpretedNeed] = {}
        weaknesses = set(self_awareness.perceived_weaknesses)

        # ── Healing need ─────────────────────────────────────────────────────
        health = self_awareness.perceived_condition.get("health", 1.0)
        if "low_health" in weaknesses:
            urgency = _URGENCY_CRITICAL if health < 0.20 else _URGENCY_HIGH
            needs["healing"] = InterpretedNeed(
                key="healing",
                urgency=urgency,
                confidence=0.95,
                reason="low_health",
            )

        # ── Food need ────────────────────────────────────────────────────────
        hunger = getattr(entity.biological, "hunger", 0.0)
        if hunger > 60.0:
            urgency = _URGENCY_CRITICAL if hunger > 85.0 else (
                _URGENCY_HIGH if hunger > 70.0 else _URGENCY_MEDIUM
            )
            needs["food"] = InterpretedNeed(
                key="food",
                urgency=urgency,
                confidence=0.9,
                reason="hunger",
            )

        # ── Rest need ────────────────────────────────────────────────────────
        sleep_debt = getattr(entity.biological, "sleep_debt", 0.0)
        if sleep_debt > 50.0:
            urgency = _URGENCY_HIGH if sleep_debt > 75.0 else _URGENCY_MEDIUM
            needs["rest"] = InterpretedNeed(
                key="rest",
                urgency=urgency,
                confidence=0.9,
                reason="sleep_debt",
            )

        # ── Stamina rest need (different from sleep) ─────────────────────────
        if "low_stamina" in weaknesses:
            # Only create this if rest need isn't already covering it
            if "rest" not in needs:
                needs["stamina_recovery"] = InterpretedNeed(
                    key="stamina_recovery",
                    urgency=_URGENCY_MEDIUM,
                    confidence=0.85,
                    reason="low_stamina",
                )

        # ── Equipment repair ─────────────────────────────────────────────────
        if "gear_damaged" in weaknesses:
            gear_quality = self_awareness.perceived_condition.get("gear_quality", 1.0)
            urgency = _URGENCY_HIGH if gear_quality < 0.25 else _URGENCY_MEDIUM
            needs["equipment_repair"] = InterpretedNeed(
                key="equipment_repair",
                urgency=urgency,
                confidence=0.9,
                reason="gear_damaged",
            )

        # ── Equipment improvement ────────────────────────────────────────────
        if "weak_weapon" in weaknesses:
            # Lower priority than survival needs; higher priority than information
            base_urgency = _URGENCY_MEDIUM
            # Deflate further if healing is critical — survival trumps growth
            if "healing" in needs and needs["healing"].urgency >= _URGENCY_CRITICAL:
                base_urgency = _URGENCY_LOW
            needs["equipment_improvement"] = InterpretedNeed(
                key="equipment_improvement",
                urgency=base_urgency,
                confidence=0.85,
                reason="weak_weapon",
            )

        # ── Inventory space ──────────────────────────────────────────────────
        if "inventory_pressure" in weaknesses:
            load = self_awareness.perceived_condition.get("carrying_load", 0.0)
            urgency = _URGENCY_HIGH if load >= 1.0 else _URGENCY_MEDIUM
            needs["inventory_space"] = InterpretedNeed(
                key="inventory_space",
                urgency=urgency,
                confidence=0.95,
                reason="inventory_pressure",
            )

        # ── Gold need ────────────────────────────────────────────────────────
        gold = getattr(entity.inventory, "gold", 0)
        if gold < _GOLD_LOW:
            urgency = _URGENCY_HIGH if gold < _GOLD_VERY_LOW else _URGENCY_LOW
            needs["gold"] = InterpretedNeed(
                key="gold",
                urgency=urgency,
                confidence=0.9,
                reason="low_gold",
            )

        # ── Information need (from knowledge model unknowns on entity) ────────
        # Check entity's self_model knowledge unknowns if they exist
        knowledge = getattr(entity.self_model, "knowledge", None)
        if knowledge and knowledge.unknowns:
            needs["information"] = InterpretedNeed(
                key="information",
                urgency=_URGENCY_LOW,
                confidence=0.8,
                reason=f"knowledge_gaps:{len(knowledge.unknowns)}",
            )

        # ── Dominant need ────────────────────────────────────────────────────
        dominant = None
        if needs:
            dominant = max(needs, key=lambda k: needs[k].urgency)

        return NeedInterpretationComponent(
            active_needs=needs,
            dominant_need=dominant,
            last_interpreted_tick=0,  # caller sets tick
        )
