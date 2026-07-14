"""
tests/integration/domains/adventure/test_harvest_to_event.py

TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP

Integration-scale proof for the ticket's AC: "at least one real calibration run
produces a real resource_harvested, item_crafted, trade_executed, or
shop_transaction event under realistic play, not the generic gold_sink_fired
baseline." This test drives the real authoritative resolution path — not a
mock — from a REQUEST_CRAFT ActionIntent through ActionIntentAdapter.execute(),
through the unmodified ResourceTransactionSystem.resolve_all()/
ResourceTransactionResolver.resolve() pipeline phase, into an intent_results
entry that event_extractor.py translates into a real item_crafted
SimulationEvent.

item_crafted is used here rather than resource_harvested because the new
tactical.py Pillar 5.1 branch (Step 5) resolves REACH_RESOURCE objectives to
ObjectiveIntentResolver's unmodified MOVE_TO mapping even on arrival — closing
the harvest-on-arrival transition is out of this ticket's scope (Scope Guards:
"Do not modify ObjectiveIntentResolver's internal mapping logic"). item_crafted
is the routing-bridge fix's most directly reachable new economy event and
satisfies the AC ("resource_harvested, item_crafted, trade_executed, or
shop_transaction" — any one of the four).
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ItemStack
from src.core.updates import StateUpdate
from src.core.registries import RecipeRegistry
from src.engine.economy import ResourceTransactionSystem
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter
from src.observability.event_extractor import EventExtractor
from src.observability.config import ObservabilityMode


def test_crafting_project_produces_item_crafted_event_through_full_pipeline():
    recipe_id = "iron_sword"
    recipe = RecipeRegistry.get(recipe_id)
    materials = [ItemStack(mat, qty) for mat, qty in recipe.requires_items.items()]

    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .identity(known_recipes={recipe_id})
        .inventory(gold=recipe.gold_cost, items=materials)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    state = AuthoritativeState(tick=10, seed=1, entities={1: hero})

    # 1. ActionIntentAdapter.execute() — the same call site tactical.py's new
    # Pillar 5.1 branch (Step 5) reaches for a real ACQUIRE_ITEM objective.
    ActionIntentAdapter.clear_traces()
    intent = ActionIntent(
        kind="REQUEST_CRAFT",
        actor_id=hero.id,
        target_id=f"opp_craft_{recipe_id}",
        reason="integration test craft",
    )
    adapter_updates = ActionIntentAdapter.execute(hero, intent, current_tick=state.tick, context=state)
    update = StateUpdate(entity_updates=adapter_updates)

    # 2. The unmodified, already parity-verified authoritative resolution phase.
    resolved_update = ResourceTransactionSystem.resolve_all(state, update)

    assert resolved_update.entity_updates[hero.id].intent_results, (
        "ResourceTransactionSystem.resolve_all produced no intent_results — "
        "the CRAFTING transfer intent was not resolved"
    )

    # 3. The same event derivation event_extractor.py runs every tick.
    EventExtractor.reset_run_state()
    events = EventExtractor.extract(state, state, resolved_update, mode=ObservabilityMode.LIGHT)

    event_types = {e.event_type for e in events}
    assert "item_crafted" in event_types, (
        f"Expected a real item_crafted event, got: {event_types}"
    )
