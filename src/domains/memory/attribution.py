"""
src/domains/memory/attribution.py
───────────────────────────────────────────────────────────────────────────────
Phase 13 — CausalAttributionService

Attributes causes to failed events (combat loss, failed search, etc.)
and generates subjective advices.
"""

from __future__ import annotations
from typing import Tuple
from src.core.state import EntityState
from src.core.cognition import CausalMemoryEntry

class CausalAttributionService:
    """Interprets why an event failed and generates causal advice."""

    @staticmethod
    def attribute(
        entity: EntityState,
        event_id: str,
        event_kind: str,
        tick: int,
        region_id: str | None = None
    ) -> CausalMemoryEntry:
        causes: Tuple[str, ...] = ()
        advice: Tuple[str, ...] = ()

        if event_kind == "combat_loss":
            # Examine self perceived condition and gear
            hp_pct = entity.combat.hp / max(1.0, entity.combat.max_hp)
            stamina = entity.stamina.current
            
            causes_list = []
            advice_list = []

            if hp_pct < 0.3:
                causes_list.append("low_health")
                advice_list.append("heal_first")
            if stamina < 20:
                causes_list.append("low_stamina")
                advice_list.append("rest_often")
            
            # Check for weapon durability if equipment slots have values
            weapon_dur = entity.equipment.durability.get("MAIN_HAND", 1.0) if hasattr(entity.equipment, "durability") else 1.0
            if weapon_dur < 0.2:
                causes_list.append("damaged_weapon")
                advice_list.append("repair_weapon")

            if not causes_list:
                causes_list.append("strong_enemy")
                advice_list.append("avoid_enemy")

            causes = tuple(causes_list)
            advice = tuple(advice_list)

        elif event_kind == "failed_search":
            causes = ("wrong_location", "bad_rumor")
            advice = ("seek_trusted_guide", "verify_intel")

        elif event_kind == "failed_craft":
            causes = ("missing_material", "unknown_recipe")
            advice = ("acquire_mats", "train_blacksmith")

        elif event_kind == "party_abandoned":
            causes = ("grudge_decay", "cohesion_lost")
            advice = ("boost_party_trust", "realign_directive")

        return CausalMemoryEntry(
            event_id=event_id,
            event_kind=event_kind,
            interpreted_causes=causes,
            confidence=0.8,
            future_advice=advice,
            tick=tick,
            region_id=region_id
        )
