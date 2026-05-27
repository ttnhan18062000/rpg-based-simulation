"""
src/cognition/self_assessment.py
───────────────────────────────────────────────────────────────────────────────
Phase 2 — SelfAssessmentService

Converts raw EntityState into a SelfAwarenessComponent.
Stateless, deterministic, read-only.

Rules:
  - Does not mutate state.
  - Does not choose actions.
  - Simple deterministic thresholds (Phase 2 target).  Personality/memory
    modifiers belong to a later phase.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from src.core.self_model import SelfAwarenessComponent

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState


# ── Thresholds ────────────────────────────────────────────────────────────────
_HP_LOW = 0.35          # below this fraction → low_health weakness
_HP_CRITICAL = 0.20     # below this → high stress contribution
_STAMINA_LOW = 0.30     # below this fraction → low_stamina weakness
_HUNGER_HIGH = 60.0     # above this → hunger_pressure weakness
_SLEEP_DEBT_HIGH = 50.0 # above this → sleep_debt_pressure weakness
_INVENTORY_HIGH = 0.85  # above this fraction → inventory_pressure weakness
_GEAR_DAMAGE_LOW = 0.50 # below this in any slot → gear_damaged weakness
_LEVEL_WEAPON_GAP = 5   # weapon atk below level * this → weak_weapon weakness


class SelfAssessmentService:
    """
    Converts raw entity state into a subjective SelfAwarenessComponent.

    Phase 2 uses simple deterministic rules.  Later phases can inject
    personality, memory, and perception modifiers.
    """

    @staticmethod
    def assess(
        entity: "EntityState",
        state: Optional["AuthoritativeState"] = None,
    ) -> SelfAwarenessComponent:
        """
        Produce SelfAwarenessComponent from entity's raw state.

        Args:
            entity: The entity to assess.
            state:  Full authoritative world state (optional; used for
                    context like item registry lookups in later phases).
        Returns:
            A frozen SelfAwarenessComponent.
        """
        weaknesses: List[str] = []
        strengths: List[str] = []
        condition: Dict[str, float] = {}

        # ── Health ────────────────────────────────────────────────────────────
        hp_fraction = 1.0
        max_hp = getattr(entity.combat, "max_hp", 0)
        current_hp = getattr(entity.combat, "hp", max_hp)
        if max_hp > 0:
            hp_fraction = current_hp / max_hp
        condition["health"] = round(hp_fraction, 4)

        if hp_fraction < _HP_LOW:
            weaknesses.append("low_health")
        elif hp_fraction >= 0.85:
            strengths.append("good_health")

        # ── Stamina ───────────────────────────────────────────────────────────
        stamina_fraction = 1.0
        max_stamina = getattr(entity.stamina, "max_stamina", 0)
        current_stamina = getattr(entity.stamina, "current", max_stamina)
        if max_stamina > 0:
            stamina_fraction = current_stamina / max_stamina
        condition["stamina"] = round(stamina_fraction, 4)

        if stamina_fraction < _STAMINA_LOW:
            weaknesses.append("low_stamina")
        elif stamina_fraction >= 0.85:
            strengths.append("high_stamina")

        # ── Biological ────────────────────────────────────────────────────────
        hunger = getattr(entity.biological, "hunger", 0.0)
        sleep_debt = getattr(entity.biological, "sleep_debt", 0.0)
        if hunger > _HUNGER_HIGH:
            weaknesses.append("hunger_pressure")
        if sleep_debt > _SLEEP_DEBT_HIGH:
            weaknesses.append("sleep_debt_pressure")

        # ── Inventory ─────────────────────────────────────────────────────────
        inv = entity.inventory
        item_count = len(getattr(inv, "items", []))
        max_carry = getattr(inv, "max_slots", 20)
        if max_carry > 0:
            load_fraction = item_count / max_carry
        else:
            load_fraction = 0.0
        condition["carrying_load"] = round(load_fraction, 4)

        if load_fraction >= _INVENTORY_HIGH:
            weaknesses.append("inventory_pressure")

        # ── Equipment durability ──────────────────────────────────────────────
        gear_quality = 1.0
        slots = getattr(entity.equipment, "slots", {})
        if slots:
            durations = []
            for slot_item in slots.values():
                if slot_item is not None:
                    # durability may be a float 0..1 or an int; normalise
                    dur = getattr(slot_item, "durability", 1.0)
                    if isinstance(dur, int):
                        dur = dur / 100.0
                    durations.append(max(0.0, min(1.0, dur)))
            if durations:
                gear_quality = sum(durations) / len(durations)

        condition["gear_quality"] = round(gear_quality, 4)
        if gear_quality < _GEAR_DAMAGE_LOW:
            weaknesses.append("gear_damaged")
        elif gear_quality >= 0.9:
            strengths.append("good_gear")

        # ── Weapon strength vs level ─────────────────────────────────────────
        level = getattr(entity.identity, "evolution_level", 1) or 1
        entity_atk = getattr(entity.combat, "atk", 1)
        expected_atk = level * _LEVEL_WEAPON_GAP
        if entity_atk < expected_atk:
            weaknesses.append("weak_weapon")
        elif entity_atk >= expected_atk * 1.5:
            strengths.append("strong_weapon")

        # ── Composite metrics ────────────────────────────────────────────────
        severity_count = len(weaknesses)
        critical_conditions = (
            (1 if hp_fraction < _HP_CRITICAL else 0)
            + (1 if hunger > 80 else 0)
            + (1 if sleep_debt > 75 else 0)
        )

        stress_level = min(1.0, (severity_count * 0.15) + (critical_conditions * 0.25))
        confidence_level = max(0.05, min(1.0, 0.8 - (severity_count * 0.12) + (len(strengths) * 0.08)))
        uncertainty_level = 0.1  # base; later phases modulate with memory/perception

        return SelfAwarenessComponent(
            perceived_condition=condition,
            perceived_weaknesses=tuple(weaknesses),
            perceived_strengths=tuple(strengths),
            confidence_level=round(confidence_level, 4),
            stress_level=round(stress_level, 4),
            uncertainty_level=round(uncertainty_level, 4),
            last_self_check_tick=0,  # caller sets the tick after construction
        )
