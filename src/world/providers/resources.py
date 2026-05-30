from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from src.core.state import EntityState
from src.world.providers.requirements import Requirement, PerformanceBudgets
from src.core.registries import ResourceRegistry, ItemRegistry


@dataclass(frozen=True, slots=True)
class Opportunity:
    id: str
    kind: str  # "gather_resource" | "buy_item" | "craft_item" | "repair_gear" | "ask_information" | "rest_inn"
    target_id: str
    subject: str
    estimated_reward: float
    estimated_risk: float
    requirements: Tuple[Requirement, ...]
    confidence: float


class ResourceOpportunityProvider:
    """
    Exposes resource opportunities dynamically, state-free.
    """

    @staticmethod
    def get_opportunities(
        entity: EntityState,
        state: Any
    ) -> List[Opportunity]:
        # Track and budget performance
        PerformanceBudgets.provider_calls_total += 1
        PerformanceBudgets.provider_calls_by_kind["resources"] = PerformanceBudgets.provider_calls_by_kind.get("resources", 0) + 1
        
        if PerformanceBudgets.provider_calls_total > 500:
            return []

        opts: List[Opportunity] = []
        
        # Scoped to visible or known regions
        current_region = getattr(entity.navigation, "region_id", None) or "hometown"
        
        # Find active material needs from blockers or leads
        needed_materials = set()
        for blocker in getattr(entity.strategic, "blockers", {}).values():
            if blocker.kind == "material" and not blocker.resolved:
                needed_materials.add(blocker.subject)

        # Retrieve nodes from live simulation state
        nodes = getattr(state, "resource_nodes", {})
        if not nodes:
            return []

        for node_id, node in nodes.items():
            # Only consider active resource nodes with charge remaining
            if node.remaining_charges <= 0:
                continue

            # Check if this node is in the entity's current region bounds or tags
            # (ResourceRegistry definitions mapped via kind)
            res_def = ResourceRegistry.get(node.kind)
            if not res_def:
                continue

            # Ensure the node's region corresponds to entity's current region
            # We can also verify position bounds if they match
            if current_region in res_def.source_region_tags:
                is_needed = res_def.yield_item in needed_materials
                reward = 50.0 if is_needed else 10.0
                
                # Check depletion multiplier: reward decreases as remaining charges drop
                depletion_mult = node.remaining_charges / node.max_charges if node.max_charges > 0 else 1.0
                reward *= (0.5 + 0.5 * depletion_mult)

                reqs = [
                    Requirement(kind="inventory_space", quantity=1),
                    Requirement(kind="near_service", subject=current_region)
                ]
                if res_def.required_tool:
                    reqs.append(Requirement(kind="has_item", subject=res_def.required_tool, quantity=1))

                opts.append(Opportunity(
                     id=f"opp_resource_{node_id}",
                     kind="gather_resource",
                     target_id=str(node_id),
                     subject=res_def.yield_item,
                     estimated_reward=reward,
                     estimated_risk=0.1,
                     requirements=tuple(reqs),
                     confidence=1.0
                ))

        # Sort by reward descending, cap at 5
        opts.sort(key=lambda o: o.estimated_reward, reverse=True)
        res = opts[:5]
        PerformanceBudgets.opportunities_returned_total += len(res)
        return res
