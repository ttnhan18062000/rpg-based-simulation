"""Idea 10 (Heir Assignment) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS):
a scripted lethal death (OLD_AGE, fully deterministic per LifecycleSystem.resolve_lifecycle()) with
a real pre-assigned heir must transfer the deceased's inventory to the heir, through a real
Kernel.tick_once() run -- matching this M9 batch's own established deterministic-proof precedent.
"""
from __future__ import annotations

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ItemStack
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG


def test_heir_inherits_deceased_inventory_on_old_age_death():
    deceased = (
        V2EntityBuilder(1)
        .location(0.0, 0.0)
        .lifecycle(active=True, age_ticks=999_999_999, max_age_ticks=1, heir_entity_id=2)
        .inventory(items=[ItemStack(item_id="iron_sword", quantity=1), ItemStack(item_id="healing_potion", quantity=3)])
        .build()
    )
    heir = (
        V2EntityBuilder(2)
        .location(0.0, 0.0)
        .lifecycle(active=True)
        .inventory(items=[])
        .build()
    )

    state = AuthoritativeState(tick=0, seed=42, entities={1: deceased, 2: heir})

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
    finally:
        kernel.shutdown()

    final_deceased = kernel.state.entities[1]
    final_heir = kernel.state.entities[2]

    assert final_deceased.lifecycle.active is False
    assert final_deceased.lifecycle.death_reason == "OLD_AGE"

    heir_item_ids = {stack.item_id for stack in final_heir.inventory.items}
    assert "iron_sword" in heir_item_ids, "heir must inherit the deceased's iron_sword"
    assert "healing_potion" in heir_item_ids, "heir must inherit the deceased's healing_potion"
