from dataclasses import dataclass, field
from typing import Mapping, Any, Dict, Optional, Tuple
from collections.abc import Mapping as MappingType

from src.core.state import EntityState
from src.core.updates import EntityUpdate, NavigationUpdate, InventoryUpdate, BiologicalUpdate
from src.world.providers.requirements import Requirement, RequirementEvaluator
from src.engine.domain.action_router import ActionRouter
from src.core.registries import RecipeRegistry, ItemRegistry, ResourceRegistry


@dataclass(frozen=True, slots=True)
class ActionIntent:
    kind: str  # MOVE_TO, ASK_INFORMATION, BUY_ITEM, SELL_ITEM, REQUEST_CRAFT, REPAIR_GEAR, ACCEPT_QUEST, HARVEST_RESOURCE, ATTACK_TARGET, REST_AT_INN, RETURN_TOWN
    actor_id: int
    target_id: Optional[str | int] = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    source_opportunity_id: Optional[str] = None
    reason: Optional[str] = None


@dataclass(frozen=True, slots=True)
class IntentTrace:
    intent_kind: str
    actor_id: int
    why_selected: str
    opportunity_source_id: Optional[str]
    requirements_checked: Tuple[Requirement, ...]
    execution_result: str


class ActionIntentAdapter:
    """
    Adapts and executes strategic ActionIntents against the simulation engine.
    Ensures safe, requirement-gated delegation.
    """

    _traces: list[IntentTrace] = []

    @classmethod
    def get_traces(cls) -> list[IntentTrace]:
        return list(cls._traces)

    @classmethod
    def clear_traces(cls) -> None:
        cls._traces.clear()

    @classmethod
    def execute(
        cls,
        entity: EntityState,
        intent: ActionIntent,
        current_tick: int = 0,
        neighbor_view: Any = None,
        context: Any = None
    ) -> Dict[int, EntityUpdate]:
        # 1. Validate requirements first (honest requirement gating)
        reqs = []
        if intent.kind == "BUY_ITEM":
            gold_cost = intent.payload.get("gold_cost", 0)
            reqs.append(Requirement(kind="has_gold", quantity=gold_cost))
            reqs.append(Requirement(kind="inventory_space", quantity=1))
        elif intent.kind == "REQUEST_CRAFT":
            recipe_id = intent.payload.get("recipe_id")
            if recipe_id and RecipeRegistry.contains(recipe_id):
                recipe = RecipeRegistry.get(recipe_id)
                reqs.append(Requirement(kind="recipe_known", subject=recipe_id))
                reqs.append(Requirement(kind="has_gold", quantity=recipe.gold_cost))
                for m_id, m_qty in recipe.requires_items.items():
                    reqs.append(Requirement(kind="has_item", subject=m_id, quantity=m_qty))
        elif intent.kind == "HARVEST_RESOURCE":
            res_id = intent.target_id
            if res_id and ResourceRegistry.contains(res_id):
                res = ResourceRegistry.get(res_id)
                if res.required_tool:
                    reqs.append(Requirement(kind="has_item", subject=res.required_tool, quantity=1))
                reqs.append(Requirement(kind="inventory_space", quantity=1))

        # Evaluate requirements
        all_passed = True
        failed_reqs = []
        for r in reqs:
            res = RequirementEvaluator.evaluate(entity, context, r)
            if not res.passed:
                all_passed = False
                failed_reqs.append(r)

        if not all_passed:
            trace = IntentTrace(
                intent_kind=intent.kind,
                actor_id=intent.actor_id,
                why_selected=intent.reason or "strategic choice",
                opportunity_source_id=intent.source_opportunity_id,
                requirements_checked=tuple(reqs),
                execution_result=f"FAILED_REQUIREMENTS: {failed_reqs}"
            )
            cls._traces.append(trace)
            return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0)}

        # 2. Delegate execution
        router_payload = dict(intent.payload)
        router_payload["target_id"] = intent.target_id

        if intent.kind == "MOVE_TO":
            trace = IntentTrace(
                intent_kind=intent.kind,
                actor_id=intent.actor_id,
                why_selected=intent.reason or "move to destination",
                opportunity_source_id=intent.source_opportunity_id,
                requirements_checked=tuple(reqs),
                execution_result="SUCCESS"
            )
            cls._traces.append(trace)
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                navigation=NavigationUpdate(target_set=intent.payload.get("position"))
            )}

        elif intent.kind == "REST_AT_INN":
            router_payload["action"] = "SLEEP"
        elif intent.kind == "REPAIR_GEAR":
            router_payload["action"] = "REPAIR"
        elif intent.kind == "HARVEST_RESOURCE":
            router_payload["action"] = "INTERACT"
        elif intent.kind == "ATTACK_TARGET":
            router_payload["action"] = "ATTACK"
        elif intent.kind == "ASK_INFORMATION":
            trace = IntentTrace(
                intent_kind=intent.kind,
                actor_id=intent.actor_id,
                why_selected=intent.reason or "ask info",
                opportunity_source_id=intent.source_opportunity_id,
                requirements_checked=tuple(reqs),
                execution_result="SUCCESS"
            )
            cls._traces.append(trace)
            gold_deduct = intent.payload.get("cost_gold", 0)
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                inventory=InventoryUpdate(gold_delta=-gold_deduct)
            )}
        else:
            router_payload["action"] = intent.kind

        updates = ActionRouter.execute_action(entity, router_payload, current_tick, neighbor_view, context)
        
        result_status = "SUCCESS"
        if entity.id in updates and updates[entity.id].navigation and updates[entity.id].navigation.failure_reason:
            result_status = f"FAILED: {updates[entity.id].navigation.failure_reason}"

        trace = IntentTrace(
            intent_kind=intent.kind,
            actor_id=intent.actor_id,
            why_selected=intent.reason or "execute routed action",
            opportunity_source_id=intent.source_opportunity_id,
            requirements_checked=tuple(reqs),
            execution_result=result_status
        )
        cls._traces.append(trace)
        return updates
