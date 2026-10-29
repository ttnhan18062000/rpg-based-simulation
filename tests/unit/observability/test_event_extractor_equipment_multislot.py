"""Equipment events when several slots change in one tick (TCK-20261028-EVENT-EXTRACTOR-CHARACTERIZATION-TESTS).

The extractor walks ``set(eq_slots) | set(prior_eq_slots)`` and ``set(eq_dur) | set(prior_eq_dur)``, sets of ``EquipSlot`` members, so the order of
the item_equipped / item_unequipped / equipment_durability_changed events follows the string hash seed. The assertions here ignore the order, so they hold
under any seed; the characterization corpus records these calls under ``PYTHONHASHSEED=0`` and pins the order they come out in.
"""
from dataclasses import replace

from src.core.models.inventory import EquipSlot
from src.observability.event_extractor import EventExtractor
from tests.unit.observability.test_event_extractor_equipment import _equip_fixture_states


def _states(prior_slots, new_slots, prior_dur=None, new_dur=None):
    state, eid, prior_ent = _equip_fixture_states()
    prior_eq = replace(prior_ent.equipment, slots=dict(prior_slots), durability=dict(prior_dur or {}))
    prior_state = replace(state, entities={**state.entities, eid: replace(prior_ent, equipment=prior_eq)})
    new_eq = replace(prior_eq, slots=dict(new_slots), durability=dict(new_dur or {}))
    new_state = replace(prior_state, entities={**prior_state.entities, eid: replace(prior_state.entities[eid], equipment=new_eq)})
    return prior_state, new_state


def _by_type(events, event_type):
    return sorted((e.payload for e in events if e.event_type == event_type), key=lambda p: p["slot"])


def test_four_slots_equipped_in_one_tick_each_emit_item_equipped():
    prior, new = _states({}, {EquipSlot.HEAD: "helm", EquipSlot.TORSO: "mail", EquipSlot.LEGS: "greaves", EquipSlot.MAIN_HAND: "sword"})
    events = EventExtractor.extract(prior, new, None, mode=None)
    assert _by_type(events, "item_equipped") == [
        {"slot": "HEAD", "item_id": "helm", "previous_item_id": None},
        {"slot": "LEGS", "item_id": "greaves", "previous_item_id": None},
        {"slot": "MAIN_HAND", "item_id": "sword", "previous_item_id": None},
        {"slot": "TORSO", "item_id": "mail", "previous_item_id": None},
    ]


def test_equip_swap_and_unequip_across_three_slots_in_one_tick():
    prior, new = _states(
        {EquipSlot.HEAD: "old_helm", EquipSlot.MAIN_HAND: "rusted_sword", EquipSlot.OFF_HAND: "buckler"},
        {EquipSlot.HEAD: "new_helm", EquipSlot.MAIN_HAND: None, EquipSlot.TORSO: "mail"},
    )
    events = EventExtractor.extract(prior, new, None, mode=None)
    assert _by_type(events, "item_equipped") == [
        {"slot": "HEAD", "item_id": "new_helm", "previous_item_id": "old_helm"},
        {"slot": "TORSO", "item_id": "mail", "previous_item_id": None},
    ]
    assert _by_type(events, "item_unequipped") == [
        {"slot": "MAIN_HAND", "previous_item_id": "rusted_sword"},
        {"slot": "OFF_HAND", "previous_item_id": "buckler"},
    ]


def test_durability_changes_in_four_slots_in_one_tick_each_emit_an_event():
    prior_dur = {EquipSlot.HEAD: 80.0, EquipSlot.TORSO: 55.0, EquipSlot.LEGS: 1.0, EquipSlot.MAIN_HAND: 10.0}
    new_dur = {EquipSlot.HEAD: 60.0, EquipSlot.TORSO: 40.0, EquipSlot.LEGS: 0.0, EquipSlot.MAIN_HAND: 100.0}
    prior, new = _states({}, {}, prior_dur, new_dur)
    events = EventExtractor.extract(prior, new, None, mode=None)
    changed = [e for e in events if e.event_type == "equipment_durability_changed"]
    assert sorted((e.payload["slot"], e.severity) for e in changed) == [
        ("HEAD", "INFO"), ("LEGS", "CRITICAL"), ("MAIN_HAND", "INFO"), ("TORSO", "WARNING"),
    ]
