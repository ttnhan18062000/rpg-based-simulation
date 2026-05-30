from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.core.state import EntityState
from src.world.providers.requirements import Requirement, PerformanceBudgets
from src.world.providers.resources import Opportunity
from src.core.registries import ServiceRegistry, RecipeRegistry, ItemRegistry


class ServiceOpportunityProvider:
    """
    Exposes town service opportunities dynamically, state-free.
    """

    @staticmethod
    def get_opportunities(
        entity: EntityState,
        state: Any
    ) -> List[Opportunity]:
        # Track and budget performance
        PerformanceBudgets.provider_calls_total += 1
        PerformanceBudgets.provider_calls_by_kind["services"] = PerformanceBudgets.provider_calls_by_kind.get("services", 0) + 1
        
        if PerformanceBudgets.provider_calls_total > 500:
            return []

        opts: List[Opportunity] = []
        current_region = getattr(entity.navigation, "region_id", None) or "hometown"

        # Check for active blockers to target services
        blockers = getattr(entity.strategic, "blockers", {})
        has_material_blocker = any(b.kind == "material" and not b.resolved for b in blockers.values())
        
        # Blacksmith repair check: check if any equipment is damaged
        is_damaged = False
        equipped_durability = getattr(entity.equipment, "durability", {})
        for dur in equipped_durability.values():
            if dur < 50:
                is_damaged = True
                break

        # Inn rest check: check fatigue/sleep debt
        sleep_debt = getattr(entity.biological, "sleep_debt", 0.0)
        hunger = getattr(entity.biological, "hunger", 0.0)

        # Get service nodes in hometown
        for s_id, s_def in ServiceRegistry.all().items():
            if s_def.region_id == current_region:
                
                # Blacksmith opportunities
                if "craft" in s_def.supported_affordances:
                    # Craft upgrade opportunity
                    for recipe_id, recipe in RecipeRegistry.all().items():
                        reqs = [
                            Requirement(kind="recipe_known", subject=recipe_id),
                            Requirement(kind="has_gold", quantity=recipe.gold_cost)
                        ]
                        for m_id, m_qty in recipe.requires_items.items():
                            reqs.append(Requirement(kind="has_item", subject=m_id, quantity=m_qty))

                        opts.append(Opportunity(
                            id=f"opp_craft_{recipe_id}",
                            kind="craft_item",
                            target_id=s_id,
                            subject=recipe.output_item_id,
                            estimated_reward=90.0 if has_material_blocker else 30.0,
                            estimated_risk=0.0,
                            requirements=tuple(reqs),
                            confidence=1.0
                        ))

                if "repair" in s_def.supported_affordances and is_damaged:
                    opts.append(Opportunity(
                        id="opp_repair_gear",
                        kind="repair_gear",
                        target_id=s_id,
                        subject="equipment",
                        estimated_reward=80.0,
                        estimated_risk=0.0,
                        requirements=(Requirement(kind="has_gold", quantity=20),),
                        confidence=1.0
                    ))

                # Guide opportunities
                if "ask_info" in s_def.supported_affordances and has_material_blocker:
                    # Target information on active blocker
                    for blocker in blockers.values():
                        if blocker.kind == "material" and not blocker.resolved:
                            opts.append(Opportunity(
                                id=f"opp_ask_info_{blocker.subject}",
                                kind="ask_information",
                                target_id=s_id,
                                subject=blocker.subject,
                                estimated_reward=70.0,
                                estimated_risk=0.0,
                                requirements=(Requirement(kind="has_gold", quantity=10),),
                                confidence=1.0
                            ))

                # Shop opportunities
                if "buy" in s_def.supported_affordances:
                    opts.append(Opportunity(
                        id="opp_buy_small_potion",
                        kind="buy_item",
                        target_id=s_id,
                        subject="small_potion",
                        estimated_reward=40.0 if getattr(entity.combat, "hp", 100) < 40 else 10.0,
                        estimated_risk=0.0,
                        requirements=(Requirement(kind="has_gold", quantity=15), Requirement(kind="inventory_space", quantity=1)),
                        confidence=1.0
                    ))

                # Inn opportunities
                if "rest" in s_def.supported_affordances and (sleep_debt > 40 or hunger > 40):
                    opts.append(Opportunity(
                        id="opp_rest_inn",
                        kind="rest_inn",
                        target_id=s_id,
                        subject="sleep",
                        estimated_reward=sleep_debt,
                        estimated_risk=0.0,
                        requirements=(Requirement(kind="has_gold", quantity=10),),
                        confidence=1.0
                    ))

        # Sort by reward descending, cap at 5
        opts.sort(key=lambda o: o.estimated_reward, reverse=True)
        res = opts[:5]
        PerformanceBudgets.opportunities_returned_total += len(res)
        return res
