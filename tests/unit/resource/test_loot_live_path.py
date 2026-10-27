"""Looting proven on the live path: proposals go through ``AuthoritativeApplyPipeline.refine``
(which runs ``InteractionSystem.enforce``) and ``ApplyPath.apply_generation``.

Replaces the proof that ran the retired ``LootSystem`` (TOWN-009, TOWN-076).
"""
import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, CorpseState, GroundItemState, ItemStack
from src.core.treasury import total_coin
from src.core.updates import EntityUpdate, InteractionUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.interaction import InteractionSystem
from src.engine.pipeline import AuthoritativeApplyPipeline

REQUIRED_TICKS = 10


def _hero():
    return V2EntityBuilder(1).kind("hero").location(0, 0).build()


def _tick(state, target_id, **entity_fields):
    """One live tick: the entity proposes one tick of channel progress on ``target_id``."""
    proposal = StateUpdate(entity_updates={1: EntityUpdate(
        entity_id=1,
        interaction=InteractionUpdate(target_node_id=target_id, progress_delta=1.0),
        **entity_fields,
    )})
    refined = AuthoritativeApplyPipeline.refine(state, proposal)
    return refined, ApplyPath.apply_generation(state, refined)


def _channel(state, target_id, ticks):
    for _ in range(ticks):
        refined, state = _tick(state, target_id)
        yield refined, state


@pytest.mark.v2_contract
def test_ground_item_loot_is_channeled_then_completes():
    state = AuthoritativeState(tick=1, seed=42, entities={1: _hero()},
                               ground_items={101: GroundItemState(id=101, item_id="iron_ore", quantity=5, position=(0, 1))})
    for refined, state in _channel(state, 101, REQUIRED_TICKS - 1):
        assert not refined.ground_items_remove
        assert 101 in state.ground_items
        assert not state.entities[1].inventory.items
    assert state.entities[1].interaction.progress == REQUIRED_TICKS - 1
    refined, state = _tick(state, 101)
    assert 101 in refined.ground_items_remove
    assert 101 not in state.ground_items
    assert any(s.item_id == "iron_ore" and s.quantity == 5 for s in state.entities[1].inventory.items)
    assert state.entities[1].interaction.target_node_id is None


@pytest.mark.v2_contract
def test_corpse_loot_completion_transfers_all_item_stacks():
    corpse = CorpseState(id=301, original_entity_id=999, position=(0, 1),
                         items=[ItemStack("iron_ore", 3), ItemStack("wood", 2)], decay_tick=1000)
    state = AuthoritativeState(tick=1, seed=42, entities={1: _hero()}, corpses={301: corpse})
    for refined, state in _channel(state, 301, REQUIRED_TICKS - 1):
        assert not refined.corpses_remove
        assert 301 in state.corpses
    refined, state = _tick(state, 301)
    assert 301 in refined.corpses_remove and 301 not in state.corpses
    held = {s.item_id: s.quantity for s in state.entities[1].inventory.items}
    assert held == {"iron_ore": 3, "wood": 2}


@pytest.mark.v2_contract
@pytest.mark.parametrize("kind", ["ground_item", "corpse"])
def test_loot_channel_is_interrupted_by_movement(kind):
    """``InteractionSystem.enforce`` resets a channel on an entity that moved this tick; the target stays put and nothing is granted.

    Called on ``enforce`` itself: movement routing, which sets ``moved_this_tick`` on the live path, runs before it.
    """
    ground = {101: GroundItemState(id=101, item_id="iron_ore", quantity=5, position=(0, 1))} if kind == "ground_item" else {}
    corpses = {101: CorpseState(id=101, original_entity_id=999, position=(0, 1), items=[ItemStack("iron_ore", 5)], decay_tick=1000)} if kind == "corpse" else {}
    state = AuthoritativeState(tick=1, seed=42, entities={1: _hero()}, ground_items=ground, corpses=corpses)
    for _, state in _channel(state, 101, 3):
        pass
    assert state.entities[1].interaction.progress == 3
    moved = StateUpdate(entity_updates={1: EntityUpdate(
        entity_id=1, new_position=(3, 3), moved_this_tick=True,
        interaction=InteractionUpdate(target_node_id=101, progress_delta=1.0),
    )})
    enforced = InteractionSystem.enforce(state, moved)
    assert enforced.entity_updates[1].interaction.reset is True
    assert enforced.rejections_delta == {"INTERACTION_RESET": 1}
    state = ApplyPath.apply_generation(state, enforced)
    assert state.entities[1].interaction.target_node_id is None
    assert (101 in state.ground_items) or (101 in state.corpses)
    assert not state.entities[1].inventory.items


@pytest.mark.v2_contract
def test_loot_channel_resets_when_the_target_is_gone():
    state = AuthoritativeState(tick=1, seed=42, entities={1: _hero()})
    refined, state = _tick(state, 999)
    assert refined.entity_updates[1].interaction.reset is True
    assert state.entities[1].interaction.target_node_id is None


@pytest.mark.v2_contract
def test_looting_a_purse_on_the_ground_grants_its_coin_and_no_item():
    """A purse that fell from a body (EXCH-02, ruling 61) is looted like any ground stack: its coin goes to the looter's purse."""
    purse = GroundItemState(id=101, item_id="", quantity=0, position=(0, 1), gold=7, source_entity_id=9, dropped_tick=3)
    state = AuthoritativeState(tick=1, seed=42, entities={1: _hero()}, ground_items={101: purse})
    before = total_coin(state)
    for _, state in _channel(state, 101, REQUIRED_TICKS):
        pass
    assert 101 not in state.ground_items
    assert state.entities[1].inventory.gold == 7 and not state.entities[1].inventory.items
    assert total_coin(state) == before
