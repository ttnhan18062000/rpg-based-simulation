"""Law of Weight on looting: picking up a ground item or corpse contents that would push the looter past max_weight resets the interaction and removes nothing.

Source: src/core/conservation.py (loot abort under weight pressure), exercised through AuthoritativeApplyPipeline.refine.
"""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, CorpseState, GroundItemState, InteractionComponent, ItemStack
from src.core.updates import EntityUpdate, InteractionUpdate, StateUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline


def _looter(target_id, max_weight):
    entity = V2EntityBuilder(1).kind("hero").location(1.0, 1.0).combat(alive=True, readiness=100.0).build()
    entity = replace(entity, interaction=InteractionComponent(target_node_id=target_id, progress=9))
    return replace(entity, inventory=replace(entity.inventory, max_slots=8, max_weight=max_weight))


def _finish_interaction(state):
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))})
    return AuthoritativeApplyPipeline.refine(state, update)


def test_a_ground_item_heavier_than_the_weight_limit_is_not_picked_up():
    ground = GroundItemState(id=600, item_id="iron_ore", quantity=1, position=(1.0, 1.0))  # iron_ore weighs 2.0
    state = AuthoritativeState(tick=1, seed=42, entities={1: _looter(600, max_weight=1.5)}, ground_items={600: ground})

    refined = _finish_interaction(state)

    assert refined.entity_updates[1].interaction.reset is True
    assert 600 not in refined.ground_items_remove


def test_the_same_ground_item_is_picked_up_when_the_weight_limit_allows_it():
    """Control: only the weight limit differs from the refused case."""
    ground = GroundItemState(id=600, item_id="iron_ore", quantity=1, position=(1.0, 1.0))
    state = AuthoritativeState(tick=1, seed=42, entities={1: _looter(600, max_weight=10.0)}, ground_items={600: ground})

    refined = _finish_interaction(state)

    assert 600 in refined.ground_items_remove


def test_corpse_contents_heavier_than_the_weight_limit_are_not_taken():
    corpse = CorpseState(id=700, original_entity_id=99, position=(1.0, 1.0), items=[ItemStack("iron_ore", 3)], decay_tick=100)  # 6.0 total
    state = AuthoritativeState(tick=1, seed=42, entities={1: _looter(700, max_weight=1.5)}, corpses={700: corpse})

    refined = _finish_interaction(state)

    assert refined.entity_updates[1].interaction.reset is True
    assert 700 not in refined.corpses_remove
