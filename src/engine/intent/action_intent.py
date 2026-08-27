from dataclasses import dataclass, field
from typing import Mapping, Any, Dict, Optional, Tuple
from collections.abc import Mapping as MappingType

from src.core.state import EntityState, ItemStack
from src.core.updates import EntityUpdate, NavigationUpdate, InventoryUpdate, BiologicalUpdate, ResourceTransferIntent, IdentityUpdate
from src.world.providers.requirements import Requirement, RequirementEvaluator
from src.engine.domain.action_router import ActionRouter
from src.core.registries import RecipeRegistry, ItemRegistry, ResourceRegistry
from src.town.shop import ShopService


@dataclass(frozen=True, slots=True)
class ActionIntent:
    kind: str  # MOVE_TO, ASK_INFORMATION, BUY_ITEM, SELL_ITEM, REQUEST_CRAFT, REPAIR_GEAR, ACCEPT_QUEST, HARVEST_RESOURCE, ATTACK_TARGET, REST_AT_INN, RETURN_TOWN, CHANGE_OCCUPATION
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
            # ObjectiveIntentResolver never populates payload["recipe_id"] — the
            # recipe id instead travels as the opportunity id string in target_id
            # (objective.target, per AdventureDecisionService's opportunity-id
            # fallback), e.g. "opp_craft_<recipe_id>" (services.py:62).
            recipe_id = intent.payload.get("recipe_id")
            if not recipe_id and isinstance(intent.target_id, str) and intent.target_id.startswith("opp_craft_"):
                recipe_id = intent.target_id.removeprefix("opp_craft_")
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

            if "query_kind" not in intent.payload:
                # Adventure/AGENCY-domain-originated intent (ObjectiveIntentResolver) — behavior
                # must stay byte-identical to pre-fix code. Do not read "cost_paid" here.
                gold_deduct = intent.payload.get("cost_gold", 0)
                return {entity.id: EntityUpdate(
                    entity_id=entity.id,
                    inventory=InventoryUpdate(gold_delta=-gold_deduct),
                )}

            # Information-domain-originated (InformationIntentResolver) — close the loop.
            # Reuse the EXISTING canonical assimilation path (InformationResponseNormalizer +
            # InformationAssimilationService), the same two calls Branch A makes at phase.py:56-69,
            # instead of hand-rolling a second KnowledgeFact-merge implementation. Branch A's service
            # enforces capacity bounds (max_facts=10, max_unknowns=5, oldest-eviction) on this exact
            # durable field (EntityState.self_model.knowledge); a hand-rolled merge here would silently
            # skip those invariants and create two code paths reaching the same state through different,
            # divergent mechanisms — architecture-review finding, fixed here.
            gold_deduct = intent.payload.get("cost_paid", 0)  # dead-key fix: resolver.py writes "cost_paid"

            from src.domains.information.schema import InformationQuery
            from src.domains.information.normalizer import InformationResponseNormalizer
            from src.domains.information.assimilation import InformationAssimilationService
            from dataclasses import replace as dataclass_replace

            subject = intent.payload.get("subject", "")
            query = InformationQuery(subject=subject, kind=intent.payload.get("query_kind", ""))
            normalized = InformationResponseNormalizer.normalize(
                query=query,
                source_id=intent.target_id if intent.target_id is not None else "",
                raw_response={
                    "answer_kind": "KNOWN_FACT",
                    "certainty": intent.payload.get("expected_certainty", 0.5),
                    "details": {},
                },
                cost_paid=gold_deduct,
                current_tick=current_tick,
            )
            assim = InformationAssimilationService.assimilate(entity, normalized, current_tick)
            new_bundle = dataclass_replace(entity.self_model, knowledge=assim.knowledge_update)

            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                inventory=InventoryUpdate(gold_delta=-gold_deduct),
                self_model_bundle_set=new_bundle,
                strategic=assim.strategic_update,
            )}

        elif intent.kind == "REQUEST_CRAFT":
            # Durable-state commitment is deferred to the pre-existing, already
            # parity-verified ResourceTransactionResolver "CRAFTING" branch
            # (src/core/conservation.py:133) via the same ResourceTransferIntent
            # shape src/engine/blacksmith.py:205-218 already builds — do not call
            # CraftingSystem.craft() directly, it bypasses that authoritative path
            # and would not surface an item_crafted event.
            recipe = RecipeRegistry.get(recipe_id)
            materials = [ItemStack(mat, count) for mat, count in recipe.requires_items.items()]
            trace = IntentTrace(
                intent_kind=intent.kind,
                actor_id=intent.actor_id,
                why_selected=intent.reason or "request craft",
                opportunity_source_id=intent.source_opportunity_id,
                requirements_checked=tuple(reqs),
                execution_result="SUCCESS"
            )
            cls._traces.append(trace)
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                resource_transfers=[ResourceTransferIntent(
                    source_id=recipe_id,
                    source_kind="CRAFTING",
                    items_add=[ItemStack(recipe.output_item_id, 1)],
                    items_remove=materials,
                    gold_delta=-recipe.gold_cost,
                    gold_cost=recipe.gold_cost,
                    transfer_kind="CRAFT",
                )],
            )}

        elif intent.kind == "BUY_ITEM":
            # Same rationale as REQUEST_CRAFT: delegate to the existing, reusable
            # ShopService.buy_item (src/town/shop.py), which already builds the
            # authoritative ResourceTransferIntent(source_kind="SHOP_BUY") the
            # ResourceTransactionResolver "SHOP_BUY" branch expects.
            item_id = intent.payload.get("item_id")
            if not item_id and isinstance(intent.target_id, str) and intent.target_id.startswith("opp_buy_"):
                item_id = intent.target_id.removeprefix("opp_buy_")
            quantity = intent.payload.get("quantity", 1)

            result = ShopService.buy_item(entity, item_id, quantity, context) if (item_id and context is not None) else None
            if result is None:
                trace = IntentTrace(
                    intent_kind=intent.kind,
                    actor_id=intent.actor_id,
                    why_selected=intent.reason or "strategic choice",
                    opportunity_source_id=intent.source_opportunity_id,
                    requirements_checked=tuple(reqs),
                    execution_result="FAILED_REQUIREMENTS: shop_unavailable"
                )
                cls._traces.append(trace)
                return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0)}

            trace = IntentTrace(
                intent_kind=intent.kind,
                actor_id=intent.actor_id,
                why_selected=intent.reason or "buy item",
                opportunity_source_id=intent.source_opportunity_id,
                requirements_checked=tuple(reqs),
                execution_result="SUCCESS"
            )
            cls._traces.append(trace)
            return {entity.id: result.entity_updates[entity.id]}

        elif intent.kind == "CHANGE_OCCUPATION":
            # Sole new producer of IdentityUpdate(role_set=...) in the codebase -- a plain
            # EntityUpdate, the same typed-update shape every other branch in this function
            # already returns. Does not call replace() on EntityState/IdentityComponent directly
            # and does not construct an IdentityPatch itself: extract_patches()
            # (src/engine/patches.py:700-702) and IdentityPatch.apply() (patches.py:170-228)
            # remain the only code that ever builds or applies an IdentityPatch.
            role_str = intent.target_id.removeprefix("role_") if isinstance(intent.target_id, str) else None
            valid = bool(role_str) and role_str.isdigit()
            trace = IntentTrace(
                intent_kind=intent.kind,
                actor_id=intent.actor_id,
                why_selected=intent.reason or "change occupation",
                opportunity_source_id=intent.source_opportunity_id,
                requirements_checked=tuple(reqs),
                execution_result="SUCCESS" if valid else "FAILED_REQUIREMENTS: unparseable_role_target",
            )
            cls._traces.append(trace)
            if not valid:
                return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0)}
            return {entity.id: EntityUpdate(
                entity_id=entity.id,
                identity=IdentityUpdate(role_set=int(role_str)),
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
