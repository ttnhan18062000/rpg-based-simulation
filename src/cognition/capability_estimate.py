"""
src/cognition/capability_estimate.py
───────────────────────────────────────────────────────────────────────────────
Phase 2 — CapabilityEstimateService

Produces scoped subjective estimates of what the entity believes it can do.
Stateless, deterministic, read-only.

Only estimates the capability keys requested by the caller (scoped).
No full-world scan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from src.core.self_model import CapabilityEstimate, CapabilityEstimateComponent

if TYPE_CHECKING:
    from src.core.state import EntityState, AuthoritativeState


# ─────────────────────────────────────────────────────────────────────────────
# Context — caller specifies what to estimate (scoped, not world-scan)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CapabilityContext:
    """
    Caller-provided context: which capabilities to estimate and their data.

    combat_enemies   – list of enemy type ids to estimate combat against
    travel_regions   – list of region ids to estimate travel safety for
    gather_resources – list of resource ids to estimate gathering feasibility
    craft_recipes    – list of recipe ids to estimate crafting feasibility
    """
    combat_enemies: Tuple[str, ...] = ()
    travel_regions: Tuple[str, ...] = ()
    gather_resources: Tuple[str, ...] = ()
    craft_recipes: Tuple[str, ...] = ()

    # Optional reference data provided by caller
    enemy_data: Dict[str, Any] = field(default_factory=dict)     # {enemy_id: {level, danger_rating}}
    region_data: Dict[str, Any] = field(default_factory=dict)    # {region_id: {danger_rating}}
    resource_data: Dict[str, Any] = field(default_factory=dict)  # {resource_id: {required_tool}}
    recipe_data: Dict[str, Any] = field(default_factory=dict)    # {recipe_id: {requires_items, gold_cost}}

    @classmethod
    def for_combat(cls, enemy_ids: List[str], enemy_data: Optional[Dict] = None) -> "CapabilityContext":
        return cls(combat_enemies=tuple(enemy_ids), enemy_data=enemy_data or {})

    @classmethod
    def for_crafting(cls, recipe_ids: List[str], recipe_data: Optional[Dict] = None) -> "CapabilityContext":
        return cls(craft_recipes=tuple(recipe_ids), recipe_data=recipe_data or {})


# ── Internal danger level reference (Phase 2 simple defaults) ─────────────────
_ENEMY_DANGER: Dict[str, float] = {
    "rat": 0.1,
    "wolf": 0.4,
    "goblin": 0.5,
    "goblin_chief": 0.75,
    "bear": 0.6,
    "dragon": 0.95,
}

_REGION_DANGER: Dict[str, float] = {
    "hometown": 0.0,
    "near_forest": 0.3,
    "old_mine": 0.35,
    "north_ruin": 0.65,
    "deep_dungeon": 0.85,
}


class CapabilityEstimateService:
    """
    Produces scoped, deterministic capability estimates from entity state.

    Phase 2 uses simple stat-comparison rules. Later phases add memory,
    perception, and personality modifiers.
    """

    @staticmethod
    def estimate(
        entity: "EntityState",
        state: Optional["AuthoritativeState"] = None,
        context: Optional[CapabilityContext] = None,
        tick: int = 0,
    ) -> CapabilityEstimateComponent:
        """
        Produce CapabilityEstimateComponent scoped to the provided context.

        Args:
            entity:  Entity being evaluated.
            state:   World state (optional).
            context: Which capabilities to estimate. If None, returns empty.
            tick:    Current simulation tick.
        Returns:
            A frozen CapabilityEstimateComponent.
        """
        if context is None:
            return CapabilityEstimateComponent(last_updated_tick=tick)

        estimates: Dict[str, CapabilityEstimate] = {}

        # ── Entity stat snapshot ─────────────────────────────────────────
        max_hp = getattr(entity.combat, "max_hp", 100) or 100
        current_hp = getattr(entity.combat, "hp", max_hp)
        hp_frac = max(0.0, current_hp / max_hp)

        atk = getattr(entity.combat, "atk", 1)
        defense = getattr(entity.combat, "def_stat", 0)
        level = getattr(entity.identity, "evolution_level", 1) or 1

        max_stamina = getattr(entity.stamina, "max_stamina", 100) or 100
        current_stamina = getattr(entity.stamina, "current", max_stamina)
        stamina_frac = max(0.0, current_stamina / max_stamina)

        # ── Combat estimates ─────────────────────────────────────────────────
        for enemy_id in context.combat_enemies:
            key = f"combat.enemy_type.{enemy_id}"
            enemy_info = context.enemy_data.get(enemy_id, {})

            danger = enemy_info.get("danger_rating",
                      _ENEMY_DANGER.get(enemy_id, 0.5))
            enemy_level = enemy_info.get("level", max(1, int(danger * 10)))

            # Base estimate: atk vs enemy level, normalised
            base_power = (atk + defense * 0.5) / max(1.0, (enemy_level * 5 + danger * 20))
            raw_estimate = min(1.0, base_power * 1.5)

            # Modifiers
            raw_estimate *= hp_frac        # wounded = less capable
            raw_estimate *= (0.7 + 0.3 * stamina_frac)  # tired = slightly less capable
            raw_estimate = round(min(1.0, max(0.0, raw_estimate)), 4)

            # Confidence: lower when we don't have specific data
            confidence = 0.9 if enemy_id in _ENEMY_DANGER else 0.5
            confidence = round(confidence * hp_frac * 0.5 + confidence * 0.5, 4)

            estimates[key] = CapabilityEstimate(
                capability_key=key,
                estimate=raw_estimate,
                confidence=confidence,
                source="stat_comparison",
                last_updated_tick=tick,
            )

        # ── Travel estimates ─────────────────────────────────────────────────
        for region_id in context.travel_regions:
            key = f"travel.region.{region_id}"
            region_info = context.region_data.get(region_id, {})
            danger = region_info.get("danger_rating",
                      _REGION_DANGER.get(region_id, 0.5))

            # High danger + low HP = low travel safety estimate
            safety = (1.0 - danger) * hp_frac * (0.7 + 0.3 * stamina_frac)
            safety = round(max(0.0, min(1.0, safety)), 4)

            confidence = 0.85 if region_id in _REGION_DANGER else 0.4

            estimates[key] = CapabilityEstimate(
                capability_key=key,
                estimate=safety,
                confidence=round(confidence, 4),
                source="region_data",
                last_updated_tick=tick,
            )

        # ── Resource gathering estimates ──────────────────────────────────────
        for resource_id in context.gather_resources:
            key = f"gather.resource.{resource_id}"
            res_info = context.resource_data.get(resource_id, {})
            required_tool = res_info.get("required_tool")

            # Check if entity has the required tool
            has_tool = True
            if required_tool:
                inv_items = {
                    getattr(s, "item_id", None)
                    for s in getattr(entity.inventory, "items", [])
                }
                slot_items = {
                    getattr(v, "item_id", None)
                    for v in getattr(entity.equipment, "slots", {}).values()
                    if v is not None
                }
                has_tool = (required_tool in inv_items) or (required_tool in slot_items)

            gather_est = (0.8 if has_tool else 0.2) * hp_frac
            gather_est = round(max(0.0, min(1.0, gather_est)), 4)

            estimates[key] = CapabilityEstimate(
                capability_key=key,
                estimate=gather_est,
                confidence=0.8 if required_tool is not None else 0.6,
                source="tool_check",
                last_updated_tick=tick,
            )

        # ── Crafting estimates ───────────────────────────────────────────────
        for recipe_id in context.craft_recipes:
            key = f"craft.recipe.{recipe_id}"
            recipe_info = context.recipe_data.get(recipe_id, {})
            requires_items: Dict[str, int] = recipe_info.get("requires_items", {})
            gold_cost: int = recipe_info.get("gold_cost", 0)

            if not requires_items and not gold_cost:
                # Unknown recipe — low confidence, modest estimate
                estimates[key] = CapabilityEstimate(
                    capability_key=key,
                    estimate=0.3,
                    confidence=0.3,
                    source="unknown_recipe",
                    last_updated_tick=tick,
                )
                continue

            # Check gold
            gold_held = getattr(entity.inventory, "gold", 0)
            has_gold = gold_held >= gold_cost

            # Check items in inventory
            inv_item_counts: Dict[str, int] = {}
            for stack in getattr(entity.inventory, "items", []):
                iid = getattr(stack, "item_id", None)
                qty = getattr(stack, "quantity", 1)
                if iid:
                    inv_item_counts[iid] = inv_item_counts.get(iid, 0) + qty

            missing_any = False
            for item_id, qty_needed in requires_items.items():
                if inv_item_counts.get(item_id, 0) < qty_needed:
                    missing_any = True
                    break

            if missing_any or not has_gold:
                craft_est = 0.0  # cannot craft right now
                confidence = 0.9  # we know this with high confidence
            else:
                craft_est = 0.85  # materials present; crafting viable
                confidence = 0.9

            estimates[key] = CapabilityEstimate(
                capability_key=key,
                estimate=round(craft_est, 4),
                confidence=round(confidence, 4),
                source="material_check",
                last_updated_tick=tick,
            )

        return CapabilityEstimateComponent(
            estimates=estimates,
            last_updated_tick=tick,
        )
