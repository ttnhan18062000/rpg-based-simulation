from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.core.state import EntityState
from src.core.strategic import BlockerState


@dataclass(frozen=True, slots=True)
class Requirement:
    kind: str
    subject: Optional[str] = None
    quantity: int = 1


@dataclass(frozen=True, slots=True)
class RequirementResult:
    requirement: Requirement
    passed: bool
    blocker_kind: Optional[str] = None
    reason: Optional[str] = None
    suggested_resolution_tags: Tuple[str, ...] = field(default_factory=tuple)


class PerformanceBudgets:
    provider_calls_total: int = 0
    provider_calls_by_kind: Dict[str, int] = {"resources": 0, "services": 0}
    opportunities_returned_total: int = 0
    requirements_evaluated_total: int = 0
    MAX_REQUIREMENTS_BUDGET: int = 1000

    @classmethod
    def reset(cls) -> None:
        cls.provider_calls_total = 0
        cls.provider_calls_by_kind = {"resources": 0, "services": 0}
        cls.opportunities_returned_total = 0
        cls.requirements_evaluated_total = 0


class RequirementEvaluator:
    """
    Pure decision engine to evaluate game requirements.
    Does NOT mutate any state directly.
    """

    @staticmethod
    def evaluate(
        entity: EntityState,
        state: Any,
        requirement: Requirement
    ) -> RequirementResult:
        """
        Evaluate a single constraint against the entity and world state.
        Returns a rich RequirementResult containing blockers and resolution strategies.
        """
        PerformanceBudgets.requirements_evaluated_total += 1
        
        # Enforce budget limits
        if PerformanceBudgets.requirements_evaluated_total > PerformanceBudgets.MAX_REQUIREMENTS_BUDGET:
            return RequirementResult(
                requirement=requirement,
                passed=False,
                blocker_kind="budget_exceeded",
                reason="Performance budget limit for requirement evaluation exceeded"
            )

        kind = requirement.kind
        subject = requirement.subject
        qty = requirement.quantity

        if kind == "has_gold":
            gold_held = getattr(entity.inventory, "gold", 0)
            if gold_held >= qty:
                return RequirementResult(requirement, True)
            return RequirementResult(
                requirement=requirement,
                passed=False,
                blocker_kind="not_enough_gold",
                reason=f"Entity lacks sufficient gold. Held: {gold_held}, Required: {qty}",
                suggested_resolution_tags=("gather_for_gold", "easy_quest", "sell_loot")
            )

        elif kind == "has_item":
            if not subject:
                return RequirementResult(requirement, False, "invalid_requirement", "has_item requires a subject item_id")
            
            # Sum quantity of matching item_id in inventory
            held_qty = 0
            for stack in getattr(entity.inventory, "items", []):
                if stack.item_id == subject:
                    held_qty += stack.quantity

            if held_qty >= qty:
                return RequirementResult(requirement, True)
            
            return RequirementResult(
                requirement=requirement,
                passed=False,
                blocker_kind="missing_material",
                reason=f"Entity lacks item: {subject}. Held: {held_qty}, Required: {qty}",
                suggested_resolution_tags=("ask_information", "buy_material", "harvest_resource")
            )

        elif kind == "inventory_space":
            max_slots = getattr(entity.inventory, "max_slots", 16)
            current_slots = len(getattr(entity.inventory, "items", []))
            if current_slots + qty <= max_slots:
                return RequirementResult(requirement, True)
            return RequirementResult(
                requirement=requirement,
                passed=False,
                blocker_kind="inventory_full",
                reason=f"Inventory space exceeded. Slots: {current_slots}/{max_slots}, Need: {qty}",
                suggested_resolution_tags=("sell_loot", "store_items", "upgrade_inventory")
            )

        elif kind == "knows_fact":
            if not subject:
                return RequirementResult(requirement, False, "invalid_requirement", "knows_fact requires a subject key")
            
            # Check belief system or leads
            known = False
            for belief in getattr(entity.strategic, "beliefs", {}).values():
                if belief.subject == subject and getattr(belief, "certainty", 0.0) >= 0.5:
                    known = True
                    break
            
            if not known:
                for lead in getattr(entity.strategic, "leads", {}).values():
                    if lead.subject == subject:
                        known = True
                        break

            if known:
                return RequirementResult(requirement, True)
            
            return RequirementResult(
                requirement=requirement,
                passed=False,
                blocker_kind="unknown_source",
                reason=f"Entity lacks knowledge of fact: {subject}",
                suggested_resolution_tags=("ask_information", "research_location", "explore_region")
            )

        elif kind == "near_service":
            if not subject:
                return RequirementResult(requirement, False, "invalid_requirement", "near_service requires a service_kind subject")
            
            # Check if entity is near a functioning service of the specified kind
            # We mock proximity validation for Phase 1 (requires location match in same region)
            near = False
            if state is not None:
                from src.town.town_navigation import TownNavigation
                building = TownNavigation.get_nearest_service(entity, subject, state)
                if building is not None:
                    ex, ey = entity.position
                    bx, by = building.position
                    near = ((bx - ex)**2 + (by - ey)**2) ** 0.5 <= 5.0

            if near:
                return RequirementResult(requirement, True)

            return RequirementResult(
                requirement=requirement,
                passed=False,
                blocker_kind="too_far_from_service",
                reason=f"Entity is too far from service: {subject}",
                suggested_resolution_tags=("travel_to_region", "return_town")
            )

        elif kind == "target_alive":
            if not subject:
                return RequirementResult(requirement, False, "invalid_requirement", "target_alive requires target_id")
            
            # Mock or check from AuthoritativeState
            alive = True
            if state and hasattr(state, "entities"):
                tgt = state.entities.get(subject)
                if tgt and hasattr(tgt, "combat") and not getattr(tgt.combat, "alive", True):
                    alive = False

            if alive:
                return RequirementResult(requirement, True)
            
            return RequirementResult(
                requirement=requirement,
                passed=False,
                blocker_kind="target_dead",
                reason=f"Target entity {subject} is not alive",
                suggested_resolution_tags=("choose_new_target", "quest_complete")
            )

        elif kind == "recipe_known":
            if not subject:
                return RequirementResult(requirement, False, "invalid_requirement", "recipe_known requires recipe_id")
            
            known_recipes = getattr(entity.identity, "known_recipes", set())
            if subject in known_recipes:
                return RequirementResult(requirement, True)
            
            return RequirementResult(
                requirement=requirement,
                passed=False,
                blocker_kind="unknown_recipe",
                reason=f"Entity lacks knowledge of recipe: {subject}",
                suggested_resolution_tags=("train_at_blacksmith", "buy_recipe")
            )

        return RequirementResult(
            requirement=requirement,
            passed=False,
            blocker_kind="unsupported_requirement",
            reason=f"Unsupported requirement kind: {kind}"
        )
