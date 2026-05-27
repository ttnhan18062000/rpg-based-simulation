import pytest
from src.core.builder import V2EntityBuilder
from src.core.models.inventory import ItemStack
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter
from src.core.registries import seed_phase1_content

# Seed content pack
seed_phase1_content()


def test_move_to_intent():
    """Verify MOVE_TO intent maps correctly to a NavigationUpdate and records trace."""
    ActionIntentAdapter.clear_traces()
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .build())

    intent = ActionIntent(
        kind="MOVE_TO",
        actor_id=ent.id,
        payload={"position": (10.0, 20.0)},
        source_opportunity_id="opp_move_1",
        reason="test movement"
    )

    updates = ActionIntentAdapter.execute(ent, intent)
    assert ent.id in updates
    assert updates[ent.id].navigation.target_set == (10.0, 20.0)

    # Verify trace
    traces = ActionIntentAdapter.get_traces()
    assert len(traces) == 1
    assert traces[0].intent_kind == "MOVE_TO"
    assert traces[0].execution_result == "SUCCESS"
    assert traces[0].opportunity_source_id == "opp_move_1"


def test_buy_item_insufficient_gold():
    """Verify BUY_ITEM fails cleanly when lacking enough gold."""
    ActionIntentAdapter.clear_traces()
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .inventory(gold=5)
        .build())

    intent = ActionIntent(
        kind="BUY_ITEM",
        actor_id=ent.id,
        target_id="small_potion",
        payload={"gold_cost": 15},
        source_opportunity_id="opp_buy_1",
        reason="need potion"
    )

    updates = ActionIntentAdapter.execute(ent, intent)
    # Failed requirement should not mutate state
    assert updates == {ent.id: updates[ent.id]}  # Or read-only/no update returned
    assert updates[ent.id].readiness_delta == 0.0

    # Verify trace shows failure
    traces = ActionIntentAdapter.get_traces()
    assert len(traces) == 1
    assert "FAILED_REQUIREMENTS" in traces[0].execution_result


def test_buy_item_success():
    """Verify BUY_ITEM delegates correctly when gold is sufficient."""
    ActionIntentAdapter.clear_traces()
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .inventory(gold=20)
        .build())

    intent = ActionIntent(
        kind="BUY_ITEM",
        actor_id=ent.id,
        target_id="shop_hometown",
        payload={"gold_cost": 15, "item_id": "small_potion"},
        source_opportunity_id="opp_buy_2",
        reason="potion buy"
    )

    updates = ActionIntentAdapter.execute(ent, intent)
    # Success should yield standard execution updates from ActionRouter
    assert ent.id in updates


def test_request_craft_missing_materials():
    """Verify REQUEST_CRAFT requirements check correctly flags missing items."""
    ActionIntentAdapter.clear_traces()
    # Missing moon_resin for hunter_blade
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .inventory(gold=100, items=[ItemStack(item_id="iron_ore", quantity=2), ItemStack(item_id="beast_fang", quantity=1)])
        .build())
    # Learn the recipe first
    object.__setattr__(ent.identity, "known_recipes", {"hunter_blade"})

    intent = ActionIntent(
        kind="REQUEST_CRAFT",
        actor_id=ent.id,
        target_id="blacksmith_hometown",
        payload={"recipe_id": "hunter_blade"},
        source_opportunity_id="opp_craft_1",
        reason="upgrade sword"
    )

    updates = ActionIntentAdapter.execute(ent, intent)
    assert updates[ent.id].readiness_delta == 0.0

    traces = ActionIntentAdapter.get_traces()
    assert len(traces) == 1
    assert "FAILED_REQUIREMENTS" in traces[0].execution_result
