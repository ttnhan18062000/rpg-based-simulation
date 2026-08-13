"""Unit tests for TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE Step 1.

Covers `StrategicUpdate.last_routing_family_set`/`last_routing_tick_set` — the dedicated
scalar-pair fields that carry a winning ADVENTURE_ROUTE candidate's route family through to
`EntityUpdate.property_updates` (see intelligence.py Steps 2/3 for the write/consume sites).
Follows `update_intents.md` Extension Rule #10: `is_noop()` on a default-constructed instance,
and `merge()`'s "set last-write-wins" semantics.
"""
from __future__ import annotations

from src.core.updates import StrategicUpdate


def test_strategic_update_last_routing_family_set_is_noop_default():
    upd = StrategicUpdate()
    assert upd.last_routing_family_set is None
    assert upd.last_routing_tick_set is None
    assert upd.is_noop() is True


def test_strategic_update_merge_last_routing_family_last_write_wins():
    a = StrategicUpdate()
    b = StrategicUpdate(last_routing_family_set="take_easy_quest", last_routing_tick_set=50)

    merged = a.merge(b)
    assert merged.last_routing_family_set == "take_easy_quest"
    assert merged.last_routing_tick_set == 50

    # A no-op update (both fields None) must leave the prior merged values unchanged.
    noop = StrategicUpdate()
    merged_again = merged.merge(noop)
    assert merged_again is merged
    assert merged_again.last_routing_family_set == "take_easy_quest"
    assert merged_again.last_routing_tick_set == 50

    # Full last-write-wins case: A already has values, B carries new ones -> B wins.
    a2 = StrategicUpdate(last_routing_family_set="recover", last_routing_tick_set=10)
    b2 = StrategicUpdate(last_routing_family_set="hunt_weak_enemy", last_routing_tick_set=20)
    merged2 = a2.merge(b2)
    assert merged2.last_routing_family_set == "hunt_weak_enemy"
    assert merged2.last_routing_tick_set == 20
