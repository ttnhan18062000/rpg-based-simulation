"""TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP — item_equipped/item_unequipped/
equipment_durability_changed event coverage.

Real-kernel verification was attempted first (per this ticket's own investigation.md): every
equipment-mutating producer with real narrative weight (combat durability decay,
progression-conversion equip/repair) is gated off corpus-wide (ENABLE_COMBAT_ENGAGEMENT,
ENABLE_PROGRESSION_EVOLUTION, both OFF in every shipped profile); the one live producer
(src/engine/evolution.py's goblin-kind species-evolution gear grant) requires a goblin-kind
entity reaching evolution level >= 10, confirmed absent from sandbox_world within a real
1500-tick Kernel.tick_once() loop (checked directly, not assumed). Falls back to this repo's own
precedented hand-built-state pattern, same as the sibling vitals/attributes tickets.
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tools.calibrate_simq import _load_world_state  # noqa: E402
from src.core.models.inventory import EquipSlot  # noqa: E402
from src.observability.event_extractor import EventExtractor  # noqa: E402


def _equip_fixture_states():
    state, _report = _load_world_state("sandbox_world", 42)
    eid = next(iter(state.entities.keys()))
    prior_ent = state.entities[eid]
    return state, eid, prior_ent


def test_item_equipped_fires_on_fresh_equip():
    state, eid, prior_ent = _equip_fixture_states()
    extractor = EventExtractor()
    new_eq = replace(prior_ent.equipment, slots={**prior_ent.equipment.slots, EquipSlot.MAIN_HAND: "iron_sword"})
    new_ent = replace(prior_ent, equipment=new_eq)
    new_state = replace(state, entities={**state.entities, eid: new_ent})

    events = extractor.extract(state, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "item_equipped"]
    assert len(matches) == 1
    assert matches[0].payload == {"slot": "MAIN_HAND", "item_id": "iron_sword", "previous_item_id": None}


def test_item_equipped_fires_on_swap_with_previous_item_id():
    state, eid, prior_ent = _equip_fixture_states()
    extractor = EventExtractor()
    prior_slots = {**prior_ent.equipment.slots, EquipSlot.MAIN_HAND: "rusted_sword"}
    prior_eq = replace(prior_ent.equipment, slots=prior_slots)
    prior_ent2 = replace(prior_ent, equipment=prior_eq)
    state2 = replace(state, entities={**state.entities, eid: prior_ent2})

    new_slots = {**prior_slots, EquipSlot.MAIN_HAND: "iron_sword"}
    new_eq = replace(prior_eq, slots=new_slots)
    new_ent = replace(prior_ent2, equipment=new_eq)
    new_state = replace(state2, entities={**state2.entities, eid: new_ent})

    events = extractor.extract(state2, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "item_equipped"]
    assert len(matches) == 1
    assert matches[0].payload["previous_item_id"] == "rusted_sword"
    assert matches[0].payload["item_id"] == "iron_sword"


def test_item_unequipped_fires_when_slot_cleared():
    state, eid, prior_ent = _equip_fixture_states()
    extractor = EventExtractor()
    prior_slots = {**prior_ent.equipment.slots, EquipSlot.MAIN_HAND: "iron_sword"}
    prior_eq = replace(prior_ent.equipment, slots=prior_slots)
    prior_ent2 = replace(prior_ent, equipment=prior_eq)
    state2 = replace(state, entities={**state.entities, eid: prior_ent2})

    new_slots = {**prior_slots, EquipSlot.MAIN_HAND: None}
    new_eq = replace(prior_eq, slots=new_slots)
    new_ent = replace(prior_ent2, equipment=new_eq)
    new_state = replace(state2, entities={**state2.entities, eid: new_ent})

    events = extractor.extract(state2, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "item_unequipped"]
    assert len(matches) == 1
    assert matches[0].payload == {"slot": "MAIN_HAND", "previous_item_id": "iron_sword"}


def _durability_states(old_dur, new_dur):
    state, eid, prior_ent = _equip_fixture_states()
    prior_dur = {**prior_ent.equipment.durability, EquipSlot.MAIN_HAND: old_dur}
    prior_eq = replace(prior_ent.equipment, durability=prior_dur)
    prior_ent2 = replace(prior_ent, equipment=prior_eq)
    state2 = replace(state, entities={**state.entities, eid: prior_ent2})

    new_dur_map = {**prior_dur, EquipSlot.MAIN_HAND: new_dur}
    new_eq = replace(prior_eq, durability=new_dur_map)
    new_ent = replace(prior_ent2, equipment=new_eq)
    new_state = replace(state2, entities={**state2.entities, eid: new_ent})
    return state2, new_state


def test_equipment_durability_changed_severity_info_above_50():
    state2, new_state = _durability_states(80.0, 60.0)
    extractor = EventExtractor()
    events = extractor.extract(state2, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "equipment_durability_changed"]
    assert len(matches) == 1
    assert matches[0].severity == "INFO"


def test_equipment_durability_changed_severity_warning_below_50():
    state2, new_state = _durability_states(55.0, 40.0)
    extractor = EventExtractor()
    events = extractor.extract(state2, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "equipment_durability_changed"]
    assert len(matches) == 1
    assert matches[0].severity == "WARNING"


def test_equipment_durability_changed_severity_critical_at_zero():
    state2, new_state = _durability_states(1.0, 0.0)
    extractor = EventExtractor()
    events = extractor.extract(state2, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "equipment_durability_changed"]
    assert len(matches) == 1
    assert matches[0].severity == "CRITICAL"


def test_equipment_durability_changed_severity_info_on_repair_increase():
    state2, new_state = _durability_states(10.0, 100.0)
    extractor = EventExtractor()
    events = extractor.extract(state2, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "equipment_durability_changed"]
    assert len(matches) == 1
    assert matches[0].severity == "INFO"


def test_no_event_on_zero_delta():
    state, eid, prior_ent = _equip_fixture_states()
    extractor = EventExtractor()
    same_state = replace(state, entities={**state.entities, eid: prior_ent})

    events = extractor.extract(state, same_state, None, mode=None)
    matches = [e for e in events if e.event_type in ("item_equipped", "item_unequipped", "equipment_durability_changed")]
    assert not matches, "equipment event fired with zero real delta"


def test_equipment_events_suppressed_in_light_and_long_run_modes():
    from src.observability.config import ObservabilityMode

    state, eid, prior_ent = _equip_fixture_states()
    new_eq = replace(prior_ent.equipment, slots={**prior_ent.equipment.slots, EquipSlot.MAIN_HAND: "iron_sword"})
    new_ent = replace(prior_ent, equipment=new_eq)
    new_state = replace(state, entities={**state.entities, eid: new_ent})

    extractor = EventExtractor()
    for mode in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
        events = extractor.extract(state, new_state, None, mode=mode)
        matches = [e for e in events if e.event_type == "item_equipped"]
        assert not matches, f"item_equipped fired in {mode}, should be suppressed"
