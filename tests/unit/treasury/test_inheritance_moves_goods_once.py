"""An heir receives what the dead entity carried, once (EXCH-02 audit, defect b): the corpse does not keep a second copy of what the heir
was given, and the dead entity's own record does not keep a third."""
from __future__ import annotations

from dataclasses import replace

from src.core.state import InventoryComponent, ItemStack
from tests.helpers.scenario import compile_world, empty_inventories, run_scenario

ITEMS = (ItemStack("wood", 3), ItemStack("iron_ore", 2))
GOLD = 9


def _pair(state):
    humans = [i for i, e in sorted(state.entities.items()) if e.combat.alive and (e.identity.properties or {}).get("species_id") == "human"]
    return humans[0], humans[1]


def _stage(state):
    state = empty_inventories(state)  # nobody else carries the staged items, so every copy found is the staged goods
    dead, heir = _pair(state)
    d = state.entities[dead]
    d = replace(d, inventory=InventoryComponent(items=list(ITEMS), gold=GOLD),
                lifecycle=replace(d.lifecycle, age_ticks=d.lifecycle.max_age_ticks, heir_entity_id=heir))
    h = state.entities[heir]
    return replace(state, entities={**state.entities, dead: d, heir: h})


def _count(state, item_id):
    held = sum(s.quantity for e in state.entities.values() for s in e.inventory.items if s.item_id == item_id)
    on_corpses = sum(s.quantity for c in state.corpses.values() for s in c.items if s.item_id == item_id)
    return held, on_corpses


def test_the_goods_of_a_dead_entity_with_an_heir_exist_once():
    base = compile_world("frontier_living_world")
    dead, heir = _pair(base)
    run = run_scenario(_stage(base), ticks=3, observe=lambda s: s)
    final = run.final_state
    assert not final.entities[dead].combat.alive or final.entities[dead].lifecycle.death_reason is not None, "the staged entity should have died of old age"
    for item in ITEMS:
        held, corpses = _count(final, item.item_id)
        assert held + corpses == item.quantity, f"{item.item_id}: {held} carried + {corpses} on corpses, only {item.quantity} existed"
        assert sum(s.quantity for s in final.entities[heir].inventory.items if s.item_id == item.item_id) == item.quantity


def test_the_heir_takes_the_coin_and_the_dead_record_keeps_none():
    base = compile_world("frontier_living_world")
    dead, heir = _pair(base)
    final = run_scenario(_stage(base), ticks=3, observe=lambda s: s).final_state
    assert final.entities[heir].inventory.gold == GOLD
    assert final.entities[dead].inventory.gold == 0
    assert not final.entities[dead].inventory.items
