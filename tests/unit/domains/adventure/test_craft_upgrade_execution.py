"""
tests/unit/domains/adventure/test_craft_upgrade_execution.py

TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP

Verifies:
  - test #3: an ACQUIRE_ITEM objective drives the REQUEST_CRAFT dispatch added to
    ActionIntentAdapter.execute() into a ResourceTransferIntent(source_kind="CRAFTING"),
    resolved by the existing, unmodified ResourceTransactionResolver into an
    InventoryUpdate whose items_add matches the recipe's output_item_id. This is
    the "reaches the authoritative crafting entry point" bar (test_plan.md's own
    hedge: "or the equivalent authoritative crafting entry point chosen in Plan" —
    ResourceTransferIntent + ResourceTransactionResolver, not CraftingSystem.craft()
    directly, per Step 6's architecture decision).
  - test #6: ServiceOpportunityProvider actually produces a craft_item Opportunity
    that AdventureRouteGenerator.generate turns into a CRAFT_UPGRADE
    AdventureRouteOption (closing investigation's Open Question 3 — the provider
    existed but was never wired into AdventureDecisionPhase.apply).
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ItemStack, BuildingState
from src.core.registries import RecipeRegistry
from src.core.conservation import ResourceTransactionResolver
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter
from src.domains.adventure.generator import AdventureRouteGenerator
from src.domains.adventure.schema import RouteFamily
from src.world.providers.services import ServiceOpportunityProvider


def _hero_with_recipe(recipe_id: str):
    recipe = RecipeRegistry.get(recipe_id)
    materials = [ItemStack(mat, qty) for mat, qty in recipe.requires_items.items()]
    return (
        V2EntityBuilder(1)
        .kind("hero")
        .identity(known_recipes={recipe_id})
        .inventory(gold=recipe.gold_cost, items=materials)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )


def test_crafting_project_reaches_craft_system():
    recipe_id = "iron_sword"
    recipe = RecipeRegistry.get(recipe_id)
    hero = _hero_with_recipe(recipe_id)

    intent = ActionIntent(
        kind="REQUEST_CRAFT",
        actor_id=hero.id,
        target_id=f"opp_craft_{recipe_id}",
        reason="test craft execution",
    )

    ActionIntentAdapter.clear_traces()
    updates = ActionIntentAdapter.execute(hero, intent, current_tick=10)

    assert hero.id in updates
    resource_transfers = updates[hero.id].resource_transfers
    assert resource_transfers, "REQUEST_CRAFT did not produce a resource_transfers payload"
    transfer = resource_transfers[0]
    assert transfer.source_kind == "CRAFTING"
    assert transfer.source_id == recipe_id

    traces = ActionIntentAdapter.get_traces()
    assert traces[-1].execution_result == "SUCCESS"

    # Confirm the intent resolves through the existing, unmodified authoritative
    # CRAFTING branch into a real InventoryUpdate carrying the recipe's output.
    state = AuthoritativeState(tick=10, seed=1, entities={hero.id: hero})
    result = ResourceTransactionResolver.resolve(state, hero, transfer)

    assert result.accepted
    assert result.inventory_update is not None
    output_item_ids = {stack.item_id for stack in result.inventory_update.items_add}
    assert recipe.output_item_id in output_item_ids


def test_craft_item_opportunity_is_generated():
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .identity(evolution_level=1)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    state = AuthoritativeState(
        tick=10,
        seed=1,
        entities={1: hero},
        buildings={},
    )

    opportunities = ServiceOpportunityProvider.get_opportunities(hero, state)
    assert any(o.kind == "craft_item" for o in opportunities), (
        "ServiceOpportunityProvider produced no craft_item opportunity for a "
        "blacksmith-affordance service — CRAFT_UPGRADE route candidates can "
        "never be generated regardless of the tactical.py routing fix"
    )

    routes = AdventureRouteGenerator.generate(hero, state, opportunities=opportunities)
    assert any(r.family == RouteFamily.CRAFT_UPGRADE for r in routes), (
        "craft_item opportunities were generated but AdventureRouteGenerator "
        "did not turn any of them into a CRAFT_UPGRADE AdventureRouteOption"
    )
